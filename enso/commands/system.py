import subprocess
import sys

if sys.platform.startswith("win"):
    import win32api, win32pdhutil, win32con

    def cmd_terminate(ensoapi, process_name):
        """Terminates the processes with the given name (without extension)"""
        pids = win32pdhutil.FindPerformanceAttributesByName(process_name)
        for p in pids:
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p)
            win32api.TerminateProcess(handle, 0)
            win32api.CloseHandle(handle)
else:
    def cmd_terminate(ensoapi, process_name):
        """Terminates the processes with the given name"""
        result = subprocess.run(["pkill", "-x", process_name])
        if result.returncode != 0:
            ensoapi.display_message(
                "No process named “%s”" % process_name)
