"""
GTK3 implementation of the Enso "graphics" provider (TransparentWindow).

Based on the original Enso Linux port:
Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
Rewritten for Python 3 / PyGObject; X11 only, requires a compositing
manager for true per-pixel transparency.
"""

import logging

import cairo

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from enso import config

# Max opacity as used in Enso core (converted to [0;1] in this backend).
MAX_OPACITY = 0xff

_composited = None


def _isComposited():
    """Checks once whether the screen is composited; without a compositor
    the overlays render on an opaque background."""
    global _composited
    if _composited is None:
        screen = Gdk.Screen.get_default()
        _composited = bool(screen and screen.is_composited())
        if not _composited:
            logging.warning(
                "The X screen is not composited; Enso overlays will be drawn "
                "on an opaque background.  Start a compositing manager to get "
                "proper transparency (on LXQt: install picom and run "
                "'picom -b', or enable one in the session settings)."
            )
    return _composited


class TransparentWindow(object):
    """TransparentWindow object, delegating to a Gtk.Window implementation.

    The indirection exists because Enso core deletes its reference to the
    TransparentWindow to dispose of it, while GTK itself keeps references
    to the underlying window; destruction must therefore be explicit."""

    class _impl(Gtk.Window):

        def __init__(self, x, y, maxWidth, maxHeight):
            Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
            self.__x = x
            self.__y = y
            self.__maxWidth = maxWidth
            self.__maxHeight = maxHeight
            self.__width = maxWidth
            self.__height = maxHeight
            self.__surface = None
            self.__opacity = MAX_OPACITY

            self.set_app_paintable(True)
            self.set_accept_focus(False)
            self.set_focus_on_map(False)
            self.set_keep_above(True)

            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            if visual is not None:
                self.set_visual(visual)
            else:
                logging.warning("No RGBA visual available; "
                                "falling back to the system visual.")

            self.connect("draw", self.__onDraw)
            self.connect("realize", self.__onRealize)

            self.move(self.__x, self.__y)
            self.set_default_size(self.__width, self.__height)

        def __onRealize(self, widget):
            # The overlay must never take mouse input: an empty input
            # shape makes the whole window click-through.
            self.input_shape_combine_region(cairo.Region())

        def __onDraw(self, widget, cr):
            cr.rectangle(0, 0, self.__width, self.__height)
            cr.clip()
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_rgba(0, 0, 0, 0)
            cr.paint()
            if self.__surface:
                cr.set_operator(cairo.OPERATOR_OVER)
                cr.set_source_surface(self.__surface)
                if _isComposited():
                    cr.paint_with_alpha(self.__opacity / MAX_OPACITY)
                else:
                    cr.paint()
            return False

        def update(self):
            if self.__surface:
                self.queue_draw()

        def makeCairoSurface(self):
            if not self.__surface:
                self.__surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                                    self.__maxWidth,
                                                    self.__maxHeight)
                self.show_all()
            return self.__surface

        def setOpacity(self, opacity):
            self.__opacity = opacity
            self.update()

        def getOpacity(self):
            return self.__opacity

        def setPosition(self, x, y):
            self.__x = x
            self.__y = y
            self.move(self.__x, self.__y)

        def getX(self):
            return self.__x

        def getY(self):
            return self.__y

        def setSize(self, width, height):
            self.__width = width
            self.__height = height
            self.resize(self.__width, self.__height)

        def getWidth(self):
            return self.__width

        def getHeight(self):
            return self.__height

        def getMaxWidth(self):
            return self.__maxWidth

        def getMaxHeight(self):
            return self.__maxHeight

        def setForeground(self):
            window = self.get_window()
            if window is not None:
                window.raise_()

        def finish(self):
            if self.__surface:
                self.__surface.finish()
                self.__surface = None
            self.destroy()

    def __init__(self, x, y, maxWidth, maxHeight):
        instance = TransparentWindow._impl(x, y, maxWidth, maxHeight)
        self.__dict__["_TransparentWindow__instance"] = instance

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __del__(self):
        self.finish()


def getCurrentMonitor():
    """Returns the Gdk.Monitor under the mouse pointer."""
    display = Gdk.Display.get_default()
    pointer = display.get_default_seat().get_pointer()
    _, x, y = pointer.get_position()
    return display.get_monitor_at_point(x, y)


def _getCurrentMonitorRect():
    monitor = getCurrentMonitor()
    if config.APPEAR_OVER_TASKBAR:
        return monitor.get_geometry()
    return monitor.get_workarea()


def getDesktopOffset():
    """Offset of the current monitor, so Enso can draw on any of them."""
    rect = _getCurrentMonitorRect()
    return rect.x, rect.y


def getDesktopSize():
    rect = _getCurrentMonitorRect()
    return rect.width, rect.height
