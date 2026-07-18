# voicecmd — voice recognition architecture

Grammar-constrained voice command recognition for Enso. A C++20 core drives a
pluggable recognizer backend (SAPI 5 in-process on Windows), and is exposed to
Enso as a single abi3 extension module, `voicecmdlib.pyd`.

### The layers

Bottom to top, each layer depends only on the one below it:

| Layer | CMake target | Responsibility |
|---|---|---|
| **Backend** | `voicecmd_sapi`, `FakeBackend` (header-only) | Owns the speech engine and its grammars. Turns a recognition into a `RawRecognition` — *what was said*, identified semantically — and posts it. All COM lives here, behind a pimpl. |
| **Core** | `voicecmd_core` | The `Engine`: lifecycle state machine, message queue, classification, confirmation. Portable, COM-free, Python-free. Talks to backends only through `IRecognizerBackend` / `BackendSink`. |
| **Platform** | `voicecmd_win32` | `SessionMonitor` — workstation lock/unlock notifications. Kept out of the core (not portable) and out of the backend (not a recognition concern). |
| **Binding** | `voicecmdlib` (nanobind) | The `Recognizer` facade: Python-shaped config mirrors, `UserData` ⇄ `nb::object`, and `poll_events()`. The only layer that touches CPython. |
| **Host** | `enso.contrib.voice` | Builds the grammar from Enso's registered commands, pumps events on the main-loop tick, dispatches to `CommandManager`, draws the confirmation prompt. |

### The design commitments

Three commitments explain nearly every structural decision below:

1. **Single owner.** All engine state lives on one worker thread. Every
   transition is a message on one queue. Backends and UI only *post*.
2. **Pull-mode delivery.** The native threads never call into Python. Enso
   drains events on its own main-loop tick, so a voice command runs on exactly
   the same thread as a keyboard-triggered one.
3. **One engine, swapped rulesets.** There is exactly one recognizer and one
   grammar. Everything the user can say — every enabled command, the two
   pause-control phrases, and yes/no — is a top-level rule in it. A "mode" is
   just which of those rules are currently active:

   | Ruleset | Active rules | When |
   |---|---|---|
   | `Commands` | all enabled verb rules + `stop listening` | normal listening |
   | `ResumeOnly` | `resume listening`, and nothing else | soft-paused |
   | `YesNo` | `yes` / `no`, and nothing else | confirmation prompt is up |

   Switching mode is a set of `SetRuleIdState` calls on the grammar already
   loaded — never a second recognizer. That is what keeps the microphone
   handover deterministic and avoids audio-device contention entirely.

   Spoken verbatim, the pause-control commands are:

   - **"computer stop listening"** — suspends command recognition. The mic stays
     open but the grammar shrinks to the single resume phrase.
   - **"computer resume listening"** — the only phrase recognized while paused.
     Accepted at any confidence, so a paused engine can always be recovered.

   Both take the keyword prefix (`computer` by default, configurable, and
   optional if `keyword_required` is false), exactly like command phrases.
   **"yes"** and **"no"** are the exception: they are spoken bare, with no
   keyword, because they are only ever live inside a confirmation window.

---

## 1. Layering

The core is portable, Python-free and COM-free. Windows-specific code is confined
to two leaf libraries; the binding layer is the only place that touches CPython.

```mermaid
graph TB
    subgraph host["Host — Enso (Python, main thread)"]
        subgraph plugin["Enso plugin"]
            VOICE["enso.contrib.voice<br/><i>grammar build, tick pump,<br/>command dispatch, confirm UI</i>"]
        end
        CMDMGR["CommandManager"]
        MSG["messages.displayMessage"]
        TRAY["win32 tray menu"]
    end

    subgraph binding["Binding — src/python/module.cpp"]
        NB["nanobind / STABLE_ABI<br/><b>voicecmdlib.pyd</b>"]
        RECOG["Recognizer facade<br/><i>ConfigSpec/VerbSpec mirrors,<br/>UserData ⇄ nb::object,<br/>poll_events()</i>"]
    end

    subgraph core["Core — voicecmd_core (portable, no COM, no Python)"]
        ENG["Engine<br/><i>state machine, message queue,<br/>classification, confirmation</i>"]
        EV["Event variant<br/><i>events.h</i>"]
        CFG["Config / Verb / Noun<br/><i>config.h</i>"]
        IFACE["IRecognizerBackend + BackendSink<br/><i>backend.h</i>"]
        UI["IConfirmationUI<br/><i>confirm.h — optional, null in Enso</i>"]
    end

    subgraph backends["Backends"]
        SAPI["SapiBackend<br/><i>voicecmd_sapi — pimpl, COM confined to .cpp</i>"]
        FAKE["FakeBackend<br/><i>header-only test double</i>"]
        VOSK["Vosk<br/><i>reserved</i>"]
    end

    subgraph win32["voicecmd_win32"]
        SM["SessionMonitor<br/><i>WTS lock/unlock</i>"]
    end

    OS["SAPI 5 / ISpRecognizer<br/>+ user's trained reco profile"]

    VOICE -->|"Config, Verb, Noun<br/>start/stop/pause/update_grammar"| NB
    NB --> RECOG
    RECOG -->|"owns"| ENG
    VOICE -->|"poll_events() each tick"| RECOG
    RECOG -->|"RecognitionEvent → text"| VOICE
    VOICE --> CMDMGR
    VOICE -->|"ConfirmationEvent"| MSG
    TRAY -->|"is_listening / set_listening"| VOICE

    ENG --- EV
    ENG --- CFG
    ENG -->|"create/start/stop/<br/>setActiveRuleset/updateGrammar"| IFACE
    ENG -.->|"optional"| UI
    IFACE -.->|implements| SAPI
    IFACE -.->|implements| FAKE
    IFACE -.->|planned| VOSK
    SAPI --> OS
    SAPI -->|"BackendSink.onRecognition"| ENG
    SM -->|"stop() / start()"| ENG
    RECOG -->|"owns"| SM

    classDef dim fill:#eee,stroke:#999,stroke-dasharray:3 3,color:#555
    class VOSK,UI dim
    style plugin fill:none,stroke:#888,stroke-dasharray:4 3
```

**Why `voicecmdlib` and not `voicecmd`:** an extension module shadows a same-named
`.py` in the package. The `lib` suffix keeps the native binary distinct from
`enso/contrib/voice.py` around it (same convention as `retreatlib`).

---

## 2. Threading model

Four threads, with a strict rule about who may touch what. The queue is the only
crossing point into engine state; the event list is the only crossing point out.

```mermaid
graph LR
    subgraph T1["① Enso main thread (GIL)"]
        TICK["timer tick → poll_events()"]
        RUN["cmd.run()"]
        CTRL["start / stop / pause /<br/>update_grammar"]
    end

    subgraph T2["② Engine worker (single owner)"]
        LOOP["workerLoop()<br/>wait / wait_until(confirm_deadline)"]
        HANDLE["handle(Msg)<br/><i>the ONLY mutator of engine state</i>"]
    end

    subgraph T3["③ SAPI listener thread (own COM MTA)"]
        WAIT["WaitForMultipleObjects<br/>{stop_event, notify}"]
        DRAINE["drainEvents() → handleResult()"]
    end

    subgraph T4["④ Session monitor thread"]
        PUMP["message-only HWND<br/>GetMessage pump"]
    end

    QUEUE[["std::deque&lt;Msg&gt;<br/>qmx_ + qcv_"]]
    EVENTS[["std::vector&lt;Event&gt;<br/>emx_"]]

    CTRL -->|"post() → future&lt;void&gt;<br/>(GIL released while waiting)"| QUEUE
    DRAINE -->|"onRecognition / onBackendEnded / onLog<br/><i>enqueue only, returns at once</i>"| QUEUE
    PUMP -->|"WM_WTSSESSION_CHANGE<br/>fire-and-forget stop()/start()"| QUEUE
    QUEUE --> LOOP --> HANDLE
    HANDLE -->|"emit()"| EVENTS
    HANDLE -->|"backend_-&gt;* calls"| T3
    EVENTS -->|"drain() — swap under lock"| TICK
    TICK --> RUN

    style QUEUE fill:#fff3cd,stroke:#856404
    style EVENTS fill:#d4edda,stroke:#155724
```

Invariants worth stating explicitly:

- Every `backend_->…` call and every mutation of `created_ / started_ /
  confirming_ / pending_` happens on ② and nowhere else.
- ③ and ④ never block on ②. The session-monitor callback drops its future on the
  floor deliberately — it comes from a `promise`, not `std::async`, so dropping
  it never blocks and never stalls the message pump.
- Push delivery (`event_sink_`) is invoked *outside* every internal lock, and a
  throwing handler is swallowed so the worker can never die on host code.
- Python callbacks fire only inside `poll_events()`, on ①, with the GIL already
  held. There is no cross-thread GIL acquisition anywhere on the hot path.

---

## 3. Engine state machine

`Config → Engine` starts the worker immediately but does **not** create the
backend. `Idle` means constructed-but-not-realized; `Stopped` retains the engine
and compiled grammars so a re-start is cheap.

```mermaid
stateDiagram-v2
    [*] --> Idle : Engine(cfg, backend, ui)<br/>worker thread starts

    Idle --> Listening : start()<br/><i>ensureCreated() → backend.create()<br/>setActiveRuleset(Commands) → backend.start()</i>
    Listening --> SoftPaused : pause() or "stop listening"<br/><i>ruleset → ResumeOnly</i>
    SoftPaused --> Listening : resume() / start() / "resume listening"<br/><i>ruleset → Commands</i>

    Listening --> Stopped : stop()<br/><i>backend.stop(), engine + grammars RETAINED</i>
    SoftPaused --> Stopped : stop()
    Stopped --> Listening : start()<br/><i>cheap: no re-create</i>

    Listening --> Restarting : SPEI_END_SR_STREAM<br/>(unexpected, !host_stopping_)
    Restarting --> Idle : doStop(keep_engine=false)<br/><i>dispose()</i>
    Restarting --> Listening : after restart_delay_sec back-off<br/><i>interruptible wait, close() cuts it short</i>

    Listening --> Idle : shutdown()<br/><i>dispose(), engine released</i>
    Stopped --> Idle : shutdown()

    Idle --> Closed : close()
    Listening --> Closed : close()
    Stopped --> Closed : close()
    SoftPaused --> Closed : close()
    Closed --> [*] : worker joined (terminal)

    note right of SoftPaused
        Mic stays OPEN. Grammar reduced to
        "resume listening" only. This is the
        tray toggle and the spoken pause.
    end note

    note right of Stopped
        Mic RELEASED (SPRST_INACTIVE_WITH_PURGE).
        This is what the session lock uses —
        a soft pause would leave the mic live
        at the lock screen.
    end note
```

`Starting` / `Stopping` / `ShuttingDown` exist in the `State` enum as
transitional labels; the current transitions are short enough to be atomic on the
worker, so they are not dwelt in.

---

## 4. Grammar and ruleset swapping

One `ISpRecoGrammar` holds every rule. Semantic identity is read from the matched
**rule id** and from `SPPROPERTYINFO` tags — never from word positions — so
multi-word verbs, multi-word nouns and the optional keyword prefix all work
without any string slicing.

```mermaid
graph TB
    subgraph G["Single dynamic grammar (kGrammarId = 1)"]
        direction TB
        subgraph VR["Verb rules — id = kVerbBase(1000) + index"]
            V0["'open' → prop V=0<br/>├ 'notepad' → prop N=0<br/>├ 'chrome'  → prop N=1<br/>└ …up to 300 nouns"]
            V1["'help' → prop V=1<br/><i>(verb-only, no nouns)</i>"]
        end
        C1["__ctl_stop__ (id 1)<br/>'stop listening' → prop C=1"]
        C2["__ctl_resume__ (id 2)<br/>'resume listening' → prop C=2"]
        Y["__yes__ (id 3) → prop Y=1"]
        N["__no__ (id 4) → prop Y=2"]
        GB["__garbage__ (id 5)<br/>SPRULETRANS_WILDCARD, weight 0.30<br/><i>opt-in: use_garbage_rule</i>"]
    end

    KW["keyword prefix state<br/>'computer' + optional ε transition<br/><i>prepended to verb & control rules;<br/>yes/no are spoken bare</i>"]
    KW -.-> VR
    KW -.-> C1
    KW -.-> C2

    style GB fill:#eee,stroke:#999,stroke-dasharray:3 3
```

A **ruleset** is a named subset of those rules that is active at one moment.
`setActiveRuleset(r)` simply walks the rule ids and calls `SetRuleIdState` with
`SPRS_ACTIVE` or `SPRS_INACTIVE` on each — nothing is created, compiled or
destroyed, so the swap is effectively free and cannot fail halfway.

Each ruleset exists to make one class of misrecognition *structurally
impossible* rather than filtering it after the fact:

- **`Commands`** — the normal state. Verb rules are live, and so is
  `stop listening`. `resume listening` is deliberately **off**: saying it while
  already listening should do nothing, and leaving it active would let it
  compete with real commands for a match.
- **`ResumeOnly`** — the soft pause. Every verb rule is off, so a command spoken
  while paused cannot possibly be matched; the engine has nothing to match it
  *to*. Only `resume listening` remains.
- **`YesNo`** — the confirmation window. Both command and control rules are off,
  so an answer can never be misheard as a new command, and a command spoken
  during the prompt cannot queue up behind it. Only `yes` and `no` are live.

The `__garbage__` wildcard, when enabled, stays active in all three — its job is
to absorb out-of-grammar speech in whatever mode the engine is in.

```mermaid
graph LR
    subgraph RS["Ruleset → which rules are ACTIVE"]
        direction TB
        R1["<b>Commands</b><br/>✅ all enabled verb rules<br/>✅ __ctl_stop__<br/>❌ __ctl_resume__<br/>❌ yes / no"]
        R2["<b>ResumeOnly</b> (soft-paused)<br/>❌ verb rules<br/>❌ __ctl_stop__<br/>✅ __ctl_resume__<br/>❌ yes / no"]
        R3["<b>YesNo</b> (confirming)<br/>❌ verb rules<br/>❌ both control rules<br/>✅ __yes__ / __no__"]
    end
    R1 -->|"pause() / 'stop listening'"| R2
    R2 -->|"resume() / 'resume listening'"| R1
    R1 -->|"beginConfirmation()"| R3
    R3 -->|"resolved / timed out / stop()"| R1
```

`updateGrammar()` (fired when the webui voice checkboxes change) clears the verb
rule bodies, rebuilds them, re-commits and reapplies `Commands` — the recognizer,
the context and the audio binding all survive untouched.

---

## 5. Recognition path and classification

`handleResult()` on the listener thread turns a SAPI phrase into a
`RawRecognition` — kind, verb/noun indices, resolved text, normalized confidence
— and posts it. `Engine::classify()` on the worker decides what it means.

```mermaid
flowchart TD
    A["SPEI_RECOGNITION /<br/>SPEI_FALSE_RECOGNITION"] --> B["GetPhrase() → Rule.ulId<br/>mapConfidence(tri-level, SREngineConfidence) → 0..1"]
    B --> C{"rule id?"}
    C -->|"≥ 1000"| D["kind=Command<br/>verb_index = id − 1000<br/>noun_index = findProp('N')<br/>text = CONFIGURED strings (no keyword)"]
    C -->|"1 / 2"| E["kind=Control<br/>StopListening / ResumeListening"]
    C -->|"3 / 4"| F["kind=YesNo<br/>Yes / No"]
    C -->|"other"| G["kind=Garbage<br/>text = GetText()"]
    D & E & F & G --> H[["sink→onRecognition() — enqueue, return"]]

    H ==> I["<b>Engine::classify()</b> — worker thread"]
    I --> J{"kind == Control?"}
    J -->|"StopListening"| K["ruleset→ResumeOnly<br/>state→SoftPaused<br/>emit PauseChangeEvent{true}"]
    J -->|"ResumeListening"| L["ruleset→Commands<br/>state→Listening<br/>emit PauseChangeEvent{false}<br/><i>accepted at ANY confidence</i>"]
    J -->|no| M{"confirming_?"}

    M -->|yes| N{"YesNo?"}
    N -->|"Yes ≥ confirm_yes_confidence"| O["resolveConfirmation(true)"]
    N -->|"Yes below threshold"| P["emit RejectionEvent<br/><i>keep listening</i>"]
    N -->|"No"| Q["resolveConfirmation(false)<br/><i>any confidence</i>"]
    N -->|"anything else"| P

    M -->|no| R{"state == SoftPaused?"}
    R -->|yes| P
    R -->|no| S{"kind == Command<br/>and verb_index valid?"}
    S -->|no| P
    S -->|yes| T{"cfg.trust_grammar_match?"}

    T -->|"true (default)"| U["need_confirm = verb.confirm ‖ noun.confirm<br/><i>grammar match IS the accept signal;<br/>confidence reported, not gated</i>"]
    T -->|"false"| V{"confidence bands"}
    V -->|"below reject_confidence"| P
    V -->|"≥ reject"| W["need_confirm = verb.confirm ‖ noun.confirm<br/>‖ confidence &lt; (noun.min_confidence<br/>?? accept_confidence)"]

    U & W --> X{"need_confirm?"}
    X -->|yes| Y["beginConfirmation()"]
    X -->|no| Z["emit <b>RecognitionEvent</b><br/>verb, noun, text, confidence,<br/>verb_data/noun_data, confirmed=true"]

    style Z fill:#d4edda,stroke:#155724
    style Y fill:#fff3cd,stroke:#856404
    style P fill:#f8d7da,stroke:#721c24
```

**Why `trust_grammar_match` defaults to true:** SAPI's per-recognition confidence
is unreliable for command-and-control grammars — it reports correct, fully-matched
command phrases at the same low confidence as noise. The required keyword plus the
closed grammar are the precision guard instead. Set it false for a backend with a
confidence signal worth gating on (Vosk).

**Why the in-process recognizer still gets good confidence:** `create()` explicitly
loads the default SR engine token *and the user's trained recognition profile*
(`SPCAT_RECOGNIZERS` / `SPCAT_RECOPROFILES`) into `CLSID_SpInprocRecognizer`. That
buys the calibration of the shared recognizer without launching the Windows Speech
Recognition app. `shared_recognizer=true` switches to `CLSID_SpSharedRecognizer`
if the system-wide engine is wanted instead.

---

## 6. Confirmation

Confirmation is *host-rendered*: the engine emits bracketing events and owns the
timeout; `IConfirmationUI` is optional and Enso passes null. The answer is spoken,
so there is nothing to click.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant S as SAPI listener
    participant W as Engine worker
    participant B as Backend
    participant P as poll_events() (Enso tick)
    participant E as enso.contrib.voice

    U->>S: "computer shutdown"
    S->>W: onRecognition(Command, verb.confirm=true)
    activate W
    W->>W: beginConfirmation(pending)
    W->>B: setActiveRuleset(YesNo)
    Note over B: command rules OFF —<br/>normal listening fully suspended
    W->>W: confirm_deadline_ = now + confirm_timeout_sec
    W-->>P: emit ConfirmationEvent{active=true, phrase}
    deactivate W
    P->>E: _renderConfirmation(event)
    E->>E: displayMessage("shutdown?<br/>say yes or no")

    alt spoken "yes" ≥ confirm_yes_confidence
        U->>S: "yes"
        S->>W: onRecognition(YesNo, Yes)
        W->>W: resolveConfirmation(true) → endConfirmation()
        W-->>P: emit ConfirmationEvent{active=false}
        W->>B: setActiveRuleset(Commands)
        W-->>P: emit RecognitionEvent{confirmed=true}
        P->>E: _hideConfirmation() → triggerEvent("dismissal")
        P->>E: _handleRecognition() → CommandManager.getCommand(text).run()
    else spoken "no" (any confidence)
        U->>S: "no"
        S->>W: onRecognition(YesNo, No)
        W->>W: resolveConfirmation(false) → endConfirmation()
        W-->>P: emit ConfirmationEvent{active=false}
        W->>B: setActiveRuleset(Commands)
        Note over W: command dropped SILENTLY —<br/>no RecognitionEvent
        P->>E: _hideConfirmation()
    else timeout (wait_until wakes with empty queue)
        W->>W: Cmd::ConfirmTimeout → endConfirmation()
        W-->>P: emit ConfirmationEvent{active=false}
        W->>B: setActiveRuleset(Commands)
        P->>E: _hideConfirmation()
    else host stop() / close() mid-prompt
        W->>W: doStop() → endConfirmation()
        W-->>P: emit ConfirmationEvent{active=false}
    end
```

Every exit from `confirming_` funnels through `endConfirmation()` — the one place
that clears the flag, hides any attached UI and emits the closing event — so the
UI and the host-visible event can never drift apart. Enso's `_shutdown()` calls
`_hideConfirmation()` *before* checking whether the engine still exists, because a
prompt left up at exit would otherwise outlive the process that can dismiss it.

---

## 7. Session lock

```mermaid
sequenceDiagram
    participant OS as Windows WTS
    participant M as SessionMonitor thread
    participant W as Engine worker
    participant B as SAPI backend

    Note over M: message-only HWND<br/>WTSRegisterSessionNotification<br/>NOTIFY_FOR_THIS_SESSION<br/>callback ptr in GWLP_USERDATA

    OS ->> M: WM_WTSSESSION_CHANGE, WTS_SESSION_LOCK
    M ->> W: Engine.stop
    Note over M: future dropped on purpose —<br/>it comes from a promise, so this<br/>never blocks the message pump
    W ->> B: backend.stop, SPRST_INACTIVE_WITH_PURGE
    Note over B: microphone RELEASED —<br/>engine and compiled grammars retained

    OS ->> M: WTS_SESSION_UNLOCK
    M ->> W: Engine.start
    W ->> B: setActiveRuleset Commands, then backend.start
    Note over B: cheap re-start — no create,<br/>no grammar rebuild
```

A hard `stop()` is the only correct answer here. `pause()` keeps the recognizer
and the microphone alive and leaves "resume listening" in the grammar — live to
anyone standing at the lock screen.

Teardown order matters: `monitor_` is declared *after* `eng_` so it is destroyed
first, and `close()` resets it explicitly, so a lock event arriving mid-shutdown
can never post to a dying engine. The destructor posts `WM_QUIT` to the monitor
thread and joins it.

---

## 8. Event delivery into Enso

Everything the engine wants to tell the host is one `Event` — a
`std::variant` of six alternatives — and everything goes out through a single
funnel, `Engine::emit()`. That funnel feeds two independent channels:

- **Pull (what Enso uses).** `emit()` appends to `events_` under `emx_`. The host
  calls `drain()`, which *swaps* the vector out under the lock and hands back the
  whole batch — O(1), no copying, and the engine starts accumulating into a fresh
  one immediately.
- **Push (optional).** `emit()` also invokes `event_sink_`, if one is set, on the
  worker thread — *outside* every internal lock, with a `catch (...)` around it so
  a throwing handler can never kill the worker. Enso does not set one; it exists
  for hosts that want immediate notification and are prepared to handle it on a
  foreign thread.

The pull channel is what makes commitment #2 work. `Recognizer::poll_events()`
drains, converts each variant alternative to its Python mirror via `toPy()`,
*and* fires any registered `on_*` callback — all on the caller's thread with the
GIL already held. So a recognition that arrived on the SAPI listener thread at
some arbitrary moment does not touch Python until Enso's `"timer"` responder
picks it up, and `cmd.run()` then executes on the same thread as a
keyboard-triggered command. No cross-thread GIL acquisition happens anywhere on
this path.

Two consequences of the buffer sitting between the threads. **Latency** is
bounded by the tick interval, not by recognition — the engine never waits on the
host. **Ordering is FIFO and load-bearing**: `resolveConfirmation()` emits the
closing `ConfirmationEvent` *before* the `RecognitionEvent`, so within a single
`poll_events()` batch Enso is guaranteed to retract the prompt before it runs the
command it was asking about. The queue is unbounded, so a host that stops polling
accumulates rather than drops — acceptable here because the only consumer is a
tick that runs as long as Enso is alive.

On the Python side `_onTick` is a flat `isinstance` dispatch over the batch, with
one piece of work ahead of it: if `config.VOICE_COMMANDS_CHANGED` is set (the
webui toggled a voice checkbox), the grammar is rebuilt and pushed down before
the batch is drained.

```mermaid
graph LR
    subgraph V["std::variant&lt;Event&gt;"]
        E1["RecognitionEvent<br/>verb, noun, text, confidence,<br/>verb_data, noun_data, confirmed"]
        E2["RejectionEvent<br/>text, confidence"]
        E3["StateChangeEvent<br/>old_state, new_state"]
        E4["PauseChangeEvent<br/>paused"]
        E5["ConfirmationEvent<br/>active, phrase"]
        E6["LogEvent<br/>level, message"]
    end

    E1 --> D[["Engine::emit()<br/>→ events_ (pull)<br/>→ event_sink_ (push, optional)"]]
    E2 --> D
    E3 --> D
    E4 --> D
    E5 --> D
    E6 --> D

    D -->|"drain() swaps the vector"| PE["Recognizer::poll_events()<br/><i>caller's thread, GIL held</i>"]
    PE -->|"toPy(): variant visit → nb::cast"| PY["Python event objects"]
    PE -->|"callbackFor(e.index())"| CB["on_recognized / on_rejected /<br/>on_state_change / on_pause_change /<br/>on_confirmation / on_log"]
    PY --> TICK["_onTick(msPassed) — isinstance dispatch"]

    TICK --> R1["RecognitionEvent → CommandManager.getCommand(text).run()"]
    TICK --> R2["ConfirmationEvent → displayMessage / dismissal"]
    TICK --> R3["Rejection/State/Log → VOICE_DEBUG console"]

    style D fill:#d4edda,stroke:#155724
```

Two details that are load-bearing:

- **`callbackFor()` resolves the variant index at compile time**
  (`variantIndex<T, Event>()`), not from hard-coded ordinals. Inserting a new
  alternative into `Event` therefore cannot silently reroute callbacks to the
  wrong handler.
- **`UserData` is a `shared_ptr<void>` whose deleter re-acquires the GIL**, since
  a grammar replacement can drop the last reference to a Python object on the
  worker thread. The core never inspects the payload; Enso stores the original
  command expression there and gets it back on every event.
- **`_onTick` catches everything.** `EventManager.onTick()` has no exception
  handling of its own, so an escape would propagate through the native
  `InputManager` callback and take down the whole Enso event loop.

---

## 9. Host integration (Enso)

```mermaid
graph TB
    WEBUI["webui commands page<br/>🎤 voice · 👂 voice-only · 🆗 confirm"] -->|"GET /api/enso/commands/voice/*"| CFG["config.VOICE_COMMANDS<br/>VOICE_ONLY_COMMANDS<br/>VOICE_CONFIRM_COMMANDS<br/>VOICE_COMMANDS_CHANGED"]
    CFG -->|"persisted"| USERCFG["~/.enso/enso.cfg<br/><i>usercfg LIST_CONFIG_KEYS</i>"]
    CFG -->|"dirty flag read on tick"| TICK["_onTick → update_grammar(_buildVerbs())"]

    LOAD["load() — plugin, after scriptotron<br/>so all commands are registered"] --> BV["_buildVerbs()"]
    CMDS["CommandManager.getCommands()"] --> BV
    BV -->|"'open {object}' → Verb('open')<br/>+ Noun per getCommandList() entry<br/>(capped at 300)"| GRAM["Config.verbs"]
    GRAM --> REC["Recognizer(cfg).start()"]
    LOAD -->|"atexit.register"| SD["_shutdown() → close() (blocking)"]
    LOAD -->|"registerResponder('timer')"| TICK

    TRAY["tray: &Listen (checkable)"] -->|"is_listening() / set_listening()"| API["State.Listening ⇄ start()/pause()"]

    MISSING["ImportError: voicecmdlib.pyd absent"] -.->|"log + no-op"| DEGRADE["plugin degrades gracefully;<br/>later plugins still load"]

    style DEGRADE fill:#f8f9fa,stroke:#ccc
```

`set_listening(True)` calls `start()` rather than `resume()` on purpose:
`resume()` only lifts a soft pause, while `start()` also covers the engine having
been stopped outright — which is exactly what the session lock does.

The `.pyd` is an optional install component (NSIS `Section /o "Voice Recognition"`),
so its absence must be survivable: `voice.py` imports it defensively and no-ops,
because `plugins.py` logs *and re-raises*, which would otherwise abort every
plugin queued after it.

---

## 10. Build

```mermaid
graph TB
    CORE["voicecmd_core (STATIC)<br/>src/core/engine.cpp<br/>C++20, /W4 /permissive-"]
    SAPILIB["voicecmd_sapi (STATIC)<br/>+ ole32 oleaut32<br/><i>GUIDs via initguid.h — no sapi.lib</i>"]
    WIN32LIB["voicecmd_win32 (STATIC)<br/>+ wtsapi32"]
    TESTS["voicecmd_tests<br/>core + FakeBackend<br/><i>76 checks</i>"]
    SMOKE["voicecmd_sapi_smoke<br/><i>link + runtime check</i>"]
    PYD["<b>voicecmdlib</b> (nanobind_add_module)<br/>STABLE_ABI + NB_STATIC"]
    DEPLOY["POST_BUILD → enso/enso/contrib/voicecmdlib.pyd<br/><i>non-fatal if Enso holds the file</i>"]

    CORE --> SAPILIB --> PYD
    CORE --> WIN32LIB --> PYD
    CORE --> PYD --> DEPLOY
    CORE --> TESTS
    SAPILIB --> SMOKE

    D1["VOICECMD_HAS_SAPI=1"] -.-> PYD
    D2["VOICECMD_HAS_SESSION_MONITOR=1"] -.-> PYD
```

`build.ps1` is machine-independent by construction: Visual Studio and its bundled
CMake are located with **vswhere**; the target interpreter is Enso's own bundled
Python found *relative to the script*, passed as `-DPython_ROOT_DIR` (an embedded
distribution has no registry entry, so `find_package(Python)` cannot locate it
otherwise); and nanobind — a build-time source dependency — is probed across
candidate interpreters and otherwise auto-provisioned at a pinned version into
`build-msvc\.tools`.

```
.\build.ps1              # incremental build + deploy
.\build.ps1 -Configure   # re-run cmake configure (after CMakeLists edits)
.\build.ps1 -StopEnso    # close a running Enso so the .pyd isn't locked
.\build.ps1 -Tests       # build and run the core unit tests
```

**nanobind, not pybind11:** pybind11 under `Py_LIMITED_API` triggers an internal
compiler error on MSVC 14.44. Note that abi3 is *forward*-compatible only — the
binary is built against Enso's bundled 3.14 headers and is not loadable on an
older interpreter, which is fine given it only ever loads inside Enso.

---

## 11. Testing

`FakeBackend` is a header-only `IRecognizerBackend` with atomic counters and a
`feed()` / `endUnexpectedly()` interface, standing in for the SAPI callback
thread. It needs no audio, no COM and no host, so the entire state machine —
lifecycle transitions, ruleset swaps, classification bands, confirmation
begin/resolve/timeout/stop, and unexpected-end auto-recovery — is exercised
deterministically by `voicecmd_tests`. `Engine::sync()` provides the FIFO barrier
that makes those assertions race-free: it resolves only once every message queued
before it has been handled.
