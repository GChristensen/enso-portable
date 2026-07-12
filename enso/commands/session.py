import os
import subprocess
import sys

_WIN32 = sys.platform.startswith("win")
_DARWIN = sys.platform == "darwin"

if _WIN32:
    from ctypes import *
    import win32api
    import win32con
    import win32security

    def adjust_privilege(priv, enable = 1):
        flags = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
        id = win32security.LookupPrivilegeValue(None, priv)
        if enable:
            newPrivileges = [(id, win32con.SE_PRIVILEGE_ENABLED)]
        else:
            newPrivileges = [(id, 0)]
        win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)

    def perform_exit(ensoapi, action):
        adjust_privilege(win32con.SE_SHUTDOWN_NAME)
        try:
            windll.user32.ExitWindowsEx(action, c_uint(0x80000000))
        finally:
            adjust_privilege(win32con.SE_SHUTDOWN_NAME, 0)


def _run(ensoapi, args, error_message):
    try:
        subprocess.Popen(args)
    except Exception:
        ensoapi.display_message(error_message)


def _osascript(ensoapi, statement, error_message):
    _run(ensoapi, ["osascript", "-e",
                   'tell application "System Events" to %s' % statement],
         error_message)


def cmd_shutdown(ensoapi):
    """Shut down the PC"""
    if _WIN32:
        try:
            perform_exit(ensoapi, win32con.EWX_SHUTDOWN)
        except:
            ensoapi.display_message('Error shutting down')
    elif _DARWIN:
        _osascript(ensoapi, "shut down", 'Error shutting down')
    else:
        _run(ensoapi, ["systemctl", "poweroff"], 'Error shutting down')

def cmd_reboot(ensoapi):
    """Reboot the PC"""
    if _WIN32:
        try:
            perform_exit(ensoapi, win32con.EWX_REBOOT)
        except:
            ensoapi.display_message('Error rebooting')
    elif _DARWIN:
        _osascript(ensoapi, "restart", 'Error rebooting')
    else:
        _run(ensoapi, ["systemctl", "reboot"], 'Error rebooting')

def cmd_logoff(ensoapi):
    """Log off the current user"""
    if _WIN32:
        try:
            perform_exit(ensoapi, win32con.EWX_LOGOFF)
        except:
            ensoapi.display_message('Error logging off')
    elif _DARWIN:
        _osascript(ensoapi, "log out", 'Error logging off')
    else:
        session = os.environ.get("XDG_SESSION_ID")
        if session:
            _run(ensoapi, ["loginctl", "terminate-session", session],
                 'Error logging off')
        else:
            ensoapi.display_message('Error logging off: no session id')

def cmd_suspend(ensoapi):
    """Suspend the PC"""
    if _WIN32:
        try:
            windll.powrprof.SetSuspendState(c_int(0), c_int(1), c_int(1))
        except:
            ensoapi.display_message('Error suspending')
    elif _DARWIN:
        _run(ensoapi, ["pmset", "sleepnow"], 'Error suspending')
    else:
        _run(ensoapi, ["systemctl", "suspend"], 'Error suspending')

def cmd_hibernate(ensoapi):
    """Hibernate the PC"""
    if _WIN32:
        try:
            windll.powrprof.SetSuspendState(c_int(1), c_int(1), c_int(1))
        except:
            ensoapi.display_message('Error hibernating')
    elif _DARWIN:
        ensoapi.display_message('Hibernation is not supported on macOS')
    else:
        _run(ensoapi, ["systemctl", "hibernate"], 'Error hibernating')
