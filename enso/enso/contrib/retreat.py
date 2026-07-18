# ----------------------------------------------------------------------------
#
#   enso.contrib.retreat
#
# ----------------------------------------------------------------------------

"""
    Enso Retreat -- break reminders, backed by the native ``retreatlib``
    module.

    This is an ordinary Enso plugin: it is listed in ``enso.config.PLUGINS``
    and started from load(), rather than being driven by the launcher around
    enso.run(). Shutdown goes through atexit, which enso.plugins documents as
    the cleanup mechanism for plugins (there is no unload hook), and which
    covers both the quit and the restart paths since each ends this process
    normally.

    The native module is an optional Windows component and may legitimately be
    absent, so every entry point degrades to a no-op rather than raising.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import atexit
import importlib
import importlib.util
import logging

from enso import config

# The compiled module (retreatlib.pyd). Deliberately not named "retreat": an
# extension module shadows a same-named .py in the same package, which would
# hide this wrapper and its guards entirely.
_NATIVE_MODULE = "enso.contrib.retreatlib"


# ----------------------------------------------------------------------------
# Plugin lifecycle
# ----------------------------------------------------------------------------

def load():
    """Plugin entry point; called on Enso's init event."""
    if not _enabled():
        logging.info("enso.contrib.retreat: not started (%s).",
                     "disabled by RETREAT_DISABLE" if installed()
                     else "native module not installed")
        return

    start()
    atexit.register(stop)


# ----------------------------------------------------------------------------
# Native module access
# ----------------------------------------------------------------------------

def installed():
    """True if the native retreat module is present."""
    return importlib.util.find_spec(_NATIVE_MODULE) is not None


def _enabled():
    return not config.RETREAT_DISABLE and installed()


def _call(name):
    """
    Invoke a native entry point by name, or do nothing if retreat is disabled
    or not installed. Returns None in that case, which every caller already
    treats as "not locked" / "nothing happened".
    """
    if not _enabled():
        return None
    try:
        module = importlib.import_module(_NATIVE_MODULE)
        return getattr(module, name)()
    except Exception:
        logging.error("enso.contrib.retreat: %s() failed", name, exc_info=True)
        return None


# ----------------------------------------------------------------------------
# Public API. These double as the actions of the "retreat" command, which
# looks them up by name -- see enso/commands/retreat.py.
# ----------------------------------------------------------------------------

def start():
    return _call("start")


def stop():
    return _call("stop")


def is_locked():
    return _call("is_locked")


def take_break():
    return _call("take_break")


def delay():
    return _call("delay")


def skip():
    return _call("skip")


def settings():
    return _call("settings")


def about():
    return _call("about")


def debug():
    return _call("debug")