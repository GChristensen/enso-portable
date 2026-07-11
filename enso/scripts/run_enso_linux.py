#!/usr/bin/env python3

# Enso launcher for Linux (X11 only; KDE, LXQt and other desktops).
#
# Prerequisites on openSUSE:
#   sudo zypper install python3-gobject python3-gobject-Gdk \
#       typelib-1_0-Gtk-3_0 python3-cairo python3-xlib xmodmap xset
# Optional: python3-Flask (web UI), picom (compositor, needed on LXQt).
#
# See README.linux.md at the repository root for details.

import logging
import os
import shutil
import sys

from optparse import OptionParser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.path.pardir)))

if not os.environ.get("DISPLAY"):
    sys.exit("Error: DISPLAY is not set. Enso requires an X11 session.")

if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
    print("Warning: this looks like a Wayland session. Enso's global "
          "key grab only sees X11 applications; log into an X11 session "
          "for reliable operation.", file=sys.stderr)

import enso
from enso import config
from enso.user import import_package_by_path

sys.path.append(config.ENSO_DIR)
sys.path.append(os.path.join(config.ENSO_DIR, "lib"))
sys.path.append(os.path.join(config.ENSO_USER_DIR, "lib"))


def process_options(argv):
    version = "1.0"
    usageStr = "%prog [options]\n\n"
    parser = OptionParser(usage=usageStr, version="%prog " + version)
    parser.add_option("-l", "--log-level", action="store", dest="loglevel",
                      default="ERROR",
                      help="logging level (CRITICAL, ERROR, INFO, WARNING, DEBUG)")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      default=False,
                      help="No information windows are shown on startup/shutdown")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False, help="Debug mode")

    opts, args = parser.parse_args(argv)
    return opts, args


def configure_logging(opts):
    loglevel = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "DEBUG": logging.DEBUG,
    }[opts.loglevel]

    if opts.debug:
        logging.basicConfig(level=loglevel, force=True)
    else:
        user_log = os.path.join(config.ENSO_USER_DIR, "enso.log")
        print("Redirecting log output to: " + user_log)
        logging.basicConfig(filename=user_log, level=loglevel, force=True)


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
        shutil.copyfile(os.path.join(config.ENSO_DIR, "scripts",
                                     "ensorc.py.default"),
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


def main(argv=None):
    opts, args = process_options(argv)
    config.ENSO_IS_QUIET = opts.quiet
    config.DEBUG = opts.debug

    configure_logging(opts)

    configure_init_files()

    user_lib_index = os.path.join(config.ENSO_USER_DIR, "lib")
    import_package_by_path(user_lib_index)

    enso.run()

    logging.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
