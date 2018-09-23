from win32comext.shell import shell, shellcon
from enso.platform.win32.scriptfolder import get_script_folder_name
import os
import glob
import operator
import re
import time
import win32api
import win32con
import win32process
import pythoncom
import logging


unlearn_open_undo = []

my_documents_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
LEARN_AS_DIR = os.path.join(os.path.expanduser("~"), ".enso", "learned-commands")

# Check if Learn-as dir exist and create it if not
if (not os.path.isdir(LEARN_AS_DIR)):
    os.makedirs(LEARN_AS_DIR)

SHORTCUT_TYPE_EXECUTABLE = 'x'
SHORTCUT_TYPE_FOLDER = 'f'
SHORTCUT_TYPE_URL = 'u'
SHORTCUT_TYPE_DOCUMENT = 'd'
SHORTCUT_TYPE_CONTROL_PANEL = 'c'

def _cpl_exists(cpl_name):
    return (
        os.path.isfile(
            os.path.expandvars("${WINDIR}\\%s.cpl") % cpl_name)
        or os.path.isfile(
            os.path.expandvars("${WINDIR}\\system32\\%s.cpl") % cpl_name)
        )


control_panel_applets = [i[:3] for i in (
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "control panel",
        "rundll32.exe shell32.dll,Control_RunDLL"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "accessibility options (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL access.cpl"),
    #accessibility options (Keyboard):
    #    rundll32.exe shell32.dll,Control_RunDLL access.cpl,,1
    #accessibility options (Sound):
    #    rundll32.exe shell32.dll,Control_RunDLL access.cpl,,2
    #accessibility options (Display):
    #    rundll32.exe shell32.dll,Control_RunDLL access.cpl,,3
    #accessibility options (Mouse):
    #    rundll32.exe shell32.dll,Control_RunDLL access.cpl,,4
    #accessibility options (General):
    #    rundll32.exe shell32.dll,Control_RunDLL access.cpl,,5
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "add or remove programs (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL appwiz.cpl"),
    #add or remove programs (Install/Uninstall):
    #    rundll32.exe shell32.dll,Control_RunDLL appwiz.cpl,,1
    #add or remove programs (Windows Setup):
    #    rundll32.exe shell32.dll,Control_RunDLL appwiz.cpl,,2
    #add or remove programs (Startup Disk):
    #    rundll32.exe shell32.dll,Control_RunDLL appwiz.cpl,,3
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "display properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL desk.cpl"),
    #Display Properties (Background):
    #    rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,0
    #Display Properties (Screen Saver):
    #    rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,1
    #Display Properties (Appearance):
    #    rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,2
    #Display Properties (Settings):
    #    rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,3

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "regional and language options (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL intl.cpl"),
    #Regional Settings Properties (Regional Settings):
    #    rundll32.exe shell32.dll,Control_RunDLL intl.cpl,,0
    #Regional Settings Properties (Number):
    #    rundll32.exe shell32.dll,Control_RunDLL intl.cpl,,1
    #Regional Settings Properties (Currency):
    #    rundll32.exe shell32.dll,Control_RunDLL intl.cpl,,2
    #Regional Settings Properties (Time):
    #    rundll32.exe shell32.dll,Control_RunDLL intl.cpl,,3
    #Regional Settings Properties (Date):
    #    rundll32.exe shell32.dll,Control_RunDLL intl.cpl,,4

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "game controllers (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL joy.cpl"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "mouse properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL main.cpl @0"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "keyboard properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL main.cpl @1"),
    # DOES NOT WORK
    #Printers:
    #   rundll32.exe shell32.dll,Control_RunDLL main.cpl @2

    # DOES NOT WORK
    #Fonts:
    #    rundll32.exe shell32.dll,Control_RunDLL main.cpl @3

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "microsoft exchange profiles (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL mlcfg32.cpl",
        _cpl_exists("mlcfg32")),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "sounds and audio devices (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl"),
    #Multimedia Properties (Audio):
    #    rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,0
    #Multimedia Properties (Video):
    #    rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,1
    #Multimedia Properties (MIDI):
    #    rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,2
    #Multimedia Properties (CD Music):
    #    rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,3
    #Multimedia Properties (Advanced):
    #    rundll32.exe shell32.dll,Control_RunDLL mmsys.cpl,,4

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "modem properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL modem.cpl",
        _cpl_exists("modem")),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "network connections (control panel)",
        "RUNDLL32.exe SHELL32.DLL,Control_RunDLL NCPA.CPL"),

    #Password Properties (Change Passwords):
    #    rundll32.exe shell32.dll,Control_RunDLL password.cpl
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "system properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL sysdm.cpl,,0"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "device manager (control panel)",
        #"rundll32.exe shell32.dll,Control_RunDLL sysdm.cpl,,1"
        "devmgmt.msc"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "disk management (control panel)",
        "diskmgmt.msc"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "scanners and cameras (control panel)",
        "control.exe sticpl.cpl"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "removable storage (control panel)",
        "ntmsmgr.msc"),

    #dfrg.msc Disk defrag
    #eventvwr.msc Event viewer
    #eventvwr.exe \\computername View the Event Log at a remote computer
    #fsmgmt.msc Shared folders
    #gpedit.msc Group policies
    #lusrmgr.msc Local users and groups
    #perfmon.msc Performance monitor
    #rsop.msc Resultant set of policies
    #secpol.msc Local security settings
    #services.msc Various Services

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "hardware profiles (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL sysdm.cpl,,2"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "advanced system properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL sysdm.cpl,,3"),

    #Add New Hardware Wizard:
    #    rundll32.exe shell32.dll,Control_RunDLL sysdm.cpl @1

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "date and time (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL timedate.cpl"),

    #Microsoft Workgroup Postoffice Admin:
    #    rundll32.exe shell32.dll,Control_RunDLL wgpocpl.cpl

    #Open With (File Associations):
    #    rundll32.exe shell32.dll,OpenAs_RunDLL d:\path\filename.ext

    #Run Diskcopy Dialog:
    #    rundll32 diskcopy.dll,DiskCopyRunDll

    #Create New Shortcut Wizard:
    #    'puts the new shortcut in the location specified by %1
    #    rundll32.exe AppWiz.Cpl,NewLinkHere %1

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "add new hardware wizard (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL hdwwiz.cpl @1"),

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "add printer wizard (control panel)",
        "rundll32.exe shell32.dll,SHHelpShortcuts_RunDLL AddPrinter"),
    #(SHORTCUT_TYPE_CONTROL_PANEL,
    #    u"dialup networking wizard (cp)",
    #    "rundll32.exe rnaui.dll,RnaWizard"),

    #Open a Scrap Document:
    #    rundll32.exe shscrap.dll,OpenScrap_RunDLL /r /x %1

    #Create a Briefcase:
    #    rundll32.exe syncui.dll,Briefcase_Create

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "printers and faxes (control panel)",
        "rundll32.exe shell32.dll,SHHelpShortcuts_RunDLL PrintersFolder"),

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "fonts (control panel)",
        "rundll32.exe shell32.dll,SHHelpShortcuts_RunDLL FontsFolder"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "windows firewall (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL firewall.cpl"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "speech properties (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL \"${COMMONPROGRAMFILES}\\Microsoft Shared\\Speech\\sapi.cpl\"",
        os.path.isfile(os.path.expandvars("${COMMONPROGRAMFILES}\\Microsoft Shared\\Speech\\sapi.cpl"))),

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "internet options (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL inetcpl.cpl"),

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "odbc data source administrator (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL odbccp32.cpl"),
    (SHORTCUT_TYPE_CONTROL_PANEL,
        "power options (control panel)",
        "rundll32.exe shell32.dll,Control_RunDLL powercfg.cpl"),

    (SHORTCUT_TYPE_CONTROL_PANEL,
        "bluetooth properties (control panel)",
        "control.exe bhtprops.cpl",
        _cpl_exists("bhtprops")),

    #Pick a Time Zone Dialog:
    #    rundll32.exe shell32.dll,Control_RunDLL timedate.cpl,,/f
) if len(i) < 4 or i[3]]
#print control_panel_applets

class _PyShortcut():
    def __init__( self, base ):
        self._base = base
        self._base_loaded = False
        self._shortcut_type = None

    def load( self, filename = None):
        if filename:
            self._filename = filename
        try:
            self._base.QueryInterface( pythoncom.IID_IPersistFile ).Load( self._filename )
        except:
            logging.error("Error loading shell-link for file %s" % self._filename)
        self._base_loaded = True

    def save( self, filename = None):
        if filename:
            self._filename = filename
        self._base.QueryInterface( pythoncom.IID_IPersistFile ).Save( self._filename, 0 )

    def get_filename(self):
        return self._filename

    def get_type(self):
        if not self._base_loaded:
            raise Exception("Shortcut data has not been loaded yet. Use load(filename) before using get_type()")

        name, ext = os.path.splitext(self._filename)
        if ext.lower() == '.lnk':
            file_path = self._base.GetPath(0)
            if file_path and file_path[0]:
                if os.path.isdir(file_path[0]):
                    self._shortcut_type = SHORTCUT_TYPE_FOLDER
                elif (os.path.splitext(file_path[0])[1].lower()
                    in ('.exe', '.com', '.cmd', '.bat')):
                    self._shortcut_type = SHORTCUT_TYPE_EXECUTABLE
                else:
                    self._shortcut_type = SHORTCUT_TYPE_DOCUMENT
            else:
                self._shortcut_type = SHORTCUT_TYPE_DOCUMENT
        elif ext.lower() == '.url':
            self._shortcut_type = SHORTCUT_TYPE_URL
        else:
            self._shortcut_type = SHORTCUT_TYPE_DOCUMENT
        return self._shortcut_type

    def __getattr__( self, name ):
        if name != "_base":
            return getattr( self._base, name )


class PyShellLink(_PyShortcut):
    def __init__( self ):
        base = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        _PyShortcut.__init__(self, base)


class PyInternetShortcut(_PyShortcut):
    def __init__( self ):
        base = pythoncom.CoCreateInstance(
            shell.CLSID_InternetShortcut,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IUniformResourceLocator
        )
        _PyShortcut.__init__(self, base)


def expand_path_variables(file_path):
    import re
    re_env = re.compile(r'%\w+%')

    def expander(mo):
        return os.environ.get(mo.group()[1:-1], 'UNKNOWN')

    return os.path.expandvars(re_env.sub(expander, file_path))


def displayMessage(msg):
    import enso.messages
    enso.messages.displayMessage("<p>%s</p>" % msg)


ignored = re.compile("(uninstall|read ?me|faq|f.a.q|help)", re.IGNORECASE)

"""
def get_control_panel_applets():
    import _winreg as reg

    reghandle = None
    cpl_applets = []
    try:
        regkey = None
        try:
            reghandle = reg.ConnectRegistry(None, reg.HKEY_LOCAL_MACHINE)
            key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Control Panel\\Cpls"
            regkey = reg.OpenKey(reghandle, key)
            index = 0
            try:
                while True:
                    regval = reg.EnumValue(regkey, index)
                    cpl_applets.append((
                        SHORTCUT_TYPE_CONTROL_PANEL,
                        regval[0].lower().replace("/"," ") + " (control panel)",
                        regval[1]))
                    index += 1
            except Exception, e:
                pass
        except Exception, e:
            print e
        finally:
            if regkey:
                reg.CloseKey(regkey)

        regkey = None
        try:
            key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ControlPanel\\Namespace"
            regkey = reg.OpenKey(reghandle, key)
            index = 0
            try:
                while True:
                    cplkey = reg.EnumKey(regkey, index)
                    regkey1 = None
                    try:
                        regkey1 = reg.OpenKey(reghandle, key + "\\" + cplkey)
                        cpl_applets.append((
                            SHORTCUT_TYPE_CONTROL_PANEL,
                            reg.QueryValueEx(regkey1, "Name")[0].lower().replace("/"," ") + " (control panel)",
                            reg.QueryValueEx(regkey1, "Module")[0]))
                    except:
                        pass
                    finally:
                        if regkey1:
                            reg.CloseKey(regkey1)
                    index += 1
            except Exception, e:
                pass
        except Exception, e:
            print e
        finally:
            if regkey:
                reg.CloseKey(regkey)
    finally:
        if reghandle:
            reg.CloseKey(reghandle)
    return cpl_applets


print get_control_panel_applets()
"""

def get_shortcuts(directory):
    shortcuts = []
    sl = PyShellLink()

    if os.path.exists(directory):
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if ignored.search(filename):
                    continue
                name, ext = os.path.splitext(filename)
                if not ext.lower() in (".lnk", ".url"):
                    continue
                #print name, ext
                shortcut_type = SHORTCUT_TYPE_DOCUMENT
                if ext.lower() == ".lnk":
                    shortcut_path = os.path.join(dirpath, filename)
                    sl.load(shortcut_path)
                    shortcut_type = sl.get_type()
                elif ext.lower() == ".url":
                    shortcut_type = SHORTCUT_TYPE_URL

                shortcuts.append((shortcut_type, name.lower(), shortcut_path))
    return shortcuts


def reload_shortcuts_map():
    desktop_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, 0, 0)
    quick_launch_dir = os.path.join(
        shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0),
        "Microsoft",
        "Internet Explorer",
        "Quick Launch")
    start_menu_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_STARTMENU, 0, 0)
    common_start_menu_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_STARTMENU, 0, 0)
    #control_panel = shell.SHGetFolderPath(0, shellcon.CSIDL_CONTROLS, 0, 0)

    shortcuts = get_shortcuts(LEARN_AS_DIR) + \
        get_shortcuts(desktop_dir) + \
        get_shortcuts(quick_launch_dir) + \
        get_shortcuts(start_menu_dir) + \
        get_shortcuts(common_start_menu_dir) + \
        control_panel_applets

    return dict((s[1], s) for s in shortcuts)

shortcuts_map = reload_shortcuts_map()



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
        print(shortcuts_map[application][2])
        print(shortcuts_map[application])
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
    shortcuts_map = reload_shortcuts_map()
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
    shortcuts_map = reload_shortcuts_map()
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
