import os
import weakref
import cStringIO

import objc
import AppKit
import Foundation
import cairo

from enso.platform.osx.quartz_cairo_bridge import \
    cairo_surface_from_NSGraphicsContext
from enso.platform.osx.utils import sendMsg

MAX_OPACITY = 0xff

class _TransparentWindowView( AppKit.NSView ):
    def initWithParent_( self, parent ):
        self = super( _TransparentWindowView, self ).init()
        if self == None:
            return None
        self.__parent = weakref.ref( parent )
        return self

    def drawRect_( self, rect ):
        parent = self.__parent()
        if not parent:
            return

        surface = parent._surface
        if not surface:
            return

        context = AppKit.NSGraphicsContext.currentContext()

        # Taken from the OS X Cocoa Drawing Guide section on
        # "Creating a Flip Transform".
        frameRect = self.bounds()
        xform = AppKit.NSAffineTransform.transform()
        sendMsg( xform,
                 "translateXBy:", 0.0,
                 "yBy:", frameRect.size.height )

        sendMsg( xform,
                 "scaleXBy:", 1.0,
                 "yBy:", -1.0 )

        xform.concat()

        parent._imageRep.draw()

def _convertY( y, height ):
    """
    Flip a y-coordinate to account for the fact that OS X has its
    origin at the bottom-left of an image instead of the top-left, as
    Enso expects it to be.
    """

    screenSize = getDesktopSize()
    return screenSize[1] - y - height

class TransparentWindow( object ):
    def __init__( self, x, y, maxWidth, maxHeight ):
        self.__x = x
        self.__y = y
        self.__maxWidth = maxWidth
        self.__maxHeight = maxHeight
        self.__width = maxWidth
        self.__height = maxHeight
        self._surface = None
        self.__opacity = 0xff

        rect = Foundation.NSMakeRect( self.__x,
                                      _convertY( self.__y, self.__height ),
                                      self.__width,
                                      self.__height )
        style = AppKit.NSBorderlessWindowMask
        self.__wind = sendMsg(
            AppKit.NSWindow.alloc(),
            "initWithContentRect:", rect,
            "styleMask:", style,
            "backing:", AppKit.NSBackingStoreBuffered,
            "defer:", objc.YES
            )

        self.__wind.setBackgroundColor_( AppKit.NSColor.clearColor() )
        self.__view = _TransparentWindowView.alloc().initWithParent_( self )
        self.__wind.setContentView_( self.__view )
        self.__wind.setLevel_( AppKit.NSPopUpMenuWindowLevel )
        self.__wind.setOpaque_( objc.NO )
        self.__wind.setAlphaValue_( 1.0 )

    def update( self ):
        if self._surface:
            self.__wind.makeKeyAndOrderFront_( objc.nil )
            self.__view.setNeedsDisplay_( objc.YES )

    def makeCairoSurface( self ):
        if not self._surface:
            self._imageRep = sendMsg(
                AppKit.NSBitmapImageRep.alloc(),
                "initWithBitmapDataPlanes:", None,
                "pixelsWide:", self.__maxWidth,
                "pixelsHigh:", self.__maxHeight,
                "bitsPerSample:", 8,
                "samplesPerPixel:", 4,
                "hasAlpha:", True,
                "isPlanar:", False,
                "colorSpaceName:", AppKit.NSCalibratedRGBColorSpace,
                "bitmapFormat:", 0,
                "bytesPerRow:", 4 * self.__maxWidth,
                "bitsPerPixel:", 32
                )

            # This NSGraphicsContext retains the NSBitmapImageRep we
            # pass it, but for some reason it doesn't release it on
            # destruction... See this class' __del__() method for how
            # we deal with this.
            nsContext = sendMsg(
                AppKit.NSGraphicsContext,
                "graphicsContextWithBitmapImageRep:",
                self._imageRep
                )

            self._surface = cairo_surface_from_NSGraphicsContext(
                nsContext,
                self.__maxWidth,
                self.__maxHeight
                )

        return self._surface

    def setOpacity( self, opacity ):
        self.__opacity = opacity
        self.__wind.setAlphaValue_( (float(opacity)/MAX_OPACITY) * 1.0 )

    def getOpacity( self ):
        return self.__opacity

    def setPosition( self, x, y ):
        self.__x = x
        self.__y = y
        topLeft = Foundation.NSPoint( self.__x,
                                      _convertY( self.__y, self.__height ) )
        self.__wind.setFrameTopLeftPoint_( topLeft )

    def getX( self ):
        return self.__x

    def getY( self ):
        return self.__y

    def setSize( self, width, height ):
        self.__width = width
        self.__height = height
        rect = Foundation.NSMakeRect( self.__x,
                                      _convertY( self.__y, self.__height ),
                                      self.__width,
                                      self.__height )
        self.__wind.setFrame_display_( rect, objc.YES )

    def getWidth( self ):
        return self.__width

    def getHeight( self ):
        return self.__height

    def getMaxWidth( self ):
        return self.__maxWidth

    def getMaxHeight( self ):
        return self.__maxHeight

    def __del__( self ):
        if self._surface:
            self._surface.finish()
            self._surface = None

def getDesktopSize():
    size = AppKit.NSScreen.mainScreen().frame().size
    return ( size.width, size.height )

def getDesktopOffset():
    return (0, 0)