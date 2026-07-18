# ----------------------------------------------------------------------------
#
#   enso.contrib.voice
#
# ----------------------------------------------------------------------------

"""
    An Enso plugin that bridges the native ``voicecmd`` voice-recognition
    library into Enso's event/command system.

    Delivery is pull-mode: the native engine's background threads never call
    into Python; recognitions are drained on Enso's main thread via
    ``poll_events()`` from the ``"timer"`` tick, so command execution happens
    on the same thread as keyboard-triggered commands.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import atexit
import gc
import logging
from xml.sax.saxutils import escape

from enso import config
from enso.events import EventManager
from enso.commands import CommandManager
from enso.messages import displayMessage

try:
    # The native module exposes the spec-named API (Config/Verb/Noun/Recognizer).
    from enso.contrib.voicecmd import (
        Config, Verb, Noun, Recognizer, State, RecognitionEvent, RejectionEvent,
        StateChangeEvent, ConfirmationEvent, LogEvent,
    )
    _VOICECMD_AVAILABLE = True
except ImportError:
    # The native voicecmd.pyd may legitimately be absent (unsupported platform,
    # partial install) -- degrade gracefully rather than abort loading of every
    # plugin listed after this one.
    _VOICECMD_AVAILABLE = False


_voiceManager = None


# ----------------------------------------------------------------------------
# Plugin initialization
# ----------------------------------------------------------------------------

def load():
    global _voiceManager

    if not _VOICECMD_AVAILABLE:
        logging.warning(
            "enso.contrib.voice: voicecmd module not available "
            "(missing .pyd?); voice commands disabled."
        )
        return

    cfg = _buildConfig()
    if getattr(config, "VOICE_DEBUG", False):
        for v in cfg.verbs:
            sample = [n.name for n in v.nouns]
            if len(sample) > 8:
                sample = sample[:8] + ["..."]
            print("voicecmd: grammar verb '%s'%s"
                  % (v.name, (" nouns=%r" % sample) if v.nouns else " (verb-only)"))

    _voiceManager = Recognizer(cfg)
    _voiceManager.start()

    # print() rather than logging so it is visible at Enso's default ERROR level.
    kw = getattr(config, "VOICE_KEYWORD", "computer")
    required = getattr(config, "VOICE_KEYWORD_REQUIRED", True)
    print("voicecmd: listening (%s%s); %d command(s) enabled for voice"
          % ("keyword '%s' " % kw if required else "no keyword",
             "required" if required else "",
             len(config.VOICE_COMMANDS)))

    # Enso's quit and restart paths both end this process by stopping the event
    # loop and letting the interpreter exit normally (restart spawns a fresh
    # process via subprocess, it does not exec over this one), so atexit fires
    # for both. Close the engine there, blocking until its worker thread exits.
    atexit.register(_shutdown)

    EventManager.get().registerResponder(_onTick, "timer")


def _shutdown():
    """Blocking shutdown of the voice engine; runs at interpreter exit."""
    global _voiceManager
    # Before the engine check, not after: the engine emits a closing
    # ConfirmationEvent on stop but nothing polls it past this point, so a live
    # prompt has to be retracted here or it outlives Enso -- and that is just
    # as true when the engine has already gone away.
    _hideConfirmation()
    if _voiceManager is None:
        return
    try:
        _voiceManager.close()
    except Exception:
        logging.error("enso.contrib.voice: shutdown failed", exc_info=True)
    finally:
        _voiceManager = None
        # Drop the last native references so nanobind's exit-time leak checker
        # sees a clean slate instead of warning about the live Recognizer.
        gc.collect()


# ----------------------------------------------------------------------------
# Engine state, for hosts that surface it in their UI (the tray menu)
# ----------------------------------------------------------------------------

def is_installed():
    """
    True if the voicecmd library is importable.

    Static, unlike is_listening() -- it does not depend on the plugin having
    loaded yet, so it is safe to call while building UI during startup, where
    plugin load order is not guaranteed.
    """
    return _VOICECMD_AVAILABLE


def is_listening():
    """
    True while the engine is actively listening. False when it is soft-paused,
    stopped (the session lock does this), or not running at all.
    """
    manager = _voiceManager
    if manager is None:
        return False
    try:
        return manager.state == State.Listening
    except Exception:
        logging.error("enso.contrib.voice: could not read engine state",
                      exc_info=True)
        return False


def set_listening(listening):
    """Soft-pause or resume recognition. A no-op if the engine isn't running."""
    manager = _voiceManager
    if manager is None:
        return
    try:
        if listening:
            # start(), not resume(): resume() only acts on a soft pause, while
            # start() also covers the engine having been stopped outright --
            # which is what the session lock does.
            manager.start()
        else:
            manager.pause()
    except Exception:
        logging.error("enso.contrib.voice: could not toggle recognition",
                      exc_info=True)


# ----------------------------------------------------------------------------
# Grammar / config construction
# ----------------------------------------------------------------------------

def _buildConfig():
    return Config(
        keyword=getattr(config, "VOICE_KEYWORD", "computer"),
        keyword_required=getattr(config, "VOICE_KEYWORD_REQUIRED", True),
        accept_confidence=getattr(config, "VOICE_ACCEPT_CONFIDENCE", 0.85),
        reject_confidence=getattr(config, "VOICE_REJECT_CONFIDENCE", 0.5),
        backend=getattr(config, "VOICE_BACKEND", "sapi"),
        language=getattr(config, "VOICE_LANGUAGE", "en-US"),
        # Recognition-quality knobs (see config.py). trust_grammar_match=True
        # accepts any grammar match (max recall, risks force-matched garbage);
        # False uses the confidence bands. shared_recognizer uses the trained
        # Windows Speech profile for far better confidence discrimination.
        trust_grammar_match=getattr(config, "VOICE_TRUST_GRAMMAR_MATCH", True),
        shared_recognizer=getattr(config, "VOICE_SHARED_RECOGNIZER", False),
        use_garbage_rule=getattr(config, "VOICE_GARBAGE_RULE", False),
        verbs=_buildVerbs(),
    )


# Cap nouns per verb so a command factory with a huge learned list can't
# balloon the grammar (hurting recognition accuracy and load time).
_MAX_NOUNS_PER_VERB = 300


def _buildVerbs():
    """
    Builds the voice grammar from every registered command enabled for voice
    via the webui checkbox. Filtering happens here -- voicecmd has no per-verb
    "enabled" flag.

    A plain command becomes a verb-only phrase. A parameterized command
    ("open {object}") becomes a verb ("open") plus one noun per concrete
    argument enumerated from its command factory ("notepad", "google chrome",
    ...), so "computer open notepad" is a full grammar phrase that both
    recognizes and resolves.
    """
    commands = CommandManager.get().getCommands()
    verbs = []
    for name, command in commands.items():
        if name not in config.VOICE_COMMANDS:
            continue
        prefix = name.split("{", 1)[0].strip()
        if not prefix:
            continue
        nouns = _buildNouns(name, command) if "{" in name else []
        verbs.append(Verb(
            name=prefix,
            nouns=nouns,
            # Engine holds the command until the user says "yes" (or the
            # confirm timeout drops it). Honored regardless of the confidence
            # bands, so it works with trust_grammar_match too.
            confirm=name in config.VOICE_CONFIRM_COMMANDS,
            description=command.getDescription() or "",
            data=name,  # original command-expression, echoed back in events
        ))
    return verbs


def _buildNouns(name, command):
    """
    Enumerate the concrete argument values of a parameterized command from its
    factory (GenericPrefixFactory.getCommandList() -> ["open notepad", ...]) and
    turn each into a spoken noun. Factories that accept arbitrary arguments (no
    finite list) yield nothing, so such commands are recognized by verb alone.
    """
    get_list = getattr(command, "getCommandList", None)
    if not callable(get_list):
        return []
    prefix = name.split("{", 1)[0]  # keep the trailing space, if any
    nouns, seen = [], set()
    try:
        for full in get_list():
            if not isinstance(full, str) or not full.startswith(prefix):
                continue
            obj = full[len(prefix):].strip()
            if obj and "{" not in obj and obj not in seen:
                seen.add(obj)
                nouns.append(Noun(name=obj))
                if len(nouns) >= _MAX_NOUNS_PER_VERB:
                    logging.warning(
                        "enso.contrib.voice: '%s' capped at %d nouns",
                        name, _MAX_NOUNS_PER_VERB)
                    break
    except Exception:
        logging.error("enso.contrib.voice: noun enumeration failed for '%s'",
                      name, exc_info=True)
    return nouns


# ----------------------------------------------------------------------------
# Tick pump (main thread)
# ----------------------------------------------------------------------------

def _onTick(msPassed):
    # enso.events.EventManager.onTick() calls "timer" responders with no
    # exception handling of its own -- anything raised here propagates straight
    # through the native InputManager callback and takes down the whole event
    # loop. Never let that happen; log and move on.
    try:
        if config.VOICE_COMMANDS_CHANGED:
            config.VOICE_COMMANDS_CHANGED = False
            _voiceManager.update_grammar(_buildVerbs())

        debug = getattr(config, "VOICE_DEBUG", False)
        for event in _voiceManager.poll_events():
            if isinstance(event, RecognitionEvent):
                _handleRecognition(event)
            elif debug and isinstance(event, RejectionEvent):
                # Calibration channel: shows what the mic heard and how confident
                # the engine was, so accept/reject thresholds can be tuned.
                print("voicecmd: rejected '%s' (confidence=%.2f)"
                      % (event.text, event.confidence))
            elif isinstance(event, ConfirmationEvent):
                _renderConfirmation(event)
            elif debug and isinstance(event, StateChangeEvent):
                print("voicecmd: state %s -> %s"
                      % (event.old_state, event.new_state))
            elif debug and isinstance(event, LogEvent):
                print("voicecmd: %s" % event.message)
    except Exception:
        logging.error("enso.contrib.voice: tick handler failed", exc_info=True)


# True while one of our confirmation prompts is on screen, so we only ever
# dismiss a message we actually put up.
_confirmShown = False


def _renderConfirmation(event):
    """
    Shows/hides the prompt for a command awaiting confirmation.

    A primary message (the large centred overlay) rather than a mini message:
    this is a question blocking on an answer, not a passive notice tucked into
    the corner of the screen. The engine has already switched the grammar to
    yes/no and owns the timeout; the answer is spoken, so this is display only
    -- there is nothing to click.
    """
    global _confirmShown
    try:
        if event.active:
            displayMessage(config.VOICE_CONFIRM_MSG_XML % escape(event.phrase))
            _confirmShown = True
        else:
            _hideConfirmation()
    except Exception:
        logging.error("enso.contrib.voice: confirmation prompt failed",
                      exc_info=True)


def _hideConfirmation():
    """Retracts the prompt, if one of ours is up. Safe to call at any time."""
    global _confirmShown
    if not _confirmShown:
        return
    _confirmShown = False
    try:
        # A primary message otherwise sits there until the user dismisses it by
        # hand. The primary message window is the only "dismissal" responder in
        # Enso, so this fades exactly that message and nothing else. It
        # registers itself WAIT_TIME (80ms) after the message appears; before
        # then this is a no-op, which no spoken answer can outrun.
        EventManager.get().triggerEvent("dismissal")
    except Exception:
        logging.error("enso.contrib.voice: could not hide the confirmation "
                      "prompt", exc_info=True)


def _handleRecognition(event):
    # event.text is the resolved utterance ("open notepad" / "help") -- exactly
    # what getCommand parses, against both plain commands and "open {object}"
    # factories. (event.data still carries the original expression for the host.)
    target = event.text or event.data
    try:
        cmd = CommandManager.get().getCommand(target)
    except Exception:
        logging.error(
            "enso.contrib.voice: failed to resolve '%s'", target, exc_info=True
        )
        return

    if cmd is None:
        logging.warning(
            "enso.contrib.voice: recognized '%s' but no matching command", target
        )
        return

    # print() so it is visible at Enso's default ERROR log level.
    print("voicecmd: VOICE COMMAND '%s' (confidence=%.2f)" % (target, event.confidence))
    logging.info("VOICE COMMAND: %s (confidence=%.2f)", target, event.confidence)
    try:
        cmd.run()
    except Exception:
        logging.error(
            "enso.contrib.voice: command '%s' failed", target, exc_info=True
        )

# vim:set tabstop=4 shiftwidth=4 expandtab:
