"""
Cocoa implementation of the Enso "graphics" provider (TransparentWindow).

Based on the original Enso OS X port:
Copyright (c) 2008, Humanized, Inc.
Rewritten for Python 3 / modern PyObjC; renders a pycairo ImageSurface
into a borderless transparent NSWindow (no Cairo<->Quartz bridge).
"""

import logging
import weakref

import cairo

import objc
import AppKit
import Foundation
import Quartz

from enso import config

# Max opacity as used in Enso core (converted to [0;1] in this backend).
MAX_OPACITY = 0xff


def _mainScreenHeight():
    return AppKit.NSScreen.screens()[0].frame().size.height


def _convertY(y, height):
    """Converts a top-left-origin global y coordinate (as used by Enso
    core, matching the win32 and X11 conventions) into Cocoa's
    bottom-left-origin global coordinate space."""
    return _mainScreenHeight() - y - height


class _TransparentWindowView(AppKit.NSView):
    """View that paints the parent's cairo ImageSurface, cropped to the
    window's current size."""

    def initWithParent_(self, parent):
        self = objc.super(_TransparentWindowView, self).init()
        if self is None:
            return None
        self.__parent = weakref.ref(parent)
        return self

    def isFlipped(self):
        # A flipped view puts the origin at the top-left, so the window
        # content maps 1:1 onto Enso's coordinate conventions.
        return True

    def drawRect_(self, rect):
        parent = self.__parent()
        if parent is None:
            return
        image = parent._makeCGImage()
        if image is None:
            return
        context = AppKit.NSGraphicsContext.currentContext().CGContext()
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        # The view is flipped but CGImages are not; flip back locally so
        # the image is not drawn upside down.
        Quartz.CGContextSaveGState(context)
        Quartz.CGContextTranslateCTM(context, 0, height)
        Quartz.CGContextScaleCTM(context, 1.0, -1.0)
        Quartz.CGContextDrawImage(
            context, Quartz.CGRectMake(0, 0, width, height), image)
        Quartz.CGContextRestoreGState(context)


class TransparentWindow(object):
    """TransparentWindow object, delegating to a Cocoa implementation.

    The indirection exists because Enso core deletes its reference to
    the TransparentWindow to dispose of it, while Cocoa itself keeps
    references to the underlying window; destruction must therefore be
    explicit."""

    class _impl(object):

        def __init__(self, x, y, maxWidth, maxHeight):
            self.__x = x
            self.__y = y
            self.__maxWidth = maxWidth
            self.__maxHeight = maxHeight
            self.__width = maxWidth
            self.__height = maxHeight
            self.__surface = None
            self.__opacity = MAX_OPACITY
            self.__shown = False

            rect = Foundation.NSMakeRect(x, _convertY(y, self.__height),
                                         self.__width, self.__height)
            self.__wind = (
                AppKit.NSWindow.alloc()
                .initWithContentRect_styleMask_backing_defer_(
                    rect,
                    AppKit.NSWindowStyleMaskBorderless,
                    AppKit.NSBackingStoreBuffered,
                    False))
            self.__wind.setBackgroundColor_(AppKit.NSColor.clearColor())
            self.__wind.setOpaque_(False)
            self.__wind.setHasShadow_(False)
            self.__wind.setLevel_(AppKit.NSPopUpMenuWindowLevel)
            # The overlay must never take mouse input (parity with the
            # win32 WS_EX_TRANSPARENT style and the X11 empty input
            # shape).
            self.__wind.setIgnoresMouseEvents_(True)
            self.__wind.setCollectionBehavior_(
                AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                | AppKit.NSWindowCollectionBehaviorStationary)

            self.__view = (_TransparentWindowView.alloc()
                           .initWithParent_(self))
            self.__wind.setContentView_(self.__view)

        def _makeCGImage(self):
            """Wraps the current crop of the cairo surface in a CGImage.
            cairo ARGB32 is premultiplied BGRA in memory on
            little-endian, which CGImageCreate describes exactly as
            AlphaPremultipliedFirst | ByteOrder32Little."""
            if not self.__surface:
                return None
            self.__surface.flush()
            stride = self.__surface.get_stride()
            provider = Quartz.CGDataProviderCreateWithData(
                None, bytes(self.__surface.get_data()),
                stride * self.__maxHeight, None)
            image = Quartz.CGImageCreate(
                self.__maxWidth, self.__maxHeight, 8, 32, stride,
                Quartz.CGColorSpaceCreateDeviceRGB(),
                (Quartz.kCGImageAlphaPremultipliedFirst
                 | Quartz.kCGBitmapByteOrder32Little),
                provider, None, False, Quartz.kCGRenderingIntentDefault)
            if (self.__width, self.__height) != (self.__maxWidth,
                                                 self.__maxHeight):
                image = Quartz.CGImageCreateWithImageInRect(
                    image, Quartz.CGRectMake(0, 0, self.__width,
                                             self.__height))
            return image

        def update(self):
            if self.__surface:
                if not self.__shown:
                    # Never before there is real content to show, and
                    # never with makeKeyAndOrderFront: the overlay must
                    # not steal focus.
                    self.__wind.orderFrontRegardless()
                    self.__shown = True
                self.__view.setNeedsDisplay_(True)

        def makeCairoSurface(self):
            if not self.__surface:
                self.__surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                                    self.__maxWidth,
                                                    self.__maxHeight)
            return self.__surface

        def setOpacity(self, opacity):
            self.__opacity = opacity
            self.__wind.setAlphaValue_(opacity / MAX_OPACITY)

        def getOpacity(self):
            return self.__opacity

        def setPosition(self, x, y):
            self.__x = x
            self.__y = y
            self.__wind.setFrameTopLeftPoint_(
                Foundation.NSPoint(x, _convertY(y, 0)))

        def getX(self):
            return self.__x

        def getY(self):
            return self.__y

        def setSize(self, width, height):
            self.__width = width
            self.__height = height
            rect = Foundation.NSMakeRect(self.__x,
                                         _convertY(self.__y, height),
                                         width, height)
            self.__wind.setFrame_display_(rect, True)

        def getWidth(self):
            return self.__width

        def getHeight(self):
            return self.__height

        def getMaxWidth(self):
            return self.__maxWidth

        def getMaxHeight(self):
            return self.__maxHeight

        def setForeground(self):
            self.__wind.orderFrontRegardless()

        def finish(self):
            if self.__surface:
                self.__surface.finish()
                self.__surface = None
            if self.__wind is not None:
                self.__wind.orderOut_(None)
                self.__wind = None
                self.__view = None

    def __init__(self, x, y, maxWidth, maxHeight):
        instance = TransparentWindow._impl(x, y, maxWidth, maxHeight)
        self.__dict__["_TransparentWindow__instance"] = instance

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __del__(self):
        self.finish()


def _getCurrentScreen():
    """Returns the NSScreen under the mouse pointer."""
    location = AppKit.NSEvent.mouseLocation()
    for screen in AppKit.NSScreen.screens():
        if Foundation.NSPointInRect(location, screen.frame()):
            return screen
    return AppKit.NSScreen.screens()[0]


def _getCurrentScreenRect():
    screen = _getCurrentScreen()
    if config.APPEAR_OVER_TASKBAR:
        return screen.frame()
    return screen.visibleFrame()


def getDesktopOffset():
    """Offset of the current screen in top-left-origin global
    coordinates, so Enso can draw on any of them."""
    rect = _getCurrentScreenRect()
    x = rect.origin.x
    y = _mainScreenHeight() - rect.origin.y - rect.size.height
    return (x, y)


def getDesktopSize():
    rect = _getCurrentScreenRect()
    return (rect.size.width, rect.size.height)
