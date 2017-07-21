import os
import sys
import operator
import time
import logging
import subprocess

import enso
from enso import config
from enso import input
from enso.messages import displayMessage
from enso.commands.manager import CommandManager
from SendKeys import SendKeys as sendkeys
from enso.quasimode import Quasimode
from enso.platform.win32 import gracefully_exit_enso

def cmd_enso(ensoapi, cmd):
    """ Enso system command """
    if cmd == 'quit':
        gracefully_exit_enso()
    if cmd == 'restart':
        subprocess.Popen([enso.enso_executable, "--restart " + str(os.getpid())])
        gracefully_exit_enso()
    elif cmd == 'about':
        displayMessage(enso.config.ABOUT_BOX_XML)

cmd_enso.valid_args = ['about', 'quit', 'restart']

from enso.events import EventManager
from win32api import GetKeyState 
from win32con import VK_CAPITAL 

def cmd_capslock_toggle(ensoapi):
    """ Toggles current CAPSLOCK state"""
    EventManager.get().setCapsLockMode(GetKeyState(VK_CAPITAL) == 0) 
