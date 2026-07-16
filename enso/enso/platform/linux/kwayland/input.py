"""
KDE Wayland implementation of the Enso "input" provider.

Wayland offers no global key grabs, so the quasimode is implemented
entirely on the raw evdev devices (python-evdev, requiring membership
in the 'input' group):

  * The trigger key (Caps Lock) is watched on the evdev keyboards in a
    companion thread -- the only way to see both the press and the
    release of an arbitrary key regardless of window focus.

  * The moment the trigger goes down, the listener thread takes an
    exclusive grab (EVIOCGRAB) on every keyboard device and keeps
    consuming their events itself.  While the grab is held, the
    compositor -- and therefore the focused application, and any
    active input method -- receives nothing at all: the Wayland
    counterpart of the X11 active keyboard grab, with no window-focus
    round-trip and no leakage race at quasimode start.  The grab is
    released when the quasimode ends, and unconditionally when the
    listener exits, since a leaked grab would freeze the keyboard.

  * The trigger release is consumed by the grab, but the compositor
    saw the original press, so a balancing release is injected through
    a uinput virtual keyboard (which the listener ignores by name).

Grabbing is best-effort: if a device cannot be grabbed (e.g. another
remapper owns it), its keys still reach Enso -- reading works without
the grab -- but also leak to the focused application.

Enso core's keycode conventions carry over unchanged: evdev keycodes
+ 8 are X-style keycodes, and the printable-character map is built
from the GDK keymap.  The Caps Lock toggle action is suppressed
session-wide via the caps:none XKB option (see kwayland.xkb), with an
LED-based drift correction as a safety net.
"""

import logging
import os
import select
import signal
import threading
import time
import traceback

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try:
    import evdev
    from evdev import ecodes
except ImportError as exc:
    raise ImportError(
        "python-evdev is required for the KDE Wayland backend but is not "
        "installed (pip install evdev)."
    ) from exc

from enso.platform.linux.kwayland import utils, xkb

# Timer tick interval, in milliseconds.
TICK_INTERVAL_MS_FAST = 10
TICK_INTERVAL_MS_SLOW = 50

# Event types, matching the win32 InputManager constants.
EVENT_KEY_UP = 0
EVENT_KEY_DOWN = 1
EVENT_KEY_QUASIMODE = 2

# Quasimode keycode "slots".
KEYCODE_QUASIMODE_START = 0
KEYCODE_QUASIMODE_END = 1
KEYCODE_QUASIMODE_CANCEL = 2

# Offset between evdev keycodes and X-style/GTK hardware keycodes.
EVDEV_OFFSET = 8

# Standard X-style keycodes for the keys Enso core refers to by name
# (evdev code + 8; these are fixed in the evdev/xkb keycode era).
# Resolution through the GDK keymap is deliberately avoided: with the
# caps:none option active, Caps_Lock maps to no keysym at all.
KEYCODE_CAPITAL = ecodes.KEY_CAPSLOCK + EVDEV_OFFSET      # 66
KEYCODE_RETURN = ecodes.KEY_ENTER + EVDEV_OFFSET          # 36
KEYCODE_ESCAPE = ecodes.KEY_ESC + EVDEV_OFFSET            # 9
KEYCODE_TAB = ecodes.KEY_TAB + EVDEV_OFFSET               # 23
KEYCODE_BACK = ecodes.KEY_BACKSPACE + EVDEV_OFFSET        # 22
KEYCODE_UP = ecodes.KEY_UP + EVDEV_OFFSET                 # 111
KEYCODE_DOWN = ecodes.KEY_DOWN + EVDEV_OFFSET             # 116
KEYCODE_NUMLOCK = ecodes.KEY_NUMLOCK + EVDEV_OFFSET       # 77
KEYCODE_SPACE = ecodes.KEY_SPACE + EVDEV_OFFSET           # 65
KEYCODE_LSHIFT = ecodes.KEY_LEFTSHIFT + EVDEV_OFFSET      # 50
KEYCODE_RSHIFT = ecodes.KEY_RIGHTSHIFT + EVDEV_OFFSET     # 62
KEYCODE_SHIFT = KEYCODE_LSHIFT

_SPECIAL_KEYCODES = frozenset((
    KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE, KEYCODE_TAB,
    KEYCODE_BACK, KEYCODE_UP, KEYCODE_DOWN, KEYCODE_NUMLOCK,
))

# Maps hardware keycodes to the characters they produce, with the
# shifted character of a keycode stored at keycode + 1000 (the same
# convention the win32 CharMaps module uses).  Shifted letters are
# deliberately absent so that command names stay case-insensitive.
CASE_INSENSITIVE_KEYCODE_MAP = {}


def _fillKeymap():
    keymap = Gdk.Keymap.get_for_display(Gdk.Display.get_default())
    for keycode in range(8, 256):
        if keycode in _SPECIAL_KEYCODES:
            continue
        ok, keyval, _, _, _ = keymap.translate_keyboard_state(
            keycode, Gdk.ModifierType(0), 0)
        char = utils.keyval_to_char(keyval) if ok else None
        if char:
            CASE_INSENSITIVE_KEYCODE_MAP[keycode] = char
            ok, keyval, _, _, _ = keymap.translate_keyboard_state(
                keycode, Gdk.ModifierType.SHIFT_MASK, 0)
            shifted = utils.keyval_to_char(keyval) if ok else None
            if shifted and shifted.lower() != char.lower():
                CASE_INSENSITIVE_KEYCODE_MAP[keycode + 1000] = shifted
    CASE_INSENSITIVE_KEYCODE_MAP[KEYCODE_SPACE] = " "


_fillKeymap()

# The listener singleton, so getKeyState() can reach its state.
_listener = None

# Lazily created uinput keyboard (all key codes) used to balance the
# swallowed trigger release and to undo a Caps Lock toggle; it bears
# UINPUT_DEVICE_NAME, so the evdev listener ignores it.
_virtual_keyboard = None


def _virtualKeyboard():
    global _virtual_keyboard
    if _virtual_keyboard is None:
        _virtual_keyboard = evdev.UInput(name=utils.UINPUT_DEVICE_NAME)
        time.sleep(0.2)  # let the compositor pick the device up
    return _virtual_keyboard


def _injectKey(evdev_code, value):
    try:
        device = _virtualKeyboard()
        device.write(ecodes.EV_KEY, evdev_code, value)
        device.syn()
    except Exception:
        logging.exception("Couldn't inject a key event via uinput.")


def _tapCapsLock():
    _injectKey(ecodes.KEY_CAPSLOCK, 1)
    _injectKey(ecodes.KEY_CAPSLOCK, 0)


def getKeyState(keyCode):
    """Queries the current keyboard state, with win32 GetKeyState()
    semantics: negative means held down, low bit means toggled on."""
    if _listener is None:
        return 0
    if keyCode in (KEYCODE_SHIFT, KEYCODE_LSHIFT, KEYCODE_RSHIFT):
        return -128 if _listener.shift_is_down() else 0
    if keyCode == KEYCODE_NUMLOCK:
        return 1 if _listener.led_is_on(ecodes.LED_NUML) else 0
    if keyCode == KEYCODE_CAPITAL:
        return 1 if _listener.led_is_on(ecodes.LED_CAPSL) else 0
    return 0


# Mouse button key range (BTN_LEFT .. BTN_TASK).
_BTN_RANGE = range(0x110, 0x118)

# Minimum interval between synthetic mouse-move notifications.
_MOUSE_MOVE_THROTTLE = 0.05

# How often the device list is rescanned for hotplugged keyboards.
_RESCAN_INTERVAL = 5.0


class _EvdevListener(threading.Thread):
    """Thread that watches the raw input devices and owns the
    quasimode state machine: on the trigger press it grabs the
    keyboards and consumes the keystrokes itself, releasing them when
    the quasimode ends.  Results are marshalled onto the GTK main
    thread."""

    def __init__(self, parent):
        threading.Thread.__init__(self, daemon=True)
        self.__parent = parent
        self.__terminate = False
        self.__leaveRequested = False
        self.__wakeup_r, self.__wakeup_w = os.pipe()
        self.__devices = {}          # fd -> InputDevice
        self.__keyboardFds = set()
        self.__grabbedFds = set()
        self.__capturing = False
        self.__currentlyModal = False
        self.__shiftDown = set()     # evdev codes of held shift keys
        self.__lastScan = 0.0
        self.__lastMouseMove = 0.0
        self.__permissionWarned = False
        # The Caps Lock LED state observed at the trigger press, i.e.
        # the state the user actually wants; read by the manager's
        # drift correction.
        self.caps_baseline = None
        # Written from the main thread, read here; a plain attribute is
        # enough for a single int under the GIL.
        self.trigger_keycode = KEYCODE_CAPITAL

    # ------------------------------------------------------------------
    # Requests from other threads
    # ------------------------------------------------------------------

    def stop(self):
        self.__terminate = True
        self.__wake()

    def leave_quasimode(self):
        """Asks the listener to abandon the current capture; used when
        Enso core refuses to enter the quasimode."""
        self.__leaveRequested = True
        self.__wake()

    def __wake(self):
        try:
            os.write(self.__wakeup_w, b"x")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # State queries (any thread)
    # ------------------------------------------------------------------

    def shift_is_down(self):
        return bool(self.__shiftDown)

    def led_is_on(self, led):
        for device in list(self.__devices.values()):
            try:
                if led in device.leds():
                    return True
            except OSError:
                continue
        return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        try:
            self.__scanDevices()
            while not self.__terminate:
                if self.__leaveRequested:
                    self.__leaveRequested = False
                    if self.__capturing:
                        self.__endCapture()
                        self.__post("quasimodeEnd")
                if time.monotonic() - self.__lastScan > _RESCAN_INTERVAL:
                    self.__scanDevices()
                fds = list(self.__devices) + [self.__wakeup_r]
                ready, _, _ = select.select(fds, [], [], 1.0)
                for fd in ready:
                    if fd == self.__wakeup_r:
                        os.read(self.__wakeup_r, 64)
                        continue
                    self.__drainDevice(fd)
        except Exception:
            logging.critical("evdev listener died:\n%s"
                             % traceback.format_exc())
            GLib.idle_add(Gtk.main_quit)
        finally:
            # A leaked keyboard grab would freeze the user's session;
            # release everything unconditionally on the way out.
            self.__ungrabAll()
            for device in self.__devices.values():
                try:
                    device.close()
                except Exception:
                    pass

    def __scanDevices(self):
        self.__lastScan = time.monotonic()
        known = set(d.path for d in self.__devices.values())
        found_keyboard = bool(self.__keyboardFds)
        denied = 0
        for path in evdev.list_devices():
            try:
                if path in known:
                    continue
                device = evdev.InputDevice(path)
                if device.name == utils.UINPUT_DEVICE_NAME:
                    device.close()
                    continue
                caps = device.capabilities()
                keys = set(caps.get(ecodes.EV_KEY, ()))
                is_keyboard = ecodes.KEY_CAPSLOCK in keys \
                    and ecodes.KEY_A in keys
                is_mouse = ecodes.BTN_LEFT in keys \
                    or ecodes.EV_REL in caps
                if is_keyboard or is_mouse:
                    self.__devices[device.fd] = device
                    if is_keyboard:
                        self.__keyboardFds.add(device.fd)
                        found_keyboard = True
                        # A keyboard hotplugged mid-quasimode must be
                        # captured like the others.
                        if self.__capturing:
                            self.__grab(device)
                else:
                    device.close()
            except PermissionError:
                denied += 1
            except OSError:
                continue
        if not found_keyboard and not self.__permissionWarned:
            self.__permissionWarned = True
            if denied:
                logging.critical(
                    "No permission to read /dev/input/event* (%d devices "
                    "denied).  The Wayland quasimode trigger needs it: "
                    "add yourself to the 'input' group with 'sudo "
                    "usermod -a -G input %s' and log in again."
                    % (denied, os.environ.get("USER", "$USER")))
            else:
                logging.critical("No keyboard found among the evdev "
                                 "devices; the quasimode trigger will "
                                 "not work.")

    def __drainDevice(self, fd):
        device = self.__devices.get(fd)
        if device is None:
            return
        try:
            for event in device.read():
                self.__handleEvent(event)
        except OSError:
            # Device unplugged; forget it and rescan soon.
            del self.__devices[fd]
            self.__keyboardFds.discard(fd)
            self.__grabbedFds.discard(fd)
            self.__lastScan = 0.0

    # ------------------------------------------------------------------
    # Grab management
    # ------------------------------------------------------------------

    def __grab(self, device):
        try:
            device.grab()
            self.__grabbedFds.add(device.fd)
        except OSError as error:
            logging.warning("Couldn't grab %s (%s); its keystrokes will "
                            "leak to the focused application during the "
                            "quasimode." % (device.path, error))

    def __grabAll(self):
        for fd in self.__keyboardFds:
            device = self.__devices.get(fd)
            if device is not None and fd not in self.__grabbedFds:
                self.__grab(device)

    def __ungrabAll(self):
        for fd in list(self.__grabbedFds):
            device = self.__devices.get(fd)
            if device is not None:
                try:
                    device.ungrab()
                except OSError:
                    pass
            self.__grabbedFds.discard(fd)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def __handleEvent(self, event):
        if event.type == ecodes.EV_REL:
            self.__onMouseActivity(moved=True)
            return
        if event.type != ecodes.EV_KEY:
            return
        if event.code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
            if event.value:
                self.__shiftDown.add(event.code)
            else:
                self.__shiftDown.discard(event.code)
        if event.code in _BTN_RANGE:
            if event.value == 1:
                self.__onMouseActivity(moved=False)
            return
        keycode = event.code + EVDEV_OFFSET
        try:
            self.__handleKey(event, keycode)
        except Exception:
            # Never leave the keyboard grabbed because of a handler bug.
            self.__endCapture()
            raise

    def __handleKey(self, event, keycode):
        trigger = self.trigger_keycode
        if not self.__capturing:
            if keycode == trigger and event.value == 1:
                self.__capturing = True
                self.__currentlyModal = self.__parent.getModality()
                self.caps_baseline = self.led_is_on(ecodes.LED_CAPSL) \
                    if trigger == KEYCODE_CAPITAL else None
                self.__grabAll()
                self.__post("quasimodeStart")
            elif event.value == 1:
                self.__post("someKey")
            return

        # --- capturing ---
        if keycode == trigger:
            if event.value == 0:
                # The compositor saw the trigger press but this release
                # was consumed by the grab; balance its keyboard state.
                _injectKey(event.code, 0)
                if not self.__currentlyModal:
                    self.__endCapture()
                    self.__post("quasimodeEnd")
            return
        if event.value in (1, 2):   # press or auto-repeat
            if self.__currentlyModal and event.value == 1:
                if keycode == self.__parent.getQuasimodeKeycode(
                        KEYCODE_QUASIMODE_END):
                    self.__endCapture()
                    self.__post("quasimodeEnd")
                    return
                if keycode == self.__parent.getQuasimodeKeycode(
                        KEYCODE_QUASIMODE_CANCEL):
                    self.__endCapture()
                    self.__post("quasimodeCancel")
                    return
            self.__post("keyDown", keycode)
        elif event.value == 0:
            self.__post("keyUp", keycode)

    def __endCapture(self):
        if self.__capturing:
            self.__capturing = False
            self.__ungrabAll()

    def __onMouseActivity(self, moved):
        if self.__capturing or not self.__parent._mouseEventsEnabled():
            return
        if moved:
            now = time.monotonic()
            if now - self.__lastMouseMove < _MOUSE_MOVE_THROTTLE:
                return
            self.__lastMouseMove = now
            self.__post("mouseMove")
        else:
            self.__post("mouseButton")

    def __post(self, eventName, keycode=None):
        GLib.idle_add(self.__parent._dispatchEvent,
                      {"event": eventName, "keycode": keycode})


class InputManager(object):
    """Input event manager: owns the GTK main loop and the evdev
    listener.  Enso's EventManager subclasses this and overrides the
    on* hooks."""

    def __init__(self):
        self.__mouseEventsEnabled = False
        self.__qmKeycodes = [KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE]
        self.__isModal = False
        self.__listener = None
        self.__tickIntervalMs = TICK_INTERVAL_MS_SLOW
        self.__timeoutId = None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        global _listener
        logging.info("Entering InputManager.run() (KDE Wayland backend)")

        self.__timeoutId = GLib.timeout_add(self.__tickIntervalMs,
                                            self.__onTimer)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,
                             self.__onSigint)

        self.__listener = _EvdevListener(self)
        self.__listener.trigger_keycode = self.__triggerKeycode()
        _listener = self.__listener
        self.__listener.start()

        if self.__triggerKeycode() == KEYCODE_CAPITAL:
            xkb.disable_caps_lock()

        try:
            self.onInit()
            Gtk.main()
        except KeyboardInterrupt:
            pass
        finally:
            self.__listener.stop()
            self.__listener.join(2.0)
            _listener = None
            xkb.enable_caps_lock()
            if self.__timeoutId:
                GLib.source_remove(self.__timeoutId)
                self.__timeoutId = None

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
            self.onTick(self.__tickIntervalMs)
        except Exception:
            logging.error("Exception in timer event handler:\n%s"
                          % traceback.format_exc())
        return GLib.SOURCE_CONTINUE

    def setTickRate(self, fast):
        """Switch between fast (10ms) and slow (50ms) tick rates.
        Called by EventManager when active UI work begins/ends."""
        desired = TICK_INTERVAL_MS_FAST if fast else TICK_INTERVAL_MS_SLOW
        if desired == self.__tickIntervalMs:
            return
        self.__tickIntervalMs = desired
        if self.__timeoutId is not None:
            GLib.source_remove(self.__timeoutId)
            self.__timeoutId = GLib.timeout_add(desired, self.__onTimer)

    # ------------------------------------------------------------------
    # Event dispatch (GTK main thread)
    # ------------------------------------------------------------------

    def __triggerKeycode(self):
        return self.__qmKeycodes[KEYCODE_QUASIMODE_START] or KEYCODE_CAPITAL

    def _dispatchEvent(self, info):
        """Delivers a listener event on the GTK main thread."""
        try:
            event = info["event"]
            if event == "quasimodeStart":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_START)
            elif event == "quasimodeEnd":
                self.__scheduleCapsDriftCheck()
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)
            elif event == "quasimodeCancel":
                self.__scheduleCapsDriftCheck()
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_CANCEL)
            elif event == "keyDown":
                self.onKeypress(EVENT_KEY_DOWN, info["keycode"])
            elif event == "keyUp":
                self.onKeypress(EVENT_KEY_UP, info["keycode"])
            elif event == "someKey":
                if self.__mouseEventsEnabled:
                    self.onSomeKey()
            elif event == "mouseMove":
                # The pointer position is not observable on Wayland; a
                # sentinel position is enough for the dismiss-on-activity
                # behavior the core uses this for.
                if self.__mouseEventsEnabled:
                    self.onMouseMove(-1, -1)
            elif event == "mouseButton":
                if self.__mouseEventsEnabled:
                    self.onSomeMouseButton()
            else:
                logging.warning("Don't know what to do with event: %s" % info)
        except Exception:
            logging.error("Exception in input event handler:\n%s"
                          % traceback.format_exc())
        return GLib.SOURCE_REMOVE

    def __scheduleCapsDriftCheck(self):
        if self.__listener and self.__listener.caps_baseline is not None:
            # Give the compositor time to process the balancing trigger
            # release before checking for Caps Lock drift.
            GLib.timeout_add(250, self.__fixCapsLockDrift)

    def __fixCapsLockDrift(self):
        """Safety net: undoes a Caps Lock toggle caused by the trigger.
        With caps:none in effect the trigger cannot toggle the lock and
        this never fires; when the suppression is unavailable, a
        corrective Caps Lock tap from a uinput device (ignored by the
        evdev listener) puts the state back."""
        if self.__listener:
            baseline = self.__listener.caps_baseline
            current = self.__listener.led_is_on(ecodes.LED_CAPSL)
            if baseline is not None and current != baseline:
                logging.debug("Caps Lock toggled by the trigger; "
                              "tapping it back.")
                _tapCapsLock()
        return GLib.SOURCE_REMOVE

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _mouseEventsEnabled(self):
        return self.__mouseEventsEnabled

    def enableMouseEvents(self, isEnabled):
        self.__mouseEventsEnabled = isEnabled

    def getQuasimodeKeycode(self, quasimodeKeycode):
        return self.__qmKeycodes[quasimodeKeycode]

    def setQuasimodeKeycode(self, quasimodeKeycode, keycode):
        self.__qmKeycodes[quasimodeKeycode] = keycode
        if quasimodeKeycode == KEYCODE_QUASIMODE_START and self.__listener:
            self.__listener.trigger_keycode = self.__triggerKeycode()
            if self.__triggerKeycode() == KEYCODE_CAPITAL:
                xkb.disable_caps_lock()

    def setModality(self, isModal):
        self.__isModal = bool(isModal)

    def getModality(self):
        return self.__isModal

    def setCapsLockMode(self, capsLockEnabled):
        if capsLockEnabled:
            xkb.enable_caps_lock()
        else:
            xkb.disable_caps_lock()

    def leaveQuasimode(self):
        if self.__listener:
            self.__listener.leave_quasimode()

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
