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
#   enso.commands.factories
#
# ----------------------------------------------------------------------------

"""
    A couple useful CommandFactory implementations.

    GenericPrefixFactory is likely to be the base of most actual command
    factory implementations, since it deals with the relatively common case
    of a family of simple arguments, all sharing a common prefix.

    ArbitraryPostfixFactory can be used as the base for any command factory
    implementation that can accept *any* postfix or argument, such as
      "learn as open <blah>"
      "learn as format <blah>"
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import re

from enso.commands.suggestions import AutoCompletion, Suggestion
from enso.commands.interfaces import AbstractCommandFactory, CommandObject
from enso.messages import displayMessage


# ----------------------------------------------------------------------------
# Private Utility Functions
# ----------------------------------------------------------------------------

def _equivalizeChars( userText ):
    """
    Returns a regular expression in which certain characters are
    replaced with equivalent character sets, e.g., "2" by "[2@]".
    """
    
    # TODO: These appear to only be equivalent characters for US
    # keyboard layouts.

    EQUIVALENT_CHARS = {
        "1" : "1!",
        "2" : "2@",
        "3" : "3#",
        "4" : "4$",
        "5" : "5%",
        "6" : "6^",
        "7" : "7&",
        "8" : "8*",
        "9" : "9(",
        "0" : "0)",
        "-" : "-_",
        "=" : "=+",
        ";" : ":;",
        "-" : "-_",
        "'" : "'\"",
        }
    
    searchText = re.escape( userText )
    for char in EQUIVALENT_CHARS.keys():
        expr = EQUIVALENT_CHARS[char]
        expr = re.escape( expr )
        expr = "[%s]" % expr
        char = re.escape(char)
        searchText = searchText.replace( char, expr )

    # {{{searchText}}} is a pattern that may contain spaces.  To
    # determine whether a string matches searchText, we want any
    # number of spaces in the string to match a single space in
    # searchText.  Therefore, we replace each space in searchText with
    # a "multispace" match RE, i.e., a regular expression that will
    # match one or more spaces.
    space = re.escape( " " )
    multiSpace = "[%s]+" % space
    searchText = searchText.replace( space, multiSpace )

    return searchText


# ----------------------------------------------------------------------------
# Prefix Command Factory
# ----------------------------------------------------------------------------

class GenericPrefixFactory( AbstractCommandFactory ):
    """
    Uses a postfix-prefix system to generate autocompletions and
    suggestions.

    This class can be used to avoid the necessity of implementing
    autocompletion and suggestion functionality, for command factories
    which simply correspond to a finite list of postfixes applied to a
    single prefix.
    """

    # The portion of the command expression that is common to all
    # the command names that this command factory produces.
    PREFIX = ""
    
    # This class variable defines the "help text" displayed in
    # place of a valid postfix; because *any* postfix is valid,
    # we want to display something to indicate to the user
    # that a postfix is required.
    # LONGTERM TODO: Decide whether having a default is acceptable.
    HELP_TEXT = "argument"

    # This class variable defines the "description text" displayed in
    # the top line of the quasimode when a concrete parameter has
    # not been displayed.
    DESCRIPTION_TEXT = None

    def __init__( self ):
        """
        Instantiantes the command factory.

        Must be called by overriden constructors.
        """
        
        AbstractCommandFactory.__init__( self )

        # Each postfix corresponds to one command that this command
        # factory can produce; when combined with the prefix (above),
        # the resulting string is a complete command name.
        self.__postfixes = []
        self.__postfixesChanged = False

        self.__searchString = ""

    def getPostfixes( self ):
        return self.__postfixes 

    def setPostfixes( self, postfixes ):
        self.__postfixesChanged = True
        self.__postfixes = postfixes

    #A protected property; subclasses should maintain this and update
    #it in the .update() method.
    _postfixes = property( fget = getPostfixes, fset = setPostfixes, )

    # Subclasses should use _addPostfix and _removePostfix instead of
    # modifying the postfix list themselves, because modifying the list
    # in place will not invoke the property set method, which means
    # postfixesChanged won't get updated, which is bad.
    def _addPostfix( self, cmdName ):
        self._postfixes = self._postfixes[:] + [cmdName]

    def _removePostfix( self, cmdExpr ):
        newPostfixes = self._postfixes[:]
        newPostfixes.remove( cmdExpr )
        self._postfixes = newPostfixes

    def getCommandList( self ):
        """
        Returns a list of all available command names based on the
        most recently set list of postfixes.
        """

        self.update()
        return [ self.PREFIX + post for post in self._postfixes ]
        

    def __update( self ):
        """
        Private method for maintaining a search-string structure.
        """

        self.update()
        
        if self.__postfixesChanged:
            self.__postfixesChanged = False
            self.__searchString = "\n".join( self.__postfixes )
            

    # LONGTERM TODO: This is not the greatest design.  Perhaps in
    # Mehitabel Core 2.0 this can be replaced with an Observer pattern.
    def update( self ):
        """
        Template Method - Designed to allow sub-classes to update the
        class's interal command/postfix information.

        NOTE: BE CAREFUL! This function gets called on every keystroke
        while the user has typed something that might match this
        factory.  If you don't need to update that often, then do
        something to get out of this function quickly!
        """

        raise NotImplementedError


    def retrieveSuggestions( self, userText ):
        """
        Retrieves the VERY LATEST suggestions available that match
        the userText string.

        NOTE: This method calls self.update() to update the internal
        data structures of the CommandFactory to reflect any changes
        in system state.

        This returns a list of Suggestion objects.
        """

        pattern = userText[len(self.PREFIX):]
        pattern = _equivalizeChars( pattern )

        # Match any command that contains the user postfix (i.e.,
        # any characters followed by the user postfix).
        pattern = ".*" + pattern
        
        matches = self.__findMatches( pattern )

        suggestions = [ Suggestion( userText, self.PREFIX + m )
                        for m in matches ]

        if self.PREFIX.startswith( userText ):
            # If seed text is all or part of the prefix, then
            # autocomplete with help text.
            suggestions.insert(
                0,
                Suggestion( userText, self.PREFIX, self.HELP_TEXT )
                )

        return suggestions


    def autoComplete( self, userText ):
        """
        If userText begins with this factory's prefix, and the
        remainder of userText begins a word of one of this factory's
        postfixes, then returns an Autocompletion object for the
        match.  Otherwise, returns None.
        """

        if self.PREFIX.startswith( userText ):
            # If seed text is all or part of the prefix, then
            # autocomplete with help text.
            return AutoCompletion( userText, self.PREFIX, self.HELP_TEXT )

        elif not userText.startswith( self.PREFIX ):
            return None

        pattern = userText[len(self.PREFIX):]
        pattern = _equivalizeChars( pattern )
        matches = self.__findMatches( pattern )
        if len( self.PREFIX ) > 0 and len( matches ) == 0:
            # We have a real prefix; look for beginings of words.
            matches = self.__findMatches( ".*\\b" + pattern )
        if len(matches) < 1:
            return None
        match = matches[0]
        matchLocation = re.search( pattern, match, re.I ).start()

        newUserText = self.PREFIX
        start = matchLocation
        end = matchLocation + len(userText) - len(self.PREFIX)
        newUserText += match[start:end]
        completion = AutoCompletion( newUserText, self.PREFIX + match )
        return completion


    def __findMatches( self, pattern ):
        """
        Finds all command names that:
          (1) start with the correct prefix, and
          (2) match pattern.
        """
        
        self.__update()

        # This part works by using regular expressions to quickly grab
        # all the new-line delimited substrings that contain
        # the pattern.  NOTE: This will allow us to modify the pattern
        # into a more advanced regexp, allowing ( for example ) the
        # user text "open boo 9temp0" to match to the command named
        # "open boo (temp)".  

        # ^ matches begining of line or begining of string
        # $ matches end of line or end of string
        # .* matches any number of any character, except newlines

        # re.M means that "multiline mode" is used, so "." does not
        # match newlines.
        # re.I matches case-insensitively
        matches = re.findall( pattern = "^" + pattern +".*$",
                              string = self.__searchString,
                              flags = re.M | re.I )
        matches = [ m for m in matches if len(m) > 0 ]
        matches.sort()
        return matches

    def getCommandObj( self, commandName ):
        """
        Returns the command object that matches commandName, if any.
        """

        prefix = self.PREFIX
        if ( len( commandName ) > len( prefix ) ) and \
               commandName.startswith( prefix ):
            parameter = commandName.split( self.PREFIX, 1 )[1]
            return self._generateCommandObj( parameter )
        elif commandName.startswith( prefix ) or \
             prefix.startswith( commandName ):
            parameter = None
            return self._generateCommandObj( parameter )
        else:
            return None


    def _generateCommandObj( self, postfix ):
        """
        Virtual method for getting an actual command object.
        'postfix' is the name of the postfix supplied, if any.

        Must be overriden by subclasses.
        """

        raise NotImplementedError()


class ArbitraryPostfixFactory( GenericPrefixFactory ):
    """
    Abstract factory class for factories that produce "learn as"
    commands, and other command families that can take any argument.
    """

    def autoComplete( self, seedText ):
        """
        Returns an autocompletion for seedText if seedText begins
        with all or part of the prefix for this command factory.
        If the seedText did not have a postfix, then the returned
        suggestion object will have help text.

        Returns None otherwise.
        """
        
        if self.PREFIX.startswith( seedText ):
            # If seed text is all or part of the prefix, then
            # autocomplete with help text.
            return AutoCompletion( seedText, self.PREFIX, self.HELP_TEXT )
        elif seedText.startswith( self.PREFIX ):
            # If the seed text begins with the prefix, but has
            # more than just the seed text (i.e., made it beyond
            # the previous condition), then there is a postfix;
            # autocomplete without trailing help text.
            return AutoCompletion( seedText, seedText )
        else:
            return None


    def retrieveSuggestions( self, userText ):
        """
        Returns a suggestion if the userText is contained in the
        prefix.
        """

        if userText in self.PREFIX:
            return [ Suggestion( userText,
                                 self.PREFIX,
                                 self.HELP_TEXT ) ]
        else:
            return []


    def update( self ):
        """
        Updates the available command list.
        """

        # Since this command factory accepts any postfix, don't do
        # anything.
        pass
