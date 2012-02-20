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
#   enso.quasimode.window
#
# ----------------------------------------------------------------------------

"""
    Implements the quasimode's transparent window.

    Throughout this module, it is important to keep in mind what the
    various visual elements of the quasimode are.  Below is a mediocre
    ASCII representation of those elements:

      Description Text
      user and auto-complete text
      suggestion 1
      suggestion 2
      suggestion 3
      suggestion 4
      ...

    The number of suggestions is limited by a constant declared in the
    suggestion list module.

    Each line of text is drawn by a separate "window", meaning that
    there are actual separate transparent windows for each of them.
    This allows a performance tweak: only those windows that have text
    in them are actually drawn.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import time

from enso.quasimode.linewindows import TextWindow
from enso.quasimode.layout import QuasimodeLayout
from enso.quasimode.layout import HEIGHT_FACTOR
from enso.quasimode.layout import DESCRIPTION_SCALE
from enso.quasimode.layout import AUTOCOMPLETE_SCALE, SUGGESTION_SCALE
from enso import config


# ----------------------------------------------------------------------------
# TheQuasimodeWindow
# ----------------------------------------------------------------------------

class TheQuasimodeWindow:
    """
    Implements the quasimode's display, in a multi-line transparent window.
    """

    # LONGTERM TODO: We will eventually need to deal with the overflow
    # cases in the correct ways: the autocompletion/user text should
    # wrap (as much as necessary), the suggestion list entries should
    # (1) have a max size using ellipses and (2) should "vertically
    # wrap" if there are more suggestions than will fit on one screen,
    # the help text should have a max length with ellipsis
        
    def __init__( self ):
        """
        Instantiates the quasimode window, creating all the necessary
        windows.
        """

        # Create a window for each line, keeping track of how tall
        # that window is.  Use a "top" variable to know how far down
        # the screen the top of the next window should start.

        height = DESCRIPTION_SCALE[-1]*HEIGHT_FACTOR
        self.__descriptionWindow = TextWindow(
            height = height,
            position = [ 0, 0 ],
            )
        top = height
        
        height = AUTOCOMPLETE_SCALE[-1]*HEIGHT_FACTOR
        self.__userTextWindow = TextWindow(
            height = height,
            position = [ 0, top ],
            )
        top += height
    
        self.__suggestionWindows = []
        for i in range( config.QUASIMODE_MAX_SUGGESTIONS ):
            height = SUGGESTION_SCALE[-1]*HEIGHT_FACTOR
            self.__suggestionWindows.append( TextWindow(
                height = height,
                position = [ 0, top ],
                ) )
            top += height

        # The time, in float seconds since the epoch, when the last
        # drawing of the quasimode display started.
        self.__drawStart = 0


    def update( self, quasimode, isFullRedraw ):
        """
        Fetches updated information from the quasimode, lays out and
        draws the quasimode window.

        This should only be called when the quasimode itself has
        changed.

        'isFullRedraw' is a boolean; if it is True, then the entire
        quasimode display, including suggestion list, will be redrawn
        when this function returns.  Otherwise, only the description
        text and user text will be redrawn, and the suggestions will
        be scheduled for redraw later.
        """

        # Instantiate a layout object, effectively laying out the
        # quasimode display.
        layout = QuasimodeLayout( quasimode )

        self.__drawStart = time.time()

        newLines = layout.newLines

        self.__descriptionWindow.draw( newLines[0] )

        suggestions = quasimode.getSuggestionList().getSuggestions()
        if len( suggestions[0].toXml() ) == 0 \
           and len( suggestions[0].getSource() ) == 0:
            self.__userTextWindow.hide()
        else:
            self.__userTextWindow.draw( newLines[1] )

        suggestionLines = newLines[2:]

        # We now need to hide all line windows.
        for i in range( len( suggestionLines ),
                        len( self.__suggestionWindows ) ):
            self.__suggestionWindows[i].hide()

        self.__suggestionsLeft = _makeSuggestionIterator(
            suggestionLines,
            self.__suggestionWindows
            )

        if isFullRedraw:
            while self.continueDrawing( ignoreTimeElapsed = True ):
                pass


    def continueDrawing( self, ignoreTimeElapsed = False ):
        """
        Continues drawing any parts of the quasimode display that
        haven't yet been drawn, such as the suggestion list.

        If 'ignoreTimeElapsed' is True, then the
        QUASIMODE_SUGGESTION_DELAY constant will be ignored and any
        pending suggestion waiting to be drawn will be rendered.

        Returns whether a suggestion was drawn.

        This function should only be called after update() has been
        called.
        """

        if self.__suggestionsLeft:
            timeElapsed = time.time() - self.__drawStart
            if ( (not ignoreTimeElapsed) and 
                 (timeElapsed < config.QUASIMODE_SUGGESTION_DELAY) ):
                return False
            try:
                suggestionDrawer = self.__suggestionsLeft.next()
                suggestionDrawer.draw()
                return True
            except StopIteration:
                self.__suggestionsLeft = None
        return False


class _SuggestionDrawer:
    """
    Private object encapsulating the rendering of a suggestion to a
    suggestion window, useful for the delayed rendering of a
    suggestion.
    """

    def __init__( self, line, suggestionWindow ):
        self.__suggestionWindow = suggestionWindow
        self.__line = line

    def draw( self ):
        self.__suggestionWindow.draw( self.__line )


def _makeSuggestionIterator( lines, suggestionWindows ):
    """
    Returns a generator that provides _SuggestionDrawer objects for
    each suggestion in the given suggestion lines, allowing each
    suggestion line to be drawn to a respective suggestion window at a
    later time.
    """

    for i in range( len(lines) ):
        yield _SuggestionDrawer( lines[i],
                                 suggestionWindows[i] )
