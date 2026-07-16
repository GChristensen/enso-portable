"""
KDE Wayland implementation of the Enso "input" provider.

Wayland offers no global key grabs, so the quasimode is composed from
two mechanisms:

  * The trigger key (Caps Lock) is watched on the raw evdev devices in
    a companion thread (python-evdev), which is the only way to see
    both the press and the release of an arbitrary key regardless of
    window focus.  This requires read access to /dev/input/event*,
    i.e. membership in the 'input' group.

  * While the quasimode is active, an invisible 1x1 layer-shell
    surface (the "key sink") takes *exclusive* keyboard focus, so the
    compositor routes every keystroke to Enso as ordinary GTK key
    events -- and away from the application below, exactly like the
    active X grab did.  The sink stays mapped the whole session (only
    its keyboard mode is toggled) so entering the quasimode costs a
    single compositor round-trip.

GTK's hardware keycodes are X-style keycodes (evdev code + 8) under
both backends, so Enso core's keycode conventions carry over
unchanged.  The Caps Lock toggle action is suppressed session-wide via
the caps:none XKB option (see kwayland.xkb).
"""

import logging
import os
import select
import signal
import threading
import time
import traceback

import cairo

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

from enso.platform.linux.kwayland import layershell, utils, xkb
from enso.platform.linux.kwayland.layershell import GtkLayerShell

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

# Lazily created uinput keyboard used only to undo a Caps Lock toggle;
# it bears UINPUT_DEVICE_NAME, so the evdev listener ignores it.
_corrective_uinput = None


def _tapCapsLock():
    global _corrective_uinput
    try:
        if _corrective_uinput is None:
            _corrective_uinput = evdev.UInput(
                {ecodes.EV_KEY: [ecodes.KEY_CAPSLOCK]},
                name=utils.UINPUT_DEVICE_NAME)
            time.sleep(0.2)  # let the compositor pick the device up
        for value in (1, 0):
            _corrective_uinput.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK,
                                     value)
            _corrective_uinput.syn()
    except Exception:
        logging.exception("Couldn't tap Caps Lock to undo its toggle.")


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
    """Thread that watches the raw input devices for the quasimode
    trigger key, shift state, and (when enabled) mouse activity.
    Results are marshalled onto the GTK main thread."""

    def __init__(self, parent):
        threading.Thread.__init__(self, daemon=True)
        self.__parent = parent
        self.__terminate = False
        self.__wakeup_r, self.__wakeup_w = os.pipe()
        self.__devices = {}          # fd -> InputDevice
        self.__shiftDown = set()     # evdev codes of held shift keys
        self.__lastScan = 0.0
        self.__lastMouseMove = 0.0
        self.__permissionWarned = False
        # Written from the main thread, read here; a plain attribute is
        # enough for a single int under the GIL.
        self.trigger_keycode = KEYCODE_CAPITAL

    # ------------------------------------------------------------------
    # Requests from other threads
    # ------------------------------------------------------------------

    def stop(self):
        self.__terminate = True
        os.write(self.__wakeup_w, b"x")

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
            for device in self.__devices.values():
                try:
                    device.close()
                except Exception:
                    pass

    def __scanDevices(self):
        self.__lastScan = time.monotonic()
        known = set(d.path for d in self.__devices.values())
        found_keyboard = False
        denied = 0
        for path in evdev.list_devices():
            try:
                if path in known:
                    found_keyboard = True
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
                    found_keyboard = found_keyboard or is_keyboard
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
            self.__lastScan = 0.0

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
        if keycode == self.trigger_keycode:
            if event.value == 1:
                self.__post(self.__parent._onTriggerDown)
            elif event.value == 0:
                self.__post(self.__parent._onTriggerUp)
        elif event.value == 1:
            self.__post(self.__parent._onSomeKey)

    def __onMouseActivity(self, moved):
        if not self.__parent._mouseEventsEnabled():
            return
        if moved:
            now = time.monotonic()
            if now - self.__lastMouseMove < _MOUSE_MOVE_THROTTLE:
                return
            self.__lastMouseMove = now
            self.__post(self.__parent._onMouseMoved)
        else:
            self.__post(self.__parent._onMouseButton)

    def __post(self, callback):
        GLib.idle_add(self.__safeCall, callback)

    @staticmethod
    def __safeCall(callback):
        try:
            callback()
        except Exception:
            logging.error("Exception in input event handler:\n%s"
                          % traceback.format_exc())
        return GLib.SOURCE_REMOVE


class _KeySink(Gtk.Window):
    """Invisible 1x1 layer-shell surface that takes exclusive keyboard
    focus while the quasimode is active, delivering the captured
    keystrokes as GTK key events."""

    def __init__(self, manager):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self.__manager = manager
        visual = self.get_screen().get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)
        # GDK's Wayland backend never commits a frame for a childless
        # (or app-paintable) toplevel, and an uncommitted layer surface
        # is not mapped and cannot take keyboard focus; a 1x1
        # transparent DrawingArea child makes the surface real.
        area = Gtk.DrawingArea()
        area.set_size_request(1, 1)
        area.connect("draw", self.__onDraw)
        self.add(area)
        layershell.init_layer_window(self, "enso-keysink")
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.NONE)
        self.connect("realize", self.__onRealize)
        self.connect("key-press-event", self.__onKeyPress)
        self.connect("key-release-event", self.__onKeyRelease)
        self.show_all()

    def __onRealize(self, widget):
        # Never take mouse input.
        self.input_shape_combine_region(cairo.Region())

    def __onDraw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        return False

    def grab_keyboard(self):
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

    def ungrab_keyboard(self):
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.NONE)

    def __onKeyPress(self, widget, event):
        self.__manager._onSinkKey(EVENT_KEY_DOWN, event.hardware_keycode)
        return True

    def __onKeyRelease(self, widget, event):
        self.__manager._onSinkKey(EVENT_KEY_UP, event.hardware_keycode)
        return True


class InputManager(object):
    """Input event manager: owns the GTK main loop, the key sink and
    the evdev listener.  Enso's EventManager subclasses this and
    overrides the on* hooks."""

    def __init__(self):
        self.__mouseEventsEnabled = False
        self.__qmKeycodes = [KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE]
        self.__isModal = False
        self.__inQuasimode = False
        self.__currentlyModal = False
        self.__capsBaseline = None
        self.__listener = None
        self.__keySink = None
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

        self.__keySink = _KeySink(self)

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
            self.__endQuasimode()
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
    # Quasimode state machine (all on the GTK main thread)
    # ------------------------------------------------------------------

    def __triggerKeycode(self):
        return self.__qmKeycodes[KEYCODE_QUASIMODE_START] or KEYCODE_CAPITAL

    def _onTriggerDown(self):
        if self.__inQuasimode:
            return
        self.__inQuasimode = True
        self.__currentlyModal = self.__isModal
        # The Caps Lock state the user actually wants, read before
        # KWin's LED update for this press can land; used to detect and
        # undo a toggle when the caps:none suppression is not in effect
        # (non-KDE compositor, kwriteconfig missing, ...).
        if self.__triggerKeycode() == KEYCODE_CAPITAL and self.__listener:
            self.__capsBaseline = self.__listener.led_is_on(ecodes.LED_CAPSL)
        else:
            self.__capsBaseline = None
        self.__keySink.grab_keyboard()
        self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_START)

    def _onTriggerUp(self):
        if self.__inQuasimode and not self.__currentlyModal:
            self.__endQuasimode()
            self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)

    def _onSinkKey(self, eventType, keycode):
        if not self.__inQuasimode:
            return
        # The trigger key is owned by the evdev side; its release also
        # shows up here once the sink has keyboard focus.
        if keycode == self.__triggerKeycode():
            return
        if eventType == EVENT_KEY_DOWN and self.__currentlyModal:
            if keycode == self.__qmKeycodes[KEYCODE_QUASIMODE_END]:
                self.__endQuasimode()
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)
                return
            if keycode == self.__qmKeycodes[KEYCODE_QUASIMODE_CANCEL]:
                self.__endQuasimode()
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_CANCEL)
                return
        self.onKeypress(eventType, keycode)

    def __endQuasimode(self):
        if self.__inQuasimode:
            self.__inQuasimode = False
            if self.__keySink:
                self.__keySink.ungrab_keyboard()
            if self.__capsBaseline is not None:
                # Give the compositor time to process the trigger
                # release before checking for Caps Lock drift.
                GLib.timeout_add(250, self.__fixCapsLockDrift)

    def __fixCapsLockDrift(self):
        """Safety net: undoes a Caps Lock toggle caused by the trigger.
        With caps:none in effect the trigger cannot toggle the lock and
        this never fires; when the suppression is unavailable, a
        corrective Caps Lock tap from a uinput device (ignored by the
        evdev listener) puts the state back."""
        if self.__capsBaseline is not None and not self.__inQuasimode \
                and self.__listener:
            current = self.__listener.led_is_on(ecodes.LED_CAPSL)
            if current != self.__capsBaseline:
                logging.debug("Caps Lock toggled by the trigger; "
                              "tapping it back.")
                _tapCapsLock()
        return GLib.SOURCE_REMOVE

    def _onSomeKey(self):
        if not self.__inQuasimode and self.__mouseEventsEnabled:
            self.onSomeKey()

    # ------------------------------------------------------------------
    # Mouse activity (position is not observable on Wayland; motion is
    # reported with a sentinel position, which is enough for the
    # dismiss-on-activity behavior the core uses it for)
    # ------------------------------------------------------------------

    def _mouseEventsEnabled(self):
        return self.__mouseEventsEnabled

    def _onMouseMoved(self):
        if self.__mouseEventsEnabled:
            self.onMouseMove(-1, -1)

    def _onMouseButton(self):
        if self.__mouseEventsEnabled:
            self.onSomeMouseButton()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

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
        """Abandons the current capture; used when Enso core refuses to
        enter the quasimode."""
        if self.__inQuasimode:
            self.__endQuasimode()
            self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)

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
