# platforms: linux, darwin

# The 'go' command for Linux (per-window, via EWMH) and macOS
# (per-application, via NSWorkspace).  The Windows version lives in
# go.py.

import logging
import sys
import xml.sax.saxutils

from enso.commands import CommandObject

if sys.platform == "darwin":
    from enso.platform.osx import windows as _backend
else:
    from enso.platform.linux import windows as _backend

CATEGORY = "go"


class GoCommand(CommandObject):
    """
    Go to specified window
    """

    def __init__(self, parameter = None):
        super( GoCommand, self ).__init__()
        self.parameter = parameter
        self.windows = []

    def on_quasimode_start(self):
        self.windows = _backend.get_windows()
        self.valid_args = sorted(
            xml.sax.saxutils.escape(label) for _, label in self.windows)

    def __call__(self, ensoapi, window = None):
        if window is None:
            return None

        logging.debug("Go to window '%s'" % window)

        for handle, label in self.windows:
            if xml.sax.saxutils.escape(label) == window:
                try:
                    _backend.activate(handle)
                except Exception:
                    logging.exception("Couldn't activate '%s'" % label)
                return handle
        return None


cmd_go = GoCommand()
cmd_go.valid_args = []
