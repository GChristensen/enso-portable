import win32api, win32pdhutil, win32con

def cmd_terminate(ensoapi, process_name):
    """Terminates the processes with the given name."""
    pids = win32pdhutil.FindPerformanceAttributesByName(process_name)
    for p in pids:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)

