"""
Caps Lock toggle suppression for KDE Plasma Wayland.

The X11 backend runs 'setxkbmap -option caps:none' so that holding the
quasimode trigger does not toggle Caps Lock.  On Plasma Wayland the
XKB configuration is owned by KWin and read from ~/.config/kxkbrc, so
the same option is applied by editing that file; this covers native
Wayland and XWayland applications alike.

Three Plasma quirks matter here (verified against KWin 6.6):

  * KWin only honors the Options key of [Layout] when ResetOldOptions
    is true in the same group (kwin src/xkb.cpp), so that flag must be
    set alongside.
  * KWin 6 reloads kxkbrc through a KConfigWatcher, which reacts to
    KConfig's own D-Bus change notifications -- hence every write must
    go through 'kwriteconfig6 --notify'.  A write that does not change
    the value emits no notification, so to force a reload the Options
    value is first cleared and then set.
  * The org.kde.keyboard /Layouts reloadConfig D-Bus call of Plasma 5
    no longer exists (the name survives only as a broadcast signal that
    current KWin ignores); it is still emitted for older Plasmas.

The original values are restored on exit (also via atexit, so a crash
of Enso core does not leave the user without Caps Lock).
"""

import atexit
import logging
import shutil
import subprocess

_original_options = None
_original_reset = None
_applied = False


def _tool(*names):
    for name in names:
        if shutil.which(name):
            return name
    return None


def _run(argv):
    return subprocess.run(argv, capture_output=True, text=True)


def _write(kwriteconfig, key, value):
    _run([kwriteconfig, "--notify", "--file", "kxkbrc",
          "--group", "Layout", "--key", key, value])


def _delete(kwriteconfig, key):
    _run([kwriteconfig, "--notify", "--file", "kxkbrc",
          "--group", "Layout", "--key", key, "--delete"])


def _read(kreadconfig, key):
    result = _run([kreadconfig, "--file", "kxkbrc",
                   "--group", "Layout", "--key", key])
    return result.stdout.strip()


def _emit_legacy_reload_signal():
    """Plasma 5 reloaded layouts on this broadcast; harmless on 6."""
    gdbus = _tool("gdbus")
    if gdbus:
        _run([gdbus, "emit", "--session", "--object-path", "/Layouts",
              "--signal", "org.kde.keyboard.reloadConfig"])


def disable_caps_lock():
    """Adds caps:none to the session XKB options so the trigger key no
    longer toggles Caps Lock.  Safe to call repeatedly."""
    global _original_options, _original_reset, _applied
    if _applied:
        return
    kwriteconfig = _tool("kwriteconfig6", "kwriteconfig5")
    kreadconfig = _tool("kreadconfig6", "kreadconfig5")
    if not kwriteconfig or not kreadconfig:
        logging.warning("kwriteconfig/kreadconfig not found; Caps Lock "
                        "will keep toggling while used as the Enso "
                        "trigger key.")
        return
    options = _read(kreadconfig, "Options")
    reset = _read(kreadconfig, "ResetOldOptions")
    parts = [o for o in options.split(",") if o]
    if "caps:none" in parts and reset == "true":
        # Configured by the user; applied at session start, and there
        # is nothing for us to restore later.
        _applied = True
        return
    _original_options = options
    _original_reset = reset
    if "caps:none" not in parts:
        parts.append("caps:none")
    if reset != "true":
        _write(kwriteconfig, "ResetOldOptions", "true")
    # Clear first: the config watcher only fires on actual changes,
    # and the file may already hold the target value without it being
    # in effect (e.g. left behind by a crash).
    _write(kwriteconfig, "Options", "")
    _write(kwriteconfig, "Options", ",".join(parts))
    _emit_legacy_reload_signal()
    _applied = True
    atexit.register(enable_caps_lock)
    logging.info("Applied XKB option caps:none for the Enso trigger key.")


def enable_caps_lock():
    """Restores the XKB options that were in effect before
    disable_caps_lock().  Safe to call repeatedly."""
    global _original_options, _original_reset, _applied
    if not _applied or _original_options is None:
        _applied = False
        return
    kwriteconfig = _tool("kwriteconfig6", "kwriteconfig5")
    if kwriteconfig:
        if _original_options:
            _write(kwriteconfig, "Options", _original_options)
        else:
            _delete(kwriteconfig, "Options")
        if _original_reset:
            _write(kwriteconfig, "ResetOldOptions", _original_reset)
        else:
            _delete(kwriteconfig, "ResetOldOptions")
        _emit_legacy_reload_signal()
    _original_options = None
    _original_reset = None
    _applied = False
