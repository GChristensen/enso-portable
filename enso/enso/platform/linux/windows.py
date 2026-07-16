"""
Window enumeration and manipulation for the Linux port, used by the
'go' and window-management commands.

Facade over the active backend: EWMH on X11, KWin scripting over
D-Bus on KDE Wayland.  Both expose the same API: STATE_* constants,
get_windows(), get_active(), activate(), set_state(), close(),
minimize(); window handles are opaque and only valid with the backend
that produced them.
"""

from enso.platform.linux import detect

if detect.get_backend() == "kwayland":
    from enso.platform.linux.kwayland.windows import *
else:
    from enso.platform.linux.x11.windows import *
