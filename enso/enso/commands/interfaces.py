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
#   enso.commands.interfaces
#
# ----------------------------------------------------------------------------

"""
    This module defines classes that can be sub-classed to implement
    commands.

    == Background ==============================================
    
    In Enso, we are ultimately attempting to transform the characters
    typed by the user (the "user text") into an action (a "command").

    In general, there are two ways of doing this.  The first is an
    absolute mapping between a unique string of characters (the
    "command name") and a distinct action (the "command").
    Technically, every single command can be implemented in this way;
    but from both the user's perspective and the developer's
    perspective, it is unwieldy to think of "fontsize 12" as a
    seperate command from "fontsize 8".

    So enters the second method of mapping user text to commands:
    commands with arguments.  For a command with arguments, the
    command name is split into its "prefix" (the part that is fixed)
    and an "argument" (that part that changes).

    So where does that leave us?  With a complex situation that cannot
    be simplified.

    == Module Description =======================================

    This module lays out four class interfaces: _CommandImpl,
    CommandObject, AbstractCommandFactory, and CommandExpression.

    The _CommandImpl is an abstract class that any command
    implementation should inherit from, i.e., a base class common to
    both CommandObject and AbstractCommandFactory.

    The CommandObject defines the interface for objects that execute a
    single command.  This object encapsulates the actual code
    associated with exactly one unique string of characters typed by
    the user.  It has methods for describing and executing the action
    corresponding to exactly one possible user text.

    The AbstractCommandFactory defines a generic interface for objects
    that implement commands with arguments, and therefore can respond
    to a range of possible user text strings.  As its name implies,
    the ultimate goal of a CommandFactory is to produce an actual
    command, in this case, a CommandObject.  The CommandFactory has
    methods for determining whether or not it can produce a command
    corresponding to some user text, as well as for producing a
    CommandObject when required.

    Finally, the CommandExpression encapsulates the form that a
    command name can take. For many commands, this will simply be the
    unique string of characters that form the command's name.  But for
    commands that can take arguments, a CommandExpression can take a
    more complicated form.

    Whereever commands are implemented, there should be an exact
    mapping between CommandExpression and _CommandImpl objects.
"""

# ----------------------------------------------------------------------------
# Command Objects
# ----------------------------------------------------------------------------

class _CommandImpl( object ):
    """
    A "command implementation" is either a CommandObject (for commands
    that take no arguments) or a CommandFactory (for commands that
    take arguments).

    This class is a placeholder ancestor class that holds
    functionality common to both kinds of implementations.
    """

    def __init__( self ):
        """
        Initializes the command implementation object.
        """
        
        self.__description = None
        self.__helpText = None

    # LONGTERM TODO: Consider using Python's property() function
    # for providing access to these data members.
    
    def setDescription( self, descr ):
        self.__description = descr

    def getDescription( self ):
        return self.__description


    def setHelp( self, helpText ):
        self.__helpText = helpText

    def getHelp( self ):
        return self.__helpText


class CommandObject( _CommandImpl ):
    """
    An object with a run() method which implements the action of a
    command.  It also has various getters and setters for certain
    properties of commands.
    """
    
    def __init__( self ):
        """
        Initializes the command object.
        """
        
        _CommandImpl.__init__( self )
        
        self.__name = None


    def getName( self ):
        return self.__name

    def setName( self, name ):
        self.__name = name


    def run( self ):
        """
        Abstract Method: Should execute the command.

        NOTE: This method should execute shortly, and return
        immediately. If the command implementation needs to launch a
        thread or process in order to accomplish this, then so be it.

        NOTE: Commands should only raise exceptions when they are
        actually broken.  Any "user errors", like malformed selections
        or invalid applications, should cause the command to do
        something graceful (e.g., showing a primary message), and
        should not raise an exception.
        """

        raise NotImplementedError()

class AbstractCommandFactory( _CommandImpl ):
    """
    A "CommandFactory" is an object which can take some text, and
    return the best matched CommandObject from among some collection
    that it understands.  It is intended to implement commands with
    arguments (i.e., sets of closely related commands with a common
    prefix in their name).

    To allow for implementation optimizations, this class has methods
    for fetching Suggestions for a given chunk of user text.  That
    way, subclasses can determine the most appropriate autocompletions
    and suggestions.  For example, a command factory implementing the
    "FONT SIZE {number}" set of commands might never provide
    autocompletions, because it may be determined that the user should
    always enter an exact number.
    """

    def getCommandList( self ):
        """
        Returns a list of all available command names (a list of strings).
        """

        raise NotImplementedError()


    def retrieveSuggestions( self, userText ):
        """
        Returns a list containing the VERY LATEST suggestions (in the
        form of Suggestion objects) available that match the userText
        string.  Can (and often will) have side effects on the object's
        internal data structure.
        """

        raise NotImplementedError()

        
    def autoComplete( self, userText ):
        """
        If this factory can produce a match to userText, then returns
        an AutoCompletion object.  Otherwise, returns None.
        """

        raise NotImplementedError()


    def getCommandObj( self, commandName ):
        """
        Should return a CommandObject matching commandName, or else
        None.
        """

        raise NotImplementedError()


# ----------------------------------------------------------------------------
# Command Expression Class
# ----------------------------------------------------------------------------

class CommandExpression:
    """
    A "CommandExpression" is an object that encapsulates the basic form
    of the name or names of a given command implementation.

    Command expressions, in their string form, are either strings
    that are exactly one command name, or are strings containing
    curly brackets {} to indicate that they take a parameter, e.g.:
      "minimize"
      "upper case"
      "open {object}"
      "goto {window name}"
      "font size {number}"
    There must be at most one curly-bracket parameter, and it must come
    at the end of the string.
    """

    def __init__( self, stringExpression ):
        """
        Instantiates the expression object.
        """

        expr, prefix, arg = self.__computeExpression( stringExpression )
        self.__string = expr
        self.__prefix = prefix
        self.__arg = arg


    def __str__( self ):
        return self.getString()
    
    def getString( self ):
        return self.__string

    def getPrefix( self ):
        return self.__prefix

    def getArg( self ):
        return self.__arg

    def hasArgument( self ):
        return len(self.__arg) > 0

    def __computeExpression( self, expr ):
        """
        Calculates and stores all approriate information for
        expr.
        """
        
        bracket1 = expr.find( "{" )
        bracket2 = expr.find( "}" )

        why = "Malformed command expression: %s" % expr
        # The end bracket must be at the end, or not found at all.
        assert ( bracket2 == len(expr)-1 ) or \
               ( bracket2 == -1 ), why
        # Either both brackets are found, or neither are found.
        assert ( bracket1 == -1 or not bracket2 == -1 ), why

        string = expr
        # The argument is everything after the first bracket, up to
        # but not including the second bracket:
        if bracket1 > -1:
            arg = expr[bracket1+1:bracket2]
            prefix = expr[:bracket1]
        else:
            arg = ""
            prefix = expr

        return string, prefix, arg


    def matches( self, userText ):
        """
        Determines whether userText matches this command expression;
        note that this does not necessarily guarantee that userText
        maps to an existing command.

        Returns True if:
          (1) self.__prefix starts with userText, or
          (2) userText starts with self.__prefix.
        Returns False otherwise.
        """

        if len(userText)<len(self.__prefix):
            return self.__prefix.startswith( userText )
        else:
            return userText.startswith( self.__prefix )
        return True


