"""
Author : Guillaume "iXce" Seguin
Email  : guillaume@segu.in

Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

  3. Neither the name of Enso nor the names of its contributors may
     be used to endorse or promote products derived from this
     software without specific prior written permission.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import logging
from time import sleep

import gtk
import cairo

from enso.events import EventManager

# Max opacity as used in Enso core (opacities will be converted to fit in 
# [0;1] in this backend)
MAX_OPACITY = 0xff
# Enable Fake transparency when no the screen isn't composited?
FAKE_TRANSPARENCY = False

class TransparentWindow (object):
    '''TransparentWindow object, using a gtk.Window'''

    __instance = None

    class _impl (gtk.Window):
        '''Actual implementation of the TransparentWindow ; this mechanism is
due to the way Enso handles TransparentWindows deletion, which requires the 
main TransparentWindow object to not be referenced by other modules, which
gtk would do, for instance.'''

        __gsignals__ = {
            "expose-event"      : "override",
            "screen-changed"    : "override",
        }

        __wallpaper_surface = None
        __wallpaper_screen = None

        def __init__ (self, x, y, maxWidth, maxHeight):
            '''Initialize object'''
            gtk.Window.__init__ (self, gtk.WINDOW_POPUP)
            self.__x = x
            self.__y = y
            self.__maxWidth = maxWidth
            self.__maxHeight = maxHeight
            self.__width = maxWidth
            self.__height = maxHeight
            self.__surface = None
            self.__opacity = 0xff
            self.__screen_composited = False
            self.__eventMgr = EventManager.get ()

            self.set_app_paintable (True)
            self.do_screen_changed ()
            self.connect ("motion-notify-event", self.on_motion_notify_event)
            self.connect ("delete-event", self.ensure_pointer_ungrabbed)

            self.move (self.__x, self.__y)
            self.set_default_size (self.__width, self.__height)

        def grab_pointer (self, *args):
            '''Grab pointer to be able to catch all motion events'''
            if not gtk.gdk.pointer_is_grabbed ():
                mask = gtk.gdk.POINTER_MOTION_MASK
                while gtk.gdk.pointer_grab (self.window, True, mask) \
                        != gtk.gdk.GRAB_SUCCESS:
                    sleep (0.1)

        def ensure_pointer_ungrabbed (self, *args):
            '''Make sure the pointer is ungrabbed to avoid bad deadlocks'''
            if gtk.gdk.pointer_is_grabbed ():
                gtk.gdk.pointer_ungrab ()

        def on_motion_notify_event (self, window, event):
            '''Forward mouse motion events to Enso core'''
            self.__eventMgr.onMouseMove (event.x, event.y)

        def do_expose_event (self, event):
            '''Handle expose events'''
            if event.window == self.window:
                cr = self.window.cairo_create ()
                self.draw_surface (cr)

        def draw_surface (self, cr):
            '''Draw surface to the window Cairo context'''
            cr.rectangle (0, 0, self.__width, self.__height)
            cr.clip ()
            cr.set_operator (cairo.OPERATOR_CLEAR)
            cr.paint ()
            if self.__surface:
                cr.set_operator (cairo.OPERATOR_OVER)
                cr.set_source_surface (self.__surface)
                if not self.__screen_composited and not FAKE_TRANSPARENCY:
                    cr.paint ()
                else:
                    cr.paint_with_alpha (float (self.__opacity) / MAX_OPACITY)
                if not self.__screen_composited and FAKE_TRANSPARENCY:
                    self.draw_wallpaper (cr)

        def draw_wallpaper (self, cr):
            '''Draw wallpaper below surface contents to fake transparency'''
            if not TransparentWindow._impl.__wallpaper_surface:
                update_wallpaper_surface ()
                if not TransparentWindow._impl.__wallpaper_surface:
                    return
            cr.set_operator (cairo.OPERATOR_DEST_ATOP)
            cr.set_source_surface (TransparentWindow._impl.__wallpaper_surface)
            cr.mask_surface (self.__surface)

        def __update_wallpaper_surface (self):
            '''Internal function that fetches the root window pixmap to use
as background when doing fake transparency'''
            screen = self.get_screen ()
            if TransparentWindow._impl.__wallpaper_screen == screen:
                return
            TransparentWindow._impl.__wallpaper_screen = screen
            root = screen.get_root_window ()
            id = root.property_get ("_XROOTPMAP_ID", "PIXMAP")[2][0]
            if hasattr (gtk.gdk, "gdk_pixmap_foreign_new"):
                pixmap = gtk.gdk.gdk_pixmap_foreign_new (long (id))
            else:
                pixmap = gtk.gdk.pixmap_foreign_new (long (id))
            width, height = screen.get_width (), screen.get_height ()
            if (width, height) != pixmap.get_size():
                return
            pixmap.set_colormap (screen.get_rgb_colormap ())
            wallpaper_surface = cairo.ImageSurface (cairo.FORMAT_ARGB32,
                                                    width, height)
            cr2 = cairo.Context (wallpaper_surface)
            gdkcr = gtk.gdk.CairoContext (cr2)
            gdkcr.set_source_pixmap (pixmap, 0, 0)
            gdkcr.paint ()
            TransparentWindow._impl.__wallpaper_surface = wallpaper_surface

        def do_screen_changed (self, old_screen = None):
            '''Update colormap/background and so on when screen changes'''
            screen = self.get_screen ()
            colormap = None
            if hasattr (screen, "get_rgba_colormap"):
                colormap = screen.get_rgba_colormap ()
            if not colormap:
                logging.warn ('''No RGBA colormap available, \
falling back to RGB''')
                colormap = screen.get_rgb_colormap ()
            self.set_colormap (colormap)
            self.__screen_composited = False
            if hasattr (screen, "is_composited"):
                self.__screen_composited = screen.is_composited ()
            if not self.__screen_composited and FAKE_TRANSPARENCY:
                logging.warn ('''Switching to fake transparency mode, \
please use a compositing manager to get proper blending.''')
                self.__update_wallpaper_surface ()

        def update_shape (self):
            '''Update the window shape'''
            pixmap = gtk.gdk.Pixmap (None, self.__width, self.__height, 1)
            cr = pixmap.cairo_create ()
            cr.rectangle (0, 0, self.__width, self.__height)
            cr.clip ()
            self.draw_surface (cr)
            if hasattr (self, "input_shape_combine_mask"):
                self.input_shape_combine_mask (None, 0, 0)
                self.input_shape_combine_mask (pixmap, 0, 0)
            if not self.__screen_composited:
                self.shape_combine_mask (pixmap, 0, 0)

        def update (self):
            '''Queue drawing when Enso core requests it'''
            if self.__surface:
                self.update_shape ()
                self.queue_draw ()

        def makeCairoSurface (self):
            '''Prepare a Cairo Surface large enough for this window'''
            if not self.__surface:
                self.__surface = cairo.ImageSurface (cairo.FORMAT_ARGB32,
                                                     self.__maxWidth,
                                                     self.__maxHeight)
                self.update_shape ()
                self.show ()
            return self.__surface

        def setOpacity (self, opacity):
            '''Set window opacity and grab or ungrab the pointer according to
the opacity level ; this is probably a FIXME cause it looks really ugly and
might cause bad conflicts or race conditions in the future.'''
            self.__opacity = opacity
            # FIXME: I'm not clean
            if self.__opacity == MAX_OPACITY:
                self.grab_pointer ()
            else:
                self.ensure_pointer_ungrabbed ()
            self.update ()

        def getOpacity (self):
            '''Get window opacity'''
            return self.__opacity

        def setPosition( self, x, y ):
            '''Set window position'''
            self.__x = x
            self.__y = y
            self.move (self.__x, self.__y)

        def getX (self):
            '''Get window x coordinate'''
            return self.__x

        def getY (self):
            '''Get window y coordinate'''
            return self.__y

        def setSize (self, width, height):
            '''Resize window and update input shape'''
            self.__width = width
            self.__height = height
            self.resize (self.__width, self.__height)
            self.update_shape ()

        def getWidth (self):
            '''Get window width'''
            return self.__width

        def getHeight (self):
            '''Get window height'''
            return self.__height

        def getMaxWidth (self):
            '''Get window maximum width'''
            return self.__maxWidth

        def getMaxHeight (self):
            '''Get window maximum height'''
            return self.__maxHeight

        def finish (self):
            '''Finish this window: delete the Cairo surface, ungrab pointer
and destroy it.'''
            if self.__surface:
                self.__surface.finish ()
                self.__surface = None
            self.ensure_pointer_ungrabbed ()
            self.destroy ()

    def __init__ (self, x, y, maxWidth, maxHeight):
        '''Initialize object'''
        instance = TransparentWindow._impl (x, y, maxWidth, maxHeight)
        self.__dict__['_TransparentWindow__instance'] = instance

    def __getattr__ (self, attr):
        '''Delegate to inner implementation'''
        return getattr (self.__instance, attr)

    def __setattr__ (self, attr, value):
        '''Delegate to inner implementation'''
        return setattr (self.__instance, attr, value)

    def __del__ (self):
        '''Destroy the inner instance'''
        self.finish ()

def getCurrentMonitor ():
    '''Helper fetching the current monitor of focus'''
    from enso.platform.linux import utils
    display = utils.get_display ()
    input_focus = display.get_input_focus ()
    if input_focus != None and input_focus.focus:
        window = input_focus.focus
        geom = window.get_geometry()
        width = geom.width
        if (width == display.screen().width_in_pixels):
            '''Either a full screen window or desktop.
            We will use mouse coordinates for this'''
            _, x, y, _ = gtk.gdk.display_get_default().get_pointer() 
        else:
            '''A floating window.  We will see which monitor
            the majority of the window is on'''
            root = window.query_tree().root
            trans = root.translate_coords(window, 0, 0)
            x = trans.x + (width / 2)
            y = trans.y        
    else:
        x, y = 0, 0
        print "no focus"
    
    return gtk.gdk.screen_get_default ().get_monitor_at_point(x, y)
    
def getDesktopOffset ():
    '''Helper fetching the offset so that Enso can draw on multiple desktops'''
    left, top, _, _ = gtk.gdk.screen_get_default ().get_monitor_geometry (getCurrentMonitor ())
    return left, top    
    
def getDesktopSize ():
    _, _, width, height = gtk.gdk.screen_get_default ().get_monitor_geometry (getCurrentMonitor ())
    return width, height 
