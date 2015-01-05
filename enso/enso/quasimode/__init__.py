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
#   enso.quasimode
#
# ----------------------------------------------------------------------------

"""
    Implements the Quasimode.

    This module implements a singleton class that represents the
    quasimode. It handles all quasimodal key events, and the logic for
    transitioning in and out of the quasimode.  When the quasimode
    terminates, it initiates the execution of the command, if any,
    that the user indicated while in the quasimode.  It also handles
    the various kinds of user "error", which primarily consist of "no command
    matches the text the user typed".
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import weakref
import logging
import traceback

from win32api import GetKeyState

from enso import messages
from enso import config
from enso import input

from enso.utils.strings import stringRatioBestMatch
from enso.utils.xml_tools import escape_xml
from enso.quasimode.suggestionlist import TheSuggestionList
from enso.quasimode.window import TheQuasimodeWindow

# Import the standard allowed key dictionary, which relates virtual
# key codes to character strings.
from enso.quasimode.charmaps import STANDARD_ALLOWED_KEYCODES \
    as ALLOWED_KEYCODES

# Import functions to simulate keypresses so that we can sync the
# Num Lock state when entering and exiting quasimode.
from enso.platform.win32.selection import _ContextUtils \
    as ContextUtils


# ----------------------------------------------------------------------------
# TheQuasimode
# ----------------------------------------------------------------------------

class Quasimode:
    """
    Encapsulates the command quasimode state and event-handling.

    Future note: In code review, we realized that implementing the
    quasimode is an ideal case for the State pattern; the Quasimode
    singleton would have a private member for quasimode state, which
    would be an instance of one of two classes, InQuasimode or
    OutOfQuasimode, both descended from a QuasimodeState interface
    class.  Consequances of this include much cleaner transition code
    and separation of event handling into the two states.
    """

    __instance = None

    @classmethod
    def get( cls ):
        return cls.__instance

    @classmethod
    def install( cls, eventManager ):
        from enso.commands import CommandManager

        cls.__instance = cls( eventManager, CommandManager.get() )

    def __init__( self, eventManager, commandManager ):
        """
        Initialize the quasimode.
        """

        self.__cmdManager = commandManager

        # Boolean variable that records whether the quasimode key is
        # currently down, i.e., whether the user is "in the quasimode".
        self._inQuasimode = False

        # Record Num Lock states here so that we can sync the state upon
        # exiting quasimode.
        self._numLockStart = False
        self._numLockNow = False

        # Is the Shift key currently pressed? If it is, then allow
        # entering symbols such as "(" by pressing Shift + 9.
        self._shiftKeyDown = False

        # The QuasimodeWindow object that is responsible for
        # drawing the quasimode; set to None initially.
        # A QuasimodeWindow object is created at the beginning of
        # the quasimode, and destroyed at the completion of the
        # quasimode.
        self.__quasimodeWindow = None

        # The suggestion list object, which is responsible for
        # maintaining all the information about the auto-completed
        # command and suggested command names, and the text typed
        # by the user.
        self.__suggestionList = TheSuggestionList( self.__cmdManager )

        # Boolean variable that should be set to True whenever an event
        # occurs that requires the quasimode to be redrawn, and which
        # should be set to False when the quasimode is drawn.
        self.__needsRedraw = False

        # Whether the next redraw should redraw the entire quasimodal
        # display, or only the description and user text.
        self.__nextRedrawIsFull = False

        self.__eventMgr = eventManager

        # Register a key event responder, so that the quasimode can
        # actually respond to quasimode events.
        self.__eventMgr.registerResponder( self.onKeyEvent, "key" )

        # Register a meta key event responder for Shift so that we can
        # enter characters such as "(" and "^", which allows us to use
        # Enso as an inline calculator instead of having to select an
        # expression first.
        self.__eventMgr.registerResponder( self.onSomeKeyEvent, "somekey" )

        # Creates new event types that code can subscribe to, to find out
        # when the quasimode (or mode) is started and completed.
        self.__eventMgr.createEventType( "startQuasimode" )
        self.__eventMgr.createEventType( "endQuasimode" )

        # Read settings from config file: are we modal?
        # What key activates the quasimode?
        # What keys exit and cancel the quasimode?

        self.setQuasimodeKeyByName( input.KEYCODE_QUASIMODE_START,
                                    config.QUASIMODE_START_KEY )
        self.setQuasimodeKeyByName( input.KEYCODE_QUASIMODE_END,
                                    config.QUASIMODE_END_KEY )
        self.setQuasimodeKeyByName( input.KEYCODE_QUASIMODE_CANCEL,
                                    config.QUASIMODE_CANCEL_KEY )

        self.__isModal = config.IS_QUASIMODE_MODAL

        self.__eventMgr.setModality( self.__isModal )

    def setQuasimodeKeyByName( self, function_name, key_name ):
        # Sets the quasimode to use the given key (key_name must be a
        # string corresponding to a constant defined in the os-specific
        # input module) for the given function ( which should be one of
        # the KEYCODE_QUASIMODE_START/END/CANCEL constants also defined
        # in input.)
        key_code = getattr( input, key_name )
        assert( key_code, "Undefined quasimode key in config file." )
        self.__eventMgr.setQuasimodeKeycode( function_name, key_code )

    def getQuasimodeKey( self ):
        self.__eventMgr.getQuasimodeKeycode()

    def isModal( self ):
        return self.__isModal

    def setModal( self, isModal ):
        assert type( isModal ) == bool
        config.IS_QUASIMODE_MODAL = isModal

        self.__isModal = isModal
        self.__eventMgr.setModality( isModal )

    def getSuggestionList( self ):
        return self.__suggestionList

    def onKeyEvent( self, eventType, keyCode ):
        """
        Handles a key event of particular type.
        """

        if eventType == input.EVENT_KEY_QUASIMODE:

            if keyCode == input.KEYCODE_QUASIMODE_START:
                assert not self._inQuasimode
                self.__quasimodeBegin()
            elif keyCode == input.KEYCODE_QUASIMODE_END:
                assert self._inQuasimode
                self.__quasimodeEnd()
            elif keyCode == input.KEYCODE_QUASIMODE_CANCEL:
                self.__suggestionList.clearState()
                self.__quasimodeEnd()

        elif eventType == input.EVENT_KEY_DOWN and self._inQuasimode:
            # The user has typed a character, and we need to redraw the
            # quasimode.
            self.__needsRedraw = True

            if keyCode == input.KEYCODE_TAB:
                self.__suggestionList.autoType()
            elif keyCode == input.KEYCODE_RETURN:
                self.__suggestionList.autoType()
            elif keyCode == input.KEYCODE_ESCAPE:
                self.__suggestionList.clearState()
            elif keyCode == input.KEYCODE_BACK:
                # Backspace has been pressed.
                self.__onBackspace()
            elif keyCode == input.KEYCODE_DOWN:
                # The user has pressed the down arrow; change which of the
                # suggestions is "active" (i.e., will be executed upon
                # termination of the quasimode)
                self.__suggestionList.cycleActiveSuggestion( 1 )
                self.__nextRedrawIsFull = True
            elif keyCode == input.KEYCODE_UP:
                # Up arrow; change which suggestion is active.
                self.__suggestionList.cycleActiveSuggestion( -1 )
                self.__nextRedrawIsFull = True
            elif keyCode == input.KEYCODE_NUMLOCK:
                # The user has pressed the Num Lock key.
                self._numLockNow = not self._numLockNow
            elif ALLOWED_KEYCODES.has_key( keyCode ):
                # The user has typed a valid key to add to the userText.y
                self.__addUserChar( keyCode )
            else:
                # The user has pressed a key that is not valid.
                pass


    def onSomeKeyEvent( self ):
        """
        Handles a key event for meta keys such as Shift.
        """

        if self._inQuasimode:
            self._shiftKeyDown = (GetKeyState(input.KEYCODE_SHIFT) < 0)


    def __addUserChar( self, keyCode ):
        """
        Adds the character corresponding to keyCode to the user text.
        """

        newCharacter = ALLOWED_KEYCODES[keyCode + (0 if not self._shiftKeyDown else 1000)]
        oldUserText = self.__suggestionList.getUserText()
        self.__suggestionList.setUserText( oldUserText + newCharacter )

        # If the user had indicated one of the suggestions, then
        # typing a character snaps the active suggestion back to the
        # user text and auto-completion.
        self.__suggestionList.resetActiveSuggestion()


    def __onBackspace( self ):
        """
        Deletes one character, if possible, from the user text.
        """

        oldUserText = self.__suggestionList.getUserText()
        if len( oldUserText ) == 0:
            # There is no user text; backspace does nothing.
            return

        self.__suggestionList.setUserText( oldUserText[:-1] )

        # If the user had indicated anything on the suggestion list,
        # then hitting backspace snaps the active suggestion back to
        # the user text.
        self.__suggestionList.resetActiveSuggestion()


    def __quasimodeBegin( self ):
        """
        Executed when user presses the quasimode key.
        """

        assert self._inQuasimode == False

        if self.__quasimodeWindow == None:
            logging.info( "Created a new quasimode window!" )
            self.__quasimodeWindow = TheQuasimodeWindow()

        self.__eventMgr.triggerEvent( "startQuasimode" )

        self.__eventMgr.registerResponder( self.__onTick, "timer" )

        self._inQuasimode = True
        self.__needsRedraw = True

        self._numLockStart = GetKeyState(input.KEYCODE_NUMLOCK)
        self._numLockNow = self._numLockStart

        # Postcondition
        assert self._inQuasimode == True


    def __onTick( self, timePassed ):
        """
        Timer event responder.  Re-draws the quasimode, if it needs it.
        Only registered while in the quasimode.

        NOTE: Drawing the quasimode takes place in __onTick() for
        performance reasons.  If a user mashed down 10 keys in
        the space of a few milliseconds, and the quasimode was re-drawn
        on every single keystroke, then the quasimode could suddenly
        be lagging behind the user a half a second or more.
        """

        # So pychecker doesn't complain...
        dummy = timePassed

        assert self._inQuasimode == True

        if self.__needsRedraw:
            self.__needsRedraw = False
            self.__quasimodeWindow.update( self, self.__nextRedrawIsFull )
            self.__nextRedrawIsFull = False
        else:
            # If the quasimode hasn't changed, then continue drawing
            # any parts of it (such as the suggestion list) that
            # haven't been drawn/updated yet.
            self.__quasimodeWindow.continueDrawing()


    def __quasimodeEnd( self ):
        """
        Executed when user releases the quasimode key.
        """

        # The quasimode has terminated; remove the timer responder
        # function as an event responder.
        self.__eventMgr.triggerEvent( "endQuasimode" )
        self.__eventMgr.removeResponder( self.__onTick )

        # LONGTERM TODO: Determine whether deleting or hiding is better.
        logging.info( "Deleting the quasimode window." )

        # Delete the Quasimode window.
        del self.__quasimodeWindow
        self.__quasimodeWindow = None

        activeCommand = self.__suggestionList.getActiveCommand()
        userText = self.__suggestionList.getUserText()
        if activeCommand != None:
            cmdName = self.__suggestionList.getActiveCommandName()
            self.__executeCommand( activeCommand, cmdName )
        elif len( userText ) > config.BAD_COMMAND_MSG_MIN_CHARS:
            # The user typed some text, but there was no command match
            self.__showBadCommandMsg( userText )

        self._inQuasimode = False
        self.__suggestionList.clearState()

        # Sync the Num Lock state
        if self._numLockStart != self._numLockNow:
            ContextUtils.tapKey( input.KEYCODE_NUMLOCK )


    def __executeCommand( self, cmd, cmdName ):
        """
        Attempts to execute the command.  Catches any errors raised by
        the command code and deals with them appropriately, e.g., by
        launching a bug report, informing the user, etc.

        Commands should deal with user-errors, like lack of selection,
        by displaying messages, etc.  Exceptions should only be raised
        when the command is actually broken, or code that the command
        calls is broken.
        """

        # The following message may be used by system tests.
        logging.info( "COMMAND EXECUTED: %s" % cmdName )
        try:
            cmd.run()
        except Exception:
            # An exception occured during the execution of the command.
            logging.error( "Command \"%s\" failed." % cmdName )
            logging.error( traceback.format_exc() )
            raise


    def __showBadCommandMsg( self, userText ):
        """
        Displays an error message telling the user that userText does
        not match any command.  Also, if there are any reasonable
        commands that were similar but not matching, offers those to
        the user as suggestions.
        """

        # Generate a caption for the message with a couple suggestions
        # for command names similar to the user's text
        caption = self.__commandSuggestionCaption( escape_xml( userText ) )
        badCmd = userText.lower()
        badCmd = escape_xml( badCmd )
        # Create and display a primary message.
        text = config.BAD_COMMAND_MSG
        text = text % ( badCmd, caption )

        messages.displayMessage( text )


    def __commandSuggestionCaption( self, userText ):
        """
        Creates and returns a caption suggesting one or two commands
        that are similar to userText.
        """

        # Retrieve one or two command name suggestions.
        suggestions = self.__cmdManager.retrieveSuggestions( userText )
        cmds = [ s.toText() for s in suggestions ]
        if len(cmds) > 0:
            ratioBestMatch = stringRatioBestMatch( userText.lower(), cmds )
            caption = config.ONE_SUGG_CAPTION
            caption = caption % ratioBestMatch
        else:
            # There were no suggestions; so we don't want a caption.
            caption = ""

        return caption
