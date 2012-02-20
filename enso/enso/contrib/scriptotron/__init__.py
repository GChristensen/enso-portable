from enso.events import EventManager
from enso.commands import CommandManager
from enso.contrib.scriptotron.tracker import ScriptTracker

def load():
    ScriptTracker.install( EventManager.get(),
                           CommandManager.get() )
