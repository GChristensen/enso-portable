# System tray icon integration for the Windows launcher (run_enso.py).

import os
import subprocess

import pythoncom
from win32com.shell import shell, shellcon

from enso import config, tray_actions, webui
from enso.messages import displayMessage
from enso.events import EventManager
from enso.contrib import retreat
from enso.platform.win32.taskbar import SysTrayIcon


def _on_quit(systray):
    if not retreat.is_locked():
        EventManager.get().stop()
    else:
        displayMessage(config.BLOCKED_BY_RETREAT_MSG)


def _on_about(systray):
    displayMessage(config.ABOUT_BOX_XML)


def _on_settings(systray, get_state = False):
    if not get_state:
        os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/options.html")


def _on_help(systray):
    pass


def _on_exec_at_startup(systray, get_state = False):
    startup_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_STARTUP, 0, 0)
    assert os.path.isdir(startup_dir)

    link_file = os.path.join(startup_dir, "Enso.lnk")

    if get_state:
        return os.path.isfile(link_file)
    else:
        if not os.path.isfile(link_file):
            try:
                pythoncom.CoInitialize()
            except:
                # already initialized.
                pass

            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink
            )

            shortcut.SetPath(config.ENSO_EXECUTABLE)
            shortcut.SetWorkingDirectory(config.ENSO_DIR)
            shortcut.SetIconLocation(os.path.join(config.ENSO_DIR, "Enso.ico"), 0)

            shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
                link_file, 0 )
            try:
                pythoncom.CoUnInitialize()
            except:
                pass

            displayMessage("<p><command>Enso</command> will be automatically executed" \
                           " at system startup</p><caption>enso</caption>")
        else:
            os.remove(link_file)
            displayMessage("<p><command>Enso</command> will not start at system startup</p>" \
                           "<caption>enso</caption>")


def _on_restart(systray, get_state = False):
    if not get_state:
        if not retreat.is_locked():
            subprocess.Popen([config.ENSO_EXECUTABLE, "--restart " + str(os.getpid())])
            _on_quit(systray)
        else:
            displayMessage(config.BLOCKED_BY_RETREAT_MSG)


def run(enso_config):
    """Creates and runs the tray icon; blocks the calling thread, so
    this must be called on its own thread."""

    enso_icon = tray_actions.get_icon_path()

    enso_config.SYSTRAY_ICON = SysTrayIcon(
            enso_icon,
            "Enso Open-Source",
            None,
            on_quit = _on_quit)

    enso_config.SYSTRAY_ICON.on_about = _on_about
    enso_config.SYSTRAY_ICON.on_doubleclick = _on_about
    enso_config.SYSTRAY_ICON.add_menu_item("&Restart", _on_restart)

    if config.ENABLE_WEB_UI:
        enso_config.SYSTRAY_ICON.add_menu_item("&Settings", _on_settings)
    if not config.ENSO_EXECUTABLE.endswith("run-enso.exe"):
        enso_config.SYSTRAY_ICON.add_menu_item("E&xecute on startup", _on_exec_at_startup)

    enso_config.SYSTRAY_ICON.main_thread()