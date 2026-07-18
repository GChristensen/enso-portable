// M1 acceptance tests: lifecycle, confidence bands, confirm flow, pause,
// auto-recovery — all against the fake backend, no audio/COM.
#include <chrono>
#include <memory>
#include <thread>

#include "fake_backend.h"
#include "test_util.h"
#include "voicecmd/engine.h"

using namespace voicecmd;
using namespace vctest;

namespace {

Config makeConfig() {
    Config c;
    c.accept_confidence = 0.85;
    c.reject_confidence = 0.5;
    c.confirm_yes_confidence = 0.92;
    c.confirm_timeout_sec = 0.15;
    c.restart_delay_sec = 0.05;
    // Exercise the three-band confidence logic in these tests. (The default is
    // true -- grammar match trusted -- which is covered by its own test.)
    c.trust_grammar_match = false;

    Verb open;
    open.name = "open";
    Noun browser; browser.name = "browser"; open.nouns.push_back(browser);
    Noun chrome; chrome.name = "google chrome"; open.nouns.push_back(chrome);

    Verb sd;
    sd.name = "shutdown";
    Noun pc; pc.name = "pc"; pc.confirm = true; sd.nouns.push_back(pc);

    Verb mute;
    mute.name = "mute";  // verb-only

    c.verbs = {open, sd, mute};
    return c;
}

RawRecognition cmd(int v, int n, double conf, std::string text) {
    RawRecognition r;
    r.kind = RawKind::Command;
    r.verb_index = v;
    r.noun_index = n;
    r.confidence = conf;
    r.text = std::move(text);
    return r;
}
RawRecognition ctl(ControlPhrase c) {
    RawRecognition r;
    r.kind = RawKind::Control;
    r.control = c;
    r.confidence = 1.0;
    return r;
}
RawRecognition yesno(YesNoAnswer a, double conf) {
    RawRecognition r;
    r.kind = RawKind::YesNo;
    r.answer = a;
    r.confidence = conf;
    return r;
}
RawRecognition garbage() {
    RawRecognition r;
    r.kind = RawKind::Garbage;
    r.confidence = 0.1;
    r.text = "blah blah";
    return r;
}

struct Fixture {
    FakeBackend* fb;
    FakeUI ui;
    std::unique_ptr<Engine> eng;
    explicit Fixture(Config c = makeConfig()) {
        auto backend = std::make_unique<FakeBackend>();
        fb = backend.get();
        eng = std::make_unique<Engine>(std::move(c), std::move(backend), &ui);
    }
};

void test_start_stop_lifecycle() {
    Fixture f;
    f.eng->start().get();
    CHECK(f.eng->state() == State::Listening);
    CHECK(f.fb->created.load());
    CHECK(f.fb->started.load());
    CHECK(f.fb->create_count.load() == 1);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);

    // stop() retains the engine (cheap re-start, no re-create).
    f.eng->stop().get();
    CHECK(f.eng->state() == State::Stopped);
    CHECK(!f.fb->started.load());
    CHECK(f.fb->created.load());
    f.eng->start().get();
    CHECK(f.fb->create_count.load() == 1);
    CHECK(f.fb->started.load());

    // shutdown() disposes; next start rebuilds.
    f.eng->shutdown().get();
    CHECK(f.eng->state() == State::Idle);
    CHECK(!f.fb->created.load());
    CHECK(f.fb->dispose_count.load() == 1);
    f.eng->start().get();
    CHECK(f.fb->create_count.load() == 2);
    f.eng->close();
    CHECK(f.eng->state() == State::Closed);
}

void test_accept_band_dispatch() {
    Fixture f;
    f.eng->start().get();
    f.fb->feed(cmd(0, 1, 0.90, "open google chrome"));  // >= accept
    flush(*f.eng);
    auto evs = f.eng->drain();
    const auto* r = first<RecognitionEvent>(evs);
    CHECK(r != nullptr);
    if (r) {
        CHECK(r->verb == "open");
        CHECK(r->noun == "google chrome");     // original casing
        CHECK(r->text == "open google chrome");
        CHECK(r->confirmed);
    }
    // verb-only command
    f.fb->feed(cmd(2, -1, 0.95, "mute"));
    flush(*f.eng);
    auto evs2 = f.eng->drain();
    const auto* r2 = first<RecognitionEvent>(evs2);
    CHECK(r2 != nullptr);
    if (r2) {
        CHECK(r2->verb == "mute");
        CHECK(r2->noun.empty());
    }
    f.eng->close();
}

void test_reject_band_and_garbage() {
    Fixture f;
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.30, "open browser"));  // < reject
    f.fb->feed(garbage());
    flush(*f.eng);
    auto evs = f.eng->drain();
    CHECK(count<RecognitionEvent>(evs) == 0);
    CHECK(count<RejectionEvent>(evs) == 2);
    f.eng->close();
}

void test_middle_band_requires_confirm_yes() {
    Fixture f;
    f.ui.auto_answer = true;  // click "yes"
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));  // reject < c < accept
    flush(*f.eng);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);  // restored after confirm
    CHECK(f.ui.begin_count.load() == 1);
    CHECK(f.ui.end_count.load() == 1);
    auto evs = f.eng->drain();
    const auto* r = first<RecognitionEvent>(evs);
    CHECK(r != nullptr);
    if (r) CHECK(r->verb == "open" && r->noun == "browser" && r->confirmed);
    f.eng->close();
}

void test_confirm_no_drops() {
    Fixture f;
    f.ui.auto_answer = false;  // click "no"
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));
    flush(*f.eng);
    auto evs = f.eng->drain();
    CHECK(count<RecognitionEvent>(evs) == 0);  // dropped silently
    CHECK(f.ui.end_count.load() == 1);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);
    f.eng->close();
}

void test_confirm_timeout_defaults_no() {
    Fixture f;  // no auto_answer -> nobody clicks
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));
    flush(*f.eng);
    CHECK(f.fb->ruleset.load() == Ruleset::YesNo);  // still confirming
    std::this_thread::sleep_for(std::chrono::milliseconds(200));  // > timeout
    flush(*f.eng);
    auto evs = f.eng->drain();
    CHECK(count<RecognitionEvent>(evs) == 0);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);  // restored on timeout
    CHECK(f.ui.end_count.load() == 1);
    f.eng->close();
}

// A host that draws its own prompt (Enso) relies on these events rather than on
// an attached IConfirmationUI, so they must bracket every confirmation.
void test_confirmation_events_bracket_the_prompt() {
    Fixture f;
    f.ui.auto_answer = true;
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));
    flush(*f.eng);
    auto evs = f.eng->drain();
    CHECK(count<ConfirmationEvent>(evs) == 2);  // begin + end
    const auto* c = first<ConfirmationEvent>(evs);
    CHECK(c != nullptr);
    if (c) CHECK(c->active && c->phrase == "open browser");
    f.eng->close();
}

// The closing event must also fire when nobody answers, or a host prompt would
// stay on screen forever.
void test_confirmation_end_event_on_timeout() {
    Fixture f;  // no auto_answer -> nobody answers
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));
    flush(*f.eng);
    auto evs = f.eng->drain();
    CHECK(count<ConfirmationEvent>(evs) == 1);  // begin only, still confirming
    std::this_thread::sleep_for(std::chrono::milliseconds(200));  // > timeout
    flush(*f.eng);
    evs = f.eng->drain();
    CHECK(count<ConfirmationEvent>(evs) == 1);  // the end
    const auto* c = first<ConfirmationEvent>(evs);
    CHECK(c != nullptr && !c->active);
    f.eng->close();
}

// Confirmations do not survive a stop(); the prompt must be retracted too.
void test_confirmation_end_event_on_stop() {
    Fixture f;
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));
    flush(*f.eng);
    (void)f.eng->drain();  // discard the begin
    f.eng->stop().get();
    flush(*f.eng);
    auto evs = f.eng->drain();
    const auto* c = first<ConfirmationEvent>(evs);
    CHECK(c != nullptr && !c->active);
    f.eng->close();
}

void test_noun_confirm_flag_forces_confirm() {
    Fixture f;
    f.ui.auto_answer = true;
    f.eng->start().get();
    // High confidence, but noun "pc" has confirm=true.
    f.fb->feed(cmd(1, 0, 0.99, "shutdown pc"));
    flush(*f.eng);
    CHECK(f.ui.begin_count.load() == 1);  // confirmation was required
    auto evs = f.eng->drain();
    const auto* r = first<RecognitionEvent>(evs);
    CHECK(r != nullptr && r->verb == "shutdown" && r->noun == "pc");
    f.eng->close();
}

void test_gated_yes_keeps_listening() {
    Fixture f;  // drive yes/no by voice
    f.eng->start().get();
    f.fb->feed(cmd(0, 0, 0.70, "open browser"));  // -> confirming
    flush(*f.eng);
    CHECK(f.fb->ruleset.load() == Ruleset::YesNo);
    // Low-confidence "yes" fails the high gate: stays listening, emits rejection.
    f.fb->feed(yesno(YesNoAnswer::Yes, 0.60));
    flush(*f.eng);
    CHECK(f.fb->ruleset.load() == Ruleset::YesNo);  // still confirming
    auto mid = f.eng->drain();
    CHECK(count<RecognitionEvent>(mid) == 0);
    CHECK(count<RejectionEvent>(mid) == 1);
    // High-confidence "yes" now clears the gate.
    f.fb->feed(yesno(YesNoAnswer::Yes, 0.95));
    flush(*f.eng);
    auto evs = f.eng->drain();
    const auto* r = first<RecognitionEvent>(evs);
    CHECK(r != nullptr && r->verb == "open");
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);
    f.eng->close();
}

void test_soft_pause_via_control() {
    Fixture f;
    f.eng->start().get();
    f.fb->feed(ctl(ControlPhrase::StopListening));
    flush(*f.eng);
    CHECK(f.eng->state() == State::SoftPaused);
    CHECK(f.fb->ruleset.load() == Ruleset::ResumeOnly);
    auto p1 = f.eng->drain();
    const auto* pc = first<PauseChangeEvent>(p1);
    CHECK(pc != nullptr && pc->paused);

    // A command while paused is ignored (only rejection telemetry).
    f.fb->feed(cmd(0, 0, 0.95, "open browser"));
    flush(*f.eng);
    auto p2 = f.eng->drain();
    CHECK(count<RecognitionEvent>(p2) == 0);

    // Resume (accepted at any confidence — no lockout).
    f.fb->feed(ctl(ControlPhrase::ResumeListening));
    flush(*f.eng);
    CHECK(f.eng->state() == State::Listening);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);
    f.eng->close();
}

void test_host_pause_resume() {
    Fixture f;
    f.eng->start().get();
    f.eng->pause().get();
    CHECK(f.eng->state() == State::SoftPaused);
    CHECK(f.fb->ruleset.load() == Ruleset::ResumeOnly);
    f.eng->resume().get();
    CHECK(f.eng->state() == State::Listening);
    CHECK(f.fb->ruleset.load() == Ruleset::Commands);
    f.eng->close();
}

void test_auto_recovery_on_backend_end() {
    Fixture f;
    f.eng->start().get();
    CHECK(f.fb->start_count.load() == 1);
    f.fb->endUnexpectedly();  // device error / stream end
    std::this_thread::sleep_for(std::chrono::milliseconds(150));  // > restart delay
    flush(*f.eng);
    CHECK(f.fb->dispose_count.load() >= 1);
    CHECK(f.fb->create_count.load() == 2);
    CHECK(f.fb->start_count.load() == 2);
    CHECK(f.fb->started.load());
    CHECK(f.eng->state() == State::Listening);
    f.eng->close();
}

void test_no_recovery_when_host_stops() {
    Fixture f;
    f.eng->start().get();
    f.eng->stop().get();
    f.fb->endUnexpectedly();  // must NOT trigger a restart (host stopped)
    std::this_thread::sleep_for(std::chrono::milliseconds(120));
    flush(*f.eng);
    CHECK(f.fb->start_count.load() == 1);
    CHECK(f.eng->state() == State::Stopped);
    f.eng->close();
}

void test_trust_grammar_match_dispatches_low_confidence() {
    Config c = makeConfig();
    c.trust_grammar_match = true;  // grammar match is the accept signal
    Fixture f(c);
    f.eng->start().get();
    // Very low confidence, but a full command-rule match -> dispatch anyway.
    f.fb->feed(cmd(0, 1, 0.15, "open google chrome"));
    flush(*f.eng);
    auto evs = f.eng->drain();
    const auto* r = first<RecognitionEvent>(evs);
    CHECK(r != nullptr);
    if (r) {
        CHECK(r->verb == "open" && r->noun == "google chrome");
        CHECK(r->confidence == 0.15);  // real value still reported
    }
    // An explicit confirm flag is still honored even when trusting the match.
    f.ui.auto_answer = true;
    f.fb->feed(cmd(1, 0, 0.10, "shutdown pc"));  // noun pc has confirm=true
    flush(*f.eng);
    CHECK(f.ui.begin_count.load() == 1);
    f.eng->close();
}

void test_push_sink_and_grammar_update() {
    Fixture f;
    std::atomic<int> pushed{0};
    f.eng->setEventSink([&](const Event& e) {
        if (std::holds_alternative<RecognitionEvent>(e)) pushed.fetch_add(1);
    });
    f.eng->start().get();
    f.eng->updateGrammar(makeConfig().verbs).get();
    CHECK(f.fb->update_count.load() == 1);
    f.fb->feed(cmd(2, -1, 0.95, "mute"));
    flush(*f.eng);
    CHECK(pushed.load() == 1);
    f.eng->close();
}

}  // namespace

int main() {
    RUN(test_start_stop_lifecycle);
    RUN(test_accept_band_dispatch);
    RUN(test_reject_band_and_garbage);
    RUN(test_middle_band_requires_confirm_yes);
    RUN(test_confirm_no_drops);
    RUN(test_confirm_timeout_defaults_no);
    RUN(test_confirmation_events_bracket_the_prompt);
    RUN(test_confirmation_end_event_on_timeout);
    RUN(test_confirmation_end_event_on_stop);
    RUN(test_noun_confirm_flag_forces_confirm);
    RUN(test_gated_yes_keeps_listening);
    RUN(test_soft_pause_via_control);
    RUN(test_host_pause_resume);
    RUN(test_auto_recovery_on_backend_end);
    RUN(test_no_recovery_when_host_stops);
    RUN(test_trust_grammar_match_dispatches_low_confidence);
    RUN(test_push_sink_and_grammar_update);

    std::printf("\n%d checks, %d failures\n", vctest::checks(), vctest::failures());
    return vctest::failures() == 0 ? 0 : 1;
}
