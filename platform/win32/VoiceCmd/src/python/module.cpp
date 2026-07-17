// voicecmd — nanobind bindings (built with STABLE_ABI => single abi3 voicecmd.pyd
// importable on any CPython >= 3.10). nanobind is used instead of pybind11 because
// pybind11 under Py_LIMITED_API triggers an internal compiler error on MSVC 14.44.
//
// Canonical spec-named API: Config / Verb / Noun / Recognizer, @on_recognized-style
// callbacks, pull-mode poll_events().
//
// Delivery model (plan §3.3): the native worker thread NEVER calls into Python.
// All Python delivery happens inside poll_events() on the CALLER's thread (GIL
// already held); registered callbacks are invoked from there too. This is what
// Enso's single-threaded tick needs and avoids every cross-thread GIL hazard.
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <chrono>
#include <memory>
#include <new>
#include <optional>
#include <string>
#include <vector>

#include "fake_backend.h"
#include "voicecmd/engine.h"
#ifdef VOICECMD_HAS_SAPI
#include "sapi_backend.h"
#endif

namespace nb = nanobind;
using namespace voicecmd;

namespace {

// ---- opaque user-data payloads (arbitrary Python objects) -----------------
// Stored verbatim; the deleter re-acquires the GIL because the shared_ptr may be
// released on the worker thread (e.g. when the grammar is replaced).
UserData wrapData(nb::object o) {
    if (o.is_none()) return nullptr;
    auto* held = new nb::object(std::move(o));
    return UserData(held, [](void* p) {
        nb::gil_scoped_acquire gil;
        delete static_cast<nb::object*>(p);
    });
}
nb::object unwrapData(const UserData& d) {
    if (!d) return nb::none();
    return *static_cast<nb::object*>(d.get());  // caller holds the GIL
}

std::chrono::duration<double> secs(double s) {
    return std::chrono::duration<double>(s);
}

// ---- Python-facing config mirrors (Py* names collide with CPython) --------
struct NounSpec {
    std::string name;
    bool confirm = false;
    std::optional<double> min_confidence;
    nb::object data = nb::none();
};
struct VerbSpec {
    std::string name;
    std::vector<NounSpec> nouns;
    bool confirm = false;
    bool disabled = false;
    std::string description;
    nb::object data = nb::none();
};
struct ConfigSpec {
    std::string keyword = "computer";
    bool keyword_required = true;
    double accept_confidence = 0.85;
    double reject_confidence = 0.5;
    double confirm_yes_confidence = 0.92;
    std::vector<VerbSpec> verbs;
    std::string backend = "sapi";
    std::string language = "en-US";
    bool session_lock = true;
    bool rejection_events = true;
    bool use_garbage_rule = true;
    bool trust_grammar_match = true;
    bool shared_recognizer = false;
    double confirm_timeout_sec = 10.0;
};

Noun toNoun(const NounSpec& n) {
    Noun o;
    o.name = n.name;
    o.confirm = n.confirm;
    o.min_confidence = n.min_confidence;
    o.user_data = wrapData(n.data);
    return o;
}
Verb toVerb(const VerbSpec& v) {
    Verb o;
    o.name = v.name;
    o.confirm = v.confirm;
    o.disabled = v.disabled;
    o.description = v.description;
    o.user_data = wrapData(v.data);
    for (const auto& n : v.nouns) o.nouns.push_back(toNoun(n));
    return o;
}
std::vector<Verb> toVerbs(const std::vector<VerbSpec>& vs) {
    std::vector<Verb> out;
    out.reserve(vs.size());
    for (const auto& v : vs) out.push_back(toVerb(v));
    return out;
}
Config toConfig(const ConfigSpec& c) {
    Config o;
    o.keyword = c.keyword;
    o.keyword_required = c.keyword_required;
    o.accept_confidence = c.accept_confidence;
    o.reject_confidence = c.reject_confidence;
    o.confirm_yes_confidence = c.confirm_yes_confidence;
    o.language = c.language;
    o.session_lock = c.session_lock;
    o.rejection_events = c.rejection_events;
    o.use_garbage_rule = c.use_garbage_rule;
    o.trust_grammar_match = c.trust_grammar_match;
    o.shared_recognizer = c.shared_recognizer;
    o.confirm_timeout_sec = c.confirm_timeout_sec;
    o.backend = (c.backend == "fake") ? Backend::Fake : Backend::Sapi;
    o.verbs = toVerbs(c.verbs);
    return o;
}

// ---- Python-facing event mirrors -----------------------------------------
struct RecognitionEventPy {
    std::string verb, noun, text;
    double confidence = 0.0;
    nb::object verb_data = nb::none();
    nb::object noun_data = nb::none();
    nb::object data = nb::none();  // convenience: noun data, else verb data
    bool confirmed = true;
};
struct RejectionEventPy {
    std::string text;
    double confidence = 0.0;
};
struct StateChangeEventPy {
    State old_state, new_state;
};
struct PauseChangeEventPy {
    bool paused = false;
};
struct LogEventPy {
    LogLevel level;
    std::string message;
};

nb::object toPy(const Event& e) {
    return std::visit(
        [](auto&& ev) -> nb::object {
            using T = std::decay_t<decltype(ev)>;
            if constexpr (std::is_same_v<T, RecognitionEvent>) {
                RecognitionEventPy r;
                r.verb = ev.verb;
                r.noun = ev.noun;
                r.text = ev.text;
                r.confidence = ev.confidence;
                r.verb_data = unwrapData(ev.verb_data);
                r.noun_data = unwrapData(ev.noun_data);
                r.data = r.noun_data.is_none() ? r.verb_data : r.noun_data;
                r.confirmed = ev.confirmed;
                return nb::cast(r);
            } else if constexpr (std::is_same_v<T, RejectionEvent>) {
                return nb::cast(RejectionEventPy{ev.text, ev.confidence});
            } else if constexpr (std::is_same_v<T, StateChangeEvent>) {
                return nb::cast(StateChangeEventPy{ev.old_state, ev.new_state});
            } else if constexpr (std::is_same_v<T, PauseChangeEvent>) {
                return nb::cast(PauseChangeEventPy{ev.paused});
            } else {
                return nb::cast(LogEventPy{ev.level, ev.message});
            }
        },
        e);
}

// ---- Recognizer facade ----------------------------------------------------
class Recognizer {
public:
    explicit Recognizer(const ConfigSpec& c) {
        Config cfg = toConfig(c);
        std::unique_ptr<IRecognizerBackend> backend;
        if (cfg.backend == Backend::Fake) {
            backend = std::make_unique<FakeBackend>();
        } else {
#ifdef VOICECMD_HAS_SAPI
            backend = std::make_unique<SapiBackend>();
#else
            throw std::runtime_error("SAPI backend not built into this module");
#endif
        }
        eng_ = std::make_unique<Engine>(std::move(cfg), std::move(backend),
                                        /*ui=*/nullptr);
    }

    void start(double timeout) { await(eng_->start(), timeout); }
    void stop(double timeout) { await(eng_->stop(), timeout); }
    void pause(double timeout) { await(eng_->pause(), timeout); }
    void resume(double timeout) { await(eng_->resume(), timeout); }
    void restart(double timeout) { await(eng_->restart(), timeout); }

    void close() {
        nb::gil_scoped_release rel;
        if (eng_) eng_->close();
    }

    void update_grammar(const std::vector<VerbSpec>& verbs, double timeout) {
        await(eng_->updateGrammar(toVerbs(verbs)), timeout);
    }

    // Pull-mode pump: drain, build Python events, fire registered callbacks
    // (errors reported-and-swallowed), return the list.
    nb::list poll_events() {
        std::vector<Event> events = eng_->drain();
        nb::list out;
        for (const auto& e : events) {
            nb::object o = toPy(e);
            out.append(o);
            nb::object cb = callbackFor(e.index());
            if (cb.is_valid() && !cb.is_none()) {
                try {
                    cb(o);
                } catch (nb::python_error& err) {
                    err.restore();
                    PyErr_WriteUnraisable(cb.ptr());  // report + clear
                }
            }
        }
        return out;
    }

    // Registration doubles as a decorator (returns the callback).
    nb::object on_recognized(nb::object f) { cb_recognized_ = f; return f; }
    nb::object on_rejected(nb::object f) { cb_rejected_ = f; return f; }
    nb::object on_state_change(nb::object f) { cb_state_ = f; return f; }
    nb::object on_pause_change(nb::object f) { cb_pause_ = f; return f; }
    nb::object on_log(nb::object f) { cb_log_ = f; return f; }

    State state() const { return eng_->state(); }

private:
    void await(std::future<void> fut, double timeout) {
        {
            nb::gil_scoped_release rel;
            if (timeout > 0.0) {
                if (fut.wait_for(secs(timeout)) != std::future_status::ready) {
                    throw std::runtime_error("voicecmd: operation timed out");
                }
            }
        }
        fut.get();  // propagate any handler exception (GIL held here)
    }

    nb::object callbackFor(std::size_t idx) const {
        switch (idx) {
            case 0: return cb_recognized_;
            case 1: return cb_rejected_;
            case 2: return cb_state_;
            case 3: return cb_pause_;
            case 4: return cb_log_;
            default: return nb::none();
        }
    }

    std::unique_ptr<Engine> eng_;
    nb::object cb_recognized_ = nb::none();
    nb::object cb_rejected_ = nb::none();
    nb::object cb_state_ = nb::none();
    nb::object cb_pause_ = nb::none();
    nb::object cb_log_ = nb::none();
};

}  // namespace

NB_MODULE(voicecmd, m) {
    m.doc() = "Grammar-constrained voice command recognition (native).";

    nb::enum_<State>(m, "State")
        .value("Idle", State::Idle)
        .value("Starting", State::Starting)
        .value("Listening", State::Listening)
        .value("SoftPaused", State::SoftPaused)
        .value("Stopping", State::Stopping)
        .value("Stopped", State::Stopped)
        .value("Restarting", State::Restarting)
        .value("ShuttingDown", State::ShuttingDown)
        .value("Closed", State::Closed);

    nb::enum_<LogLevel>(m, "LogLevel")
        .value("Debug", LogLevel::Debug)
        .value("Info", LogLevel::Info)
        .value("Warning", LogLevel::Warning)
        .value("Error", LogLevel::Error);

    nb::class_<NounSpec>(m, "Noun")
        .def(
            "__init__",
            [](NounSpec* self, std::string name, bool confirm,
               std::optional<double> min_confidence, nb::object data) {
                new (self) NounSpec{std::move(name), confirm, min_confidence,
                                    std::move(data)};
            },
            nb::arg("name"), nb::arg("confirm") = false,
            nb::arg("min_confidence") = nb::none(), nb::arg("data") = nb::none())
        .def_rw("name", &NounSpec::name)
        .def_rw("confirm", &NounSpec::confirm)
        .def_rw("min_confidence", &NounSpec::min_confidence)
        .def_rw("data", &NounSpec::data);

    nb::class_<VerbSpec>(m, "Verb")
        .def(
            "__init__",
            [](VerbSpec* self, std::string name, std::vector<NounSpec> nouns,
               bool confirm, bool disabled, std::string description,
               nb::object data) {
                new (self) VerbSpec{std::move(name),        std::move(nouns),
                                    confirm,                disabled,
                                    std::move(description), std::move(data)};
            },
            nb::arg("name"), nb::arg("nouns") = std::vector<NounSpec>{},
            nb::arg("confirm") = false, nb::arg("disabled") = false,
            nb::arg("description") = "", nb::arg("data") = nb::none())
        .def_rw("name", &VerbSpec::name)
        .def_rw("nouns", &VerbSpec::nouns)
        .def_rw("confirm", &VerbSpec::confirm)
        .def_rw("disabled", &VerbSpec::disabled)
        .def_rw("description", &VerbSpec::description)
        .def_rw("data", &VerbSpec::data);

    nb::class_<ConfigSpec>(m, "Config")
        .def(
            "__init__",
            [](ConfigSpec* self, std::string keyword, bool keyword_required,
               double accept_confidence, double reject_confidence,
               double confirm_yes_confidence, std::vector<VerbSpec> verbs,
               std::string backend, std::string language, bool session_lock,
               bool rejection_events, bool use_garbage_rule,
               bool trust_grammar_match, bool shared_recognizer,
               double confirm_timeout_sec) {
                ConfigSpec c;
                c.keyword = std::move(keyword);
                c.keyword_required = keyword_required;
                c.accept_confidence = accept_confidence;
                c.reject_confidence = reject_confidence;
                c.confirm_yes_confidence = confirm_yes_confidence;
                c.verbs = std::move(verbs);
                c.backend = std::move(backend);
                c.language = std::move(language);
                c.session_lock = session_lock;
                c.rejection_events = rejection_events;
                c.use_garbage_rule = use_garbage_rule;
                c.trust_grammar_match = trust_grammar_match;
                c.shared_recognizer = shared_recognizer;
                c.confirm_timeout_sec = confirm_timeout_sec;
                new (self) ConfigSpec{std::move(c)};
            },
            nb::arg("keyword") = "computer", nb::arg("keyword_required") = true,
            nb::arg("accept_confidence") = 0.85,
            nb::arg("reject_confidence") = 0.5,
            nb::arg("confirm_yes_confidence") = 0.92,
            nb::arg("verbs") = std::vector<VerbSpec>{}, nb::arg("backend") = "sapi",
            nb::arg("language") = "en-US", nb::arg("session_lock") = true,
            nb::arg("rejection_events") = true,
            nb::arg("use_garbage_rule") = false,
            nb::arg("trust_grammar_match") = true,
            nb::arg("shared_recognizer") = false,
            nb::arg("confirm_timeout_sec") = 10.0)
        .def_rw("verbs", &ConfigSpec::verbs)
        .def_rw("keyword", &ConfigSpec::keyword);

    nb::class_<RecognitionEventPy>(m, "RecognitionEvent")
        .def_ro("verb", &RecognitionEventPy::verb)
        .def_ro("noun", &RecognitionEventPy::noun)
        .def_ro("text", &RecognitionEventPy::text)
        .def_ro("confidence", &RecognitionEventPy::confidence)
        .def_ro("verb_data", &RecognitionEventPy::verb_data)
        .def_ro("noun_data", &RecognitionEventPy::noun_data)
        .def_ro("data", &RecognitionEventPy::data)
        .def_ro("confirmed", &RecognitionEventPy::confirmed);

    nb::class_<RejectionEventPy>(m, "RejectionEvent")
        .def_ro("text", &RejectionEventPy::text)
        .def_ro("confidence", &RejectionEventPy::confidence);

    nb::class_<StateChangeEventPy>(m, "StateChangeEvent")
        .def_ro("old_state", &StateChangeEventPy::old_state)
        .def_ro("new_state", &StateChangeEventPy::new_state);

    nb::class_<PauseChangeEventPy>(m, "PauseChangeEvent")
        .def_ro("paused", &PauseChangeEventPy::paused);

    nb::class_<LogEventPy>(m, "LogEvent")
        .def_ro("level", &LogEventPy::level)
        .def_ro("message", &LogEventPy::message);

    nb::class_<Recognizer>(m, "Recognizer")
        .def(nb::init<const ConfigSpec&>(), nb::arg("config"))
        .def("start", &Recognizer::start, nb::arg("timeout") = 5.0)
        .def("stop", &Recognizer::stop, nb::arg("timeout") = 5.0)
        .def("pause", &Recognizer::pause, nb::arg("timeout") = 2.0)
        .def("resume", &Recognizer::resume, nb::arg("timeout") = 2.0)
        .def("restart", &Recognizer::restart, nb::arg("timeout") = 5.0)
        .def("close", &Recognizer::close)
        .def("update_grammar", &Recognizer::update_grammar, nb::arg("verbs"),
             nb::arg("timeout") = 5.0)
        .def("poll_events", &Recognizer::poll_events)
        .def("on_recognized", &Recognizer::on_recognized, nb::arg("callback"))
        .def("on_rejected", &Recognizer::on_rejected, nb::arg("callback"))
        .def("on_state_change", &Recognizer::on_state_change, nb::arg("callback"))
        .def("on_pause_change", &Recognizer::on_pause_change, nb::arg("callback"))
        .def("on_log", &Recognizer::on_log, nb::arg("callback"))
        .def_prop_ro("state", &Recognizer::state);
}
