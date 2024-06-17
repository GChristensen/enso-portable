import time

import win32con
import win32api
import win32gui
import win32process

from test.test_ctypes import ctypes


def setForegroundWindow(hwnd):
    try:
        dwCurrentThread = win32api.GetCurrentThreadId()
        dwFGWindow = win32gui.GetForegroundWindow()
        [dwFGThread, _] = win32process.GetWindowThreadProcessId(dwFGWindow)
        ctypes.windll.user32.AttachThreadInput(dwCurrentThread, dwFGThread, 1)

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)

            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                print(e)

            try:
                win32gui.SetFocus(hwnd)
            except Exception as e:
                print(e)

            try:
                win32gui.SetActiveWindow(hwnd)
            except Exception as e:
                print(e)

        finally:
            ctypes.windll.user32.AttachThreadInput(dwCurrentThread, dwFGThread, 0)

    except Exception as e:
        print(e)
        if e[0] == 0:
            time.sleep(0.2)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                time.sleep(0.2)
                try:
                    win32gui.BringWindowToTop(hwnd)
                except Exception as e:
                    pass
        elif e[0] == 2:
            pass
