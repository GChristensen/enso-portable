# Shared helpers for the single cross-platform launcher (run_enso.py).
# The launcher itself is just a fixed sequence of calls into this
# module; every OS-specific branch (CLI options, tray/startup
# integration, output redirection, X11 preflight checks) lives here
# behind a sys.platform check, so the launcher never needs one of its
# own. Windows' run-enso.exe hardcodes the "scripts/run_enso.py" path,
# so that filename can't change; Linux users run the same file.

import logging
import os
import shutil
import sys
import time

from optparse import OptionParser

from enso import config

LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "DEBUG": logging.DEBUG,
}


def create_option_parser(version="1.0"):
    """Returns an OptionParser with the options common to every
    launcher already added; callers may add more before parsing."""
    parser = OptionParser(usage="%prog [options]\n\n", version="%prog " + version)
    parser.add_option("-l", "--log-level", action="store", dest="loglevel",
                      default="ERROR",
                      help="logging level (CRITICAL, ERROR, INFO, WARNING, DEBUG)")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      default=False,
                      help="No information windows are shown on startup/shutdown")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False, help="Debug mode")
    return parser


def bootstrap_sys_path():
    """Adds Enso's own dir and the system/user 'lib' package dirs to
    sys.path, so packages under lib/ are importable."""
    sys.path.append(config.ENSO_DIR)
    sys.path.append(os.path.join(config.ENSO_DIR, "lib"))
    sys.path.append(os.path.join(config.ENSO_USER_DIR, "lib"))


def preflight():
    """OS-specific startup checks that may abort the process before
    anything else runs (e.g. no X11 session on Linux)."""
    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY"):
            sys.exit("Error: DISPLAY is not set. Enso requires an X11 session.")
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
            print("Warning: this looks like a Wayland session. Enso's global "
                  "key grab only sees X11 applications; log into an X11 "
                  "session for reliable operation.", file=sys.stderr)


def platform_bootstrap():
    """One-time OS-specific setup that must run before any Enso
    provider (graphics/input/etc.) is loaded."""
    if sys.platform.startswith("win") and sys.version_info > (3, 7):
        os.add_dll_directory(os.path.join(config.ENSO_DIR, "enso", "platform", "win32"))


def add_platform_options(parser):
    """Adds CLI options that only make sense on some platforms."""
    if sys.platform.startswith("win"):
        parser.add_option("-c", "--no-console", action="store_false", dest="show_console",
                          default=True, help="Hide console window")
        parser.add_option("-r", "--redirect-stdout", action="store_true", dest="redirect_stdout",
                          default=False, help="Hide console window")
        parser.add_option("-t", "--no-tray", action="store_false", dest="show_tray_icon",
                          default=True, help="Hide tray icon")


def configure_basic_logging(loglevel_name, log_file=None):
    """Configures the root logger, either to the console or, if
    'log_file' is given, to that file."""
    loglevel = LOG_LEVELS[loglevel_name]
    if log_file is None:
        logging.basicConfig(level=loglevel, force=True)
    else:
        print("Redirecting log output to: " + log_file)
        logging.basicConfig(filename=log_file, level=loglevel, force=True)


def configure_logging(opts):
    """Configures logging for the given parsed options. On Windows,
    also captures stdout/stderr to a file when no console is attached
    (run-enso.exe launches pythonw.exe, which has none).

    Runs before configure_init_files(), so ENSO_USER_DIR may not exist
    yet on a fresh install; make sure it does before opening any log
    file in it."""
    os.makedirs(config.ENSO_USER_DIR, exist_ok=True)
    user_log = os.path.join(config.ENSO_USER_DIR, "enso.log")

    if sys.platform.startswith("win"):
        user_log_stdout = user_log + ".stdout"

        if not opts.debug or opts.redirect_stdout:
            user_log_file = open(user_log_stdout, "wb", 0)

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

            print("Redirecting stdout output to: " + user_log_stdout)

        if opts.show_console:
            print("Logging to console")

        configure_basic_logging(opts.loglevel, None if opts.show_console else user_log)
    else:
        configure_basic_logging(opts.loglevel, None if opts.debug else user_log)


def start_platform_extras(opts):
    """Starts any OS-specific background integration requested via
    the CLI options (currently: the Windows tray icon)."""
    if sys.platform.startswith("win") and opts.show_tray_icon:
        import threading
        from enso.platform.win32 import tray
        threading.Thread(target=tray.run, args=(config,)).start()


def stop_platform_extras():
    """Shuts down whatever start_platform_extras() started."""
    if sys.platform.startswith("win") and getattr(config, "SYSTRAY_ICON", None):
        import win32con
        import win32gui
        config.SYSTRAY_ICON.change_tooltip("Closing Enso...")
        win32gui.PostMessage(config.SYSTRAY_ICON.hwnd, win32con.WM_COMMAND,
                             config.SYSTRAY_ICON.CMD_FINALIZE, 0)


def platform_shutdown_delay():
    """Gives OS-specific background threads a moment to exit cleanly."""
    if sys.platform.startswith("win"):
        time.sleep(1)


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

    open(user_commands, "a").close()

    default_enso_rc = os.path.join(config.ENSO_USER_DIR, "ensorc.py")
    if not os.path.exists(default_enso_rc):
        shutil.copyfile(os.path.join(config.ENSO_DIR, "scripts", "ensorc.py.default"),
                        default_enso_rc)

    load_rc_config(default_enso_rc)

    # legacy ensorc, currently undocumented
    load_rc_config(os.path.join(config.HOME_DIR, ".ensorc"))


def load_rc_config(ensorcPath):
    if os.path.exists(ensorcPath):
        try:
            logging.info("Loading '%s'." % ensorcPath)
            contents = open(ensorcPath, "r").read()
            compiledContents = compile(contents + "\n", ensorcPath, "exec")
            allLocals = {}
            exec(compiledContents, {}, allLocals)
            for k, v in allLocals.items():
                setattr(config, k, v)
        except Exception:
            logging.exception("Error reading init file")