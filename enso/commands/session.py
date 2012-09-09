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

def cmd_shutdown(ensoapi):
    """Shut down the PC
    The <b>shutdown</b> power management command shuts down the computer."""
    try:
        perform_exit(ensoapi, win32con.EWX_SHUTDOWN)
    except:
        ensoapi.display_message('Error shutting down')
 
def cmd_reboot(ensoapi):
    """Reboot the PC
    The <b>reboot</b> power management command reboots the computer."""
    try:
        perform_exit(ensoapi, win32con.EWX_REBOOT)
    except:
        ensoapi.display_message('Error rebooting')
 
def cmd_logoff(ensoapi):
    """Log off the PC
    The <b>logoff</b> power management command logs of the computer."""
    try:
        perform_exit(ensoapi, win32con.EWX_LOGOFF)
    except:
        ensoapi.display_message('Error logging off')

def cmd_suspend(ensoapi):
    """Suspend the PC
    The <b>suspend</b> power management command suspends the computer."""
    try:
        windll.powrprof.SetSuspendState(c_int(0), c_int(1), c_int(1))
    except:
        ensoapi.display_message('Error suspending')
 
def cmd_hibernate(ensoapi):
    """Hibernate the PC
    The <b>hibernate</b> power management command hibernates the computer."""
    try:
        windll.powrprof.SetSuspendState(c_int(1), c_int(1), c_int(1))
    except:
        ensoapi.display_message('Error hibernating')
