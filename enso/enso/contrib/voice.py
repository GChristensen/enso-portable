# ----------------------------------------------------------------------------
#
#   enso.contrib.voice
#
# ----------------------------------------------------------------------------

"""
    An Enso plugin that bridges the (currently mocked) voicecmd
    voice-recognition library into Enso's event/command system.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

from enso import config
from enso.events import EventManager
from enso.commands import CommandManager

try:
    from enso.contrib.voicecmd import VoiceConfig, VoiceRecognitionManager, VerbPhrase
    _VOICECMD_AVAILABLE = True
except ImportError:
    # The native voicecmd module may legitimately be absent (unsupported
    # platform, partial install) -- degrade gracefully rather than let
    # this abort loading of every plugin listed after this one.
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

    _voiceManager = VoiceRecognitionManager(VoiceConfig(verbs=_buildVerbs()))
    _voiceManager.start()

    EventManager.get().registerResponder(_onTick, "timer")


def _buildVerbs():
    """
    Builds the voice grammar from every registered command that has been
    enabled for voice via the webui checkbox. Filtering happens here,
    before the library is initialized/updated -- voicecmd itself has no
    notion of a per-verb "enabled" flag.
    """
    commands = CommandManager.get().getCommands()
    return [
        VerbPhrase(name=name, description=command.getDescription() or "")
        for name, command in commands.items()
        if name in config.VOICE_COMMANDS
    ]


def _onTick(msPassed):
    # enso.events.EventManager.onTick() calls "timer" responders with no
    # exception handling of its own -- anything raised here propagates
    # straight through the native InputManager callback and takes down
    # the whole event loop. Never let that happen; log and move on.
    try:
        if config.VOICE_COMMANDS_CHANGED:
            config.VOICE_COMMANDS_CHANGED = False
            _voiceManager.update_verbs(_buildVerbs())

        for event in _voiceManager.poll_events():
            _handleRecognition(event)
    except Exception:
        logging.error("enso.contrib.voice: tick handler failed", exc_info=True)


def _handleRecognition(event):
    try:
        cmd = CommandManager.get().getCommand(event.text)
    except Exception:
        logging.error(
            "enso.contrib.voice: failed to resolve '%s'", event.text, exc_info=True
        )
        return

    if cmd is None:
        logging.warning(
            "enso.contrib.voice: recognized '%s' but no matching command",
            event.text,
        )
        return

    logging.info("VOICE COMMAND: %s", event.text)
    try:
        cmd.run()
    except Exception:
        logging.error(
            "enso.contrib.voice: command '%s' failed", event.text, exc_info=True
        )

# vim:set tabstop=4 shiftwidth=4 expandtab:
