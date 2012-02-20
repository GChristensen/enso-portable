import types

from enso.commands import CommandObject
from enso.commands.factories import GenericPrefixFactory
from enso.commands.factories import ArbitraryPostfixFactory
from enso.contrib.scriptotron.tracebacks import safetyNetted

ARG_REQUIRED_MSG = "An argument is required."

class FuncCommand( CommandObject ):
    def __init__( self, cmdName, func, desc, help, ensoapi, 
                  generatorManager, takesArg = False, argValue = None ):
        CommandObject.__init__( self )

        self.name = cmdName
        self.func = func
        self.takesArg = takesArg
        self.argValue = argValue
        self.ensoapi = ensoapi
        self.generatorManager = generatorManager

        self.setName( cmdName )
        self.setHelp( help )
        self.setDescription( desc )

    @safetyNetted
    def run( self ):
        if self.takesArg:
            result = self.func(self.ensoapi, self.argValue)
        else:
            result = self.func(self.ensoapi)

        if isinstance( result, types.GeneratorType ):
            self.generatorManager.add( result )

class NoArgumentCommand( CommandObject ):
    def __init__( self, description, message, ensoapi ):
        CommandObject.__init__( self )
        self.setDescription( description )
        self.ensoapi = ensoapi
        self.message = message

    def run( self ):
        self.ensoapi.display_message( self.message )

class ArgFuncMixin( object ):
    def __init__( self, cmdName, cmdExpr, func, argName, desc,
                  help, ensoapi, generatorManager, isArgRequired ):
        self.cmdName = cmdName
        self.func = func
        self.desc = desc
        self.isArgRequired = isArgRequired
        self.ensoapi = ensoapi
        self.generatorManager = generatorManager

        self.HELP_TEXT = argName
        self.NAME = cmdExpr
        self.PREFIX = "%s " % cmdName
        self.DESCRIPTION_TEXT = desc
        self.setHelp( help )

    def _generateCommandObj( self, postfix ):
        """
        Returns the command object that matches commandName, if any.
        """

        if not postfix and self.isArgRequired:
            return NoArgumentCommand( self.DESCRIPTION_TEXT,
                                      ARG_REQUIRED_MSG,
                                      self.ensoapi )
        else:
            return FuncCommand(
                cmdName = self.cmdName,
                func = self.func,
                desc = self.desc,
                help = self.getHelp(),
                ensoapi = self.ensoapi,
                generatorManager = self.generatorManager,
                takesArg = bool(postfix),
                argValue = postfix
                )

class ArbitraryArgFuncCommand( ArbitraryPostfixFactory, ArgFuncMixin ):
    def __init__( self, *args, **kwargs ):
        ArbitraryPostfixFactory.__init__( self )
        ArgFuncMixin.__init__( self, *args, **kwargs )

    _generateCommandObj = ArgFuncMixin._generateCommandObj

class BoundedArgFuncCommand( GenericPrefixFactory, ArgFuncMixin ):
    def __init__( self, *args, **kwargs ):
        GenericPrefixFactory.__init__( self )
        ArgFuncMixin.__init__( self, *args, **kwargs )

    @safetyNetted
    def update( self ):
        self._postfixes = self.func.valid_args

    _generateCommandObj = ArgFuncMixin._generateCommandObj

def makeCommandFromInfo( info, ensoapi, generatorManager ):
    if info["cmdType"] == "no-arg":
        return FuncCommand(
            info["cmdName"],
            info["func"],
            info["desc"],
            info["help"],
            ensoapi,
            generatorManager
            )
    elif info["cmdType"] in ["bounded-arg", "arbitrary-arg"]:
        if info["cmdType"] == "bounded-arg":
            CommandClass = BoundedArgFuncCommand
        else:
            CommandClass = ArbitraryArgFuncCommand
        return CommandClass(
            info["cmdName"],
            info["cmdExpr"],
            info["func"],
            info["argName"],
            info["desc"],
            info["help"],
            ensoapi,
            generatorManager,
            info["isArgRequired"]
            )
    else:
        raise ValueError( "Unknown command type: %s" % info["cmdType"] )
