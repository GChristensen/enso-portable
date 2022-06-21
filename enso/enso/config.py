# Configuration settings for Enso.

# Load Windows Universal Platform Apps
LOAD_UWP_APPS = True

# Should Enso take into account the top- or left- positioned
# Windows taskbar, it appears atop of the taskbar by default.
APPEAR_OVER_TASKBAR = True

# Take the current keyboard layout into account
# May not work if a console window is in the foreground
LOCALIZED_INPUT = True

# Check if all known command files are changed upon each invocation of the command line
# Only changes in commands entered through WebUI are tracked by default
TRACK_COMMAND_CHANGES = False

# Web UI can be disabled as a security option
ENABLE_WEB_UI = True

# Whether the Quasimode is actually modal ("sticky").
IS_QUASIMODE_MODAL = True

# The keys to start, exit, and cancel the quasimode.
# Their values are strings referring to the names of constants defined
# in the os-specific input module in use.
QUASIMODE_START_KEY = "KEYCODE_CAPITAL"
QUASIMODE_END_KEY = "KEYCODE_RETURN"
QUASIMODE_CANCEL_KEY = "KEYCODE_ESCAPE"

# Amount of time, in seconds (float), to wait from the time
# that the quasimode begins drawing to the time that the
# suggestion list begins to be displayed.  Setting this to a
# value greater than 0 will effectively create a
# "spring-loaded suggestion list" behavior.
QUASIMODE_SUGGESTION_DELAY = 0.2

# The maximum number of suggestions to display in the quasimode.
QUASIMODE_MAX_SUGGESTIONS = 10

# The minimum number of characters the user must type before the
# auto-completion mechanism engages.
QUASIMODE_MIN_AUTOCOMPLETE_CHARS = 1

# Enso color theme
COLOR_THEME = "green"

# List of default platforms supported by Enso; platforms are specific
# types of providers that provide a suite of platform-specific
# functionality.
DEFAULT_PLATFORMS = ["enso.platform.win32",
                     "enso.platform.linux",
                     "enso.platform.osx"]

# List of modules/packages that support the provider interface to
# provide required platform-specific functionality to Enso.
PROVIDERS = []
PROVIDERS.extend(DEFAULT_PLATFORMS)

# List of modules/packages that support the plugin interface to
# extend Enso.  The plugins are loaded in the order that they
# are specified in this list.
PLUGINS = ["enso.contrib.scriptotron",
           "enso.contrib.help",
           "enso.contrib.google",
           "enso.contrib.evaluate"]

# Detect default system locale and use it for google search.
# If set to False, no locale is forced.dddasdfasdf
PLUGIN_GOOGLE_USE_DEFAULT_LOCALE = True

import os

ENSO_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

ENSO_USER_DIR = None

HOME_DIR = os.getenv("HOME")

if HOME_DIR:
    ENSO_USER_DIR = os.path.join(HOME_DIR, ".enso")
else:
    HOME_DIR = os.getenv("USERPROFILE")
    if HOME_DIR:
        ENSO_USER_DIR = os.path.join(HOME_DIR, ".enso")

if not ENSO_USER_DIR:
    ENSO_USER_DIR = os.path.expanduser(os.path.join("~", ".enso"))

ENSO_EXECUTABLE = os.path.join(ENSO_DIR, "run-enso.exe")

if not os.path.exists(ENSO_EXECUTABLE):
    ENSO_EXECUTABLE = os.path.join(ENSO_DIR, "enso-portable.exe")

CONFIG_FILE = os.path.join(ENSO_USER_DIR, "enso.cfg")

RETREAT_DISABLE = False

RETREAT_SHOW_ICON = True

DISABLED_COMMANDS = []
COMMAND_STATE_CHANGED = False

from . import usercfg

usercfg.init(globals())

from .usercfg import storeValue

from .strings import *

