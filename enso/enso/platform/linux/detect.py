"""
Session-type and backend detection for the Enso Linux port.

Chooses between the two Linux backends:

  * "x11"      -- classic X11 session (root-window key grabs, EWMH).
  * "kwayland" -- Wayland session, targeting KDE Plasma (wlr-layer-shell
                  overlays, evdev trigger, KWin scripting).

WAYLAND_DISPLAY is the authoritative signal for a Wayland session:
DISPLAY is almost always also set there (XWayland), and
XDG_SESSION_TYPE can be wrong for processes started via ssh or cron.
"""

import logging
import os

_backend = None


def get_session_type():
    """Returns "wayland", "x11" or None (no graphical session found)."""
    if os.environ.get("WAYLAND_DISPLAY") \
            or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return None


def get_desktop():
    """Returns the desktop environment identifiers as a lowercase set,
    e.g. {"kde"} on Plasma (XDG_CURRENT_DESKTOP is colon-separated)."""
    desktops = set()
    for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP",
                "DESKTOP_SESSION"):
        for entry in os.environ.get(var, "").split(":"):
            entry = entry.strip().lower()
            if entry:
                desktops.add(entry)
    return desktops


def get_backend():
    """Returns the backend name ("x11" or "kwayland"), detecting it on
    the first call.  ENSO_LINUX_BACKEND overrides the detection."""
    global _backend
    if _backend is None:
        _backend = _detect_backend()
        logging.info("Using the '%s' Linux backend." % _backend)
    return _backend


def _detect_backend():
    forced = os.environ.get("ENSO_LINUX_BACKEND")
    if forced:
        if forced in ("x11", "kwayland"):
            return forced
        logging.warning("Ignoring unknown ENSO_LINUX_BACKEND=%r "
                        "(expected 'x11' or 'kwayland')." % forced)

    session = get_session_type()
    if session == "wayland":
        desktops = get_desktop()
        if "kde" not in desktops:
            # The kwayland backend needs wlr-layer-shell, which most
            # non-KDE compositors other than GNOME also implement; the
            # X11 backend under XWayland would only see XWayland
            # windows, which is worse.
            logging.warning(
                "Wayland session on an untested desktop (%s); using the "
                "KDE Wayland backend, which requires wlr-layer-shell "
                "support in the compositor."
                % (", ".join(sorted(desktops)) or "unknown"))
        return "kwayland"
    if session == "x11":
        return "x11"
    logging.error("Neither WAYLAND_DISPLAY nor DISPLAY is set; "
                  "Enso requires a graphical session.")
    return "x11"
