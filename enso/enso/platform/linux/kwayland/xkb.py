"""
Caps Lock toggle suppression for KDE Plasma Wayland.

The X11 backend runs 'setxkbmap -option caps:none' so that holding the
quasimode trigger does not toggle Caps Lock.  On Plasma Wayland the
XKB configuration is owned by KWin and read from ~/.config/kxkbrc, so
the same option is applied by editing that file with kwriteconfig and
asking the keyboard daemon to reload; this covers native Wayland and
XWayland applications alike.

The original Options value is restored on exit (also via atexit, so a
crash of Enso core does not leave the user without Caps Lock).
"""

import atexit
import logging
import shutil
import subprocess

_original_options = None
_applied = False


def _tool(*names):
    for name in names:
        if shutil.which(name):
            return name
    return None


def _run(argv):
    return subprocess.run(argv, capture_output=True, text=True)


def _reload_layouts():
    """Asks the Plasma keyboard daemon to re-read kxkbrc."""
    gdbus = _tool("gdbus")
    if gdbus:
        result = _run([gdbus, "call", "--session",
                       "--dest", "org.kde.keyboard",
                       "--object-path", "/Layouts",
                       "--method", "org.kde.keyboard.reloadConfig"])
        if result.returncode == 0:
            return True
    qdbus = _tool("qdbus6", "qdbus")
    if qdbus:
        result = _run([qdbus, "org.kde.keyboard", "/Layouts",
                       "org.kde.keyboard.reloadConfig"])
        if result.returncode == 0:
            return True
    logging.warning("Couldn't ask org.kde.keyboard to reload the XKB "
                    "configuration; is this a Plasma session?")
    return False


def _read_options(kreadconfig):
    result = _run([kreadconfig, "--file", "kxkbrc",
                   "--group", "Layout", "--key", "Options"])
    return result.stdout.strip()


def disable_caps_lock():
    """Adds caps:none to the session XKB options so the trigger key no
    longer toggles Caps Lock.  Safe to call repeatedly."""
    global _original_options, _applied
    if _applied:
        return
    kwriteconfig = _tool("kwriteconfig6", "kwriteconfig5")
    kreadconfig = _tool("kreadconfig6", "kreadconfig5")
    if not kwriteconfig or not kreadconfig:
        logging.warning("kwriteconfig/kreadconfig not found; Caps Lock "
                        "will keep toggling while used as the Enso "
                        "trigger key.")
        return
    options = _read_options(kreadconfig)
    parts = [o for o in options.split(",") if o]
    if "caps:none" in parts:
        # Already configured by the user; nothing to apply or restore.
        _applied = True
        return
    _original_options = options
    parts.append("caps:none")
    _run([kwriteconfig, "--file", "kxkbrc",
          "--group", "Layout", "--key", "Options", ",".join(parts)])
    _reload_layouts()
    _applied = True
    atexit.register(enable_caps_lock)
    logging.info("Applied XKB option caps:none for the Enso trigger key.")


def enable_caps_lock():
    """Restores the XKB options that were in effect before
    disable_caps_lock().  Safe to call repeatedly."""
    global _original_options, _applied
    if not _applied or _original_options is None:
        _applied = False
        return
    kwriteconfig = _tool("kwriteconfig6", "kwriteconfig5")
    if kwriteconfig:
        if _original_options:
            _run([kwriteconfig, "--file", "kxkbrc",
                  "--group", "Layout", "--key", "Options",
                  _original_options])
        else:
            _run([kwriteconfig, "--file", "kxkbrc",
                  "--group", "Layout", "--key", "Options", "--delete"])
        _reload_layouts()
    _original_options = None
    _applied = False
