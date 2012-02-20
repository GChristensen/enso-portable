import enso.providers

from enso.graphics.measurement import pointsToPixels, pixelsToPoints
from enso.graphics.measurement import convertUserSpaceToPoints
from enso import cairo

_graphics = enso.providers.getInterface( "graphics" )

# This is a wrapper for the platform-specific implementation of a
# TransparentWindow that makes the class use points instead of
# pixels.

class TransparentWindow( object ):
    def __init__( self, xPos, yPos, width, height ):
        # Convert from points to pixels
        xPos = int( pointsToPixels( xPos ) )
        yPos = int( pointsToPixels( yPos ) )
        width = max( int( pointsToPixels( width ) ), 1 )
        height = max( int( pointsToPixels( height ) ), 1 )
        
        self._impl = _graphics.TransparentWindow( xPos, yPos,
                                                  width, height )

    def makeCairoContext( self ):
        context = cairo.Context( self._impl.makeCairoSurface() )
        convertUserSpaceToPoints( context )
        return context

    def update( self ):
        return self._impl.update()

    def setOpacity( self, opacity ):
        return self._impl.setOpacity( opacity )

    def getOpacity( self ):
        return self._impl.getOpacity()

    def setPosition( self, x, y ):
        x = int( pointsToPixels( x ))
        y = int( pointsToPixels( y ))
        return self._impl.setPosition( x, y )

    def getX( self ):
        return pixelsToPoints( self._impl.getX() )

    def getY( self ):
        return pixelsToPoints( self._impl.getY() )

    def setSize( self, width, height ):
        width = max( int(pointsToPixels(width)), 1 )
        height = max( int(pointsToPixels(height)), 1 )
        return self._impl.setSize( width, height )

    def getWidth( self ):
        return pixelsToPoints( self._impl.getWidth() )

    def getHeight( self ):
        return pixelsToPoints( self._impl.getHeight() )

    def getMaxWidth( self ):
        return pixelsToPoints( self._impl.getMaxWidth() )

    def getMaxHeight( self ):
        return pixelsToPoints( self._impl.getMaxHeight() )

