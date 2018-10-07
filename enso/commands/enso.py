import os
import subprocess

import enso
from enso import webui
from enso import config
from enso.messages import displayMessage
from enso.quasimode import layout
from enso.events import EventManager
from win32api import GetKeyState
from win32con import VK_CAPITAL

def cmd_enso(ensoapi, action):
    """ Enso system command
    <b>Actions:</b><br>
    &nbsp;&nbsp- quit - quit Enso<br>
    &nbsp;&nbsp- restart - restart Enso<br>
    &nbsp;&nbsp- settings - open Enso settings page<br>
    &nbsp;&nbsp- commands - open Enso command list<br>
    &nbsp;&nbsp- scheduler - open Enso scheduler<br>
    &nbsp;&nbsp- editor - open Enso command editor<br>
    &nbsp;&nbsp- about - show application information<br>
    """
    if action == 'quit':
        if not enso.plugin_call("retreat", "is_locked"):
            EventManager.get().stop()
    elif action == 'restart':
        if not enso.plugin_call("retreat", "is_locked"):
            EventManager.get().stop()
            subprocess.Popen([config.ENSO_EXECUTABLE, "--restart " + str(os.getpid())])
    elif action == 'settings':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/options.html")
    elif action == 'commands':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/commands.html")
    elif action == 'scheduler':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/scheduler.html")
    elif action == 'editor':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/edit.html")
    elif action == 'about':
        displayMessage(enso.config.ABOUT_BOX_XML)

cmd_enso.valid_args = ['about', 'quit', 'restart', 'settings', 'commands', 'scheduler', 'editor']

def cmd_capslock_toggle(ensoapi):
    """ Toggles the current CAPSLOCK state"""
    EventManager.get().setCapsLockMode(GetKeyState(VK_CAPITAL) == 0) 

def cmd_enso_install(ensoapi, package):
    """ Install Python packages using built-in 'pip' package manager"""
    subprocess.Popen(["cmd", "/k " + config.ENSO_DIR + "/python/python.exe -m pip install " + package])

def cmd_enso_uninstall(ensoapi, package):
    """ Uninstall Python packages"""
    subprocess.Popen(["cmd", "/k " + config.ENSO_DIR + "/python/python.exe -m pip uninstall " + package])

def cmd_enso_theme(ensoapi, color = None):
    """ Change Enso color theme"""
    layout.setColorTheme(color)
    ensoapi.display_message("Enso theme changed to \u201c%s\u201d" % color, "enso")

cmd_enso_theme.valid_args = list(layout.COLOR_THEMES.keys())
