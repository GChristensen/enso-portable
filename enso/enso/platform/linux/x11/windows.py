"""
EWMH window enumeration and manipulation helpers for the Linux port,
used by the 'go' and window-management commands.
"""

import logging

from Xlib import X, Xatom

from enso.platform.linux.x11 import utils

# _NET_WM_STATE actions.
STATE_REMOVE = 0
STATE_ADD = 1
STATE_TOGGLE = 2

_SKIPPED_WINDOW_TYPES = ("_NET_WM_WINDOW_TYPE_DOCK",
                         "_NET_WM_WINDOW_TYPE_DESKTOP",
                         "_NET_WM_WINDOW_TYPE_TOOLBAR",
                         "_NET_WM_WINDOW_TYPE_MENU",
                         "_NET_WM_WINDOW_TYPE_SPLASH",
                         "_NET_WM_WINDOW_TYPE_NOTIFICATION")


def _atom(display, name):
    return display.intern_atom(name)


def _get_property(display, window, name, prop_type):
    try:
        prop = window.get_full_property(_atom(display, name), prop_type)
        return prop.value if prop else None
    except Exception:
        return None


def _window_title(display, window):
    title = _get_property(display, window, "_NET_WM_NAME",
                          _atom(display, "UTF8_STRING"))
    if title:
        return title.decode("utf-8", "replace") \
            if isinstance(title, bytes) else str(title)
    try:
        name = window.get_wm_name()
        if name:
            return name if isinstance(name, str) \
                else name.decode("latin-1", "replace")
    except Exception:
        pass
    return None


def _window_class(display, window):
    try:
        wm_class = window.get_wm_class()
        if wm_class:
            return wm_class[1] or wm_class[0]
    except Exception:
        pass
    return ""


def _is_normal_window(display, window):
    types = _get_property(display, window, "_NET_WM_WINDOW_TYPE",
                          Xatom.ATOM)
    if not types:
        return True
    for t in types:
        if display.get_atom_name(t) in _SKIPPED_WINDOW_TYPES:
            return False
    return True


def get_windows():
    """Returns a list of (window, label) for the application windows
    on the display."""
    display = utils.get_display()
    root = display.screen().root
    ids = _get_property(display, root, "_NET_CLIENT_LIST", Xatom.WINDOW)
    if ids is None:
        logging.warning("Window manager does not expose _NET_CLIENT_LIST")
        return []
    result = []
    for window_id in ids:
        try:
            window = display.create_resource_object("window", window_id)
            if not _is_normal_window(display, window):
                continue
            title = _window_title(display, window)
            if not title:
                continue
            wm_class = _window_class(display, window)
            result.append((window, "%s: %s" % (wm_class.lower(), title)))
        except Exception:
            continue
    return result


def _send_client_message(window, message, data):
    display = utils.get_display()
    root = display.screen().root
    from Xlib.protocol import event
    ev = event.ClientMessage(window=window,
                             client_type=_atom(display, message),
                             data=(32, (data + [0] * 5)[:5]))
    mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
    root.send_event(ev, event_mask=mask)
    display.flush()


def activate(window):
    """Activates (focuses and raises) the given window."""
    # source indication 2 = pager/direct user action.
    _send_client_message(window, "_NET_ACTIVE_WINDOW", [2, X.CurrentTime])


def get_active():
    """Returns the currently active window, or None."""
    display = utils.get_display()
    root = display.screen().root
    ids = _get_property(display, root, "_NET_ACTIVE_WINDOW", Xatom.WINDOW)
    if not ids or not ids[0]:
        return None
    return display.create_resource_object("window", ids[0])


def set_state(window, action, prop1, prop2=None):
    """Changes _NET_WM_STATE properties of a window (action is
    STATE_ADD/REMOVE/TOGGLE; props are atom names like
    '_NET_WM_STATE_MAXIMIZED_VERT')."""
    display = utils.get_display()
    data = [action, _atom(display, prop1),
            _atom(display, prop2) if prop2 else 0, 2]
    _send_client_message(window, "_NET_WM_STATE", data)


def close(window):
    """Asks the window manager to close the given window."""
    _send_client_message(window, "_NET_CLOSE_WINDOW", [X.CurrentTime, 2])


def minimize(window):
    """Iconifies the given window."""
    display = utils.get_display()
    _send_client_message(window, "WM_CHANGE_STATE", [3])  # IconicState
    display.flush()
