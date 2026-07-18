// voicecmd — single-owner lifecycle engine implementation.
//
// Threading invariant: every backend_ method (create/updateGrammar/
// setActiveRuleset/start/stop/dispose) and every mutation of engine state runs
// ONLY on the worker thread. Backend callbacks (onRecognition/onBackendEnded/
// onLog) and the confirmation UI resolver only enqueue messages.
#include "voicecmd/engine.h"

#include <chrono>
#include <exception>
#include <utility>

namespace voicecmd {

namespace {
std::chrono::steady_clock::duration dur(double seconds) {
    using namespace std::chrono;
    return duration_cast<steady_clock::duration>(duration<double>(seconds));
}
}  // namespace

const char* to_string(State s) {
    switch (s) {
        case State::Idle: return "Idle";
        case State::Starting: return "Starting";
        case State::Listening: return "Listening";
        case State::SoftPaused: return "SoftPaused";
        case State::Stopping: return "Stopping";
        case State::Stopped: return "Stopped";
        case State::Restarting: return "Restarting";
        case State::ShuttingDown: return "ShuttingDown";
        case State::Closed: return "Closed";
    }
    return "?";
}

const char* to_string(LogLevel l) {
    switch (l) {
        case LogLevel::Debug: return "debug";
        case LogLevel::Info: return "info";
        case LogLevel::Warning: return "warning";
        case LogLevel::Error: return "error";
    }
    return "?";
}

Engine::Engine(Config cfg, std::unique_ptr<IRecognizerBackend> backend,
               IConfirmationUI* ui)
    : cfg_(std::move(cfg)), backend_(std::move(backend)), ui_(ui) {
    worker_ = std::thread([this] { workerLoop(); });
}

Engine::~Engine() { close(); }

// ---- public control API ---------------------------------------------------

std::future<void> Engine::post(Cmd cmd) {
    auto p = std::make_shared<std::promise<void>>();
    auto f = p->get_future();
    Msg m;
    m.cmd = cmd;
    m.done = p;
    postMsg(std::move(m));
    return f;
}

std::future<void> Engine::start() { return post(Cmd::Start); }
std::future<void> Engine::stop() { return post(Cmd::Stop); }
std::future<void> Engine::pause() { return post(Cmd::Pause); }
std::future<void> Engine::resume() { return post(Cmd::Resume); }
std::future<void> Engine::restart() { return post(Cmd::Restart); }
std::future<void> Engine::shutdown() { return post(Cmd::Shutdown); }
std::future<void> Engine::sync() { return post(Cmd::Sync); }

std::future<void> Engine::updateGrammar(std::vector<Verb> verbs) {
    auto p = std::make_shared<std::promise<void>>();
    auto f = p->get_future();
    Msg m;
    m.cmd = Cmd::UpdateGrammar;
    m.verbs = std::move(verbs);
    m.done = p;
    postMsg(std::move(m));
    return f;
}

void Engine::close() {
    if (!worker_.joinable()) return;
    close_requested_.store(true, std::memory_order_release);
    Msg m;
    m.cmd = Cmd::Close;
    postMsg(std::move(m));
    worker_.join();
}

// ---- delivery -------------------------------------------------------------

std::vector<Event> Engine::drain() {
    std::vector<Event> out;
    std::lock_guard<std::mutex> lk(emx_);
    out.swap(events_);
    return out;
}

void Engine::setEventSink(std::function<void(const Event&)> cb) {
    std::lock_guard<std::mutex> lk(emx_);
    event_sink_ = std::move(cb);
}

void Engine::emit(Event e) {
    std::function<void(const Event&)> sink;
    {
        std::lock_guard<std::mutex> lk(emx_);
        events_.push_back(e);
        sink = event_sink_;
    }
    // Push delivery happens OUTSIDE every internal lock. A throwing handler is
    // swallowed here so the worker can never crash on host code.
    if (sink) {
        try {
            sink(e);
        } catch (...) {
        }
    }
}

// ---- BackendSink (backend callback thread) --------------------------------

void Engine::onRecognition(RawRecognition r) {
    Msg m;
    m.cmd = Cmd::Recognition;
    m.raw = std::move(r);
    postMsg(std::move(m));
}

void Engine::onBackendEnded() {
    Msg m;
    m.cmd = Cmd::BackendEnded;
    postMsg(std::move(m));
}

void Engine::onLog(LogLevel level, std::string msg) {
    Msg m;
    m.cmd = Cmd::Log;
    m.level = level;
    m.text = std::move(msg);
    postMsg(std::move(m));
}

// ---- queue ----------------------------------------------------------------

void Engine::postMsg(Msg m) {
    {
        std::lock_guard<std::mutex> lk(qmx_);
        queue_.push_back(std::move(m));
    }
    qcv_.notify_all();
}

void Engine::workerLoop() {
    for (;;) {
        Msg m;
        bool have = false;
        {
            std::unique_lock<std::mutex> lk(qmx_);
            auto ready = [this] { return !queue_.empty(); };
            if (confirming_) {
                qcv_.wait_until(lk, confirm_deadline_, ready);
            } else {
                qcv_.wait(lk, ready);
            }
            if (!queue_.empty()) {
                m = std::move(queue_.front());
                queue_.pop_front();
                have = true;
            }
        }
        if (!have) {
            // Woke with no message: the only timed wakeup is the confirm deadline.
            if (confirming_ && Clock::now() >= confirm_deadline_) {
                Msg t;
                t.cmd = Cmd::ConfirmTimeout;
                handle(t);
            }
            continue;
        }
        if (m.cmd == Cmd::Close) {
            handle(m);
            break;
        }
        handle(m);
    }
}

// ---- message dispatch (worker thread) -------------------------------------

void Engine::handle(Msg& m) {
    auto ok = [&] { if (m.done) m.done->set_value(); };
    auto err = [&] {
        if (m.done) {
            try {
                m.done->set_exception(std::current_exception());
            } catch (...) {
            }
        }
    };
    switch (m.cmd) {
        case Cmd::Start:
            try { doStart(); ok(); } catch (...) { err(); }
            break;
        case Cmd::Stop:
            try { doStop(/*keep_engine=*/true); ok(); } catch (...) { err(); }
            break;
        case Cmd::Pause:
            try {
                if (started_ && state() != State::SoftPaused) {
                    backend_->setActiveRuleset(Ruleset::ResumeOnly);
                    setState(State::SoftPaused);
                    emit(PauseChangeEvent{true});
                }
                ok();
            } catch (...) { err(); }
            break;
        case Cmd::Resume:
            try {
                if (state() == State::SoftPaused) {
                    backend_->setActiveRuleset(Ruleset::Commands);
                    setState(State::Listening);
                    emit(PauseChangeEvent{false});
                }
                ok();
            } catch (...) { err(); }
            break;
        case Cmd::Restart:
            try { doRestart(); ok(); } catch (...) { err(); }
            break;
        case Cmd::Shutdown:
            try { doShutdown(); ok(); } catch (...) { err(); }
            break;
        case Cmd::UpdateGrammar:
            try {
                if (created_) backend_->updateGrammar(m.verbs);
                cfg_.verbs = std::move(m.verbs);
                ok();
            } catch (...) { err(); }
            break;
        case Cmd::Close:
            doStop(/*keep_engine=*/false);
            setState(State::Closed);
            break;
        case Cmd::Recognition:
            classify(m.raw);
            break;
        case Cmd::BackendEnded:
            if (!host_stopping_ && started_) {
                log(LogLevel::Warning, "recognition ended unexpectedly; restarting");
                doRestart();
            }
            break;
        case Cmd::ConfirmResolve:
            resolveConfirmation(m.confirm_yes);
            break;
        case Cmd::ConfirmTimeout:
            if (confirming_) {
                endConfirmation();
                if (created_) backend_->setActiveRuleset(Ruleset::Commands);
                pending_ = RawRecognition{};
                log(LogLevel::Info, "confirmation timed out; command dropped");
            }
            break;
        case Cmd::Log:
            emit(LogEvent{m.level, std::move(m.text)});
            break;
        case Cmd::Sync:
            ok();
            break;
    }
}

// ---- transitions (worker thread only) -------------------------------------

void Engine::ensureCreated() {
    if (created_) return;
    backend_->create(cfg_, this);
    created_ = true;
}

void Engine::doStart() {
    host_stopping_ = false;
    if (state() == State::SoftPaused) {
        backend_->setActiveRuleset(Ruleset::Commands);
        setState(State::Listening);
        emit(PauseChangeEvent{false});
        return;
    }
    if (started_) return;
    ensureCreated();
    backend_->setActiveRuleset(Ruleset::Commands);
    backend_->start();
    started_ = true;
    setState(State::Listening);
}

void Engine::doStop(bool keep_engine) {
    host_stopping_ = true;
    if (confirming_) {
        endConfirmation();
        pending_ = RawRecognition{};
    }
    if (started_) {
        backend_->stop();
        started_ = false;
    }
    if (!keep_engine && created_) {
        backend_->dispose();
        created_ = false;
    }
    setState(keep_engine ? State::Stopped : State::Idle);
}

void Engine::doShutdown() { doStop(/*keep_engine=*/false); }

void Engine::doRestart() {
    doStop(/*keep_engine=*/false);
    setState(State::Restarting);
    // Interruptible back-off (proper timed wait, never a spin-wait) so the audio
    // device can release. close() cuts it short.
    {
        std::unique_lock<std::mutex> lk(qmx_);
        qcv_.wait_for(lk, dur(cfg_.restart_delay_sec),
                      [this] { return close_requested_.load(std::memory_order_acquire); });
    }
    if (close_requested_.load(std::memory_order_acquire)) return;
    host_stopping_ = false;
    doStart();
}

// ---- recognition classification -------------------------------------------

void Engine::classify(const RawRecognition& r) {
    // Control phrases are checked before everything else.
    if (r.kind == RawKind::Control) {
        if (r.control == ControlPhrase::StopListening) {
            if (started_ && state() != State::SoftPaused) {
                backend_->setActiveRuleset(Ruleset::ResumeOnly);
                setState(State::SoftPaused);
                emit(PauseChangeEvent{true});
            }
            return;
        }
        if (r.control == ControlPhrase::ResumeListening) {
            // No lockout: accepted at any confidence.
            if (state() == State::SoftPaused) {
                backend_->setActiveRuleset(Ruleset::Commands);
                setState(State::Listening);
                emit(PauseChangeEvent{false});
            }
            return;
        }
    }

    if (confirming_) {
        if (r.kind == RawKind::YesNo) {
            if (r.answer == YesNoAnswer::Yes) {
                if (r.confidence >= cfg_.confirm_yes_confidence) {
                    resolveConfirmation(true);
                } else {
                    // Gated "yes" failed: keep listening, report for calibration.
                    if (cfg_.rejection_events) emit(RejectionEvent{r.text, r.confidence});
                }
            } else if (r.answer == YesNoAnswer::No) {
                resolveConfirmation(false);  // accepted at any confidence
            }
            return;
        }
        if (cfg_.rejection_events) emit(RejectionEvent{r.text, r.confidence});
        return;
    }

    if (state() == State::SoftPaused) {
        // Only ResumeOnly is active; anything else is garbage.
        if (cfg_.rejection_events) emit(RejectionEvent{r.text, r.confidence});
        return;
    }

    if (r.kind != RawKind::Command || r.verb_index < 0 ||
        r.verb_index >= static_cast<int>(cfg_.verbs.size())) {
        if (cfg_.rejection_events) emit(RejectionEvent{r.text, r.confidence});
        return;
    }

    const Verb& v = cfg_.verbs[r.verb_index];
    const Noun* n = (r.noun_index >= 0 &&
                     r.noun_index < static_cast<int>(v.nouns.size()))
                        ? &v.nouns[r.noun_index]
                        : nullptr;

    bool need_confirm;
    if (cfg_.trust_grammar_match) {
        // Grammar match is the accept signal; confidence is reported (telemetry)
        // but does not gate. Only explicit confirm flags force confirmation.
        need_confirm = v.confirm || (n && n->confirm);
    } else {
        // Three-band confidence gating (for backends with reliable confidence).
        if (r.confidence < cfg_.reject_confidence) {
            if (cfg_.rejection_events) emit(RejectionEvent{r.text, r.confidence});
            return;
        }
        const double accept = (n && n->min_confidence) ? *n->min_confidence
                                                       : cfg_.accept_confidence;
        need_confirm = v.confirm || (n && n->confirm) || (r.confidence < accept);
    }

    if (need_confirm) {
        beginConfirmation(r);
        return;
    }

    // Accepted → dispatch immediately.
    RecognitionEvent e;
    e.verb = v.name;
    e.verb_data = v.user_data;
    if (n) {
        e.noun = n->name;
        e.noun_data = n->user_data;
    }
    e.text = r.text;
    e.confidence = r.confidence;
    e.confirmed = true;
    emit(std::move(e));
}

void Engine::beginConfirmation(RawRecognition pending) {
    confirming_ = true;
    pending_ = std::move(pending);
    // Swap the single engine to yes/no BEFORE listening for the answer — normal
    // command listening is fully suspended (deterministic mic handover).
    if (created_) backend_->setActiveRuleset(Ruleset::YesNo);
    confirm_deadline_ = Clock::now() + dur(cfg_.confirm_timeout_sec);
    // Tell the host to draw the prompt. Emitted even with no IConfirmationUI
    // attached -- an in-library dialog is optional, this event is not.
    emit(ConfirmationEvent{true, pending_.text});
    if (ui_) {
        ui_->beginConfirm(pending_.text, [this](bool yes) {
            Msg m;
            m.cmd = Cmd::ConfirmResolve;
            m.confirm_yes = yes;
            postMsg(std::move(m));
        });
    }
}

void Engine::endConfirmation() {
    confirming_ = false;
    if (ui_) ui_->endConfirm();
    emit(ConfirmationEvent{false, std::string{}});
}

void Engine::resolveConfirmation(bool yes) {
    if (!confirming_) return;
    endConfirmation();
    if (created_) backend_->setActiveRuleset(Ruleset::Commands);

    if (yes) {
        const Verb& v = cfg_.verbs[pending_.verb_index];
        const Noun* n = (pending_.noun_index >= 0 &&
                         pending_.noun_index < static_cast<int>(v.nouns.size()))
                            ? &v.nouns[pending_.noun_index]
                            : nullptr;
        RecognitionEvent e;
        e.verb = v.name;
        e.verb_data = v.user_data;
        if (n) {
            e.noun = n->name;
            e.noun_data = n->user_data;
        }
        e.text = pending_.text;
        e.confidence = pending_.confidence;
        e.confirmed = true;
        emit(std::move(e));
    }
    // "no" / decline → command dropped silently (no event).
    pending_ = RawRecognition{};
}

void Engine::setState(State s) {
    State old = state_.exchange(s, std::memory_order_acq_rel);
    if (old != s) emit(StateChangeEvent{old, s});
}

void Engine::log(LogLevel level, std::string msg) {
    emit(LogEvent{level, std::move(msg)});
}

}  // namespace voicecmd
