"""
X11 implementation of the Enso "input" provider.

Based on the original Enso Linux port:
Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
Contributions from Stuart "aquarius" Langridge.
Rewritten for Python 3 / PyGObject / python-xlib.

The InputManager owns Enso's main loop (Gtk.main) and pumps timer ticks
into the core; a companion thread listens for the quasimode trigger key
via a passive X key grab and captures the keyboard while the quasimode
is active.  All events are marshalled onto the GTK main thread, since
Enso core is not thread-safe.
"""

import atexit
import logging
import select
import shutil
import signal
import subprocess
import threading
import traceback

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from Xlib import X
from Xlib.error import ConnectionClosedError

from enso.platform.linux import utils

# Timer tick interval, in milliseconds.
TICK_INTERVAL_MS = 10

# Event types, matching the win32 InputManager constants.
EVENT_KEY_UP = 0
EVENT_KEY_DOWN = 1
EVENT_KEY_QUASIMODE = 2

# Quasimode keycode "slots".
KEYCODE_QUASIMODE_START = 0
KEYCODE_QUASIMODE_END = 1
KEYCODE_QUASIMODE_CANCEL = 2

# Real X keycodes for the keys Enso core refers to by name.
_display = utils.get_display()

KEYCODE_CAPITAL = utils.get_keycode("Caps_Lock", _display)
KEYCODE_RETURN = utils.get_keycode("Return", _display)
KEYCODE_ESCAPE = utils.get_keycode("Escape", _display)
KEYCODE_TAB = utils.get_keycode("Tab", _display)
KEYCODE_BACK = utils.get_keycode("BackSpace", _display)
KEYCODE_UP = utils.get_keycode("Up", _display)
KEYCODE_DOWN = utils.get_keycode("Down", _display)
KEYCODE_NUMLOCK = utils.get_keycode("Num_Lock", _display)
KEYCODE_SPACE = utils.get_keycode("space", _display)
KEYCODE_LSHIFT = utils.get_keycode("Shift_L", _display)
KEYCODE_RSHIFT = utils.get_keycode("Shift_R", _display)
KEYCODE_SHIFT = KEYCODE_LSHIFT

_SPECIAL_KEYCODES = frozenset(kc for kc in (
    KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE, KEYCODE_TAB,
    KEYCODE_BACK, KEYCODE_UP, KEYCODE_DOWN, KEYCODE_NUMLOCK,
) if kc)

# Maps X keycodes to the characters they produce, with the shifted
# character of a keycode stored at keycode + 1000 (the same convention
# the win32 CharMaps module uses).  Shifted letters are deliberately
# absent so that command names stay case-insensitive.
CASE_INSENSITIVE_KEYCODE_MAP = {}


def _fillKeymap(display):
    for keycode in range(8, 256):
        if keycode in _SPECIAL_KEYCODES:
            continue
        char = utils.keysym_to_char(display.keycode_to_keysym(keycode, 0))
        if char:
            CASE_INSENSITIVE_KEYCODE_MAP[keycode] = char
            shifted = utils.keysym_to_char(
                display.keycode_to_keysym(keycode, 1))
            if shifted and shifted.lower() != char.lower():
                CASE_INSENSITIVE_KEYCODE_MAP[keycode + 1000] = shifted
    if KEYCODE_SPACE:
        CASE_INSENSITIVE_KEYCODE_MAP[KEYCODE_SPACE] = " "


_fillKeymap(_display)


def getKeyState(keyCode):
    """Queries the current keyboard state, with win32 GetKeyState()
    semantics: negative means held down, low bit means toggled on."""
    display = utils.get_display()
    mask = display.screen().root.query_pointer().mask
    if keyCode in (KEYCODE_SHIFT, KEYCODE_LSHIFT, KEYCODE_RSHIFT):
        return -128 if mask & X.ShiftMask else 0
    if keyCode == KEYCODE_NUMLOCK:
        return 1 if mask & utils.get_numlock_mask(display) else 0
    if keyCode == KEYCODE_CAPITAL:
        return 1 if mask & X.LockMask else 0
    return 0


class _XKeyListener(threading.Thread):
    """Thread that grabs the quasimode trigger key and, while the
    quasimode is active, the whole keyboard.  It owns a private X
    display connection; results are posted to the main thread."""

    def __init__(self, parent):
        threading.Thread.__init__(self, daemon=True)
        self.__parent = parent
        self.__display = None
        self.__terminate = False
        self.__restart = False
        self.__leaveRequested = False
        self.__capturing = False
        self.__currentlyModal = False
        self.__grabbedKeycode = 0
        self.__capsLockKeysym = None
        self.__capsLockCleared = False
        self.__autoRepeatDisabled = False

    # ------------------------------------------------------------------
    # Requests from other threads (simple flags, polled by the loop)
    # ------------------------------------------------------------------

    def stop(self):
        self.__terminate = True

    def restart(self):
        """Re-grabs the trigger key, picking up configuration changes."""
        self.__restart = True

    def leave_quasimode(self):
        """Asks the listener to abandon the current capture; used when
        Enso core refuses to enter the quasimode."""
        self.__leaveRequested = True

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        try:
            self.__display = utils.open_display()
        except Exception:
            logging.critical("Couldn't open X display in key listener:\n%s"
                             % traceback.format_exc())
            GLib.idle_add(Gtk.main_quit)
            return

        self.__display.set_error_handler(self.__onXError)

        try:
            self.__setupTrigger()
            while not self.__terminate:
                if self.__restart:
                    self.__restart = False
                    self.__endCapture()
                    self.__setupTrigger()
                if self.__leaveRequested:
                    self.__leaveRequested = False
                    if self.__capturing:
                        self.__endCapture()
                        self.__post("quasimodeEnd")
                select.select([self.__display], [], [], 0.2)
                # Drain unconditionally: sync() calls elsewhere may have
                # queued events internally while the socket stays empty.
                while self.__display.pending_events():
                    self.__handleEvent(self.__display.next_event())
        except ConnectionClosedError:
            logging.critical("X connection closed; stopping Enso.")
            GLib.idle_add(Gtk.main_quit)
        except Exception:
            logging.critical("Key listener died:\n%s"
                             % traceback.format_exc())
            GLib.idle_add(Gtk.main_quit)
        finally:
            # A leaked keyboard grab would freeze the user's session;
            # release everything unconditionally on the way out.
            try:
                self.__endCapture()
                self.__releaseTrigger()
                self.__display.sync()
                self.__display.close()
            except Exception:
                pass

    def __onXError(self, error, *args):
        # Grab races and similar errors are not fatal; just log them.
        logging.error("X protocol error caught: %s" % error)

    # ------------------------------------------------------------------
    # Trigger key management
    # ------------------------------------------------------------------

    def __triggerKeycode(self):
        keycode = self.__parent.getQuasimodeKeycode(KEYCODE_QUASIMODE_START)
        return keycode or KEYCODE_CAPITAL

    def __setupTrigger(self):
        keycode = self.__triggerKeycode()
        if not keycode:
            logging.critical("Couldn't resolve the quasimode trigger key.")
            GLib.idle_add(Gtk.main_quit)
            return
        self.__releaseTrigger()
        self.__disableAutoRepeat(keycode)
        if keycode == KEYCODE_CAPITAL:
            self.__disableCapsLock()
        root = self.__display.screen().root
        root.grab_key(keycode, X.AnyModifier, False,
                      X.GrabModeAsync, X.GrabModeAsync)
        self.__display.sync()
        self.__grabbedKeycode = keycode

    def __releaseTrigger(self):
        if self.__grabbedKeycode:
            root = self.__display.screen().root
            root.ungrab_key(self.__grabbedKeycode, X.AnyModifier)
            self.__display.sync()
            self.__restoreAutoRepeat()
            self.__grabbedKeycode = 0
        self.enable_caps_lock()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def __handleEvent(self, event):
        if event.type not in (X.KeyPress, X.KeyRelease):
            return
        keycode = event.detail
        trigger = self.__grabbedKeycode

        if event.type == X.KeyPress:
            if not self.__capturing:
                if keycode == trigger:
                    self.__capturing = True
                    self.__currentlyModal = self.__parent.getModality()
                    self.__grabKeyboard()
                    self.__post("quasimodeStart")
            elif self.__currentlyModal and keycode == \
                    self.__parent.getQuasimodeKeycode(KEYCODE_QUASIMODE_END):
                self.__endCapture()
                self.__post("quasimodeEnd")
            elif self.__currentlyModal and keycode == \
                    self.__parent.getQuasimodeKeycode(KEYCODE_QUASIMODE_CANCEL):
                self.__endCapture()
                self.__post("quasimodeCancel")
            elif keycode != trigger:
                self.__post("keyDown", keycode)
        else:
            if self.__capturing:
                if keycode == trigger:
                    if not self.__currentlyModal:
                        self.__endCapture()
                        self.__post("quasimodeEnd")
                else:
                    self.__post("keyUp", keycode)

    def __post(self, eventName, keycode=None):
        GLib.idle_add(self.__parent._dispatchKeyEvent,
                      {"event": eventName, "keycode": keycode})

    def __grabKeyboard(self):
        # The passive key grab only lasts while the trigger key is held;
        # an explicit keyboard grab keeps the capture alive in modal
        # ("sticky") mode after the trigger is released.
        root = self.__display.screen().root
        root.grab_keyboard(False, X.GrabModeAsync, X.GrabModeAsync,
                           X.CurrentTime)
        self.__display.sync()

    def __endCapture(self):
        if self.__capturing:
            self.__capturing = False
            self.__display.ungrab_keyboard(X.CurrentTime)
            self.__display.sync()

    # ------------------------------------------------------------------
    # Caps Lock toggle suppression and trigger auto-repeat
    # ------------------------------------------------------------------

    def __disableCapsLock(self):
        if self.__capsLockCleared or not shutil.which("xmodmap"):
            if not shutil.which("xmodmap"):
                logging.warning("xmodmap not found; Caps Lock will keep "
                                "toggling while used as the Enso trigger.")
            return
        try:
            output = subprocess.run(["xmodmap", "-pm"], capture_output=True,
                                    text=True).stdout
        except OSError:
            return
        for line in output.splitlines():
            parts = line.strip().split()
            if parts and parts[0] == "lock" and len(parts) > 1:
                self.__capsLockKeysym = parts[1]
                break
        if self.__capsLockKeysym:
            logging.debug("Using xmodmap to disable Caps Lock")
            subprocess.run(["xmodmap", "-e", "clear Lock"])
            self.__capsLockCleared = True
            atexit.register(self.enable_caps_lock)
        else:
            logging.debug("Caps Lock already disabled")

    def enable_caps_lock(self):
        if self.__capsLockCleared and self.__capsLockKeysym:
            logging.debug("Using xmodmap to re-enable Caps Lock")
            subprocess.run(["xmodmap", "-e",
                            "add Lock = %s" % self.__capsLockKeysym])
            self.__capsLockCleared = False

    def disable_caps_lock(self):
        self.__disableCapsLock()

    def __disableAutoRepeat(self, keycode):
        if not shutil.which("xset"):
            logging.warning("xset not found; you might experience key-repeat "
                            "problems with the quasimode trigger key.")
            return
        subprocess.run(["xset", "-r", str(keycode)])
        self.__autoRepeatDisabled = True
        atexit.register(self.__restoreAutoRepeat)

    def __restoreAutoRepeat(self):
        if self.__autoRepeatDisabled and self.__grabbedKeycode:
            subprocess.run(["xset", "r", str(self.__grabbedKeycode)])
            self.__autoRepeatDisabled = False


class InputManager(object):
    """Input event manager: owns the GTK main loop and the key listener.
    Enso's EventManager subclasses this and overrides the on* hooks."""

    def __init__(self):
        self.__mouseEventsEnabled = False
        self.__qmKeycodes = [KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE]
        self.__isModal = False
        self.__keyListener = None
        self.__lastMousePos = None
        self.__lastMouseButtons = 0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        logging.info("Entering InputManager.run()")

        timeoutId = GLib.timeout_add(TICK_INTERVAL_MS, self.__onTimer)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,
                             self.__onSigint)

        self.__keyListener = _XKeyListener(self)
        self.__keyListener.start()

        try:
            self.onInit()
            Gtk.main()
        except KeyboardInterrupt:
            pass
        finally:
            self.__keyListener.stop()
            self.__keyListener.join(2.0)
            GLib.source_remove(timeoutId)

        logging.info("Exiting InputManager.run()")

    def stop(self):
        GLib.idle_add(Gtk.main_quit)

    def __onSigint(self):
        logging.info("SIGINT received; stopping.")
        self.stop()
        return GLib.SOURCE_CONTINUE

    def __onTimer(self):
        # A tick handler exception must not kill the timeout source:
        # returning a falsy value would remove it permanently.
        try:
            if self.__mouseEventsEnabled:
                self.__pollMouse()
            self.onTick(TICK_INTERVAL_MS)
        except Exception:
            logging.error("Exception in timer event handler:\n%s"
                          % traceback.format_exc())
        return GLib.SOURCE_CONTINUE

    def __pollMouse(self):
        # X11 has no lightweight global mouse hook comparable to
        # win32's; poll the pointer on the same tick that already
        # drives onTick(), which is cheap since query_pointer() is a
        # single round-trip and only happens while something (e.g. a
        # message window) actually asked to be notified of movement.
        pointer = utils.get_display().screen().root.query_pointer()
        pos = (pointer.root_x, pointer.root_y)
        buttonMask = pointer.mask & (X.Button1Mask | X.Button2Mask |
                                     X.Button3Mask | X.Button4Mask |
                                     X.Button5Mask)
        if self.__lastMousePos is not None and pos != self.__lastMousePos:
            self.onMouseMove(*pos)
        self.__lastMousePos = pos
        if buttonMask and not self.__lastMouseButtons:
            self.onSomeMouseButton()
        self.__lastMouseButtons = buttonMask

    def _dispatchKeyEvent(self, info):
        """Delivers a key listener event on the GTK main thread."""
        try:
            event = info["event"]
            if event == "quasimodeStart":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_START)
            elif event == "quasimodeEnd":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)
            elif event == "quasimodeCancel":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_CANCEL)
            elif event == "keyDown":
                self.onKeypress(EVENT_KEY_DOWN, info["keycode"])
            elif event == "keyUp":
                self.onKeypress(EVENT_KEY_UP, info["keycode"])
            elif event == "someKey":
                self.onSomeKey()
            else:
                logging.warning("Don't know what to do with event: %s" % info)
        except Exception:
            logging.error("Exception in key event handler:\n%s"
                          % traceback.format_exc())
        return GLib.SOURCE_REMOVE

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def enableMouseEvents(self, isEnabled):
        self.__mouseEventsEnabled = isEnabled
        if isEnabled:
            # Forget any previously observed position/buttons so the
            # next poll only records a baseline instead of comparing
            # against stale state and firing a spurious dismissal.
            self.__lastMousePos = None
            self.__lastMouseButtons = 0

    def getQuasimodeKeycode(self, quasimodeKeycode):
        return self.__qmKeycodes[quasimodeKeycode]

    def setQuasimodeKeycode(self, quasimodeKeycode, keycode):
        self.__qmKeycodes[quasimodeKeycode] = keycode
        if quasimodeKeycode == KEYCODE_QUASIMODE_START and self.__keyListener:
            self.__keyListener.restart()

    def setModality(self, isModal):
        self.__isModal = bool(isModal)

    def getModality(self):
        return self.__isModal

    def setCapsLockMode(self, capsLockEnabled):
        if self.__keyListener:
            if capsLockEnabled:
                self.__keyListener.enable_caps_lock()
            else:
                self.__keyListener.disable_caps_lock()

    def leaveQuasimode(self):
        if self.__keyListener:
            self.__keyListener.leave_quasimode()

    # ------------------------------------------------------------------
    # Hooks overridden by Enso's EventManager
    # ------------------------------------------------------------------

    def onKeypress(self, eventType, vkCode):
        pass

    def onSomeKey(self):
        pass

    def onSomeMouseButton(self):
        pass

    def onExitRequested(self):
        pass

    def onMouseMove(self, x, y):
        pass

    def onTick(self, msPassed):
        pass

    def onInit(self):
        pass
