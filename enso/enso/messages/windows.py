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
#   enso.messages.windows
#
# ----------------------------------------------------------------------------

"""
    Implements the various Message windows.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import cairo
from enso import graphics
from enso.graphics.transparentwindow import TransparentWindow


# ----------------------------------------------------------------------------
# Generic Message Window
# ----------------------------------------------------------------------------

class MessageWindow:
    """
    A generic message window class, combining the TransparentWindow
    functionality with a Cairo context to create a usable message
    window class, with sizing, positioning, and drawing methods.
    """
    
    def __init__( self, maxSize ):
        """
        Initialize the message window.
        """
        
        self.__maxSize = maxSize
        self.__currSize = ( 1, 1 )
        self.__currPos = ( 0, 0 )

        self.__setupWindow()


    def __setupWindow( self ):
        """
        Creates the MessageWindow's underlying TransparentWindow and
        Cairo Context objects, once and for all.
        """
        
        width = self.__maxSize[0]
        height = self.__maxSize[1]

        xPos = self.__currPos[0]
        yPos = self.__currPos[1]

        # The following are protected to allow subclasses access
        # to them.
        self._wind = TransparentWindow( xPos, yPos, width, height )
        self._context = self._wind.makeCairoContext()


    def getSize( self ):
        return self.__currSize
    def getMaxSize( self ):
        return self.__maxSize
    def getPos( self ):
        return self.__currPos


    # LONGTERM TODO: Consider replacing setSize,setPos with setBox, and
    # establish a clipping function isOnScreen for use in the contract.

    def setSize( self, width, height ):
        """
        Sets the current size of the message window the width, height.

        Using the function appropriately vastly improves performance,
        as it reduces the visible size of the window and the number of
        pixels that must be copied on window updates.
        """

        assert width <= self.getMaxSize()[0] 
        assert height <= self.getMaxSize()[1]

        self.__currSize = width, height

        if self._wind != None:
            self._wind.setSize( width, height )


    def setPos( self, xPos, yPos ):
        """
        Sets the current position of the window to xPos, yPos, which
        should be in points.
        """

        self.__currPos = xPos, yPos
        if self._wind != None:
            self._wind.setPosition( xPos, yPos )

            
    def hide( self ):
        """
        Sets the underlying TransparentWindow's size to (1,1) so that
        the window essentially vanishes.  This effectively "hides" the
        window, causing it to cease interfering with performance of
        windows that are "underneath" the message window.
        """

        # LONGTERM TODO: This method should eventually be
        # re-implmeneted or removed; merely setting the size of the
        # window to 1x1 pixels can still result in performance
        # degredation (see trac ticket #290).

        self._wind.setSize( 1, 1 )
        self._wind.update()

        
    def show( self ):
        """
        Sets the underlying TransparentWindow's size to the stored
        "current size" variable, essentially re-correlating the actual
        displayed rectangle on the screen to the size required by the
        MessageWindow's underlying content.
        """
        
        self.setSize( *self.getSize() )
        self._wind.update()


    def clearWindow( self ):
        """
        "Clears" the underlying cairo context.
        """

        # Works by blanking the whole surface.
        # The cairo paint() method does the whole (clipped) cairo
        # surface.
        cr = self._context
        cr.set_source_rgba( 0, 0, 0, 0 )
        cr.paint()
        
    
def computeWidth( doc ):
    """
    Utility function for computing the 'actual' width of a text layout
    document, by taking the maximum line width.
    """
    
    lines = []
    for b in doc.blocks:
        lines.extend( b.lines )

    if len(lines) == 0:
        return 0
    else:
        return max( [ l.xMax for l in lines ] )
