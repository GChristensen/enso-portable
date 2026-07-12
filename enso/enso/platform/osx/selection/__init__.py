"""
Cocoa implementation of the Enso "selection" provider (text only).

Based on the original Enso OS X port:
Copyright (c) 2008, Humanized, Inc.
Rewritten for Python 3 / modern PyObjC; the legacy key_utils.so native
library is replaced with CGEventPost-simulated Cmd+C / Cmd+V.

get() simulates Cmd+C and reads the general pasteboard; set() writes
the text to the pasteboard and simulates Cmd+V.  Like the win32 and
X11 implementations, this clobbers the clipboard contents.
"""

import logging
import time

import AppKit
import Quartz

from enso.platform.osx.input import CASE_INSENSITIVE_KEYCODE_MAP

# Delay after simulating Cmd+C, so the focused application has time to
# fill the pasteboard, and between claiming the pasteboard and pasting.
_COPY_DELAY = 0.1
_PASTE_DELAY = 0.05

# kVK_ANSI_C / kVK_ANSI_V on a US layout; overridden below from the
# layout-aware keymap when possible.
_C_KEYCODE = 8
_V_KEYCODE = 9

for _keycode, _char in CASE_INSENSITIVE_KEYCODE_MAP.items():
    if _keycode < 1000:
        if _char == "c":
            _C_KEYCODE = _keycode
        elif _char == "v":
            _V_KEYCODE = _keycode


def _simulateCommandKey(keycode):
    """Posts a Cmd+<key> press to the session."""
    for pressed in (True, False):
        event = Quartz.CGEventCreateKeyboardEvent(None, keycode, pressed)
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def get():
    """Returns a dictionary with the current selection, or {}."""
    pasteboard = AppKit.NSPasteboard.generalPasteboard()
    oldChangeCount = pasteboard.changeCount()
    _simulateCommandKey(_C_KEYCODE)
    time.sleep(_COPY_DELAY)

    if pasteboard.changeCount() == oldChangeCount:
        # Nothing was copied; there is probably no selection.
        return {}

    text = pasteboard.stringForType_(AppKit.NSPasteboardTypeString)
    if text:
        return {"text": str(text)}
    return {}


def set(seldict):
    """Pastes the text of the given selection dictionary, if any."""
    text = seldict.get("text")
    if not text:
        return False

    pasteboard = AppKit.NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    if not pasteboard.setString_forType_(text,
                                         AppKit.NSPasteboardTypeString):
        logging.warning("Couldn't write the text to the pasteboard.")
        return False

    time.sleep(_PASTE_DELAY)
    _simulateCommandKey(_V_KEYCODE)
    return True
