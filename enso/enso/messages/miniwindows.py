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
#   enso.messages.miniwindows
#
# ----------------------------------------------------------------------------

"""
    Implements the mini message windows.

    Two parts:
     - the "mini message queue" for managing all mini messages.
     - the "mini message window" for displaying each mini message.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import config
from enso import graphics
from enso.graphics.measurement import pointsToPixels, pixelsToPoints
from enso.graphics import rounded_rect
from enso.messages.windows import MessageWindow, computeWidth
from enso.messages.primarywindow import layoutMessageXml
from enso.messages import Message


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

MINI_WIND_SIZE = 256, 70
MINI_WIND_SIZE = [ pixelsToPoints( pixSize ) for pixSize in MINI_WIND_SIZE ]
MINI_MARGIN = pixelsToPoints( 10 )
MINI_SCALE = [ 10, 12, 14 ]
MINI_BG_COLOR = [ .62, .75, .34, .85 ]


# ----------------------------------------------------------------------------
# Mini Message Queue
# ----------------------------------------------------------------------------

class MiniMessageQueue:
    """
    A class for controlling the behavior and animatior of mini messages.

    LONGTERM TODO: More documentation for this class and its methods.
    """

    # Mode/state constants; the class is always in one of these states.
    EMPTY = 0
    POLLING = 1
    APPEARING = 2
    VANISHING = 3

    def __init__( self, msgMan, eventManager ):
        self.__evtManager = eventManager
        self.__msgManager = msgMan
        self.__newMessages = []
        self.__visibleMessages = []

        self.__isPolling = False

        self.__status = self.EMPTY
        self.__changingIndex = None
        self.__hidingAll = False

        self.__mouseoverIndex = None
        self.__helpWindow = None
        self.__mousePos = None
        self.__mouseChanged = False

    def hideAll( self ):
        if self.__hidingAll:
            return
        else:
            self.__hidingAll = True
            self.__startPolling()

    def addMessage( self, msg ):
        if msg.isFinished():
            return
        else:
            self.__newMessages.append( msg )
            # Switch to polling to trigger the animation.
            if self.__status == self.EMPTY:
                self.__startPolling()

    def onMouseMove( self, x, y ):
        if self.__status != self.POLLING:
            return

        if self.__mousePos != (x,y):
            self.__mousePos = (x,y)
            self.__mouseChanged = True


    def __onMouseMove( self ):
        """
        Checks whether x,y is inside any of the mini-windows.
        """

        if not self.__mouseChanged:
            return

        self.__mouseChanged = False
        x, y = self.__mousePos

        oldIndex = self.__mouseoverIndex
        newIndex = None
        for index in range( len(self.__visibleMessages) ):
            miniWind = self.__visibleMessages[index]
            size = miniWind.getSize()
            pos = miniWind.getPos()
            if ( x > pos[0] and x < (pos[0] + size[0]) ) \
                   and ( y > pos[1] and y < (pos[1] + size[1]) ):
                # The mouse is inside this miniWindow
                if index == oldIndex:
                    # Don't change the appearance; it's already
                    # 'moused-over'.
                    newIndex = oldIndex
                    break
                else:
                    newIndex = index
                    break

        if newIndex != oldIndex and oldIndex != None:
            # The mouse has changed.
            miniWind = self.__visibleMessages[oldIndex]
            miniWind._wind.setOpacity( 255 )
            miniWind._wind.update()
            self.__hideHelpMessage()
        if newIndex != None:
            miniWind = self.__visibleMessages[newIndex]
            xPos, yPos = miniWind.getPos()
            if newIndex == len( self.__visibleMessages ):
                rounded = True
            else:
                rounded = False
            self.__showHelpMessage( xPos, yPos, rounded )

            miniWind._wind.setOpacity( 0 )
            miniWind._wind.update()
            
        self.__mouseoverIndex = newIndex


    def onTick( self, msPassed ):
        if self.__status == self.POLLING:
            self.__onMouseMove()
            
            if len( self.__visibleMessages ) == 0 \
                   and len( self.__newMessages ) == 0:
                # There are no messages to poll for!
                self.__stopPolling()
            elif len( self.__newMessages ) != 0:
                self.__startAppearing( self.__newMessages.pop( 0 ) )
            elif self.__hidingAll:
                if len( self.__visibleMessages ) > 0:
                    self.__startVanishing( len(self.__visibleMessages)-1 )
            else:
                for index in range( len(self.__visibleMessages) ):
                    if self.__visibleMessages[index].message.isFinished():
                        self.__startVanishing( index )
        elif self.__status == self.APPEARING:
            # Update the appearing animation.
            self.__onAppearingTick( msPassed )
        elif self.__status == self.VANISHING:
            # Update the appearing animation.
            self.__onVanishingTick( msPassed )
        else:
            # LONGTERM TODO: Decide whether this should raise an assertion
            # error, or just set the status to polling.
            raise Exception( "What's going on!?" )


    def __showHelpMessage( self, xPos, yPos, rounded ):
        if self.__helpWindow == None:
            msgXml = config.MINI_MSG_HELP_XML
            msg = Message( fullXml = msgXml, isPrimary = False,
                           isMini = True )
            newWindow = MiniMessageWindow( msg, xPos, yPos )
            self.__helpWindow = newWindow
        else:
            self.__helpWindow.setPos( xPos, yPos )

        self.__helpWindow._wind.setOpacity( 255 )
        if rounded:
            self.__helpWindow.roundTopLeftCorner()
        else:
            self.__helpWindow.unroundTopLeftCorner()
        #self.__helpWindow._wind.update()


    def __hideHelpMessage( self ):
        self.__helpWindow.hide()
        

    def __roundTopWindow( self ):
        for msg in self.__visibleMessages[:-1]:
            msg.unroundTopLeftCorner()
        if len( self.__visibleMessages ) > 0:
            topMsg = self.__visibleMessages[-1]
            topMsg.roundTopLeftCorner()

    def __startPolling( self ):
        self.__status = self.POLLING

        if self.__isPolling:
            return
        else:
            self.__isPolling = True

            self.__evtManager.registerResponder( self.onTick, "timer" )
            self.__evtManager.registerResponder( self.onMouseMove,
                                                 "mousemove" )

    def __stopPolling( self ):
        assert self.__status == self.POLLING
        assert self.__isPolling

        self.__isPolling = False
        self.__hidingAll = False
        self.__evtManager.removeResponder( self.onTick )
        self.__evtManager.removeResponder( self.onMouseMove )
        self.__status = self.EMPTY

    def __startAppearing( self, msg ):
        xPos = graphics.getDesktopSize()[0]
        xPos -= MINI_WIND_SIZE[0]

        yPos = graphics.getDesktopSize()[1]
        # Move up for each visible message, including this one.
        numVisible = len( self.__visibleMessages ) + 1
        yPos -= ( MINI_WIND_SIZE[1] * numVisible )
        
        # TODO: Add this code back in at some point, when
        # the getStartBarRect() function (or some equivalent)
        # has been added.

        #taskBarPos, taskBarSize = graphics.getStartBarRect()
        #if taskBarPos[1] != 0:
        #    # Startbar is on bottom.
        #    yPos -= pixelsToPoints(taskBarSize[1])
        #if taskBarPos[0] > 0:
        #    # Startbar is on the right.
        #    xPos -= pixelsToPoints(taskBarSize[0])

        newWindow = MiniMessageWindow( msg, xPos, yPos )
        self.__visibleMessages.append( newWindow )
        self.__changingIndex = len(self.__visibleMessages) - 1
        self.__status = self.APPEARING
        self.__roundTopWindow()

    def __stopAppearing( self ):
        self.__changingIndex = None
        self.__startPolling()

    def __startVanishing( self, index ):
        self.__changingIndex = index
        if self.__changingIndex == self.__mouseoverIndex:
            miniWind = self.__visibleMessages[self.__changingIndex]
            miniWind._wind.setOpacity( 255 )
            miniWind._wind.update()
            self.__hideHelpMessage()
            
        self.__status = self.VANISHING

    def __stopVanishing( self ):
        self.__visibleMessages.pop( self.__changingIndex )
        if self.__mouseoverIndex != None:
            if len( self.__visibleMessages ) == 0:
                self.__mouseoverIndex = None
            elif self.__changingIndex < self.__mouseoverIndex:
                self.__mouseoverIndex = max( 0, self.__mouseoverIndex-1 )
            elif self.__changingIndex == self.__mouseoverIndex:
                self.__mouseoverIndex = None
        self.__changingIndex = None
        self.__startPolling()
        self.__roundTopWindow()
        self.__msgManager.onMiniMessageFinished()

    def __onAppearingTick( self, msPassed ):
        # So pychecker doesn't complain
        dummy = msPassed

        fracPer = 0.1
        msg = self.__visibleMessages[ self.__changingIndex ]
        if msg.isFinishedAppearing:
            self.__stopAppearing()
            return
        else:
            msg.fadeIn( fracPer )

    def __onVanishingTick( self, msPassed ):
        # So pychecker doesn't complain
        dummy = msPassed

        distancePer = 1
        msg = self.__visibleMessages[ self.__changingIndex ]
        if msg.isFinishedVanishing:
            self.__stopVanishing()
            return
        else:
            msg.slideOut( distancePer )
            if self.__changingIndex != len( self.__visibleMessages ) - 1:
                for i in range( self.__changingIndex + 1,
                                len( self.__visibleMessages) ):
                    self.__visibleMessages[i].slideDown( distancePer )


# ----------------------------------------------------------------------------
# Generic Message Window
# ----------------------------------------------------------------------------

class MiniMessageWindow( MessageWindow ):
    """
    LONGTERM TODO: More documentation for this class and its methods.
    """
        
    def __init__( self, msg, xPos, yPos ):
        MessageWindow.__init__( self, MINI_WIND_SIZE )
        self.__isRounded = False
        self.__draw( msg, xPos, yPos )
        self.isFinishedVanishing = False
        self.isFinishedAppearing = False
        self.message = msg
        self._wind.setOpacity( 0 )

    def roundTopLeftCorner( self ):
        self.clearWindow()
        self.__isRounded = True
        self.__draw( self.message, *self.getPos() )
        self._wind.update()

    def unroundTopLeftCorner( self ):
        self.clearWindow()
        self.__isRounded = False
        self.__draw( self.message, *self.getPos() )
        self._wind.update()

    def slideDown( self, distance ):
        xPos, yPos = self.getPos()
        yPos += distance
        self.setPos( xPos, yPos )
        self._wind.update()

    def slideOut( self, distance ):
        if self.isFinishedVanishing:
            return
        width, height = self.getSize()
        xPos, yPos = self.getPos()
        if height-distance < 1:
            yPos += height
            height = 1
            self.isFinishedVanishing = True
        else:
            yPos += distance
            height -= distance
        self.setPos( xPos, yPos )
        self.setSize( width, height )
        self._wind.update()

    def fadeIn( self, fraction ):
        currFrac = self._wind.getOpacity() / 255.
        currFrac = min( fraction + currFrac, 1 )
        if currFrac == 1:
            self.isFinishedAppearing = True
            return
        self._wind.setOpacity( int(currFrac*255) )
        self._wind.update()

    def __draw( self, msg, xPos, yPos ):
        width, height = MINI_WIND_SIZE
        self.setSize( width, height )

        self.setPos( xPos, yPos )

        docSize = width - 2*MINI_MARGIN, height - 2*MINI_MARGIN
        doc = self.__layout( msg, docSize[0], docSize[1] )

        afterWidth = computeWidth( doc )
        afterHeight = doc.height

        xPos = ( width - afterWidth ) / 2
        yPos = ( height - afterHeight ) / 2
        
        cr = self._context
        if self.__isRounded:
            corners = [rounded_rect.UPPER_LEFT]
        else:
            corners = []
            
        cr.set_source_rgba( *MINI_BG_COLOR )
        rounded_rect.drawRoundedRect(
            context = cr,
            rect = ( 0, 0, width, height),
            softenedCorners = corners,
            )
        cr.fill_preserve()

        doc.draw( xPos, yPos, cr )
        
            
    def __layout( self, msg, width, height ):
        text = msg.getMiniXml()
        text = "<document>%s</document>" % text
        for size in reversed( MINI_SCALE[1:] ):
            try:
                doc = layoutMessageXml( xmlMarkup = text,
                                        width = width,
                                        size = size,
                                        height = height, )
                return doc
            except Exception:
                # TODO: Lookup actual errors and catch them.
                pass

        doc = layoutMessageXml( xmlMarkup = text,
                                width = width,
                                size = size,
                                height = height,
                                ellipsify = "true",
                                )
        return doc
