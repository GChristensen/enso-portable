// voicecmd — recognizer backend abstraction (the seam SAPI / Vosk plug into).
//
// A backend owns the engine + grammars. It classifies each recognition by
// *semantic identity* (never by word position) and normalizes confidence onto
// 0..1 before posting a RawRecognition to the core-supplied sink. The sink is
// the ONLY way a backend communicates with the core; sink calls arrive on a
// backend-owned callback thread and must return promptly (they only enqueue).
#ifndef VOICECMD_BACKEND_H
#define VOICECMD_BACKEND_H

#include <string>
#include <vector>

#include "voicecmd/config.h"
#include "voicecmd/events.h"  // LogLevel

namespace voicecmd {

// Which set of rules is active on the single engine at a given moment.
enum class Ruleset {
    Commands,    // all enabled verb rules + garbage
    ResumeOnly,  // only "resume listening" + garbage (soft-paused)
    YesNo,       // only yes/no + garbage (confirmation window)
};

enum class RawKind {
    Command,  // matched a verb (+ optional noun) rule
    Control,  // matched a control phrase ("stop"/"resume listening")
    YesNo,    // matched a yes/no rule (during confirmation)
    Garbage,  // absorbed by the garbage rule / out-of-grammar
};

enum class ControlPhrase { None, StopListening, ResumeListening };
enum class YesNoAnswer { None, Yes, No };

// One classified recognition, produced by the backend from semantic tags.
struct RawRecognition {
    RawKind kind = RawKind::Garbage;

    // Valid when kind == Command. Indices into Config::verbs and Verb::nouns.
    int verb_index = -1;
    int noun_index = -1;  // -1 = verb-only

    ControlPhrase control = ControlPhrase::None;  // valid when kind == Control
    YesNoAnswer answer = YesNoAnswer::None;       // valid when kind == YesNo

    // Dictated tail for a free_text verb, verbatim as transcribed and NOT
    // normalized (spoken "two plus two" stays "two plus two"). Empty unless the
    // verb set free_text and the speaker actually said something after it.
    std::string free_text;

    std::string text;         // fully-resolved utterance (for the host)
    double confidence = 0.0;  // normalized 0..1 (backend-owned mapping)
};

// Implemented by the core; called by backends on their callback thread.
class BackendSink {
public:
    virtual ~BackendSink() = default;
    virtual void onRecognition(RawRecognition r) = 0;
    // Continuous recognition ended unexpectedly (device error / stream end not
    // requested by the host) — the core will post a restart.
    virtual void onBackendEnded() = 0;
    virtual void onLog(LogLevel level, std::string msg) = 0;
};

class IRecognizerBackend {
public:
    virtual ~IRecognizerBackend() = default;

    // Build the engine + all grammars from cfg. Does not begin recognition.
    virtual void create(const Config& cfg, BackendSink* sink) = 0;
    // Replace the command grammar (host grammar update). Cheap; keeps the engine.
    virtual void updateGrammar(const std::vector<Verb>& verbs) = 0;
    // Swap which rules are active (no second engine, no device contention).
    virtual void setActiveRuleset(Ruleset r) = 0;

    virtual void start() = 0;  // begin continuous recognition
    virtual void stop() = 0;   // cancel recognition; retain engine + grammars
    virtual void dispose() = 0;  // release the engine entirely
};

}  // namespace voicecmd

#endif  // VOICECMD_BACKEND_H
