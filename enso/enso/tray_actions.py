"""
Platform-neutral actions for the tray/menu-bar icon menus.

The win32 tray (enso.platform.win32.tray) predates this module and
keeps its own Windows-specific implementations (run-enso.exe restart,
os.startfile); the Linux and macOS trays share these.
"""

import logging
import os
import subprocess
import sys
import webbrowser

from enso import config
from enso.messages import displayMessage
from enso.events import EventManager
from enso.contrib import retreat

try:
    from enso import webui
except ImportError:
    webui = None


def quit_enso():
    if not retreat.is_locked():
        EventManager.get().stop()
    else:
        displayMessage(config.BLOCKED_BY_RETREAT_MSG)


def show_about():
    displayMessage(config.ABOUT_BOX_XML)


def restart_enso():
    if retreat.is_locked():
        displayMessage(config.BLOCKED_BY_RETREAT_MSG)
        return
    # Relaunch detached, delayed so this instance has released its key
    # grab / event tap before the new one acquires it.
    argv = [sys.executable] + sys.argv
    subprocess.Popen(["/bin/sh", "-c", 'sleep 1; exec "$@"', "_"] + argv,
                     start_new_session=True)
    EventManager.get().stop()


def settings_available():
    return bool(config.ENABLE_WEB_UI and webui)


def open_settings():
    if settings_available():
        webbrowser.open("http://" + webui.HOST + ":" + str(webui.PORT)
                        + "/options.html")


def get_icon_path():
    """Path of the .ico for the configured color theme (the same
    selection the win32 tray makes)."""
    name = ("Enso_amethyst.ico" if config.COLOR_THEME == "amethyst"
            else "Enso.ico")
    return os.path.realpath(
        os.path.join(config.ENSO_DIR, "media", "images", name))


def get_launcher_path():
    """Absolute path of the cross-platform launcher script, for
    start-at-login entries."""
    return os.path.join(config.ENSO_DIR, "scripts", "run_enso.py")
