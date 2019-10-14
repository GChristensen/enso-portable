import logging
import os
import types

import traceback

from enso import config
from enso.commands.manager import CommandAlreadyRegisteredError
from enso.contrib.scriptotron.tracebacks import TracebackCommand
from enso.contrib.scriptotron.tracebacks import safetyNetted
from enso.contrib.scriptotron.events import EventResponderList
from enso.contrib.scriptotron import adapters
from enso.contrib.scriptotron import cmdretriever
from enso.contrib.scriptotron import ensoapi
from enso.contrib.scriptotron import concurrency

# This may no longer be required (it was for backward compat)
SCRIPTS_FILE_NAME = "~/.ensocommands"

class ScriptCommandTracker:
    def __init__( self, commandManager, eventManager ):
        self._cmdExprs = []
        self._cmdMgr = commandManager
        self._genMgr = concurrency.GeneratorManager( eventManager )
        self._qmStartEvents = EventResponderList(
            eventManager,
            "startQuasimode",
            self._onQuasimodeStart
            )

    @safetyNetted
    def _callHandler( self, handler ):
        result = handler()
        if isinstance( result, types.GeneratorType ):
            self._genMgr.add( result )

    def _onQuasimodeStart( self ):
        for handler in self._qmStartEvents:
            self._callHandler( handler )

    def clearCommands( self ):
        for cmdExpr in self._cmdExprs:
            self._cmdMgr.unregisterCommand( cmdExpr )
        self._cmdExprs = []
        self._qmStartEvents[:] = []
        self._genMgr.reset()

    def _registerCommand( self, cmdObj, cmdExpr ):
        try:
            self._cmdMgr.registerCommand( cmdExpr, cmdObj )
            self._cmdExprs.append( cmdExpr )
        except CommandAlreadyRegisteredError:
            logging.warn( "Command already registered: %s" % cmdExpr )

    def registerNewCommands( self, commandInfoList ):
        for info in commandInfoList:
            if hasattr( info["func"], "on_quasimode_start" ):
                self._qmStartEvents.append( info["func"].on_quasimode_start )
            cmd = adapters.makeCommandFromInfo(
                info,
                ensoapi.EnsoApi(),
                self._genMgr
                )
            self._registerCommand( cmd, info["cmdExpr"] )

class ScriptTracker:
    def __init__( self, eventManager, commandManager ):
        self._scriptCmdTracker = ScriptCommandTracker( commandManager,
                                                       eventManager )
        #self._scriptFilename = os.path.expanduser(SCRIPTS_FILE_NAME)
        from enso.providers import getInterface
        self._scriptFolder = getInterface("scripts_folder")()
        self._lastMods = {}
        self._registerDependencies()
        self._pendingChanges = False

        eventManager.registerResponder(
            self._updateScripts,
            "startQuasimode"
            )

        commandManager.registerCommand( TracebackCommand.NAME,
                                        TracebackCommand() )
        self._updateScripts(True)

    @classmethod
    def install( cls, eventManager, commandManager ):
        cls._instance = cls( eventManager, commandManager )

    @classmethod
    def get( cls ):
        return cls._instance

    def setPendingChanges( self ):
        self._pendingChanges = True

    @safetyNetted
    def _getGlobalsFromSourceCode( self, text, filename ):
        allGlobals = {}
        code = compile( text, filename, "exec" )
        try:
            exec(code, allGlobals)
        except Exception as e:
            print(traceback.format_exc())
            raise e

        return allGlobals
    
    def _getCommandFiles( self ):
        commandFiles = []
        try:
            commandFiles = [
              os.path.join(self._scriptFolder, x)
              for x in os.listdir(self._scriptFolder)
              if x.endswith(".py")
            ]
        except:
            pass

        try:
            userScriptFolder = os.path.join(config.ENSO_USER_DIR, "commands")
            commandFiles = commandFiles + [
                os.path.join(userScriptFolder, x)
                for x in os.listdir(userScriptFolder)
                if x.endswith(".py")
            ]
        except:
            pass

        return commandFiles

    def _reloadPyScripts( self ):
        self._scriptCmdTracker.clearCommands()
        commandFiles = self._getCommandFiles()
        print(commandFiles)
        for f in commandFiles:
            try:
                text = open( f, "r" ).read()
            except:
                continue

            allGlobals = self._getGlobalsFromSourceCode(
                text,
                f
                )

            if allGlobals is not None:
                category = os.path.splitext(os.path.basename(f))[0].replace("_", " ")

                if "CATEGORY" in allGlobals:
                    category = allGlobals["CATEGORY"]

                for fn in allGlobals:
                    if callable(allGlobals[fn]) \
                            and fn.startswith(cmdretriever.SCRIPT_PREFIX):
                        allGlobals[fn].category = category
                        allGlobals[fn].cmdFile = f

                infos = cmdretriever.getCommandsFromObjects( allGlobals )
                self._scriptCmdTracker.registerNewCommands( infos )
                self._registerDependencies( allGlobals )

    def _registerDependencies( self, allGlobals = None ):
        baseDeps = self._getCommandFiles()

        if allGlobals:
            # Find any other files that the script may have executed
            # via execfile().
            extraDeps = [
                obj.__code__.co_filename
                for obj in list(allGlobals.values())
                if ( (hasattr(obj, "__module__")) and
                     (obj.__module__ is None) and 
                     (hasattr(obj, "func_code")) )
                ]
        else:
            extraDeps = []

        self._fileDependencies = list( set(baseDeps + extraDeps) )

    def _updateScripts( self, init=False):
        shouldReload = init

        if config.TRACK_COMMAND_CHANGES or self._pendingChanges:
            for fileName in self._fileDependencies:
                if os.path.exists( fileName ):
                    lastMod = os.stat( fileName ).st_mtime
                    if lastMod != self._lastMods.get(fileName):
                        self._lastMods[fileName] = lastMod
                        shouldReload = True

            for fileName in self._getCommandFiles():
                if fileName not in self._fileDependencies:
                    self._fileDependencies.append(fileName)
                    self._lastMods[fileName] = os.stat( fileName ).st_mtime
                    shouldReload = True

            self._pendingChanges = False

        if shouldReload:
            self._reloadPyScripts()

