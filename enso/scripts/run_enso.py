
import os
import sys
import time
import logging
import threading
import pythoncom
import subprocess
from win32com.shell import shell, shellcon

import enso
from enso import config
from enso.messages import displayMessage
#from enso.platform.win32.input import InputManager
#from enso.events import EventManager
from enso.platform.win32.taskbar import SysTrayIcon
from enso.platform.win32 import gracefully_exit_enso
from optparse import OptionParser

options = None

enso_dir = os.path.dirname(os.path.realpath(__file__))
enso_dir = os.path.dirname(enso_dir)
sys.path.append(enso_dir)

enso_executable = enso_dir + "\\run-enso"

config.ENSO_DIR = enso_dir

def tray_on_enso_quit(systray):
    gracefully_exit_enso()
    
def tray_on_enso_about(systray):
    displayMessage(
        config.ABOUT_BOX_XML +
        "<p> </p><caption>Hit the <command>CapsLock</command> key to invoke Enso</caption>" )

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

            shortcut.SetPath(enso_executable)
            global enso_dir
            shortcut.SetWorkingDirectory(enso_dir)
            shortcut.SetIconLocation(os.path.join(enso_dir, "Enso.ico"), 0)

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
        subprocess.Popen([enso_executable, "--restart " + str(os.getpid())])
        tray_on_enso_quit(systray)

# def tray_on_enso_pause(systray, get_state = False):
#     if get_state:
#         return enso.config.PAUSED
#     else:
#         enso.config.PAUSED = not enso.config.PAUSED
#         if (enso.config.PAUSED):
#             EventManager.get().stop()
#         else:
#             EventManager.get().run()

def systray(enso_config):
    """ Tray-icon handling code. This have to be executed in its own thread
    """

    enso_icon = os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), "..", "Enso.ico"))

    enso_config.SYSTRAY_ICON = SysTrayIcon(
            enso_icon,
            "Enso open-source",
            None,
            on_quit = tray_on_enso_quit)

    enso_config.SYSTRAY_ICON.on_about = tray_on_enso_about
    enso_config.SYSTRAY_ICON.on_doubleclick = tray_on_enso_about
    #enso_config.SYSTRAY_ICON.add_menu_item("&Pause", tray_on_enso_pause)
    enso_config.SYSTRAY_ICON.add_menu_item("&Restart", tray_on_enso_restart) #restart_enso)
    enso_config.SYSTRAY_ICON.add_menu_item("Execute on &startup", tray_on_enso_exec_at_startup)
    enso_config.SYSTRAY_ICON.main_thread()


def process_options(argv):
    version = '1.0'
    usageStr = "%prog [options]\n\n"
    parser = OptionParser(usage=usageStr, version="%prog " + version)
    #parser.add_option("-l", "--log", action="store", dest="logfile", type="string",
    #                  help="log output into auto-rotated log-file", metavar="FILE")
    #TODO: Implement more command line args
    parser.add_option("-l", "--log-level", action="store", dest="loglevel",
                      default="ERROR", help="logging level (CRITICAL, ERROR, INFO, WARNING, DEBUG)")

    parser.add_option("-n", "--no-splash", action="store_false", dest="show_splash",
                      default=True, help="Do not show splash window")
    parser.add_option("-c", "--no-console", action="store_false", dest="show_console",
                      default=True, help="Hide console window")
    parser.add_option("-t", "--no-tray", action="store_false", dest="show_tray_icon",
                      default=True, help="Hide tray icon")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,
                      help="No information windows are shown on startup/shutdown")

    opts, args = parser.parse_args(argv)
    return opts, args


def main(argv = None):
    global options
    opts, args = process_options(argv)
    options = opts

    config.ENSO_IS_QUIET = options.quiet

    loglevel = {
        'CRITICAL' : logging.CRITICAL,
        'ERROR' : logging.ERROR,
        'INFO' : logging.INFO,
        'WARNING' : logging.WARNING,
        'DEBUG' : logging.DEBUG
        }[opts.loglevel]

    if opts.show_console:
        print("Showing console")
        logging.basicConfig( level = loglevel )
    else:
        print("Hiding console")
        print("Logging into '%s'" % os.path.join(ENSO_DIR, "enso.log"))
        sys.stdout = open("stdout.log", "w", 0) #NullDevice()
        sys.stderr = open("stderr.log", "w", 0) #NullDevice()
        logging.basicConfig(
            filename = os.path.join(ENSO_DIR, "enso.log"),
            level = loglevel )

    if loglevel == logging.DEBUG:
        print(opts)
        print(args)

    global enso_dir
    ensorcPath = os.path.expanduser("~/.ensorc")
    if os.path.exists( ensorcPath ):
        logging.info( "Loading '%s'." % ensorcPath )
        contents = open( ensorcPath, "r" ).read()
        compiledContents = compile( contents + "\n", ensorcPath, "exec" )
        allLocals = {}
        exec(compiledContents, {}, allLocals)
        for k, v in allLocals.items():
            setattr(config, k, v)

#    if not opts.quiet and opts.show_splash:
#        displayMessage("<p>Starting <command>Enso</command>...</p>")

    if opts.show_tray_icon:
        # Execute tray-icon code in separate thread
        threading.Thread(target = systray, args = (config,)).start()

    enso.run()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


