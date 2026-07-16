"""
KDE Wayland implementation of the Enso "selection" provider (text only).

A Wayland client can normally only read or claim selections while it
has keyboard focus, so this module shells out to wl-clipboard
(wl-paste/wl-copy), which uses the data-control protocol and works
regardless of focus; klipper's D-Bus interface is the fallback for the
clipboard when wl-clipboard is not installed.

get() reads the PRIMARY selection (the text currently highlighted),
falling back to the clipboard.  set() puts the text on both CLIPBOARD
and PRIMARY, then synthesizes a Ctrl+V key press through a uinput
virtual keyboard (XTEST only reaches XWayland windows).  uinput needs
write access to /dev/uinput -- see the udev rule in the setup notes;
without it the text is still placed on the clipboard and a message
asks the user to paste manually.
"""

import logging
import shutil
import subprocess
import time

from evdev import UInput, ecodes

from enso.platform.linux.kwayland import utils

# Delay between claiming the clipboard and synthesizing the paste: the
# compositor needs to give focus back to the target application after
# the quasimode key sink releases it, and the target must see the new
# clipboard owner.
_PASTE_DELAY = 0.15

# Delay after creating the uinput device, so the compositor has picked
# the new "keyboard" up before it starts typing.
_UINPUT_SETTLE = 0.2

_uinput = None
_uinput_warned = False


def _run(argv, input_text=None, capture=True):
    # wl-copy forks a child that keeps serving the clipboard; that child
    # inherits captured stdout/stderr pipes and run() would then block on
    # them until the timeout, so callers spawning wl-copy pass capture=False.
    out = subprocess.PIPE if capture else subprocess.DEVNULL
    return subprocess.run(argv, input=input_text, stdout=out, stderr=out,
                          text=True, timeout=5)


def _klipper(method, *args):
    """Calls a klipper D-Bus method; returns stdout or None."""
    if not shutil.which("gdbus"):
        return None
    argv = ["gdbus", "call", "--session", "--dest", "org.kde.klipper",
            "--object-path", "/klipper",
            "--method", "org.kde.klipper.klipper." + method] + list(args)
    try:
        result = _run(argv)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    # gdbus prints "('text',)"; strip the tuple decoration.
    out = result.stdout.strip()
    if out.startswith("('") and out.endswith("',)"):
        return out[2:-3]
    return ""


def get():
    """Returns a dictionary with the current selection, or {}."""
    if shutil.which("wl-paste"):
        for extra in (["--primary"], []):
            try:
                result = _run(["wl-paste", "--no-newline"] + extra)
            except (OSError, subprocess.TimeoutExpired):
                break
            if result.returncode == 0 and result.stdout:
                return {"text": result.stdout}
        return {}
    logging.warning("wl-paste not found (install wl-clipboard); trying "
                    "klipper, which only offers the clipboard, not the "
                    "highlighted text.")
    text = _klipper("getClipboardContents")
    if text:
        return {"text": text}
    return {}


def _get_uinput():
    global _uinput, _uinput_warned
    if _uinput is None:
        try:
            _uinput = UInput(
                {ecodes.EV_KEY: [ecodes.KEY_LEFTCTRL, ecodes.KEY_V]},
                name=utils.UINPUT_DEVICE_NAME)
            time.sleep(_UINPUT_SETTLE)
        except Exception:
            if not _uinput_warned:
                _uinput_warned = True
                logging.warning(
                    "Can't open /dev/uinput, so Enso can't synthesize the "
                    "paste keystroke.  Allow it with a udev rule, e.g.: "
                    "echo 'KERNEL==\"uinput\", GROUP=\"input\", "
                    "MODE=\"0660\"' | sudo tee "
                    "/etc/udev/rules.d/99-enso-uinput.rules && sudo "
                    "udevadm trigger /dev/uinput")
            return None
    return _uinput


def _fake_paste():
    device = _get_uinput()
    if device is None:
        return False
    for code, value in ((ecodes.KEY_LEFTCTRL, 1), (ecodes.KEY_V, 1),
                        (ecodes.KEY_V, 0), (ecodes.KEY_LEFTCTRL, 0)):
        device.write(ecodes.EV_KEY, code, value)
        device.syn()
    return True


def set(seldict):
    """Pastes the text of the given selection dictionary, if any."""
    text = seldict.get("text")
    if not text:
        return False

    if shutil.which("wl-copy"):
        try:
            _run(["wl-copy"], input_text=text, capture=False)
            _run(["wl-copy", "--primary"], input_text=text, capture=False)
        except (OSError, subprocess.TimeoutExpired):
            logging.exception("wl-copy failed")
            return False
    elif _klipper("setClipboardContents", text) is None:
        logging.error("Neither wl-copy nor klipper is available; "
                      "can't set the clipboard.")
        return False

    time.sleep(_PASTE_DELAY)
    if not _fake_paste():
        # The text is on the clipboard at least; let the user know why
        # nothing appeared.
        from enso import messages
        messages.displayMessage("<p>Text placed on the clipboard; "
                                "press Ctrl+V to paste it.</p>")
    return True
