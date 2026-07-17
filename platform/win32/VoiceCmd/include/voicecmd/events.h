// voicecmd — events delivered core -> host (pull via drain(), or push callback).
#ifndef VOICECMD_EVENTS_H
#define VOICECMD_EVENTS_H

#include <string>
#include <variant>

#include "voicecmd/config.h"

namespace voicecmd {

// Public lifecycle state. Idle = constructed, backend not yet created.
enum class State {
    Idle,
    Starting,
    Listening,
    SoftPaused,
    Stopping,
    Stopped,       // engine + grammars retained; cheap re-start
    Restarting,
    ShuttingDown,  // engine being disposed
    Closed,        // worker stopped; terminal
};

const char* to_string(State s);

enum class LogLevel { Debug, Info, Warning, Error };

const char* to_string(LogLevel l);

// A successful (and, where required, confirmed) recognition.
struct RecognitionEvent {
    std::string verb;    // original casing, exactly as configured
    std::string noun;    // original casing; empty for verb-only commands
    std::string text;    // fully-resolved utterance for host command resolution
    double confidence = 0.0;
    UserData verb_data;  // opaque payload from the matched Verb
    UserData noun_data;  // opaque payload from the matched Noun (may be null)
    bool confirmed = true;
};

// Optional telemetry for discarded / out-of-grammar speech (calibration channel).
struct RejectionEvent {
    std::string text;
    double confidence = 0.0;
};

struct StateChangeEvent {
    State old_state;
    State new_state;
};

struct PauseChangeEvent {
    bool paused;
};

struct LogEvent {
    LogLevel level;
    std::string message;
};

using Event = std::variant<RecognitionEvent, RejectionEvent, StateChangeEvent,
                           PauseChangeEvent, LogEvent>;

}  // namespace voicecmd

#endif  // VOICECMD_EVENTS_H
