import os
import subprocess
import sys

if sys.platform.startswith("win"):
    import ctypes
    import logging
    import re
    import xml.sax.saxutils
    from ctypes import wintypes

    import win32con
    import win32gui
    import win32process

    from enso.commands import CommandObject
    from enso.commands.factories import _equivalizeChars

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")

    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _kernel32.TerminateProcess.restype = wintypes.BOOL
    _kernel32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)

    _ntdll.NtQueryInformationProcess.restype = ctypes.c_long
    _ntdll.NtQueryInformationProcess.argtypes = (
        wintypes.HANDLE, ctypes.c_ulong, ctypes.c_void_p,
        ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))

    class _UNICODE_STRING(ctypes.Structure):
        _fields_ = [("Length", wintypes.USHORT),
                    ("MaximumLength", wintypes.USHORT),
                    ("Buffer", ctypes.c_void_p)]

    _PROCESS_TERMINATE = 0x0001
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _ProcessCommandLineInformation = 60  # Windows 8.1+
    _STATUS_INFO_LENGTH_MISMATCH = ctypes.c_long(0xC0000004).value

    _WHITESPACE = re.compile(r"\s+")

    def _clean(text):
        # Postfixes are joined with newlines for matching, so labels
        # must stay on a single line.
        return _WHITESPACE.sub(" ", text).strip()

    # Command line tokens: a quoted string or a run of non-blank characters.
    _TOKEN = re.compile(r'"[^"]*"|[^\s"]+')
    # An absolute path starts with a drive ("c:/", but not "file:/", "file:///c:/"
    # or "/c:/") or with a UNC prefix at the start of a token or after "="
    # ("--dir=//server/x").
    _PATH_START = r'(?:(?<![\w\\/])[a-zA-Z]:[\\/]|(?<![^\s"=])[\\/]{2}(?=[^\s\\/"]))'
    # A path ends at a list separator; quoted paths may contain spaces.
    _PATH = re.compile(_PATH_START + r'[^\s";,]*')
    _QUOTED_PATH = re.compile(_PATH_START + r'[^";,]*')
    _SEPARATORS = re.compile(r'[\\/]+')

    def _fix_path(match):
        path = match.group(0)
        prefix = ""
        if path[:2] in ("\\\\", "//"):
            prefix, path = "\\\\", path[2:]
        return prefix + _SEPARATORS.sub(r"\\", path)

    def _normalize_paths(cmdline):
        """Converts separators to single backslashes in the absolute paths of a command line."""
        def fix_token(match):
            token = match.group(0)
            pattern = _QUOTED_PATH if token.startswith('"') else _PATH
            return pattern.sub(_fix_path, token)
        return _TOKEN.sub(fix_token, cmdline)

    def _get_command_line(pid):
        handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        try:
            size = ctypes.c_ulong(0)
            status = _ntdll.NtQueryInformationProcess(
                handle, _ProcessCommandLineInformation, None, 0, ctypes.byref(size))
            if status != _STATUS_INFO_LENGTH_MISMATCH or not size.value:
                return None
            buf = ctypes.create_string_buffer(size.value)
            status = _ntdll.NtQueryInformationProcess(
                handle, _ProcessCommandLineInformation, buf, size, ctypes.byref(size))
            if status < 0:
                return None
            ustr = _UNICODE_STRING.from_buffer(buf)
            if not ustr.Buffer or not ustr.Length:
                return None
            return ctypes.wstring_at(ustr.Buffer, ustr.Length // 2)
        finally:
            _kernel32.CloseHandle(handle)

    def _get_top_level_windows():
        """Returns a list of (pid, title) for visible top-level application windows."""
        result = []

        def callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_CHILD:
                    return True
                exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if not exstyle & win32con.WS_EX_APPWINDOW:
                    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
                        return True
                    if exstyle & win32con.WS_EX_TOOLWINDOW:
                        return True
                title = _clean(win32gui.GetWindowText(hwnd))
                if not title:
                    return True
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                result.append((pid, title))
            except Exception:
                pass
            return True

        win32gui.EnumWindows(callback, None)
        return result

    def _terminate(pid):
        """Terminates the process; returns an error message or None."""
        handle = _kernel32.OpenProcess(_PROCESS_TERMINATE, False, pid)
        if not handle:
            return "Cannot open process %d (error %d)" % (pid, ctypes.get_last_error())
        try:
            if not _kernel32.TerminateProcess(handle, 1):
                return "Cannot terminate process %d (error %d)" % (pid, ctypes.get_last_error())
        finally:
            _kernel32.CloseHandle(handle)
        return None

    class TerminateCommand(CommandObject):
        """
        Terminates the process selected by its top-level window title or full command line
        """

        def __init__(self):
            super(TerminateCommand, self).__init__()
            self.valid_args = []
            self._targets = {}

        def on_quasimode_start(self):
            own_pid = os.getpid()
            entries = [e for e in _get_top_level_windows() if e[0] != own_pid]

            for pid in win32process.EnumProcesses():
                if pid in (0, 4, own_pid):  # Idle, System, Enso itself
                    continue
                try:
                    cmdline = _get_command_line(pid)
                except Exception:
                    cmdline = None
                if cmdline:
                    cmdline = _clean(_normalize_paths(cmdline))
                    if cmdline:
                        entries.append((pid, cmdline))

            # Every window and every command line gets its own entry;
            # identical labels are told apart by the PID.
            counts = {}
            for _, label in entries:
                key = label.lower()
                counts[key] = counts.get(key, 0) + 1

            targets = {}
            for pid, label in entries:
                label = label.lower()
                if counts[label] > 1:
                    label = "%s [%d]" % (label, pid)
                targets[xml.sax.saxutils.escape(label)] = pid

            self._targets = targets
            self.valid_args = sorted(targets)

        def find_matching(self, text):
            """Returns the PIDs of the entries the suggestion list shows for text."""
            # The same filter GenericPrefixFactory applies to valid_args.
            pattern = re.compile(_equivalizeChars(text), re.I)
            return {pid for label, pid in self._targets.items() if pattern.search(label)}

        def __call__(self, ensoapi, process=None):
            if process is None:
                return
            pid = self._targets.get(process)
            if pid is None:
                ensoapi.display_message("No such process")
                return

            logging.debug("Terminating process %d (%s)" % (pid, process))
            error = _terminate(pid)
            if error:
                ensoapi.display_message(error)

    class TerminateAllCommand(CommandObject):
        """
        Terminates all processes whose top-level window title or full command line contains the given text
        """

        # Any text is accepted; the process list only serves as suggestions.
        arbitrary_arg = True

        def __init__(self, terminate_command):
            super(TerminateAllCommand, self).__init__()
            # Share the process list (refreshed by "terminate" at
            # quasimode start) instead of enumerating twice.
            self._terminate_command = terminate_command

        @property
        def valid_args(self):
            return self._terminate_command.valid_args

        def __call__(self, ensoapi, text):
            text = text.strip()
            if not text:
                ensoapi.display_message("An argument is required.")
                return

            pids = self._terminate_command.find_matching(text)
            if not pids:
                ensoapi.display_message("No matching processes")
                return

            logging.debug("Terminating processes %s matching '%s'" % (sorted(pids), text))
            errors = [e for e in (_terminate(pid) for pid in sorted(pids)) if e]
            ensoapi.display_message(
                "Terminated %d of %d processes" % (len(pids) - len(errors), len(pids)),
                errors[0] if errors else None)

    cmd_terminate = TerminateCommand()
    cmd_terminate_all = TerminateAllCommand(cmd_terminate)
else:
    def cmd_terminate(ensoapi, process_name):
        """Terminates the processes with the given name"""
        result = subprocess.run(["pkill", "-x", process_name])
        if result.returncode != 0:
            ensoapi.display_message(
                "No process named “%s”" % process_name)