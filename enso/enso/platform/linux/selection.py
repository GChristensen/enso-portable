"""
X11 implementation of the Enso "selection" provider (text only).

Based on the original Enso Linux port:
Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
Rewritten for Python 3 / PyGObject.

get() reads the PRIMARY selection (the text currently highlighted).
set() puts the text on both CLIPBOARD and PRIMARY, then synthesizes a
Ctrl+V key press via XTEST so the focused application pastes it.
"""

import logging
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from Xlib import X
from Xlib.ext import xtest

from enso.platform.linux import utils

# Delay between claiming the clipboard and synthesizing the paste, so
# the target application sees the new clipboard owner.
_PASTE_DELAY = 0.05


def get():
    """Returns a dictionary with the current selection, or {}."""
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
    text = clipboard.wait_for_text()
    if text:
        return {"text": text}
    return {}


def _fake_paste():
    display = utils.get_display()
    control = utils.get_keycode("Control_L", display)
    v_key = utils.get_keycode("v", display)
    if not control or not v_key:
        logging.warning("Couldn't resolve Ctrl+V keycodes for pasting.")
        return
    xtest.fake_input(display, X.KeyPress, control)
    xtest.fake_input(display, X.KeyPress, v_key)
    xtest.fake_input(display, X.KeyRelease, v_key)
    xtest.fake_input(display, X.KeyRelease, control)
    display.sync()


def set(seldict):
    """Pastes the text of the given selection dictionary, if any."""
    text = seldict.get("text")
    if not text:
        return False

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(text, -1)
    # Let a clipboard manager (e.g. klipper) take over the contents so
    # they survive after Enso's claim is replaced.
    clipboard.store()

    primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
    primary.set_text(text, -1)

    time.sleep(_PASTE_DELAY)
    _fake_paste()
    return True
