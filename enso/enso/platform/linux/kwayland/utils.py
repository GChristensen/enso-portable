"""
Shared helpers for the KDE Wayland backend (no layer-shell
dependency; the layer-shell helpers live in kwayland.layershell).
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk

# Name of the uinput virtual keyboard the selection module creates;
# the input listener must not interpret its events as user input.
UINPUT_DEVICE_NAME = "enso-virtual-keyboard"


def keyval_to_char(keyval):
    """Returns the printable character for a GDK keyval, or None."""
    codepoint = Gdk.keyval_to_unicode(keyval)
    if codepoint == 0:
        return None
    char = chr(codepoint)
    if char.isprintable() and not char.isspace():
        return char
    return None


def get_monitor():
    """Returns the Gdk.Monitor Enso draws on.  The pointer position is
    not observable on Wayland, so this is the primary monitor (or the
    first one when the compositor exposes no primary)."""
    display = Gdk.Display.get_default()
    if display is None:
        return None
    monitor = display.get_primary_monitor()
    if monitor is None and display.get_n_monitors() > 0:
        monitor = display.get_monitor(0)
    return monitor
