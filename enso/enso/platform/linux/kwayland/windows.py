"""
Window enumeration and manipulation for KDE Wayland, used by the 'go'
and window-management commands.

EWMH only reaches XWayland windows, so this module talks to KWin's
scripting interface instead: for every operation a small ephemeral
KWin script is loaded over D-Bus, runs inside the compositor with full
access to native and XWayland windows alike, and reports its result
back by calling a method on Enso's own D-Bus connection (addressed by
its unique bus name, so concurrent Enso instances don't collide).

Window handles are KWin internal-id UUID strings.  The API matches
the X11 backend: STATE_* constants, get_windows(), get_active(),
activate(), set_state(), close(), minimize().
"""

import json
import logging
import os
import tempfile

from gi.repository import Gio, GLib

# _NET_WM_STATE actions (same values as the X11 backend).
STATE_REMOVE = 0
STATE_ADD = 1
STATE_TOGGLE = 2

_SCRIPT_NAME = "enso-window-bridge"
_BRIDGE_PATH = "/org/enso/KWinBridge"
_BRIDGE_IFACE = "org.enso.KWinBridge"
_TIMEOUT_S = 3.0

_BRIDGE_XML = """
<node>
  <interface name='org.enso.KWinBridge'>
    <method name='Result'>
      <arg type='s' name='payload' direction='in'/>
    </method>
  </interface>
</node>
"""

# Helpers prepended to every script; cover the Plasma 6 API with
# Plasma 5 fallbacks.
_JS_PRELUDE = """
function _windows() {
    if (typeof workspace.windowList === "function")
        return workspace.windowList();
    return workspace.clientList();
}
function _active() {
    return workspace.activeWindow !== undefined
        ? workspace.activeWindow : workspace.activeClient;
}
function _setActive(w) {
    if (workspace.activeWindow !== undefined)
        workspace.activeWindow = w;
    else
        workspace.activeClient = w;
}
function _find(uuid) {
    var list = _windows();
    for (var i = 0; i < list.length; ++i)
        if (String(list[i].internalId) == uuid)
            return list[i];
    return null;
}
function _report(data) {
    callDBus(%(dest)s, %(path)s, %(iface)s, "Result",
             JSON.stringify(data === undefined ? null : data));
}
"""


class _KWinBridge:
    """Loads ephemeral KWin scripts and collects their reply."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.__bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        node = Gio.DBusNodeInfo.new_for_xml(_BRIDGE_XML)
        self.__bus.register_object(_BRIDGE_PATH, node.interfaces[0],
                                   self.__onMethodCall, None, None)
        self.__scripting = Gio.DBusProxy.new_sync(
            self.__bus, Gio.DBusProxyFlags.NONE, None,
            "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", None)
        self.__result = None
        self.__loop = None

    def __onMethodCall(self, connection, sender, path, iface, method,
                       params, invocation):
        if method == "Result":
            self.__result = params.unpack()[0]
            invocation.return_value(None)
            if self.__loop is not None:
                self.__loop.quit()

    def run(self, body):
        """Runs a KWin script (prelude + body) and returns the value it
        passed to _report(), or None on error/timeout."""
        js = _JS_PRELUDE % {
            "dest": json.dumps(self.__bus.get_unique_name()),
            "path": json.dumps(_BRIDGE_PATH),
            "iface": json.dumps(_BRIDGE_IFACE),
        } + body
        fd, path = tempfile.mkstemp(suffix=".js", prefix="enso-kwin-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(js)
            return self.__runFile(path)
        except GLib.Error:
            logging.exception("KWin scripting call failed; is KWin "
                              "running?")
            return None
        finally:
            os.unlink(path)

    def __runFile(self, path):
        try:
            self.__scripting.call_sync(
                "unloadScript", GLib.Variant("(s)", (_SCRIPT_NAME,)),
                Gio.DBusCallFlags.NONE, 1000, None)
        except GLib.Error:
            pass
        script_id, = self.__scripting.call_sync(
            "loadScript", GLib.Variant("(ss)", (path, _SCRIPT_NAME)),
            Gio.DBusCallFlags.NONE, 1000, None).unpack()
        if script_id < 0:
            logging.error("KWin refused to load the Enso helper script.")
            return None

        self.__result = None
        self.__loop = GLib.MainLoop()
        timeout_id = GLib.timeout_add(
            int(_TIMEOUT_S * 1000), self.__onTimeout)
        try:
            self.__runScriptObject(script_id)
            self.__loop.run()
        finally:
            GLib.source_remove(timeout_id)
            self.__loop = None
            try:
                self.__scripting.call_sync(
                    "unloadScript", GLib.Variant("(s)", (_SCRIPT_NAME,)),
                    Gio.DBusCallFlags.NONE, 1000, None)
            except GLib.Error:
                pass
        if self.__result is None:
            logging.warning("Timed out waiting for the KWin helper "
                            "script.")
            return None
        return json.loads(self.__result)

    def __runScriptObject(self, script_id):
        # Plasma >= 5.24 exposes scripts at /Scripting/Script<id>,
        # older versions at /<id>.
        last_error = None
        for object_path in ("/Scripting/Script%d" % script_id,
                            "/%d" % script_id):
            try:
                self.__bus.call_sync(
                    "org.kde.KWin", object_path, "org.kde.kwin.Script",
                    "run", None, None, Gio.DBusCallFlags.NONE, 1000, None)
                return
            except GLib.Error as error:
                last_error = error
        raise last_error

    def __onTimeout(self):
        if self.__loop is not None:
            self.__loop.quit()
        return GLib.SOURCE_REMOVE


def _run(body):
    try:
        return _KWinBridge.get().run(body)
    except GLib.Error:
        logging.exception("KWin scripting is unavailable.")
        return None


def get_windows():
    """Returns a list of (handle, label) for the application windows,
    with the same label format as the X11 backend."""
    result = _run("""
var out = [];
_windows().forEach(function(w) {
    if (!w.normalWindow || w.skipTaskbar || !w.caption)
        return;
    out.push({u: String(w.internalId),
              c: String(w.caption),
              r: String(w.resourceClass || "")});
});
_report(out);
""")
    if result is None:
        return []
    return [(w["u"], "%s: %s" % (w["r"].lower(), w["c"])) for w in result]


def activate(handle):
    """Activates (focuses and raises) the given window."""
    _run("""
var w = _find(%s);
if (w) _setActive(w);
_report(w !== null);
""" % json.dumps(handle))


def get_active():
    """Returns the currently active window, or None."""
    result = _run("""
var w = _active();
_report(w && w.normalWindow ? String(w.internalId) : null);
""")
    return result or None


def set_state(handle, action, prop1, prop2=None):
    """Changes window states, taking the same _NET_WM_STATE atom names
    as the X11 backend (action is STATE_ADD/REMOVE/TOGGLE)."""
    props = set(p for p in (prop1, prop2) if p)
    if "_NET_WM_STATE_FULLSCREEN" in props:
        if action == STATE_TOGGLE:
            body = "w.fullScreen = !w.fullScreen;"
        else:
            body = "w.fullScreen = %s;" \
                % ("true" if action == STATE_ADD else "false")
    elif props & {"_NET_WM_STATE_MAXIMIZED_VERT",
                  "_NET_WM_STATE_MAXIMIZED_HORZ"}:
        if action == STATE_TOGGLE:
            logging.warning("Toggling the maximized state is not "
                            "supported on the KWin backend.")
            return
        # KWin scripting has no per-axis maximize getters, so a
        # single-axis request resets the other axis.
        value = "true" if action == STATE_ADD else "false"
        vert = value if "_NET_WM_STATE_MAXIMIZED_VERT" in props else "false"
        horz = value if "_NET_WM_STATE_MAXIMIZED_HORZ" in props else "false"
        body = "w.setMaximize(%s, %s);" % (vert, horz)
    else:
        logging.warning("Unsupported window state change: %s" % props)
        return
    _run("""
var w = _find(%s);
if (w) { %s }
_report(w !== null);
""" % (json.dumps(handle), body))


def close(handle):
    """Asks the window manager to close the given window."""
    _run("""
var w = _find(%s);
if (w) w.closeWindow();
_report(w !== null);
""" % json.dumps(handle))


def minimize(handle):
    """Iconifies the given window."""
    _run("""
var w = _find(%s);
if (w) w.minimized = true;
_report(w !== null);
""" % json.dumps(handle))
