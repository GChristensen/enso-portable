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
#   enso.commands.manager
#
# ----------------------------------------------------------------------------

"""
    The CommandManager singleton.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

from enso.commands.interfaces import CommandExpression, CommandObject
from enso.commands.interfaces import AbstractCommandFactory
from enso.commands.factories import GenericPrefixFactory


# ----------------------------------------------------------------------------
# The Command Manager
# ----------------------------------------------------------------------------

class CommandManager:
    """
    Provides an interface to register and retrieve all commands.

    Allows client code to register new command implementations, find
    suggestions, and retrieve command objects.
    """

    __instance = None

    @classmethod
    def get( cls ):
        if not cls.__instance:
            cls.__instance = cls()
        return cls.__instance

    CMD_KEY = CommandExpression( "{all named commands}" )

    def __init__( self ):
        """
        Initializes the command manager.
        """

        self.__cmdObjReg = CommandObjectRegistry()
        self.__cmdFactoryDict = {
            self.CMD_KEY : self.__cmdObjReg,
            }


    def registerCommand( self, cmdName, cmdObj ):
        """
        Called to register a new command with the command manager.
        """

        try:
            cmdExpr = CommandExpression( cmdName )
        except AssertionError as why:
            logging.error( "Could not register %s : %s "
                           % ( cmdName, why ) )
            raise

        if cmdExpr.hasArgument():
            # The command expression has an argument; it is a command
            # with an argument.
            assert isinstance( cmdObj, AbstractCommandFactory ), \
                "Command object with a parameter must be instance " \
                "of AbstractCommandFactory"
            assert cmdExpr not in self.__cmdFactoryDict,\
                "Command is already registered: %s" % cmdExpr
            self.__cmdFactoryDict[ cmdExpr ] = cmdObj
        else:
            # The command expression has no argument; it is a
            # simple command with an exact name.
            assert isinstance( cmdObj, CommandObject ), \
                   "Could not register %s. Object has not type CommandObject." % cmdName
            self.__cmdObjReg.addCommandObj( cmdObj, cmdExpr )

    def unregisterCommand( self, cmdName ):
        cmdFound = False
        for cmdExpr in list(self.__cmdFactoryDict.keys()):
            if str(cmdExpr) == cmdName:
                del self.__cmdFactoryDict[cmdExpr]
                cmdFound = True
                break

        if not cmdFound:
            self.__cmdObjReg.removeCommandObj( cmdName )
            cmdFound = True
        if not cmdFound:
            raise RuntimeError( "Command '%s' does not exist." % cmdName )

    def getCommandExpression( self, commandName ):
        """
        Returns the unique command expression that is associated with
        commandName.  For example, if commandName is 'open emacs', and
        the command expression was 'open {file}', then a command expression
        object for 'open {file}' will be returned.
        """

        commands = []

        for expr in self.__cmdFactoryDict.keys():
            if expr.matches( commandName ):
                # This expression matches commandName; try to fetch a
                # command object from the corresponding factory.
                cmd = self.__cmdFactoryDict[expr].getCommandObj( commandName )
                if expr == self.CMD_KEY and cmd != None:
                    commands.append( ( commandName, commandName ) )
                elif cmd != None:
                    # The factory returned a non-nil command object.
                    # Make sure that nothing else has matched this
                    # commandName.
                    commands.append( (expr.getPrefix(), expr) )

        if len(commands) == 0:
            return None
        else:
            # If there are several matching commands, return only
            # the alphabetically first.
            commands.sort( key = lambda a: a[0] )
            return commands[0][1]


    def getCommand( self, commandName ):
        """
        Returns the unique command with commandName, based on the
        registered CommandObjects and the registered CommandFactories.

        If no command matches, returns None explicitly.
        """

        commands = []

        for expr in self.__cmdFactoryDict.keys():
            if expr.matches( commandName ):
                # This expression matches commandName; try to fetch a
                # command object from the corresponding factory.
                cmd = self.__cmdFactoryDict[expr].getCommandObj( commandName )
                if cmd is not None:
                    # The factory returned a non-nil command object.
                    commands.append( ( expr, cmd ) )

        if len( commands ) == 0:
            # There is no match
            return None
        elif len( commands ) == 1:
            # There is exactly one match
            return commands[0][1]
        else:
            # There are more matches, choose the best one
            prefixes = dict( (expr.getPrefix(), cmd) for (expr, cmd) in commands )
            
            # This is the old approach, returning alphabetically first
            #return sorted(prefixes.items())[0][1]

            # Try to find longest possible exact match first:
            longest_name = commandName
            # If there is no space at the end, it is a parameter there
            if not longest_name.endswith(' '):
                # Strip parameter off
                longest_name = longest_name[:longest_name.rfind(" ")]
            else:
                longest_name = longest_name.rstrip(" ")
            
            cmd = None
            for _ in range(longest_name.count(" ") + 1):
                cmd = prefixes.get(longest_name+' ')
                if cmd:
                    print("Returning longest match: %s" % longest_name)
                    logging.debug("Longest match: '%s'", longest_name)
                    break
                longest_name = longest_name[:longest_name.rfind(" ")]

            return cmd


    def autoComplete( self, userText ):
        """
        Returns the best match it can find to userText, or None.
        """

        completions = []

        # Check each of the command factories for a match.
        for expr in self.__cmdFactoryDict.keys():
            if expr.matches( userText ):
                cmdFact = self.__cmdFactoryDict[expr]
                completion = cmdFact.autoComplete( userText )
                if completion != None:
                    completions.append( completion )

        if len( completions ) == 0:
            return None
        else:
            completions.sort( key = lambda a: a.toText() )
            return completions[0]


    def retrieveSuggestions( self, userText ):
        """
        Returns an unsorted list of suggestions.
        """

        suggestions = []
        # Extend the suggestions using each of the command factories
        for expr in self.__cmdFactoryDict.keys():
            if expr.matches( userText ):
                factory = self.__cmdFactoryDict[expr]
                suggestions += factory.retrieveSuggestions( userText )

        return suggestions


    def getCommands( self ):
        """
        Returns a dictionary of command expression strings and their
        associated implementations (command objects or factories).
        """

        # Get a dictionary form of the command object registry:
        cmdDict = self.__cmdObjReg.getDict()

        # Extend the dictionary to cover the command factories.
        for expr in list(self.__cmdFactoryDict.keys()):
            if expr == self.CMD_KEY:
                # This is the command object registry; pass.
                pass
            else:
                # Cast the expression as a string.
                cmdDict[ str(expr) ] = self.__cmdFactoryDict[expr]

        return cmdDict
        
        
# ----------------------------------------------------------------------------
# A CommandObject Registry
# ----------------------------------------------------------------------------

class CommandAlreadyRegisteredError( Exception ):
    """
    Error raised when someone tries to register two commands under
    the same name with the registry.
    """

    pass


class CommandObjectRegistry( GenericPrefixFactory ):
    """
    Class for efficiently storing and searching a large number of
    commands (where each command is an object with a corresponding
    command name).
    """

    PREFIX = ""

    # added to filter disabled commands
    NAME = "__commandObjectRegistry"

    def __init__( self ):
        """
        Initialize the command registry.
        """

        GenericPrefixFactory.__init__( self )

        self.__cmdObjDict = {}
        self.__dictTouched = False

    def update( self ):
        pass

    def getDict( self ):
        return self.__cmdObjDict

    def addCommandObj( self, command, cmdExpr ):
        """
        Adds command to the registry under the name str(cmdExpr).
        """

        assert isinstance( cmdExpr, CommandExpression ),\
            "addCommandObj(): cmdExpr arg is not CommandExpression type"
        assert not cmdExpr.hasArgument()

        cmdName = str(cmdExpr)
        if cmdName in self.__cmdObjDict:
            raise CommandAlreadyRegisteredError()

        self.__cmdObjDict[ cmdName ] = command
        self.__dictTouched = True

        self._addPostfix( cmdName )


    def removeCommandObj( self, cmdExpr ):
        cmdFound = False
        if cmdExpr in self.__cmdObjDict:
            del self.__cmdObjDict[cmdExpr]
            cmdFound = True
        if cmdFound:
            self.__dictTouched = True
            self._removePostfix( cmdExpr )
        else:
            raise RuntimeError( "Command object '%s' not found." % cmdExpr )

            

    def getCommandObj( self, cmdNameString ):
        """
        Returns the object corresponding to cmdNameString.

        NOTE: This will raise a KeyError if cmdNameString is not a
        valid command name.
        """

        try:
            return self.__cmdObjDict[ cmdNameString ]
        except KeyError:
            return None


if __name__ == "__main__":
    import doctest

    doctest.testmod()


# vim:set tabstop=4 shiftwidth=4 expandtab:
