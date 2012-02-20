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
#   enso.quasimode.suggestionlist
#
# ----------------------------------------------------------------------------

"""
    Implements a SuggestionList to keep track of auto-completions,
    suggestions, and other data related to typing in the quasimode.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import commands
from enso.commands.suggestions import AutoCompletion
from enso import config


# ----------------------------------------------------------------------------
# The SuggestionList Singleton
# ----------------------------------------------------------------------------

class TheSuggestionList:
    """ 
    A singleton class that encapsulates all of the textual information
    created when a user types in the quasimode, including the user's
    typed text, the auto-completion, any suggestions, and the command
    description/help text.
    """

    # LONGTERM TODO: The trio of main data elements:
    #   ( __autoCompletion, __suggestions, __activeIndex )
    # These should never be updated except together; and they
    # should never be accessed unless updated. Right now, this
    # involves a nasty, hard-to-maintain cludge of an "update"
    # mechanism.
    # This class should be a new-style class, and these attributes
    # should be properties whose getters appropriately update them.
    # This eliminates the burden on client code to remember to call
    # update near/around fetching these attributes, and will eliminate
    # a source of errors.

    def __init__( self, commandManager ):
        """
        Initializes the SuggestionList.
        """

        self.__cmdManager = commandManager

        # Set all of the member variables to their empty values.
        self.clearState()


    def clearState( self ):
        """
        Clears all of the variables relating to the state of the
        quasimode's generated information.
        """

        # The "user text".  Together with the active index, constitutes
        # the "source" information, i.e., the information from which
        # all the rest is calculated.
        self.__userText = ""
        
        # An index of the above suggestion list indicating which
        # command name the user has indicated.
        self.__activeIndex = 0
        
        # The current auto-completion object.
        self.__autoCompletion = AutoCompletion( originalText = "",
                                                suggestedText = "" )
        
        # The current list of suggestions. The 0th element is the
        # auto-completion.
        self.__suggestions = [ self.__autoCompletion ]
        
        # A boolean telling whether the suggestion list and
        # auto-completion attributes above need to be updated.
        self.__suggestionsDirty = False


    def getUserText( self ):
        return self.__userText


    def setUserText( self, text ):
        """
        Sets the user text based on the value of text.

        NOTE: The stored user text may not be simply a copy of text
        typed by the user; for example, multiple contiguous spaces in
        text may be reduced to a single space.
        """
        
        # Only single spaces are allowed in the user text; additional
        # spaces are ignored.
        while text.find( " "*2 ) != -1:
            text = text.replace( " "*2, " " )
        
        self.__userText = text
        # One of the source variables has changed.
        self.__markDirty()


    def autoType( self ):
        """
        Sets the stored user text to the value indicated by the
        current autocompleted suggestion.
        """
        
        self.__update()

        completion = self.__suggestions[ self.__activeIndex ]
        if completion == None:
            return

        completion = completion.toText()
        if len(completion) == 0:
            return
        self.__userText = completion

        # One of the source variables has changed.
        self.resetActiveSuggestion()
        self.__markDirty()


    def __update( self ):
        """
        While not good general coding style, this method deliberately
        encapsulates all the calls necessary to update the internal
        suggestion list and auto-completion objects, as such calls (by
        their nature) involve a fair amount of string processing and can
        be performance sensitive.
        
        It updates the __suggestions and __autoCompletion attributes
        to reflect the current userText.
        """

        if self.__suggestionsDirty:
            self.__suggestionsDirty = False

            # NOTE: in the next two lines, ".strip()" is called because the
            # autcompletions and suggestions should ignore trailing whitespace.
            self.__autoCompletion = self.__autoComplete(
                self.getUserText().strip()
                )
            self.__suggestions = self.__findSuggestions(
                self.getUserText().strip()
                )
            # We need to verify that it is a valid index; if the
            # namespace changed, then the suggestionss in the above
            # getSuggestions() line might be different than the
            # suggestions were the last time the active index was
            # updated.
            maxIndex = max( [ len(self.__suggestions)-1, 0 ] )
            self.__activeIndex = min( [self.__activeIndex, maxIndex] )


    def __autoComplete( self, userText ):
        """
        Uses the CommandManager to determine if userText auto-completes
        to a command name, and what that command name is.

        Returns an AutoCompletion object; if the AutoCompletion object
        is empty (i.e., the text representation has 0 length), then there
        was no valid auto-completed command name.
        """

        if len( userText ) < config.QUASIMODE_MIN_AUTOCOMPLETE_CHARS:
            autoCompletion = AutoCompletion( userText, "" )
        else:
            autoCompletion = self.__cmdManager.autoComplete( userText )
            if autoCompletion == None:
                autoCompletion = AutoCompletion( userText, "" )
                
        return autoCompletion
    

    def __findSuggestions( self, userText ):
        """
        Uses the command manager to determine if there are any inexact
        but near matches of command names to userText.

        Returns a complete suggestion list, where the 0th element is
        the auto-completion, and each subsequent element (if any) is a
        suggestion different than the autocompletion for a command
        name that is similar to userText.
        """
        
        if len( userText ) < config.QUASIMODE_MIN_AUTOCOMPLETE_CHARS:
            return [ self.__autoCompletion ]

        suggestions = self.__cmdManager.retrieveSuggestions( userText )

        # BEGIN: Performance-improving code.
        # Eliminate most of the suggestions before sorting them.
        threshold = 0.0
        restrictedSuggestions = suggestions[:]
        oldRestrictedSuggestions = restrictedSuggestions

        # LONGTERM TODO: You may be able to optimize the algorithm
        # even further in the following way: assuming that thresh(x)
        # gives you the number of suggestions whose nearness is
        # greater than x, first see if thresh( 0.5 ) >
        # QUASIMODE_MAX_SUGGESTIONS; if so, see if thresh( 0.75 ) is,
        # but if not, see if thresh( 0.25 ) is, and so forth.
        while (len( restrictedSuggestions ) > 
               config.QUASIMODE_MAX_SUGGESTIONS):
            threshold += 0.05
            oldRestrictedSuggestions = restrictedSuggestions
            restrictedSuggestions = [ \
                s for s in oldRestrictedSuggestions \
                if s._nearness > threshold \
                ]

        # Use the second-to-last restricted suggestions, as
        # the last restricted suggestions may actually have
        # fewer than we want.
        suggestions = oldRestrictedSuggestions
        # END: Performance-improving code.
        
        # Because the Suggestion object implements __cmp__ to sort
        # by nearness, we can simply sort the suggestions in place.
        suggestions.sort()
        suggestions = suggestions[:config.QUASIMODE_MAX_SUGGESTIONS]
        
        # Make the auto-completion the 0th suggestion, and not listed
        # more than once.
        auto = self.__autoCompletion
        if len( auto.toText() ) > 0:
            suggestions = [ s for s in suggestions
                            if not s.toText() == auto.toText() ]
        return [ auto ] + suggestions


    def __markDirty( self ):
        """
        Sets an internal variable telling the class that the suggestion list
        is "dirty", and should be updated before returning any information.
        """
        
        self.__suggestionsDirty = True
        

    def getSuggestions( self ):
        """
        In a pair with getAutoCompletion(), this method gets the latest
        suggestion list, making sure that the internal variable is
        updated.
        """
        
        self.__update()

        return self.__suggestions

    
    def getAutoCompletion( self ):
        """
        In a pair with getSuggestions(), this method gets the latest
        auto-completion, making sure that the internal variable is updated.
        """
        
        self.__update()

        return self.__autoCompletion


    def getDescription( self ):
        """
        Determines and returns the description for the currently
        active command.
        """
        
        if self.getActiveCommand() == None:
            if len( self.getAutoCompletion().getSource() ) \
                   < config.QUASIMODE_MIN_AUTOCOMPLETE_CHARS:
                # The user hasn't typed enough to match a command.
                descText = config.QUASIMODE_DEFAULT_HELP
            else:
                # There is no command to match the user's text.
                descText =  config.QUASIMODE_NO_COMMAND_HELP
        else:
            # The active index is more than one, so one of the elements
            # of the suggestion list is active, and we are assured
            # that the active command exists.
            descText = self.getActiveCommand().getDescription()

        descText = descText.strip()

        # Postcondition
        assert len(descText) > 0

        return descText


    def getActiveCommand( self ):
        """
        Returns the active command, i.e., the command object that
        implements the command that is currently indicated to the
        user, either as the auto-completed command, or as a highlighted
        element on the suggestion list.  If there is no active command,
        then the function returns None.
        """

        activeName = self.getActiveCommandName()

        if activeName == "":
            return None
        else:
            return self.__cmdManager.getCommand( activeName )


    def getActiveCommandName( self ):
        """
        Determines the command name of the "active" command, i.e., the
        name that is indicated to the user as the command that will
        be activated on exiting the quasimode.
        """

        self.__update()
        activeSugg = self.__suggestions[self.__activeIndex]
        return activeSugg.toText()

        
    def cycleActiveSuggestion( self, distance ):
        """
        Changes which of the suggestions is "active", i.e., which suggestion
        will be activated when the user releases the CapsLock key.

        Used to implement the up/down arrow key behavior.
        """
        
        self.__activeIndex += distance
        if len( self.getSuggestions() ) > 0:
            truncateLength = len( self.getSuggestions() )
            self.__activeIndex = self.__activeIndex % truncateLength
        else:
            self.__activeIndex = 0
        # One of the source variables has changed.
        self.__markDirty()


    def getActiveIndex( self ):
        return self.__activeIndex
    

    def resetActiveSuggestion( self ):
        """
        Sets the active suggestion to 0, i.e., the user's
        text/auto-completion.
        """

        self.__activeIndex = 0
        # One of the source variables has changed.
        self.__markDirty()
