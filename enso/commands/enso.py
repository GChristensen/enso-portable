import os
import subprocess

import enso
from enso import config
from enso.messages import displayMessage

from enso.platform.win32 import gracefully_exit_enso

def cmd_enso(ensoapi, cmd):
    """ Enso system command """
    if cmd == 'quit':
        gracefully_exit_enso()
    elif cmd == 'restart':
        subprocess.Popen([enso.enso_executable, "--restart " + str(os.getpid())])
        gracefully_exit_enso()
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

