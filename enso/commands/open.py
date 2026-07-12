import logging
import os
import re
import sys

if sys.platform.startswith("win"):
    from enso.platform.win32.shortcuts import *
    from enso.platform.win32 import shortcuts as _backend
elif sys.platform == "darwin":
    from enso.platform.osx.shortcuts import *
    from enso.platform.osx import shortcuts as _backend
else:
    from enso.platform.linux.shortcuts import *
    from enso.platform.linux import shortcuts as _backend

unlearn_open_undo = []

shortcuts_map = Shortcuts.get().get_shortcuts()


def displayMessage(msg, foreground = False):
    import enso.messages
    enso.messages.displayMessage("<p>%s</p>" % msg, foreground)


def cmd_open(ensoapi, target):
    """ Continue typing to open an application or document """

    try:
        global shortcuts_map
        shortcut_type, shortcut_id, file_path = shortcuts_map[target]
        displayMessage("Opening <command>%s</command>..." % target, foreground=True)
        return _backend.run_shortcut(shortcut_type, shortcut_id, file_path)
    except Exception as e:
        logging.error(e)
        return False

cmd_open.valid_args = [s[1] for s in list(shortcuts_map.values())]


def cmd_open_with(ensoapi, application):
    """ Opens your currently selected file(s) or folder with the specified application """
    seldict = ensoapi.get_selection()
    if seldict.get('files'):
        file = seldict['files'][0]
    elif seldict.get('text'):
        file = seldict['text'].strip()
    else:
        file = None

    if not (file and (os.path.isfile(file) or os.path.isdir(file))):
        ensoapi.display_message("No file or folder is selected")
        return

    displayMessage("Opening <command>%s</command>..." % application, foreground=True)

    global shortcuts_map
    try:
        executable = shortcuts_map[application][2]
    except KeyError:
        ensoapi.display_message("Unknown application “%s”" % application)
        return
    _backend.open_with_shortcut(executable, file)


cmd_open_with.valid_args = [s[1] for s in list(shortcuts_map.values()) if s[0] == SHORTCUT_TYPE_EXECUTABLE]


def is_url(text):
    urlfinders = [
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]"),
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
        re.compile("(~/|/|\\./)([-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]|\\\\)+"),
        re.compile("'\\<((mailto:)|)[-A-Za-z0-9\\.]+@[-A-Za-z0-9\\.]+"),
    ]

    for urltest in urlfinders:
        if urltest.search(text, re.I):
            return True

    return False


def _refresh_valid_args():
    global shortcuts_map
    cmd_open.valid_args = [s[1] for s in list(shortcuts_map.values())]
    cmd_open_with.valid_args = [s[1] for s in list(shortcuts_map.values()) if s[0] == SHORTCUT_TYPE_EXECUTABLE]
    cmd_unlearn_open.valid_args = [s[1] for s in list(shortcuts_map.values())]


def cmd_learn_as_open(ensoapi, name):
    """ Learn to open a document or application as {name} """
    if name is None:
        displayMessage("You must provide name")
        return
    seldict = ensoapi.get_selection()
    if seldict.get('files'):
        file = seldict['files'][0]
    elif seldict.get('text'):
        file = seldict['text'].strip()
    else:
        ensoapi.display_message("No file is selected")
        return

    if not os.path.isfile(file) and not os.path.isdir(file) and not is_url(file):
        displayMessage(
            "Selection represents no existing file, folder or URL.")
        return

    file_path = _backend.learn_shortcut(name, file, is_url(file))
    if file_path is None:
        displayMessage(
            "<command>open %s</command> already exists. Please choose another name."
            % name)
        return

    Shortcuts.get().add_shortcut(file_path)
    _refresh_valid_args()

    displayMessage("<command>open %s</command> is now a command" % name)


def cmd_unlearn_open(ensoapi, name):
    """ Unlearn "open {name}" command """

    token = _backend.unlearn_shortcut(name)
    if token is not None:
        unlearn_open_undo.append(token)

    Shortcuts.get().remove_shortcut(name.lower())
    _refresh_valid_args()
    displayMessage("Unlearned <command>open %s</command>" % name)


cmd_unlearn_open.valid_args = [s[1] for s in list(shortcuts_map.values())]


def cmd_undo_unlearn(ensoapi):
    """ Undoes your last "unlearn open" command """
    if len(unlearn_open_undo) > 0:
        token = unlearn_open_undo.pop()
        name = _backend.restore_shortcut(token)
        displayMessage("Undo successful. <command>open %s</command> is now a command" % name)
    else:
        ensoapi.display_message("There is nothing to undo")


# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab:
