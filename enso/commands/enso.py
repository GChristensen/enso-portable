import os
import subprocess
import sys
import webbrowser

import enso
from enso import config
from enso.messages import displayMessage
from enso.quasimode import layout
from enso.events import EventManager
from enso.contrib import retreat
from enso import tray_actions
from enso.contrib.scriptotron.tracker import ScriptTracker

try:
    from enso import webui
except ImportError:
    webui = None

_WIN32 = sys.platform.startswith("win")

if _WIN32:
    from enso.platform.win32.shortcuts import Shortcuts
elif sys.platform == "darwin":
    from enso.platform.osx.shortcuts import Shortcuts
else:
    from enso.platform.linux.shortcuts import Shortcuts


def _open_webui_page(page):
    if config.ENABLE_WEB_UI and webui:
        webbrowser.open("http://" + webui.HOST + ":" + str(webui.PORT)
                        + "/" + page)


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
        tray_actions.quit_enso()
    elif action == 'restart':
        if _WIN32:
            if not retreat.is_locked():
                EventManager.get().stop()
                subprocess.Popen([config.ENSO_EXECUTABLE,
                                  "--restart " + str(os.getpid())])
            else:
                displayMessage(config.BLOCKED_BY_RETREAT_MSG)
        else:
            tray_actions.restart_enso()
    elif action == 'refresh':
        Shortcuts.get().refresh_shortcuts()
        ScriptTracker.get()._reloadPyScripts()
        displayMessage(config.REFRESHING_MSG_XML)
    elif action == 'settings':
        _open_webui_page("options.html")
    elif action == 'commands':
        _open_webui_page("commands.html")
    elif action == 'tasks':
        _open_webui_page("tasks.html")
    elif action == 'editor':
        _open_webui_page("edit.html")
    elif action == 'about':
        tray_actions.show_about()


cmd_enso.valid_args = ['about', 'quit', 'tasks', 'restart', 'refresh', 'settings', 'commands', 'scheduler', 'editor']


if _WIN32:
    from win32api import GetKeyState
    from win32con import VK_CAPITAL

    def cmd_capslock_toggle(ensoapi):
        """ Toggles the current CAPSLOCK state"""
        EventManager.get().setCapsLockMode(GetKeyState(VK_CAPITAL) == 0)


def cmd_enso_install(ensoapi, package):
    """ Install Python packages using built-in 'pip' package manager"""
    if _WIN32:
        args = ["cmd", "/k", config.ENSO_DIR + "\\python\\python.exe", "-m", "pip", "install", package]
        if config.ENSO_DIR.startswith("C:\\Program Files"):
            args.append("--user")
        subprocess.Popen(args)
    else:
        displayMessage("<p>Installing <command>%s</command>...</p>"
                       "<caption>enso</caption>" % package)
        subprocess.Popen([sys.executable, "-m", "pip", "install", package])


def cmd_enso_uninstall(ensoapi, package):
    """ Uninstall Python packages"""
    if _WIN32:
        args = ["cmd", "/k", config.ENSO_DIR + "\\python\\python.exe", "-m", "pip", "uninstall", package]
        subprocess.Popen(args)
    else:
        subprocess.Popen([sys.executable, "-m", "pip", "uninstall", "-y",
                          package])
        displayMessage("<p>Uninstalling <command>%s</command></p>"
                       "<caption>enso</caption>" % package)


def cmd_enso_theme(ensoapi, color = None):
    """ Change Enso color theme"""
    layout.setColorTheme(color)
    ensoapi.display_message("Enso theme changed to “%s”" % color, "enso")

cmd_enso_theme.valid_args = list(layout.COLOR_THEMES.keys())
