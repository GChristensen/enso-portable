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

private:
    enum class Cmd {
        Start, Stop, Pause, Resume, Restart, Shutdown, UpdateGrammar, Close,
        Recognition, BackendEnded, ConfirmResolve, ConfirmTimeout, Log, Sync,
    };

    struct Msg {
        Cmd cmd;
        std::shared_ptr<std::promise<void>> done;  // set for awaitable controls
        RawRecognition raw;                         // Recognition
        std::vector<Verb> verbs;                    // UpdateGrammar
        bool confirm_yes = false;                   // ConfirmResolve
        LogLevel level = LogLevel::Info;            // Log
        std::string text;                           // Log
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
    void ensureCreated();

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
