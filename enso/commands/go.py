import win32api
import win32gui
import win32process
import win32con
import operator
import os
import time
import xml.sax.saxutils
import unicodedata

from enso.commands import CommandManager, CommandObject
import logging


import ctypes
from ctypes import *
from ctypes.wintypes import HWND #, RECT, POINT

def _stdcall(dllname, restype, funcname, *argtypes):
    # a decorator for a generator.
    # The decorator loads the specified dll, retrieves the
    # function with the specified name, set its restype and argtypes,
    # it then invokes the generator which must yield twice: the first
    # time it should yield the argument tuple to be passed to the dll
    # function (and the yield returns the result of the call).
    # It should then yield the result to be returned from the
    # function call.
    def decorate(func):
        api = getattr(WinDLL(dllname), funcname)
        api.restype = restype
        api.argtypes = argtypes

        def decorated(*args, **kw):
            iterator = func(*args, **kw)
            nargs = iterator.next()
            if not isinstance(nargs, tuple):
                nargs = (nargs,)
            try:
                res = api(*nargs)
            except Exception, e:
                return iterator.throw(e)
            return iterator.send(res)
        return decorated
    return decorate


def nonzero(result):
    # If the result is zero, and GetLastError() returns a non-zero
    # error code, raise a WindowsError
    if result == 0 and GetLastError():
        raise WinError()
    return result


@_stdcall("user32", c_int, "GetWindowTextLengthW", HWND)
def GetWindowTextLength(hwnd):
    yield nonzero((yield hwnd,))


@_stdcall("user32", c_int, "GetWindowTextW", HWND, c_wchar_p, c_int)
def GetWindowText(hwnd):
    len = GetWindowTextLength(hwnd)+1
    buf = create_unicode_buffer(len)
    nonzero((yield hwnd, buf, len))
    yield buf.value


class GoCommand(CommandObject):
    """
    Go to specified window
    """

    def __init__(self, parameter = None):
        super( GoCommand, self ).__init__()
        self.parameter = parameter


    def on_quasimode_start(self):
        def callback(found_win, windows):
            # Determine if the window is application window
            if not win32gui.IsWindow(found_win):
                return True
            # Invisible windows are of no interest
            if not win32gui.IsWindowVisible(found_win):
                return True
            # Also disabled windows we do not want
            if not win32gui.IsWindowEnabled(found_win):
                return True
            exstyle = win32gui.GetWindowLong(found_win, win32con.GWL_EXSTYLE)
            # AppWindow flag would be good at this point
            if exstyle & win32con.WS_EX_APPWINDOW != win32con.WS_EX_APPWINDOW:
                style = win32gui.GetWindowLong(found_win, win32con.GWL_STYLE)
                # Child window is suspicious
                if style & win32con.WS_CHILD == win32con.WS_CHILD:
                    return True
                parent = win32gui.GetParent(found_win)
                owner = win32gui.GetWindow(found_win, win32con.GW_OWNER)
                # Also window which has parent or owner is probably not an application window
                if parent > 0 or owner > 0:
                    return True
                # Tool windows we also avoid
                # TODO: Avoid tool windows? Make exceptions? Make configurable?
                if exstyle & win32con.WS_EX_TOOLWINDOW == win32con.WS_EX_TOOLWINDOW:
                    return True
            # There are some specific windows we do not want to switch to
            win_class = win32gui.GetClassName(found_win)
            if "WindowsScreensaverClass" == win_class or "tooltips_class32" == win_class:
                return True
            # Now we probably have application window
            
            # Get title
            # Using own GetWindowText, because win32gui.GetWindowText() doesn't 
            # return unicode string.
            win_title = GetWindowText(found_win)
            # Removing all accents from characters
            win_title = unicodedata.normalize('NFKD', win_title).encode('ascii', 'ignore')

            # Get PID so we can get process name
            _, process_id = win32process.GetWindowThreadProcessId(found_win)
            process = ""
            try:
                # Get process name
                phandle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                    False, 
                    process_id)
                pexe = win32process.GetModuleFileNameEx(phandle, 0)
                pexe = os.path.normcase(os.path.normpath(pexe))
                # Remove extension
                process, _ = os.path.splitext(os.path.basename(pexe))
            except Exception, e:
                pass
            
            # Add hwnd and title to the list
            windows.append((found_win, "%s: %s" % (process, win_title)))
            return True

        # Compile list of application windows
        self.windows = []
        win32gui.EnumWindows(callback, self.windows)

        #print sorted(map(lambda x: str(x[1]).lower(), self.windows))
        self.valid_args = sorted(map(lambda x: xml.sax.saxutils.escape(x[1].lower()), self.windows))


    def __call__(self, ensoapi, window = None):
        if window is None:
            return None
        logging.debug("Go to window '%s'" % window)
        for hwnd, title in self.windows:
            title = xml.sax.saxutils.escape(title).lower()
            if title == window:
                try:
                    #windowPlacement = win32gui.GetWindowPlacement(hwnd)
                    #showCmd = windowPlacement[1]
                    #print showCmd
                    #if showCmd == SW_RESTORE:
                    #    win32gui.ShowWindow(hwnd, SW_RESTORE)
                    #else:
                    #    win32gui.BringWindowToTop(hwnd)
                    
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                except Exception, e:
                    if e[0] == 0:
                        time.sleep(0.2)
                        try:
                            win32gui.SetForegroundWindow(hwnd)
                        except Exception, e:
                            time.sleep(0.2)
                            try:
                                win32gui.BringWindowToTop(hwnd)
                            except Exception, e:
                                pass
                    elif e[0] == 2:
                       pass
                break
        return hwnd



cmd_go = GoCommand()
cmd_go.valid_args = []

# vi:set ff=unix tabstop=4 shiftwidth=4 expandtab:
