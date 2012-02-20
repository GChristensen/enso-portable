# Copyright (c) 2008, Humanized, Inc.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Enso nor the names of its contributors may
#       be used to endorse or promote products derived from this
#       software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY Humanized, Inc. ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Humanized, Inc. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ----------------------------------------------------------------------------
#
#   enso.quasimode.linewindows
#
# ----------------------------------------------------------------------------

"""
    A window class for drawing single lines of text in transparent
    windows.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import cairo
from enso import graphics
from enso.graphics.measurement import pointsToPixels, pixelsToPoints
from enso.graphics.measurement import convertUserSpaceToPoints
from enso.graphics.transparentwindow import TransparentWindow
from enso.graphics import rounded_rect
from enso.quasimode import layout


# ----------------------------------------------------------------------------
# TextWindow Class
# ----------------------------------------------------------------------------

class TextWindow:
    """
    Encapsulates the drawing of a single line of text, with optional
    rounded corners and an optional "override width", which overides the
    default width (margins + text width).
    """
    
    def __init__( self, height, position ):
        """
        Creates the underlying TransparentWindow and Cairo context.

        Position and height should be in pixels.
        """

        # Use the maximum width that we can, i.e., the desktop width.
        width, _ = graphics.getDesktopSize()
        left, top = graphics.getDesktopOffset()

        xPos, yPos = position
        self.__window = TransparentWindow(xPos + left, yPos, width, height )
        self.__context = self.__window.makeCairoContext()
        

    def getHeight( self ):
        """
        LONGTERM TODO: Document this.
        """
        
        return self.__window.getHeight()


    def draw( self, document ):
        """
        Draws the text described by document.

        An updating call; at the end of this method, the displayed
        window should reflect the drawn content.
        """

        width = document.ragWidth + layout.L_MARGIN + layout.R_MARGIN
        height = self.__window.getMaxHeight()
        cr = self.__context

        # Clear the areas where the corners of the rounded rectangle will be.

        cr.save()
        cr.set_source_rgba( 0, 0, 0, 0 )
        cr.set_operator( cairo.OPERATOR_SOURCE )
        cr.rectangle( width - rounded_rect.CORNER_RADIUS,
                      height - rounded_rect.CORNER_RADIUS,
                      rounded_rect.CORNER_RADIUS,
                      rounded_rect.CORNER_RADIUS )
        cr.rectangle( width - rounded_rect.CORNER_RADIUS,
                      0,
                      rounded_rect.CORNER_RADIUS,
                      rounded_rect.CORNER_RADIUS )
        cr.paint()

        # Draw the background rounded rectangle.
        corners = []
        if document.roundUpperRight:
            corners.append( rounded_rect.UPPER_RIGHT )
        if document.roundLowerRight:
            corners.append( rounded_rect.LOWER_RIGHT )

        cr.set_source_rgba( *document.background )
        rounded_rect.drawRoundedRect( context = cr,
                                      rect = ( 0, 0, width, height ), 
                                      softenedCorners = corners )
        cr.fill_preserve()
        cr.restore()

        # Next, draw the text.
        document.draw( layout.L_MARGIN,
                       document.shrinkOffset,
                       self.__context )

        width = min( self.__window.getMaxWidth(), width )
        height = min( self.__window.getMaxHeight(), height )

        self.__window.setSize( width, height )
        self.__window.update()


    def hide( self ):
        """
        Clears the window's surface (making it disappear).
        """

        # LONGTERM TODO: Clearing the surface, i.e., painting it
        # clear, seems like a potential performance bottleneck.

        self.__window.setSize( 1, 1 )

        # Frankly, I don't know why this works, but after this
        # function, the resulting window is totally clear. I find it
        # odd, since the alpha value is not being set.  It is a
        # wierdness of Cairo. -- Andrew

        self.__context.set_operator (cairo.OPERATOR_CLEAR)
        self.__context.paint ()
        self.__context.set_operator (cairo.OPERATOR_OVER)

        self.__window.update()
