import os
import subprocess

import enso
from enso import webui
from enso import config
from enso.messages import displayMessage
from enso.quasimode import layout
from enso.events import EventManager
from enso.contrib import retreat
from enso.platform.win32.shortcuts import Shortcuts
from enso.contrib.scriptotron.tracker import ScriptTracker
from win32api import GetKeyState
from win32con import VK_CAPITAL


def cmd_enso(ensoapi, action):
    """ Enso system command
    <b>Actions:</b><br>
    &nbsp;&nbsp- quit - quit Enso<br>
    &nbsp;&nbsp- restart - restart Enso<br>
    &nbsp;&nbsp- refresh - reload shortcuts available for the 'open' command<br>
    &nbsp;&nbsp- settings - open Enso settings page<br>
    &nbsp;&nbsp- commands - open Enso command list<br>
    &nbsp;&nbsp- tasks - open Enso task editor<br>
    &nbsp;&nbsp- editor - open Enso command editor<br>
    &nbsp;&nbsp- about - show application information<br>
    """
    if action == 'quit':
        if not retreat.is_locked():
            EventManager.get().stop()
        else:
            displayMessage(config.BLOCKED_BY_RETREAT_MSG)
    elif action == 'restart':
        if not retreat.is_locked():
            EventManager.get().stop()
            subprocess.Popen([config.ENSO_EXECUTABLE, "--restart " + str(os.getpid())])
        else:
            displayMessage(config.BLOCKED_BY_RETREAT_MSG)
    elif action == 'refresh':
        Shortcuts.get().refresh_shortcuts()
        ScriptTracker.get()._reloadPyScripts()
        displayMessage(config.REFRESHING_MSG_XML)
    elif action == 'settings':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/options.html")
    elif action == 'commands':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/commands.html")
    elif action == 'tasks':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/tasks.html")
    elif action == 'editor':
        if config.ENABLE_WEB_UI:
            os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/edit.html")
    elif action == 'about':
        displayMessage(enso.config.ABOUT_BOX_XML)


cmd_enso.valid_args = ['about', 'quit', 'tasks', 'restart', 'refresh', 'settings', 'commands', 'scheduler', 'editor']


def cmd_capslock_toggle(ensoapi):
    """ Toggles the current CAPSLOCK state"""
    EventManager.get().setCapsLockMode(GetKeyState(VK_CAPITAL) == 0) 


def cmd_enso_install(ensoapi, package):
    """ Install Python packages using built-in 'pip' package manager"""
    args = ["cmd", "/k", config.ENSO_DIR + "\\python\\python.exe", "-m", "pip", "install", package]
    if config.ENSO_DIR.startswith("C:\\Program Files"):
        args.append("--user")
    subprocess.Popen(args)


def cmd_enso_uninstall(ensoapi, package):
    """ Uninstall Python packages"""
    args = ["cmd", "/k", config.ENSO_DIR + "\\python\\python.exe", "-m", "pip", "uninstall", package]
    subprocess.Popen(args)


def cmd_enso_theme(ensoapi, color = None):
    """ Change Enso color theme"""
    layout.setColorTheme(color)
    ensoapi.display_message("Enso theme changed to \u201c%s\u201d" % color, "enso")

cmd_enso_theme.valid_args = list(layout.COLOR_THEMES.keys())
