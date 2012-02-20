import win32api, win32pdhutil, win32con

def cmd_kill(ensoapi, process_name):
    pids = win32pdhutil.FindPerformanceAttributesByName(process_name)
    for p in pids:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)

