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
#   enso.messages.primarywindow
#
# ----------------------------------------------------------------------------

"""
    Implements the various Message windows.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

from enso import graphics
from enso.graphics import xmltextlayout
from enso.graphics.measurement import inchesToPoints
from enso.graphics import rounded_rect
from enso.utils.xml_tools import escape_xml
from enso.messages.windows import MessageWindow, computeWidth
from enso.quasimode import layout

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Total length of time from dismissal to full fade-out (in ms)
ANIMATION_TIME = 250

# Amount of time (in ms) to wait after primary message creation before
# allowing dismissal events to trigger the animation
WAIT_TIME = 80


# ----------------------------------------------------------------------------
# Visual Layout Constants
# ----------------------------------------------------------------------------

# The width, height, and margins of primary messages.
PRIM_MSG_WIDTH = inchesToPoints( 8 )
MAX_MSG_HEIGHT = inchesToPoints( 6 )
PRIM_MSG_MARGIN = inchesToPoints( .2 )

MSG_BGCOLOR = [ .2, .2, .2, .85 ]

# Text sizes for main text and captions.
SCALE = [
    ( 20, 12 ),
    ( 24, 14 ),
    ( 30, 18 ),
    ]
    
PRIM_TEXT_SIZE = 24
CAPTION_TEXT_SIZE = 16
LINE_SPACING = 1
# Distance between the main text block and the caption block.
CAPTION_OFFSET = 0


# ----------------------------------------------------------------------------
# The Primary Message Window class
# ----------------------------------------------------------------------------

class PrimaryMsgWind( MessageWindow ):
    """
    Class that implements the primary message singleton's appearance
    and behavior.

    Essentially, setMessage() sets the current primary message.

    Immediately after the message is set, it is rendered, and the
    class goes into a brief wait cycle, so that user actions don't make
    the message disappear before it can be seen.

    After this wait cycle is completed, the singleton registers itself
    as a responder to dismissal events.  When a dismissal event
    happens, the singleton animates the fading out of the primary message.
    Also, the singleton notifies the message manager that the primary
    message has been dismissed.
    """
    
    def __init__( self, msgMan, eventManager ):
        """
        Initializes the PrimaryMessage singleton
        """

        # Instantiate the underlying MessageWindow to the
        # maxsize suggested by the module constants.
        width = min( PRIM_MSG_WIDTH,
                     graphics.getDesktopSize()[0]-1 )

        height = min( MAX_MSG_HEIGHT,
                      graphics.getDesktopSize()[1]-1 )

        maxSize = ( width, height )
        MessageWindow.__init__( self, maxSize )

        self.__evtManager = eventManager
        self.__msgManager = msgMan
        self.__msg = None
        self.__waiting = False
        self.__animating = False


    def setMessage( self, message ):
        """
        Sets the current primary message to "message".
        """
        
        if self.__msg != None:
            # If there already is a primary message, then "interrupt" it:
            self.__interrupt()

        # Set the current primary message, and draw it.
        self.__msg = message
        self.__drawMessage()

        # Now, set a time-responder to wait for a bit, so that the
        # user doesn't accidentally clear the message before it registers
        # as existing.
        self.__timeSinceCreated = 0
        self.__evtManager.registerResponder( self.waitTick, "timer" )
        self.__waiting = True
        

    def onDismissal( self ):
        """
        Called on a dismissal event, to start the animation process
        and make sure the underlying message does what it needs to
        when it ceases being a primary message.
        """

        self.__msgManager.onDismissal()
        
        self.__evtManager.removeResponder( self.onDismissal )
        self.__timeSinceDismissal = 0
        self.__evtManager.registerResponder( self.animationTick, "timer" )
        self.__animating = True
        

    def animationTick( self, msPassed ):
        """
        Called on a timer event to animate the window's fadeout.
        """
        
        self.__timeSinceDismissal += msPassed
        if self.__timeSinceDismissal > ANIMATION_TIME:
            self.__onAnimationFinished()
            return

        timeLeft  = ANIMATION_TIME - self.__timeSinceDismissal
        frac = timeLeft / float(ANIMATION_TIME)
        opacity = int( 255*frac )
        self._wind.setOpacity( opacity )
        self._wind.update()


    def waitTick ( self, msPassed ):
        """
        Called on a timer event, to give some time between the message
        appearing and when it can disappear.
        """
        
        self.__timeSinceCreated += msPassed
        if self.__timeSinceCreated > WAIT_TIME:
            self.__evtManager.registerResponder( self.onDismissal,
                                                 "dismissal" )
            self.__evtManager.removeResponder( self.waitTick )
            self.__waiting = False

            # The following message may be used by system tests.
            logging.info( "newMessage: %s" % self.__msg.getPrimaryXml() )


    def __position( self ):
        """
        Centers the message window horizontally using the current size.
        """
        
        desksize = graphics.getDesktopSize()
        left, top = graphics.getDesktopOffset()

        xPos = ((desksize[0] - self.getSize()[0]) / 2) + left
        # Set the height based on the "maximum" height, so that the
        # message always appears at the same vertical offset from the
        # top of the screen.
        yPos = ( desksize[1] - self.getMaxSize()[1] ) / 2
        self.setPos( xPos, yPos )


    def __interrupt( self ):
        """
        "interrupts" the current primary message, terminating
        its animation, and/or
        """

        if self.__msg != None:
            # If there's an old message, then we've got an
            # event responder registered:
            if self.__waiting:
                self.__evtManager.removeResponder( self.waitTick )
                self.__waiting = False
            if self.__animating:
                self.__evtManager.removeResponder( self.animationTick )
                self.__animating = False
            else:
                self.__evtManager.removeResponder( self.onDismissal )

        if self.__waiting:
            self.__evtManager.removeResponder( self.waitTick )

    def __drawMessage( self ):
        """
        Draws the current message to the underlying Cario context.
        """
        
        # This function is the master drawing function; all layout and
        # rendering methods are called from here.

        text = self.__msg.getPrimaryXml()
        self.clearWindow()

        msgText, capText = splitContent( text )
        width,height = self.getMaxSize()
        width -= 2*PRIM_MSG_MARGIN
        height -= 2*PRIM_MSG_MARGIN
        msgDoc, capDoc = self.__layoutText( msgText,
                                            capText,
                                            width,
                                            height )
        width, height, msgPos, capPos = \
               self.__layoutBlocks( msgDoc, capDoc )

        # Set the window size and draw the outlining rectangle
        self.__setupBackground( width, height )
        # Draw the text.
        msgDoc.draw( msgPos[0], msgPos[1], self._context )
        if capDoc != None:
            capDoc.draw( capPos[0], capPos[1], self._context )

        # Set the window opacity (which can be left at 0 by the animation)
        self._wind.setOpacity( 255 )
        # Show and update the window.
        self.show()


    def __isOneLineMsg( self, msgDoc, capDoc ):
        """
        Determines whether msgDoc and capDoc are both one line.
        """
        
        numMsgLines = 0
        for block in ( msgDoc.blocks ):
            numMsgLines += len( block.lines )
        numCapLines = 0
        for block in ( capDoc.blocks ):
            numCapLines += len( block.lines )
        return (numCapLines == 1 and numMsgLines == 1)


    def __layoutText( self, msgText, capText, width, height ):
        """
        Lays out msgText and capText into two seperate document
        objects.

        Returns a tuple: ( msgDoc, capDoc )
        NOTE: capDoc can be None, if capText is None.
        """

        root = "<document>%s</document>"

        for msgSize, capSize in reversed( SCALE[1:] ):
            try:
                msgDoc = layoutMessageXml(
                    xmlMarkup = root % msgText,
                    width = width,
                    height = height,
                    size = msgSize,
                    )
                if capText != None:
                    capDoc = layoutMessageXml(
                        xmlMarkup = root % capText,
                        width = width,
                        height = height - msgDoc.height,
                        size = capSize
                        )
                else:
                    capDoc = None
                return msgDoc, capDoc
            except Exception:
                # TODO: Lookup exact error.
                pass
            
        # This time, ellipsify.
        msgSize, capSize = SCALE[0]
        msgDoc = layoutMessageXml(
            xmlMarkup = root % msgText,
            width = width,
            height = height * .8,
            size = msgSize,
            ellipsify = "true",
            )
        if capText != None:
            capDoc = layoutMessageXml(
                xmlMarkup = root % capText,
                width = width,
                height = height * .2,
                size = capSize,
                ellipsify = "true",
                )
        else:
            capDoc = None
        return msgDoc, capDoc


    def __setupBackground( self, width, height ):
        """
        Given a text region of width and height, sets the size of the
        underlying window to be that plus margins, and draws a rounded
        background rectangle.
        """

        width += (2*PRIM_MSG_MARGIN)-2
        height += (2*PRIM_MSG_MARGIN)-2
        width = int(width)
        height = int(height)
        assert width <= self.getMaxSize()[0], \
               "width %s, self.getMaxSize()[0] %s" \
               % (width, self.getMaxSize()[0])
        self.setSize( width, height )
        self.__position()
        
        cr = self._context
        rounded_rect.drawRoundedRect(
            context = cr,
            rect = ( 0, 0, width, height ),
            softenedCorners = rounded_rect.ALL_CORNERS,
            )
        cr.set_source_rgba( *MSG_BGCOLOR )
        cr.fill_preserve()


    def __layoutBlocks( self, messageDoc, captionDoc ):
        """
        Determines how the documents messageDoc and captionDoc should
        be combined to form a complete message window.

        Returns a tuple:
          ( width, height, messagePosition, captionPosition )
        """

        capDoc, msgDoc = captionDoc, messageDoc
        if capDoc == None:
            width = computeWidth( msgDoc )
            height = msgDoc.height
            msgPos = ( PRIM_MSG_MARGIN, PRIM_MSG_MARGIN )
            capPos = None
        elif self.__isOneLineMsg( msgDoc, capDoc ):
            msgWidth = computeWidth( msgDoc )
            capWidth = computeWidth( capDoc )
            width = max( msgWidth, capWidth )
            height = msgDoc.height + capDoc.height
            msgPos = ( PRIM_MSG_MARGIN + ( ( width - msgWidth ) / 2 ), 
                       PRIM_MSG_MARGIN )
            capPos = ( PRIM_MSG_MARGIN + ( ( width - capWidth ) / 2 ),
                       msgPos[1] + msgDoc.height )
        else:
            msgWidth = computeWidth( msgDoc )
            capWidth = computeWidth( capDoc ) 
            width = max( msgWidth, capWidth )
            height = msgDoc.height + capDoc.height
            msgPos = ( PRIM_MSG_MARGIN, PRIM_MSG_MARGIN )
            capPos = ( width - capWidth + PRIM_MSG_MARGIN,
                       msgPos[1] + msgDoc.height )
        return width, height, msgPos, capPos
        

    def __onAnimationFinished( self ):
        """
        Called when the animation is finished.
        """

        if self.__animating:
            self.__evtManager.removeResponder( self.animationTick )
            self.__animating = False
        self.hide()
        self.__msg = None

        self.__msgManager.onPrimaryMessageFinished()


# ----------------------------------------------------------------------------
# Xml Layout
# ----------------------------------------------------------------------------

# The master style registry for primary messages.
_styles = xmltextlayout.StyleRegistry()

_styles.add(
    "document",
    margin_top = "0.0pt",
    margin_bottom = "0.0pt",
    font_family = "Gentium",
    font_style = "normal",
    max_lines = "0",
    ellipsify = "false",
    text_align = "left",
    )

_styles.add(
    "p",
    color = layout.WHITE,
    margin_top = "0pt",
    margin_bottom = "0pt",
    )

_styles.add(
    "caption",
    color = layout.DESIGNER_GREEN,
    margin_top = "%spt" % CAPTION_OFFSET,
    margin_bottom = "0pt",
    )

_styles.add(
    "command",
    color = layout.DESIGNER_GREEN,
    )

# The tag aliases for primary message XML.
_tagAliases = xmltextlayout.XmlMarkupTagAliases()
_tagAliases.add( "p", baseElement = "block" )
_tagAliases.add( "caption", baseElement = "block" )
_tagAliases.add( "command", baseElement = "inline" )


def layoutMessageXml( xmlMarkup, width, size, height, ellipsify="false",
                      raiseLayoutExceptions=False ):
    """
    Lays out the xmlMarkup in a block that is width wide.

    if raiseLayoutExceptions is False, then this function will
    suppress any exceptions raised when parsing xmlMarkup and replace
    it with a message that tells the end-user that the message was
    broken, providing the end-user with as much of the original
    message as possible.  If raiseLayoutExceptions is True, however,
    any exceptions raised will be passed through to the caller.
    """

    maxLines = int( height / (size*LINE_SPACING) )
    
    _styles.update( "document",
                    width = "%fpt" % width,
                    line_height = "%spt" % int(size*LINE_SPACING),
                    max_lines = maxLines,
                    font_size = "%spt" % size,
                    ellipsify = ellipsify,
                    )

    try:
        document = xmltextlayout.xmlMarkupToDocument(
            xmlMarkup,
            _styles,
            _tagAliases
            )
    except Exception, e:
        if raiseLayoutExceptions:
            raise
        logging.warn( "Could not layout message text %s; got error %s"
                      % ( xmlMarkup, e ) )
        document = xmltextlayout.xmlMarkupToDocument(
            "<document><p>%s</p>%s</document>" %
                 ( escape_xml( xmlMarkup.strip() ),
                   "<caption>from a broken message</caption>" ),
            _styles,
            _tagAliases
            )

    return document


def splitContent(  messageXml ):
    """
    Splits messageXml into two parts: main, and caption.
    """
    
    capLocation = messageXml.find( "<caption>" )
    if capLocation == -1:
        return ( messageXml, None )
    else:
        return ( messageXml[:capLocation], messageXml[capLocation:] )
