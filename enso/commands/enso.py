import os
import importlib
import subprocess

import enso
from enso import config
from enso.messages import displayMessage
from enso.events import EventManager

def retreat_locked():
    retereat_spec = importlib.util.find_spec('enso.retreat')
    if retereat_spec is not None:
        from enso import retreat
        return retreat.is_locked()
    return False


def cmd_enso(ensoapi, cmd):
    """ Enso system command """
    if cmd == 'quit':
        if not retreat_locked():
            EventManager.get().stop()
    elif cmd == 'restart':
        if not retreat_locked():
            EventManager.get().stop()
            subprocess.Popen([config.ENSO_EXECUTABLE, "--restart " + str(os.getpid())])
    elif cmd == 'userhome':
        ensoapi.display_message(os.path.expanduser("~"))
    elif cmd == 'about':
        displayMessage(enso.config.ABOUT_BOX_XML)

cmd_enso.valid_args = ['about', 'quit', 'restart', 'userhome']

from enso.events import EventManager
from win32api import GetKeyState 
from win32con import VK_CAPITAL 

def cmd_capslock_toggle(ensoapi):
    """ Toggles the current CAPSLOCK state"""
    EventManager.get().setCapsLockMode(GetKeyState(VK_CAPITAL) == 0) 

def cmd_enso_install(ensoapi, package):
    """ Install Python packages using 'pip'"""
    subprocess.Popen(["cmd", "/k " + config.ENSO_DIR + "/python/python.exe -m pip install " + package])

