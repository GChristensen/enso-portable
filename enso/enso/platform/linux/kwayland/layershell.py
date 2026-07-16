"""
wlr-layer-shell helpers for the KDE Wayland backend (gtk-layer-shell).
"""

import logging

import gi
gi.require_version("Gtk", "3.0")

try:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell
except (ValueError, ImportError) as exc:
    raise ImportError(
        "The gtk-layer-shell introspection bindings are required for the "
        "KDE Wayland backend but are not installed (on openSUSE: sudo "
        "zypper install typelib-1_0-GtkLayerShell-0_1)."
    ) from exc

from enso.platform.linux.kwayland import utils


def init_layer_window(window, namespace):
    """Makes the given (unrealized) Gtk.Window a layer-shell surface on
    the overlay layer, anchored to the top-left corner of Enso's
    monitor, unaffected by panel exclusive zones.  Positioning is done
    with layer margins afterwards."""
    GtkLayerShell.init_for_window(window)
    GtkLayerShell.set_namespace(window, namespace)
    GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, True)
    GtkLayerShell.set_exclusive_zone(window, -1)
    monitor = utils.get_monitor()
    if monitor is not None:
        GtkLayerShell.set_monitor(window, monitor)
    else:
        logging.warning("No Gdk monitor found; letting the compositor "
                        "choose an output for Enso's overlay.")


def move_layer_window(window, x, y):
    """Positions a layer-shell surface at monitor coordinates (x, y)."""
    GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, x)
    GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, y)
