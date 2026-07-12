# platforms: darwin

# Window-management commands for macOS, the counterparts of the
# Windows-only commands in win_tools.py and the Linux (EWMH) commands
# in window_tools.py.  Implemented with the Accessibility (AX) API,
# gated by the same 'Accessibility' permission Enso's event tap
# already requires.

from enso.platform.osx import windows as _wm

CATEGORY = "window tools"


def cmd_close(ensoapi):
    """ Close the current window """
    if not _wm.ax_available():
        ensoapi.display_message(
            "The close command needs the "
            "pyobjc-framework-ApplicationServices package and the "
            "Accessibility permission")
        return
    if not _wm.close_front_window():
        ensoapi.display_message("No window to close")