# ----------------------------------------------------------------------------
#
#   enso.contrib.voicecmd
#
# ----------------------------------------------------------------------------

"""
    Python mock of the "voicecmd" voice-recognition library.

    This module has no dependency on Enso; it stands in for what will
    eventually be a compiled (pybind11-wrapped) native library, exposing
    the same shape of API: config dataclasses, a VoiceRecognitionManager
    with pull-mode event delivery via poll_events(), and a background
    "engine thread" that never touches caller state except through a
    lock-protected queue.

    Instead of doing real speech recognition, it simulates a microphone
    that periodically "hears" a fixed utterance and enqueues a
    RecognitionEvent if that utterance matches something in the grammar
    it was configured with.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import threading
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

@dataclass
class VerbPhrase:
    """
    A single recognizable phrase in the grammar. 'name' is the
    caller-defined identifier for the phrase (for Enso, this is the
    registered command-expression string, e.g. "open {object}").
    """
    name: str
    description: str = ""
    user_data: Any = None


@dataclass
class VoiceConfig:
    """
    Grammar passed to VoiceRecognitionManager at construction time.
    Verbs are expected to already be filtered down to whatever the
    caller wants recognizable -- the library itself has no separate
    per-verb "enabled" flag.
    """
    verbs: List[VerbPhrase] = field(default_factory=list)


@dataclass
class RecognitionEvent:
    """
    A single recognized utterance, delivered via poll_events().
    """
    text: str
    verb: str


# ----------------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------------

class VoiceRecognitionManager:
    """
    Mock voice recognition engine.

    A background timer simulates the microphone "hearing" MOCK_UTTERANCE
    every MOCK_INTERVAL seconds. If MOCK_UTTERANCE matches a verb
    currently in the grammar, a RecognitionEvent is placed on a
    thread-safe queue for the caller to drain via poll_events(). The
    timer callback never calls back into caller code directly -- it only
    touches the queue, under lock, matching the threading contract the
    real native library will use.
    """

    MOCK_INTERVAL = 30.0
    MOCK_UTTERANCE = "open notepad"

    def __init__(self, config: VoiceConfig):
        self.__config = config
        self.__queue = []
        self.__lock = threading.Lock()
        self.__timer: Optional[threading.Timer] = None
        self.__running = False

    def start(self):
        """
        Starts the background recognition timer.
        """
        with self.__lock:
            if self.__running:
                return
            self.__running = True
        self.__scheduleNext()

    def stop(self, timeout: float = 5.0):
        """
        Stops the background recognition timer and blocks until the
        engine thread has actually terminated (any in-flight recognition
        callback runs to completion first), waiting at most `timeout`
        seconds. Idempotent and safe to call from atexit.
        """
        with self.__lock:
            self.__running = False
            timer = self.__timer
            self.__timer = None

        if timer is not None:
            # Cancel a pending (not-yet-fired) wait, then block until the
            # timer thread exits. Never join our own thread -- stop() may
            # be reached from within the recognition callback.
            timer.cancel()
            if timer is not threading.current_thread():
                timer.join(timeout)
            # print() rather than logging so it is visible at Enso's
            # default ERROR log level (mock/debug signal only).
            print("voicecmd: recognition stopped")

    def update_verbs(self, verbs: List[VerbPhrase]):
        """
        Replaces the grammar used to decide whether a mock-recognized
        utterance actually produces an event.
        """
        with self.__lock:
            self.__config.verbs = verbs

    def poll_events(self) -> List[RecognitionEvent]:
        """
        Drains and returns all events queued since the last call.
        """
        with self.__lock:
            events, self.__queue = self.__queue, []
        return events

    def __scheduleNext(self):
        with self.__lock:
            if not self.__running:
                return
            self.__timer = threading.Timer(
                self.MOCK_INTERVAL, self.__onMockRecognition
            )
            self.__timer.daemon = True
            self.__timer.start()

    def __onMockRecognition(self):
        # Runs on the mock "engine thread" -- must behave as if it can
        # never touch caller (Enso/GIL-bound) state directly, only the
        # lock-protected queue, matching the real library's contract.
        matched = self.__matchVerb(self.MOCK_UTTERANCE)
        if matched is not None:
            # print() rather than logging.info() so it is visible even at
            # Enso's default ERROR log level (mock/debug signal only).
            print("voicecmd: mock recognized '%s' (matched verb '%s')"
                  % (self.MOCK_UTTERANCE, matched.name))
            with self.__lock:
                self.__queue.append(
                    RecognitionEvent(text=self.MOCK_UTTERANCE, verb=matched.name)
                )
        else:
            with self.__lock:
                verb_count = len(self.__config.verbs)
            print("voicecmd: mock heartbeat -- '%s' matched no verb "
                  "(%d verb(s) in grammar; enable a command for voice "
                  "with the microphone checkbox)"
                  % (self.MOCK_UTTERANCE, verb_count))
        self.__scheduleNext()

    def __matchVerb(self, utterance: str) -> Optional[VerbPhrase]:
        with self.__lock:
            verbs = list(self.__config.verbs)
        for verb in verbs:
            prefix = verb.name.split("{", 1)[0]
            if utterance.startswith(prefix):
                return verb
        return None

# vim:set tabstop=4 shiftwidth=4 expandtab:
