"""
X11 helper utilities for the Linux platform backend.

Based on the original Enso Linux port:
Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
Rewritten for Python 3 / PyGObject.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the conditions of the
BSD license (see the original file header in the project history)
are met.
"""

import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk

from Xlib import XK
from Xlib.display import Display

_display = None


def get_display():
    """Returns the shared X display connection for main-thread use.
    Threads must open their own connection with open_display()."""
    global _display
    if _display is None:
        _display = open_display()
    return _display


def open_display():
    """Opens a new X display connection; the caller owns it."""
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("DISPLAY is not set; Enso requires an X11 session.")
    return Display(os.environ["DISPLAY"])


def get_keycode(keyname, display=None):
    """Returns the X keycode for a raw keysym name, e.g. \"Caps_Lock\"."""
    if display is None:
        display = get_display()
    keysym = XK.string_to_keysym(keyname)
    if keysym == 0:
        return 0
    return display.keysym_to_keycode(keysym)


def keysym_to_char(keysym):
    """Returns the printable character for an X keysym, or None.
    GDK keyvals are X keysyms, so GDK's conversion table applies."""
    codepoint = Gdk.keyval_to_unicode(keysym)
    if codepoint == 0:
        return None
    char = chr(codepoint)
    if char.isprintable() and not char.isspace():
        return char
    return None


def _get_modifier_mask(display, keyname):
    """Returns the modifier mask bit for the modifier holding the given
    key (e.g. \"Num_Lock\" -> Mod2Mask on most setups), or 0."""
    keycode = get_keycode(keyname, display)
    if not keycode:
        return 0
    mapping = display.get_modifier_mapping()
    for index, keycodes in enumerate(mapping):
        if keycode in keycodes:
            return 1 << index
    return 0


def get_numlock_mask(display=None):
    if display is None:
        display = get_display()
    return _get_modifier_mask(display, "Num_Lock")


def get_lock_mask(display=None):
    if display is None:
        display = get_display()
    return _get_modifier_mask(display, "Caps_Lock")
