// voicecmd — configuration value types (backend-agnostic, Python-free, COM-free).
//
// The core deliberately uses UTF-8 std::string everywhere; the SAPI backend is
// the only layer that converts to/from UTF-16 std::wstring at its boundary.
#ifndef VOICECMD_CONFIG_H
#define VOICECMD_CONFIG_H

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace voicecmd {

// Opaque, caller-owned payload carried verbatim through the core and returned
// in events. In the Python binding this wraps a py::object whose deleter
// re-acquires the GIL; the core never inspects it.
using UserData = std::shared_ptr<void>;

enum class Backend {
    Sapi,   // in-process SAPI 5 (default)
    Fake,   // deterministic test double, no audio/COM
    Vosk,   // reserved for a later milestone
};

enum class ConfirmStyle {
    YesNo,       // "Say 'Yes' or 'No'…"
    RepeatVerb,  // reserved
};

struct Noun {
    std::string name;                        // original casing, echoed in events
    bool confirm = false;                    // force confirmation for this noun
    std::optional<double> min_confidence;    // per-noun accept override (0..1)
    UserData user_data;                      // opaque
};

struct Verb {
    std::string name;                        // original casing, echoed in events
    std::vector<Noun> nouns;                 // may be empty (verb-only command)
    bool confirm = false;                    // force confirmation for this verb
    bool disabled = false;                   // excluded from the active grammar
    // Accept an arbitrary spoken argument after the verb, transcribed by the
    // engine's dictation topic rather than matched against `nouns`. For hosts
    // whose command takes a free-form parameter that cannot be enumerated
    // ("calculate {expression}"). The tail stays OPTIONAL, so the bare verb
    // still matches. Costs precision: a dictation transition will match almost
    // any audio, so enable it only for verbs that genuinely need it.
    bool free_text = false;
    std::string description;
    UserData user_data;                      // opaque
};

struct Config {
    // Keyword prefix
    std::string keyword = "computer";
    bool keyword_required = true;

    // Normalized confidence thresholds (0..1). See §5 of the plan — each backend
    // owns the mapping from its native scale onto this range.
    double accept_confidence = 0.85;
    double reject_confidence = 0.5;
    double confirm_yes_confidence = 0.92;

    // Grammar (already filtered by the host; disabled verbs are also honored here)
    std::vector<Verb> verbs;

    // Engine / locale
    Backend backend = Backend::Sapi;
    std::string language = "en-US";

    // Feature toggles
    bool session_lock = true;
    bool rejection_events = true;
    ConfirmStyle confirm_style = ConfirmStyle::YesNo;

    // A SAPI wildcard "garbage" rule can absorb out-of-grammar speech, but in
    // practice it OVER-matches and wins over real command rules. SAPI already
    // rejects OOV via SPEI_FALSE_RECOGNITION + low confidence, so this defaults
    // off; enable only if false-accepts prove to be a problem.
    bool use_garbage_rule = false;

    // Use the SHARED SAPI recognizer (system-wide; uses the user's trained
    // Windows Speech profile + the microphone configured in Speech settings)
    // instead of the in-process recognizer with default audio. The shared engine
    // is typically far better calibrated -- correct commands get real HIGH/NORMAL
    // confidence and out-of-grammar speech is rejected -- at the cost of sharing
    // the engine with Windows Speech Recognition.
    bool shared_recognizer = false;

    // SAPI's per-recognition confidence is unreliable for command-and-control
    // grammars -- it reports correct, fully-matched command phrases at the same
    // low confidence as noise. So by default a constrained-grammar command match
    // is TRUSTED (the required keyword + fixed grammar are the precision guard)
    // and dispatched regardless of the confidence band; explicit verb/noun
    // `confirm` flags are still honored. Set false for a backend with reliable
    // confidence (e.g. Vosk) to use the three-band thresholds instead.
    bool trust_grammar_match = true;

    // Confirmation dialog timeout (seconds); on timeout the answer defaults to "no".
    double confirm_timeout_sec = 10.0;

    // Restart back-off (seconds) to let the audio device release between
    // shutdown and start during auto-recovery / restart().
    double restart_delay_sec = 1.0;
};

}  // namespace voicecmd

#endif  // VOICECMD_CONFIG_H
