import os
import sys
import time
import logging
import threading
import pythoncom
import subprocess
import win32gui
import win32con
import shutil

from optparse import OptionParser
from win32com.shell import shell, shellcon

import enso
from enso import config

if sys.version_info > (3, 7):
    os.add_dll_directory(os.path.join(config.ENSO_DIR, "enso", "platform", "win32"))

from enso import webui
from enso.messages import displayMessage
from enso.events import EventManager
from enso.platform.win32.taskbar import SysTrayIcon
from enso.contrib import retreat

sys.path.append(config.ENSO_DIR)
sys.path.append(os.path.join(config.ENSO_DIR, "lib"))
sys.path.append(os.path.join(config.ENSO_USER_DIR, "lib"))


def tray_on_enso_quit(systray):
    if not retreat.is_locked():
        EventManager.get().stop()
    else:
        displayMessage(config.BLOCKED_BY_RETREAT_MSG)


def tray_on_enso_about(systray):
    displayMessage(config.ABOUT_BOX_XML)


def tray_on_enso_settings(systray, get_state = False):
    if not get_state:
        os.startfile("http://" + webui.HOST + ":" + str(webui.PORT) + "/options.html")


def tray_on_enso_help(systray):
    pass


def tray_on_enso_exec_at_startup(systray, get_state = False):
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


def tray_on_enso_restart(systray, get_state = False):
    if not get_state:
        if not retreat.is_locked():
            subprocess.Popen([config.ENSO_EXECUTABLE, "--restart " + str(os.getpid())])
            tray_on_enso_quit(systray)
        else:
            displayMessage(config.BLOCKED_BY_RETREAT_MSG)


def systray(enso_config):
    """ Tray-icon handling code. This have to be executed in its own thread
    """

    enso_icon = os.path.realpath(os.path.join(config.ENSO_DIR, "media", "images", \
                                              "Enso_amethyst.ico" if config.COLOR_THEME == "amethyst" else "Enso.ico"))

    enso_config.SYSTRAY_ICON = SysTrayIcon(
            enso_icon,
            "Enso Open-Source",
            None,
            on_quit = tray_on_enso_quit)

    enso_config.SYSTRAY_ICON.on_about = tray_on_enso_about
    enso_config.SYSTRAY_ICON.on_doubleclick = tray_on_enso_about
    enso_config.SYSTRAY_ICON.add_menu_item("&Restart", tray_on_enso_restart)

    if config.ENABLE_WEB_UI:
        enso_config.SYSTRAY_ICON.add_menu_item("&Settings", tray_on_enso_settings)
    if not config.ENSO_EXECUTABLE.endswith("run-enso.exe"):
        enso_config.SYSTRAY_ICON.add_menu_item("E&xecute on startup", tray_on_enso_exec_at_startup)

    enso_config.SYSTRAY_ICON.main_thread()


def process_options(argv):
    version = '1.0'
    usageStr = "%prog [options]\n\n"
    parser = OptionParser(usage=usageStr, version="%prog " + version)
    #parser.add_option("-l", "--log", action="store", dest="logfile", type="string",
    #                  help="log output into auto-rotated log-file", metavar="FILE")
    parser.add_option("-l", "--log-level", action="store", dest="loglevel",
                      default="ERROR", help="logging level (CRITICAL, ERROR, INFO, WARNING, DEBUG)")
    #parser.add_option("-n", "--no-splash", action="store_false", dest="show_splash",
    #                  default=True, help="Do not show splash window")
    parser.add_option("-c", "--no-console", action="store_false", dest="show_console",
                      default=True, help="Hide console window")
    parser.add_option("-r", "--redirect-stdout", action="store_true", dest="redirect_stdout",
                      default=False, help="Hide console window")
    parser.add_option("-t", "--no-tray", action="store_false", dest="show_tray_icon",
                      default=True, help="Hide tray icon")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,
                      help="No information windows are shown on startup/shutdown")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                      help="Debug mode")

    opts, args = parser.parse_args(argv)
    return opts, args


def configure_init_files():
    if not os.path.isdir(config.ENSO_USER_DIR):
        os.makedirs(config.ENSO_USER_DIR)

    user_lib_dir = os.path.join(config.ENSO_USER_DIR, "lib")
    if not os.path.isdir(user_lib_dir):
        os.makedirs(user_lib_dir)

    user_commands_dir = os.path.join(config.ENSO_USER_DIR, "commands")
    user_commands = os.path.join(user_commands_dir, "user.py")

    if not os.path.isdir(user_commands_dir):
        os.makedirs(user_commands_dir)

    open(user_commands, 'a').close()

    default_enso_rc = os.path.join(config.ENSO_USER_DIR, "ensorc.py")
    if not os.path.exists( default_enso_rc ):
        shutil.copyfile(os.path.join(config.ENSO_DIR, "scripts", "ensorc.py.default"),
                        os.path.join(config.ENSO_USER_DIR, "ensorc.py"))

    load_rc_config(default_enso_rc)

    # legacy ensorc, currently undocumented
    load_rc_config(os.path.join(config.HOME_DIR, ".ensorc"))


def load_rc_config(ensorcPath):
    if os.path.exists( ensorcPath ):
        try:
            logging.info( "Loading '%s'." % ensorcPath )
            contents = open( ensorcPath, "r" ).read()
            compiledContents = compile( contents + "\n", ensorcPath, "exec" )
            allLocals = {}
            exec(compiledContents, {}, allLocals)
            for k, v in allLocals.items():
                setattr(config, k, v)
        except Exception as e:
            logging.exception("Error reading init file")


def configure_logging(args, opts):
    loglevel = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'DEBUG': logging.DEBUG
    }[opts.loglevel]

    user_log = os.path.join(config.ENSO_USER_DIR, "enso.log")

    if opts.show_console:
        print("Logging to console")
        logging.basicConfig(level=loglevel, force=True)
    else:
        print("Redirecting log output to: " + user_log)

        logging.basicConfig(filename=user_log, level=loglevel, force=True)
        logging.debug("test")

    if not opts.debug or opts.redirect_stdout:
        print("Redirecting stdout output to: " + user_log)
        user_log_file = open(user_log + ".stdout", "wb", 0)

        class log():
            def __init__(self):
                self.file = user_log_file

            def write(self, what):
                self.file.write(what.encode())
                self.file.flush()

            def __getattr__(self, attr):
                return getattr(self.file, attr)

        sys.stdout = log()
        sys.stderr = log()


def main(argv = None):
    opts, args = process_options(argv)
    config.ENSO_IS_QUIET = opts.quiet
    config.DEBUG = opts.debug

    configure_logging(args, opts)

    configure_init_files()

    if opts.show_tray_icon:
        # Execute tray-icon code in a separate thread
        threading.Thread(target = systray, args = (config,)).start()

    retreat.start()

    enso.run()

    config.SYSTRAY_ICON.change_tooltip("Closing Enso...")

    win32gui.PostMessage(config.SYSTRAY_ICON.hwnd, win32con.WM_COMMAND, config.SYSTRAY_ICON.CMD_FINALIZE, 0)

    retreat.stop()

    logging.shutdown()

    time.sleep(1)

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])


