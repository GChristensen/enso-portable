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

The original values are restored on exit (also via atexit).  Since a
hard kill runs neither, the originals are additionally persisted to a
backup file in the Enso user directory when they are modified: a
backup found on the next start identifies leftover state from a
crashed session (as opposed to the user's own configuration), so it
can be adopted and restored on the next clean exit.
"""

import atexit
import json
import logging
import os
import shutil
import subprocess

from enso import config

_BACKUP_FILE = os.path.join(config.ENSO_USER_DIR, "xkb_options_backup.json")

_original_options = None
_original_reset = None
_applied = False


def _load_backup():
    try:
        with open(_BACKUP_FILE) as f:
            data = json.load(f)
        return data["options"], data["reset"]
    except (OSError, ValueError, KeyError):
        return None


def _save_backup(options, reset):
    try:
        os.makedirs(os.path.dirname(_BACKUP_FILE), exist_ok=True)
        with open(_BACKUP_FILE, "w") as f:
            json.dump({"options": options, "reset": reset}, f)
    except OSError:
        logging.exception("Couldn't write the XKB options backup; the "
                          "original options won't survive a hard kill.")


def _drop_backup():
    try:
        os.remove(_BACKUP_FILE)
    except OSError:
        pass


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
    backup = _load_backup()
    if backup is not None:
        # Leftover state from a session that was killed before it
        # could restore; the backup holds the true originals.  Adopt
        # them and re-apply from scratch below.
        logging.info("Found XKB options left over from a previous Enso "
                     "session; adopting its backup for restoration.")
        _original_options, _original_reset = backup
    else:
        parts = [o for o in options.split(",") if o]
        if "caps:none" in parts and reset == "true":
            # Genuinely configured by the user (no Enso backup exists);
            # applied at session start, nothing to restore later.
            _applied = True
            return
        _original_options = options
        _original_reset = reset
        _save_backup(options, reset)
    parts = [o for o in options.split(",") if o]
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
        _drop_backup()
    _original_options = None
    _original_reset = None
    _applied = False
