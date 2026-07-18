// voicecmd — deterministic fake backend for host-free core tests (no audio/COM).
//
// The engine calls create/updateGrammar/setActiveRuleset/start/stop/dispose on
// its worker thread. Tests drive recognitions via feed()/endUnexpectedly(),
// simulating the SAPI callback thread posting into the sink. Observable fields
// are atomic so a test thread may read them after awaiting a control future.
#ifndef VOICECMD_FAKE_BACKEND_H
#define VOICECMD_FAKE_BACKEND_H

#include <atomic>

#include "voicecmd/backend.h"

namespace voicecmd {

class FakeBackend final : public IRecognizerBackend {
public:
    void create(const Config& cfg, BackendSink* sink) override {
        sink_ = sink;
        (void)cfg;
        created.store(true);
        create_count.fetch_add(1);
    }
    void updateGrammar(const std::vector<Verb>&) override {
        update_count.fetch_add(1);
    }
    void setActiveRuleset(Ruleset r) override { ruleset.store(r); }
    void start() override {
        started.store(true);
        start_count.fetch_add(1);
    }
    void stop() override {
        started.store(false);
        stop_count.fetch_add(1);
    }
    void dispose() override {
        created.store(false);
        dispose_count.fetch_add(1);
        sink_ = nullptr;
    }

    // ---- test drivers (simulate the backend callback thread) ----
    void feed(RawRecognition r) {
        if (sink_) sink_->onRecognition(std::move(r));
    }
    void endUnexpectedly() {
        if (sink_) sink_->onBackendEnded();
    }

    // ---- observable state ----
    std::atomic<bool> created{false};
    std::atomic<bool> started{false};
    std::atomic<Ruleset> ruleset{Ruleset::Commands};
    std::atomic<int> create_count{0};
    std::atomic<int> update_count{0};
    std::atomic<int> start_count{0};
    std::atomic<int> stop_count{0};
    std::atomic<int> dispose_count{0};

private:
    BackendSink* sink_ = nullptr;
};

}  // namespace voicecmd

#endif  // VOICECMD_FAKE_BACKEND_H
