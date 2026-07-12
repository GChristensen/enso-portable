# platforms: linux

# Window-management commands for Linux (EWMH), the counterparts of the
# Windows-only commands in win_tools.py.

from enso.platform.linux import windows as _wm

CATEGORY = "window tools"


def _active(ensoapi):
    window = _wm.get_active()
    if window is None:
        ensoapi.display_message("No active window")
    return window


def cmd_maximize(ensoapi):
    """ Maximize the current window """
    window = _active(ensoapi)
    if window:
        _wm.set_state(window, _wm.STATE_ADD,
                      "_NET_WM_STATE_MAXIMIZED_VERT",
                      "_NET_WM_STATE_MAXIMIZED_HORZ")


def cmd_unmaximize(ensoapi):
    """ Unmaximize the current window """
    window = _active(ensoapi)
    if window:
        _wm.set_state(window, _wm.STATE_REMOVE,
                      "_NET_WM_STATE_MAXIMIZED_VERT",
                      "_NET_WM_STATE_MAXIMIZED_HORZ")

def cmd_restore(ensoapi):
    """ Restore the current window """
    cmd_unmaximize(ensoapi)


def cmd_height_to_maximum(ensoapi):
    """ Maximize the current window vertically """
    window = _active(ensoapi)
    if window:
        _wm.set_state(window, _wm.STATE_ADD,
                      "_NET_WM_STATE_MAXIMIZED_VERT")


def cmd_width_to_maximum(ensoapi):
    """ Maximize the current window horizontally """
    window = _active(ensoapi)
    if window:
        _wm.set_state(window, _wm.STATE_ADD,
                      "_NET_WM_STATE_MAXIMIZED_HORZ")


def cmd_fullscreen(ensoapi):
    """ Toggle fullscreen state of the current window """
    window = _active(ensoapi)
    if window:
        _wm.set_state(window, _wm.STATE_TOGGLE,
                      "_NET_WM_STATE_FULLSCREEN")


def cmd_minimize(ensoapi):
    """ Minimize the current window """
    window = _active(ensoapi)
    if window:
        _wm.minimize(window)


def cmd_close(ensoapi):
    """ Close the current window """
    window = _active(ensoapi)
    if window:
        _wm.close(window)
