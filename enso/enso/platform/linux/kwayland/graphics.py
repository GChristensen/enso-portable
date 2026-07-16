"""
KDE Wayland implementation of the Enso "graphics" provider
(TransparentWindow).

Overlays are wlr-layer-shell surfaces on the overlay layer, which
keeps them above all application windows (the layer-shell counterpart
of set_keep_above) and lets a Wayland client position them in monitor
coordinates via layer margins -- ordinary Wayland toplevels can do
neither.  Wayland is always composited, so per-pixel alpha needs no
compositor check.

Enso core keeps working in monitor-relative coordinates:
getDesktopOffset() is (0, 0) and every surface is pinned to the same
monitor (see kwayland.utils.get_monitor).
"""

import logging

import cairo

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from enso import config
from enso.platform.linux.kwayland import layershell, utils

# Max opacity as used in Enso core (converted to [0;1] in this backend).
MAX_OPACITY = 0xff

_over_taskbar_warned = False


def _warnOverTaskbar():
    """APPEAR_OVER_TASKBAR=False cannot be honored on Wayland: panel
    geometry is not observable, so overlays always use the full monitor
    (exclusive zone -1)."""
    global _over_taskbar_warned
    if not config.APPEAR_OVER_TASKBAR and not _over_taskbar_warned:
        _over_taskbar_warned = True
        logging.info("APPEAR_OVER_TASKBAR=False is ignored on Wayland; "
                     "overlays may cover panels.")


class TransparentWindow(object):
    """TransparentWindow object, delegating to a Gtk.Window implementation.

    The indirection exists because Enso core deletes its reference to the
    TransparentWindow to dispose of it, while GTK itself keeps references
    to the underlying window; destruction must therefore be explicit."""

    class _impl(Gtk.Window):

        def __init__(self, x, y, maxWidth, maxHeight):
            # Layer-shell needs a real toplevel, not a POPUP.
            Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
            self.__x = x
            self.__y = y
            self.__maxWidth = maxWidth
            self.__maxHeight = maxHeight
            self.__width = maxWidth
            self.__height = maxHeight
            self.__surface = None
            self.__opacity = MAX_OPACITY

            self.set_accept_focus(False)
            self.set_focus_on_map(False)

            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            if visual is not None:
                self.set_visual(visual)
            else:
                logging.warning("No RGBA visual available; "
                                "falling back to the system visual.")

            layershell.init_layer_window(self, "enso-overlay")
            _warnOverTaskbar()

            # GDK's Wayland backend never commits a frame for a
            # childless (or app-paintable) toplevel, and gtk-layer-shell
            # sizes the layer surface from the widget's natural size,
            # ignoring set_default_size().  A DrawingArea child with an
            # explicit size request addresses both: it drives the
            # surface size and receives the draw signal.
            self.__area = Gtk.DrawingArea()
            self.__area.set_size_request(self.__width, self.__height)
            self.__area.connect("draw", self.__onDraw)
            self.add(self.__area)

            self.connect("realize", self.__onRealize)

            layershell.move_layer_window(self, self.__x, self.__y)

            # Map the window immediately while the surface is still
            # None (the draw handler paints fully transparent in that
            # state).  This lets KWin's window-open animation play on
            # an invisible surface, so the user never sees the "grow
            # from small" scale effect that KDE applies to newly
            # mapped windows.
            self.show_all()

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
                cr.paint_with_alpha(self.__opacity / MAX_OPACITY)
            return False

        def update(self):
            if self.__surface:
                if not self.get_mapped():
                    self.show_all()
                self.queue_draw()

        def makeCairoSurface(self):
            if not self.__surface:
                self.__surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                                    self.__maxWidth,
                                                    self.__maxHeight)
            return self.__surface

        def setOpacity(self, opacity):
            self.__opacity = opacity
            self.update()

        def getOpacity(self):
            return self.__opacity

        def setPosition(self, x, y):
            self.__x = x
            self.__y = y
            layershell.move_layer_window(self, self.__x, self.__y)

        def getX(self):
            return self.__x

        def getY(self):
            return self.__y

        def setSize(self, width, height):
            self.__width = width
            self.__height = height
            # The size request drives the layer surface size; resize()
            # has no effect on a layer-shell window.
            self.__area.set_size_request(self.__width, self.__height)
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
            # Layer-shell overlay surfaces are always above normal
            # windows; there is no further raising to do.
            pass

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
    """Returns the Gdk.Monitor Enso draws on (the pointer position is
    not observable on Wayland; see kwayland.utils.get_monitor)."""
    return utils.get_monitor()


def getDesktopOffset():
    """Layer margins are already monitor-relative, so there is no
    offset to apply."""
    return 0, 0


def getDesktopSize():
    monitor = utils.get_monitor()
    if monitor is None:
        return 1920, 1080
    rect = monitor.get_geometry()
    return rect.width, rect.height
