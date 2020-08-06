# Configuration settings for Enso. Eventually this will take
# localization into account too (or we can make a separate module for
# such strings).

# Enso version for use in UI
ENSO_VERSION = "0.5.1"

# Web UI can be disabled as a security option
ENABLE_WEB_UI = True

# Enso color theme
COLOR_THEME = "green"

# Defines should Enso take into account the top- or left- positioned
# Windows taskbar, it appears atop of the taskbar by default.
APPEAR_OVER_TASKBAR = True

# Load Windows Universal Platform Apps
LOAD_UWP_APPS = True

# Check if all known command files are changed upon each invocation of the command line
# Only changes in commands entered through WebUI are tracked by default
TRACK_COMMAND_CHANGES = False

# The keys to start, exit, and cancel the quasimode.
# Their values are strings referring to the names of constants defined
# in the os-specific input module in use.
QUASIMODE_START_KEY = "KEYCODE_CAPITAL"
QUASIMODE_END_KEY = "KEYCODE_RETURN"
QUASIMODE_CANCEL_KEY = "KEYCODE_ESCAPE"

# Whether the Quasimode is actually modal ("sticky").
IS_QUASIMODE_MODAL = True

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

# The message displayed when the user types some text that is not a command.
BAD_COMMAND_MSG = "<p><command>%s</command> is not a command.</p>"\
                  "%s"

# Minimum number of characters that should have been typed into the 
# quasimode for a bad command message to be shown. 
BAD_COMMAND_MSG_MIN_CHARS = 2

# The captions for the above message, indicating commands that are related
# to the command the user typed.
ONE_SUGG_CAPTION = "<caption>Did you mean <command>%s</command>?</caption>"

# The string that is displayed in the quasimode window when the user
# first enters the quasimode.
QUASIMODE_DEFAULT_HELP = "Welcome to Enso! Enter a command, " \
    "or type \u201chelp\u201d for assistance."

# The string displayed when the user has typed some characters but there
# is no matching command.
QUASIMODE_NO_COMMAND_HELP = "There is no matching command. "\
    "Use backspace to delete characters."

# Message XML for the Splash message shown when Enso first loads.
OPENING_MSG_XML = "<p><command>Enso</command> is loaded!</p>"

# Message XML for the Splash message shown when Enso is refreshed.
REFRESHING_MSG_XML = "<p><command>Enso</command> is refreshed!</p>"

# Message XML displayed when the mouse hovers over a mini message.
MINI_MSG_HELP_XML = "<p>The <command>hide mini messages</command>" \
    " and <command>put</command> commands control" \
    " these mini-messages.</p>"

# List of default platforms supported by Enso; platforms are specific
# types of providers that provide a suite of platform-specific
# functionality.
DEFAULT_PLATFORMS = ["enso.platform.win32"]

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


ABOUT_BOX_XML = "<p><command>Enso</command> open-source " + ENSO_VERSION + "</p>" \
    "" \
    "<caption>Based on Enso Community Edition</caption><p> </p>" \
    "<p>Copyright &#169; 2008 <command>Humanized, Inc.</command></p>" \
    "<p>Copyright &#169; 2008-2009 <command>Enso Community</command></p>" \
    "<p>Copyright &#169; 2011-2020 <command>g/christensen</command></p>" \
    "<p> </p><caption>Hit the <command>CapsLock</command> key to invoke Enso</caption>"


BLOCKED_BY_RETREAT_MSG = "<p>Enso Retreat denies the operation.</p><caption>Enso</caption>"

RETREAT_DISABLE = False

RETREAT_SHOW_ICON = True

DISABLED_COMMANDS = []
COMMAND_STATE_CHANGED = False


import os, configparser
from ast import literal_eval

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


# set up user modifications of the default config
# currently there are three places that may change variables
# in the config module:
# the following code, which sets variables from enso.cfg
# ~/.ensorc file which is not available from WebUI (more secure option)
# ~/.enso/ensorc.py (can be got/set from WebUI)
CONFIG_FILE = os.path.join(ENSO_USER_DIR, "enso.cfg")
CONFIG_SECTION = "General"


def store_value(key, value):
    parser = configparser.ConfigParser()
    parser.optionxform = str

    if os.path.exists(CONFIG_FILE):
        parser.read(CONFIG_FILE)
    else:
        parser.add_section(CONFIG_SECTION)

    if key == "DISABLED_COMMANDS":
        parser[CONFIG_SECTION][key] = ",".join(value)
    else:
        parser[CONFIG_SECTION][key] = str(value)

        try:
            globals()[key] = literal_eval(value)
        except:
            globals()[key] = value

    with open(CONFIG_FILE, 'w') as stream:
        parser.write(stream)


if os.path.exists(CONFIG_FILE):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(CONFIG_FILE)

    for key in parser[CONFIG_SECTION].keys():
        if key == "DISABLED_COMMANDS":
            if parser[CONFIG_SECTION][key]:
                globals()[key] = parser[CONFIG_SECTION][key].split(",")
        else:
            try:
                globals()[key] = literal_eval(parser[CONFIG_SECTION][key])
            except:
                globals()[key] = parser[CONFIG_SECTION][key]

# vim:set tabstop=4 shiftwidth=4 expandtab: