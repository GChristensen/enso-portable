import logging
import inspect
import types
import re

COMMAND_EXPRESSION = re.compile( r"(?P<cmd>.+) {(?P<arg>.+)}" )
SCRIPT_PREFIX = "cmd_"

def _makeVarNameHumanReadable( funcName ):
    return funcName.replace( "_", " " )

def _getCommandInfoFromFunc( func, funcName, cmdName,
                             argName = None, cmdExpr = None ):
    """
    Examples:

      >>> def do_stuff(ensoapi):
      ...   pass

      >>> info = _getCommandInfoFromFunc( do_stuff, 'do_stuff',
      ...                                 'do stuff' )
      >>> info['cmdName']
      'do stuff'
      >>> info['argName']
      >>> info['cmdExpr']
      'do stuff'
      >>> info['cmdType']
      'no-arg'
      >>> info['desc']
      'Runs the python script command: do_stuff()'
      >>> info['help']
      ''
    """

    if func.__doc__:
        lines = func.__doc__.strip().splitlines()
        desc = lines[0]
        help = "\n".join( lines[1:] )
    else:
        desc = "Runs the python script command: %s()" % funcName
        help = ""

    if hasattr( func, "description" ):
        desc = func.description

    if hasattr( func, "help" ):
        help = func.help

    if isinstance( func, types.FunctionType ):
        args, _, _, argDefaults = inspect.getargspec( func )
    else:
        args, _, _, argDefaults = inspect.getargspec( func.__call__ )
        args = args[1:]

    isArgRequired = False

    if len( args ) == 2:
        if not argName:
            argName = _makeVarNameHumanReadable( args[1] )
        if not cmdExpr:
            cmdExpr = "%s {%s}" % (cmdName, argName)
        if not argDefaults:
            isArgRequired = True
        if hasattr( func, "valid_args" ):
            # It's a command that takes a bounded argument.
            cmdType = "bounded-arg"
        else:
            # It's a command that takes an arbitrary argument.
            cmdType = "arbitrary-arg"
    else:
        # It's a command that takes no arguments.

        # TODO: We also arrive here if the function takes a weird
        # number of arguments; for now we'll just assume the user can
        # figure out what's going on wrong when they get a traceback
        # that not enough/too many args were supplied to the function.

        argName = None
        cmdExpr = cmdName
        cmdType = "no-arg"

    return { "func" : func,
             "cmdName" : cmdName,
             "argName" : argName,
             "cmdExpr" : cmdExpr,
             "cmdType" : cmdType,
             "desc" : desc,
             "help" : help,
             "isArgRequired" : isArgRequired }

def getCommandsFromObjects( objects, namePrefix = SCRIPT_PREFIX ):
    """
    Example:

      >>> execGlobals = {}
      >>> exec "def cmd_do_things(ensoapi): pass" in execGlobals
      >>> commands = getCommandsFromObjects( execGlobals )
      >>> len( commands )
      1
      >>> info = commands[0]
      >>> info['cmdName']
      'do things'
    """

    names = [ name for name in objects
              if ( name.startswith( namePrefix ) and
                   callable(objects[name]) ) ]

    commands = []

    for name in names:
        func = objects[name]
        argName = None
        cmdExpr = None
        nameFound = False
        if hasattr( func, "name" ):
            match = COMMAND_EXPRESSION.match( func.name )
            if match:
                cmdName = match.group( "cmd" )
                argName = match.group( "arg" )
                cmdExpr = func.name
                nameFound = True

        if not nameFound:
            cmdName = _makeVarNameHumanReadable( name[len(namePrefix):] )

        info = _getCommandInfoFromFunc(
            func,
            name,
            cmdName,
            argName,
            cmdExpr
            )
        commands.append( info )

    return commands

if __name__ == "__main__":
    import doctest

    doctest.testmod()
