from enso.platform.win32.shortcuts import *

import os
import re
import win32api
import win32con
import pythoncom
import logging

unlearn_open_undo = []

shortcuts_map = Shortcuts.get().getShortcuts()

def displayMessage(msg):
    import enso.messages
    enso.messages.displayMessage("<p>%s</p>" % msg)

def expand_path_variables(file_path):
    re_env = re.compile(r'%\w+%')

    def expander(mo):
        return os.environ.get(mo.group()[1:-1], 'UNKNOWN')

    return os.path.expandvars(re_env.sub(expander, file_path))


def cmd_open(ensoapi, target):
    """ Continue typing to open an application or document """

    displayMessage("Opening <command>%s</command>..." % target)

    try:
        global shortcuts_map
        shortcut_type, shortuct_id, file_path = shortcuts_map[target]
        file_path = os.path.normpath(expand_path_variables(file_path))
        logging.info("Executing '%s'" % file_path)

        if shortcut_type == SHORTCUT_TYPE_CONTROL_PANEL:
            if " " in file_path:
                executable = file_path[0:file_path.index(' ')]
                params = file_path[file_path.index(' ')+1:]
            else:
                executable = file_path
                params = None
            try:
                # somewhere /name parameter of control.exe is mangled
                params = params.replace("\\name Microsoft", "/name Microsoft")

                rcode = win32api.ShellExecute(
                    0,
                    'open',
                    executable,
                    params,
                    None,
                    win32con.SW_SHOWDEFAULT)
            except Exception as e:
                logging.error(e)
        else:
            os.startfile(file_path)

        return True
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

    displayMessage("Opening <command>%s</command>..." % application)

    #print file, application
    global shortcuts_map
    try:
        executable = expand_path_variables(shortcuts_map[application][2])
    except:
        print(application)
        print(list(shortcuts_map.keys()))
        print(list(shortcuts_map.values()))
    try:
        rcode = win32api.ShellExecute(
            0,
            'open',
            executable,
            '"%s"' % file,
            os.path.dirname(file),
            win32con.SW_SHOWDEFAULT)
    except Exception as e:
        logging.error(e)

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

    file_name = name.replace(":", "").replace("?", "").replace("\\", "")
    file_path = os.path.join(LEARN_AS_DIR, file_name)

    if os.path.isfile(file_path + ".url") or os.path.isfile(file_path + ".lnk"):
        displayMessage(
            "<command>open %s</command> already exists. Please choose another name."
            % name)
        return

    if is_url(file):
        shortcut = PyInternetShortcut()

        shortcut.SetURL(file)
        shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
            file_path + ".url", 0 )
    else:
        shortcut = PyShellLink()

        shortcut.SetPath(file)
        shortcut.SetWorkingDirectory(os.path.dirname(file))
        shortcut.SetIconLocation(file, 0)

        shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
            file_path + ".lnk", 0 )

    #time.sleep(0.5)
    global shortcuts_map
    shortcuts_map = Shortcuts.get().refreshShortcuts()
    cmd_open.valid_args = [s[1] for s in list(shortcuts_map.values())]
    cmd_open_with.valid_args = [s[1] for s in list(shortcuts_map.values()) if s[0] == SHORTCUT_TYPE_EXECUTABLE]
    cmd_unlearn_open.valid_args = [s[1] for s in list(shortcuts_map.values())]

    displayMessage("<command>open %s</command> is now a command" % name)


def cmd_unlearn_open(ensoapi, name):
    """ Unlearn "open {name}" command """

    file_path = os.path.join(LEARN_AS_DIR, name)
    if os.path.isfile(file_path + ".lnk"):
        sl = PyShellLink()
        sl.load(file_path + ".lnk")
        unlearn_open_undo.append([name, sl])
        os.remove(file_path + ".lnk")
    elif os.path.isfile(file_path + ".url"):
        sl = PyInternetShortcut()
        sl.load(file_path + ".url")
        unlearn_open_undo.append([name, sl])
        os.remove(file_path + ".url")

    global shortcuts_map
    shortcuts_map = Shortcuts.get().refreshShortcuts()
    cmd_open.valid_args = [s[1] for s in list(shortcuts_map.values())]
    cmd_open_with.valid_args = [s[1] for s in list(shortcuts_map.values()) if s[0] == SHORTCUT_TYPE_EXECUTABLE]
    cmd_unlearn_open.valid_args = [s[1] for s in list(shortcuts_map.values())]
    displayMessage("Unlearned <command>open %s</command>" % name)


cmd_unlearn_open.valid_args = [s[1] for s in list(shortcuts_map.values())]


def cmd_undo_unlearn(ensoapi):
    """ Undoes your last "unlearn open" command """
    if len(unlearn_open_undo) > 0:
        name, sl = unlearn_open_undo.pop()
        sl.save()
        displayMessage("Undo successful. <command>open %s</command> is now a command" % name)
    else:
        ensoapi.display_message("There is nothing to undo")

if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab:
