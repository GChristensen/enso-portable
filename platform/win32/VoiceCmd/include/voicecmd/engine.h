// voicecmd — the single-owner lifecycle engine (state machine).
//
// All lifecycle transitions are messages on one queue consumed by one dedicated
// worker thread. Control methods return std::future<void> so callers can block
// with timeout or await; handler exceptions propagate to the awaiter. Backend
// callbacks and the confirmation UI only *post* messages — they never mutate
// engine state inline.
#ifndef VOICECMD_ENGINE_H
#define VOICECMD_ENGINE_H

#include <atomic>
#include <condition_variable>
#include <deque>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

#include "voicecmd/backend.h"
#include "voicecmd/confirm.h"
#include "voicecmd/config.h"
#include "voicecmd/events.h"

namespace voicecmd {

class Engine final : public BackendSink {
public:
    // Takes ownership of the backend. `ui` may be null (confirmations then
    // resolve to "no"). The worker thread starts, but the backend is NOT
    // created/started inline — call start().
    Engine(Config cfg, std::unique_ptr<IRecognizerBackend> backend,
           IConfirmationUI* ui = nullptr);
    ~Engine() override;

    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    // Lifecycle — each returns a future fulfilled when the transition completes
    // on the worker (or carrying the handler's exception).
    std::future<void> start();
    std::future<void> stop();
    std::future<void> pause();
    std::future<void> resume();
    std::future<void> restart();
    std::future<void> shutdown();                       // dispose the engine
    std::future<void> updateGrammar(std::vector<Verb> verbs);

    // No-op barrier: the returned future resolves once every message queued
    // before it has been processed (FIFO). Useful to await async recognitions.
    std::future<void> sync();

    // Stops and joins the worker thread. Idempotent; safe from a destructor /
    // atexit. Must never be called from within the worker thread itself.
    void close();

    // Pull-mode delivery: drain all events queued since the last call.
    std::vector<Event> drain();

    // Optional push delivery. Called on the worker thread, outside all internal
    // locks. A throwing callback is caught and logged; the worker never crashes.
    void setEventSink(std::function<void(const Event&)> cb);

    State state() const { return state_.load(std::memory_order_acquire); }

    // BackendSink — posted from the backend callback thread.
    void onRecognition(RawRecognition r) override;
    void onBackendEnded() override;
    void onLog(LogLevel level, std::string msg) override;

    // Emit a host-originated log line (e.g. the session-lock monitor). Thread-
    // safe; delivered through the normal event stream on the next drain.
    void hostLog(LogLevel level, std::string msg) { log(level, std::move(msg)); }

    // Called by the session monitor BEFORE posting stop/start, so the engine
    // can suppress auto-recovery restarts while the desktop is locked (the
    // audio device is unavailable on the secure desktop).
    void setSessionLocked(bool locked) {
        session_locked_.store(locked, std::memory_order_release);
    }
    bool sessionLocked() const {
        return session_locked_.load(std::memory_order_acquire);
    }

private:
    enum class Cmd {
        Start, Stop, Pause, Resume, Restart, Shutdown, UpdateGrammar, Close,
        Recognition, BackendEnded, ConfirmResolve, ConfirmTimeout, Sync,
    };

    struct Msg {
        Cmd cmd;
        std::shared_ptr<std::promise<void>> done;  // set for awaitable controls
        RawRecognition raw;                         // Recognition
        std::vector<Verb> verbs;                    // UpdateGrammar
        bool confirm_yes = false;                   // ConfirmResolve
    };

    using Clock = std::chrono::steady_clock;

    std::future<void> post(Cmd cmd);
    void postMsg(Msg m);
    void workerLoop();
    void handle(Msg& m);

    // Transition helpers (worker thread only).
    void doStart();
    void doStop(bool keep_engine);
    void doShutdown();
    void doRestart();
    bool hasPendingHostCmd_() const;  // queue peek (must hold qmx_)
    void ensureCreated();

    // The ruleset that matches the engine's current state, so a grammar rebuild
    // re-asserts the right rules instead of blindly reverting to Commands (which
    // would break an active pause or a pending confirmation).
    Ruleset currentRuleset() const;

    void classify(const RawRecognition& r);
    void beginConfirmation(RawRecognition pending);
    void resolveConfirmation(bool yes);
    // Tears down the confirmation prompt: hides any attached UI and emits the
    // closing ConfirmationEvent. Every path out of `confirming_` goes through
    // here so the UI and the host-visible event can never drift apart.
    void endConfirmation();
    void emit(Event e);
    void setState(State s);
    void log(LogLevel level, std::string msg);

    Config cfg_;
    std::unique_ptr<IRecognizerBackend> backend_;
    IConfirmationUI* ui_;

    std::atomic<State> state_{State::Idle};
    bool created_ = false;   // backend engine + grammars exist
    bool started_ = false;   // continuous recognition active
    bool host_stopping_ = false;  // suppress auto-recovery during host-driven stop
    int restart_attempts_ = 0;    // consecutive unexpected-end auto-restarts
    std::atomic<bool> session_locked_{false};  // desktop is locked (audio unavailable)

    // Confirmation sub-state (worker only).
    bool confirming_ = false;
    RawRecognition pending_;
    Clock::time_point confirm_deadline_{};

    // Command queue.
    std::mutex qmx_;
    std::condition_variable qcv_;
    std::deque<Msg> queue_;
    std::thread worker_;
    std::atomic<bool> close_requested_{false};

    // Event queue (pull) + optional push sink.
    std::mutex emx_;
    std::vector<Event> events_;
    std::function<void(const Event&)> event_sink_;
};

}  // namespace voicecmd

#endif  // VOICECMD_ENGINE_H
