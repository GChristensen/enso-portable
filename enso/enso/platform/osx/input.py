"""
Quartz/Cocoa implementation of the Enso "input" provider.

Based on the original Enso OS X port:
Copyright (c) 2008, Humanized, Inc.
Rewritten for Python 3 / modern PyObjC.  The external EnsoKeyNotifier
helper of the legacy port is replaced with an in-process CGEventTap
installed on the main run loop, so everything runs on the main thread
(Enso core is not thread-safe).

The event tap needs the "Input Monitoring" permission (System Settings
-> Privacy & Security); without it CGEventTapCreate returns None.
"""

import ctypes
import logging
import signal
import time
import traceback

import objc
import AppKit
import Foundation
import Quartz

from PyObjCTools import AppHelper

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

# Mac virtual keycodes (Carbon kVK_* values) for the keys Enso core
# refers to by name.
KEYCODE_CAPITAL = 57
KEYCODE_RETURN = 36
KEYCODE_ESCAPE = 53
KEYCODE_TAB = 48
KEYCODE_BACK = 51
KEYCODE_UP = 126
KEYCODE_DOWN = 125
KEYCODE_SPACE = 49
KEYCODE_LSHIFT = 56
KEYCODE_RSHIFT = 60
KEYCODE_SHIFT = KEYCODE_LSHIFT
# Macs have no NumLock; kVK_ANSI_KeypadClear stands in so the constant
# exists (getKeyState always reports it off).
KEYCODE_NUMLOCK = 71

_SPECIAL_KEYCODES = frozenset((
    KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE, KEYCODE_TAB,
    KEYCODE_BACK, KEYCODE_UP, KEYCODE_DOWN, KEYCODE_NUMLOCK,
))

# Maps mac virtual keycodes to the characters they produce with the
# current keyboard layout, with the shifted character of a keycode
# stored at keycode + 1000 (the same convention the win32 CharMaps
# module uses).  Shifted letters are deliberately absent so that
# command names stay case-insensitive.
CASE_INSENSITIVE_KEYCODE_MAP = {}


def _keycodeToChar(keycode, shifted):
    """Returns the character the given keycode produces under the
    current layout, using a throwaway CGEvent (no Carbon/UCKeyTranslate
    needed; creating events requires no special permissions)."""
    event = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    Quartz.CGEventSetFlags(
        event, Quartz.kCGEventFlagMaskShift if shifted else 0)
    _, chars = Quartz.CGEventKeyboardGetUnicodeString(event, 4, None, None)
    if chars and len(chars) == 1 and chars.isprintable():
        return chars
    return None


def _fillKeymap():
    for keycode in range(0, 128):
        if keycode in _SPECIAL_KEYCODES:
            continue
        char = _keycodeToChar(keycode, shifted=False)
        if char:
            CASE_INSENSITIVE_KEYCODE_MAP[keycode] = char
            shifted = _keycodeToChar(keycode, shifted=True)
            if shifted and shifted.lower() != char.lower():
                CASE_INSENSITIVE_KEYCODE_MAP[keycode + 1000] = shifted
    CASE_INSENSITIVE_KEYCODE_MAP[KEYCODE_SPACE] = " "


_fillKeymap()

_COMBINED_STATE = Quartz.kCGEventSourceStateCombinedSessionState

# IOKit/hidsystem constants (IOHIDShared.h / IOHIDParameter.h).
_KIOHID_PARAM_CONNECT_TYPE = 1   # kIOHIDParamConnectType
_KIOHID_CAPS_LOCK_STATE = 1      # kIOHIDCapsLockState


class _CapsLockToggle(object):
    """Undoes the system caps-lock toggle.

    The event tap consumes the trigger key's events so applications
    never see them, but the caps-lock toggle engages in the HID driver
    *upstream* of a session tap: after an odd number of trigger
    presses the system is left typing ALL CAPS.  A tap cannot prevent
    that, so the toggle is explicitly cleared through the IOHIDSystem
    'param' connection instead (the same IOHIDSetModifierLockState
    call the caps-lock utilities use; no special permission needed)."""

    def __init__(self):
        self.__iokit = None
        self.__connect = None
        try:
            iokit = ctypes.CDLL(
                "/System/Library/Frameworks/IOKit.framework/IOKit")
            iokit.IOServiceMatching.restype = ctypes.c_void_p
            iokit.IOServiceMatching.argtypes = (ctypes.c_char_p,)
            # io_service_t/io_connect_t are mach ports: 32-bit even on
            # 64-bit systems.
            iokit.IOServiceGetMatchingService.restype = ctypes.c_uint32
            iokit.IOServiceGetMatchingService.argtypes = (
                ctypes.c_uint32, ctypes.c_void_p)
            iokit.IOServiceOpen.restype = ctypes.c_int
            iokit.IOServiceOpen.argtypes = (
                ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32))
            iokit.IOObjectRelease.argtypes = (ctypes.c_uint32,)
            iokit.IOHIDSetModifierLockState.restype = ctypes.c_int
            iokit.IOHIDSetModifierLockState.argtypes = (
                ctypes.c_uint32, ctypes.c_int, ctypes.c_bool)

            service = iokit.IOServiceGetMatchingService(
                0, iokit.IOServiceMatching(b"IOHIDSystem"))
            if not service:
                raise OSError("no IOHIDSystem service")
            connect = ctypes.c_uint32(0)
            libc = ctypes.CDLL(None)
            task = ctypes.c_uint32.in_dll(libc, "mach_task_self_").value
            err = iokit.IOServiceOpen(service, task,
                                      _KIOHID_PARAM_CONNECT_TYPE,
                                      ctypes.byref(connect))
            iokit.IOObjectRelease(service)
            if err != 0:
                raise OSError("IOServiceOpen failed (%#x)" % err)
            self.__iokit = iokit
            self.__connect = connect.value
        except Exception:
            logging.error(
                "Couldn't open the IOHIDSystem connection; the "
                "caps-lock toggle can't be suppressed, so letter case "
                "will flip on every trigger press:\n%s"
                % traceback.format_exc())

    def clear(self):
        if self.__connect is None:
            return
        err = self.__iokit.IOHIDSetModifierLockState(
            self.__connect, _KIOHID_CAPS_LOCK_STATE, False)
        if err != 0:
            logging.warning("IOHIDSetModifierLockState failed (%#x)", err)


def getKeyState(keyCode):
    """Queries the current keyboard state, with win32 GetKeyState()
    semantics: negative means held down, low bit means toggled on."""
    flags = Quartz.CGEventSourceFlagsState(_COMBINED_STATE)
    if keyCode in (KEYCODE_SHIFT, KEYCODE_LSHIFT, KEYCODE_RSHIFT):
        return -128 if flags & Quartz.kCGEventFlagMaskShift else 0
    if keyCode == KEYCODE_CAPITAL:
        return 1 if flags & Quartz.kCGEventFlagMaskAlphaShift else 0
    return 0


class _Timer(Foundation.NSObject):

    def initWithCallback_(self, callback):
        self = objc.super(_Timer, self).init()
        if self is None:
            return None
        self.__callback = callback
        return self

    def onTimer_(self, timer):
        self.__callback()


class InputManager(object):
    """Input event manager: owns the Cocoa main loop and the event tap.
    Enso's EventManager subclasses this and overrides the on* hooks."""

    def __init__(self):
        self.__mouseEventsEnabled = False
        self.__qmKeycodes = [KEYCODE_CAPITAL, KEYCODE_RETURN, KEYCODE_ESCAPE]
        self.__isModal = False
        self.__capturing = False
        self.__currentlyModal = False
        self.__tap = None
        self.__lastMousePos = None
        self.__lastMouseButtons = 0
        self.__capsToggle = _CapsLockToggle()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        logging.info("Entering InputManager.run()")

        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory)

        self.__checkPermissions()

        mask = (Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
                | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
                | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged))
        self.__tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            mask,
            self.__onTapEvent,
            None)
        if self.__tap is None:
            logging.critical(
                "Couldn't create the keyboard event tap.  Grant this "
                "python binary both 'Accessibility' and 'Input "
                "Monitoring' in System Settings -> Privacy & Security, "
                "then restart Enso.")
            return
        source = Quartz.CFMachPortCreateRunLoopSource(None, self.__tap, 0)
        Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), source,
                                  Quartz.kCFRunLoopCommonModes)
        Quartz.CGEventTapEnable(self.__tap, True)

        # Start from a known caps state (it may have been left on by a
        # press made before Enso started, or by a previous crash).
        if self.getQuasimodeKeycode(KEYCODE_QUASIMODE_START) \
                == KEYCODE_CAPITAL:
            self.__capsToggle.clear()

        timerTarget = _Timer.alloc().initWithCallback_(self.__onTimer)
        timer = (Foundation.NSTimer
                 .scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                     TICK_INTERVAL_MS / 1000.0, timerTarget, "onTimer:",
                     None, True))
        # Keep ticking while menus/drags run their own run-loop modes.
        Foundation.NSRunLoop.currentRunLoop().addTimer_forMode_(
            timer, AppKit.NSEventTrackingRunLoopMode)

        # The 10 ms timer wakes the interpreter often enough for Python
        # signal handlers to run despite the ObjC main loop.
        signal.signal(signal.SIGINT, lambda signum, frame: self.stop())

        try:
            self.onInit()
            app.run()
        finally:
            timer.invalidate()
            if self.__tap is not None:
                Quartz.CGEventTapEnable(self.__tap, False)
                self.__tap = None

        logging.info("Exiting InputManager.run()")

    def stop(self):
        AppHelper.callAfter(AppHelper.stopEventLoop)

    def __checkPermissions(self):
        try:
            if not Quartz.CGPreflightListenEventAccess():
                Quartz.CGRequestListenEventAccess()
                logging.error(
                    "Input Monitoring permission is not granted; the "
                    "system permission prompt was requested.  Grant it "
                    "in System Settings -> Privacy & Security -> Input "
                    "Monitoring and restart Enso.")
        except AttributeError:
            # CGPreflightListenEventAccess needs macOS 10.15+.
            pass

    def __onTimer(self):
        # A tick handler exception must not kill the timer.
        try:
            if self.__mouseEventsEnabled:
                self.__pollMouse()
            self.onTick(TICK_INTERVAL_MS)
        except Exception:
            logging.error("Exception in timer event handler:\n%s"
                          % traceback.format_exc())

    def __pollMouse(self):
        # macOS has no reason to tap mouse events just for dismissal;
        # poll on the same tick that already drives onTick(), exactly
        # like the X11 implementation.
        location = AppKit.NSEvent.mouseLocation()
        # Convert Cocoa bottom-left global coords to the top-left
        # convention the other platforms report.
        mainHeight = AppKit.NSScreen.screens()[0].frame().size.height
        pos = (location.x, mainHeight - location.y)
        buttons = sum(
            Quartz.CGEventSourceButtonState(_COMBINED_STATE, button)
            for button in range(3))
        if self.__lastMousePos is not None and pos != self.__lastMousePos:
            self.onMouseMove(pos[0], pos[1])
        self.__lastMousePos = pos
        if buttons and not self.__lastMouseButtons:
            self.onSomeMouseButton()
        self.__lastMouseButtons = buttons

    # ------------------------------------------------------------------
    # Event tap
    # ------------------------------------------------------------------

    def __onTapEvent(self, proxy, eventType, event, refcon):
        try:
            return self.__handleTapEvent(eventType, event)
        except Exception:
            logging.error("Exception in event tap callback:\n%s"
                          % traceback.format_exc())
            return event

    def __handleTapEvent(self, eventType, event):
        """Returning None consumes the event (the focused application
        never sees it); returning the event passes it through."""
        if eventType in (Quartz.kCGEventTapDisabledByTimeout,
                         Quartz.kCGEventTapDisabledByUserInput):
            # macOS disables taps it deems too slow; recover.  Any key
            # pressed between the disable and this re-enable was lost,
            # so this matters when diagnosing missed trigger presses.
            logging.warning(
                "The keyboard event tap was disabled by macOS (%s); "
                "re-enabling it.  Keys pressed meanwhile were missed.",
                "timeout" if eventType == Quartz.kCGEventTapDisabledByTimeout
                else "user input")
            if self.__tap is not None:
                Quartz.CGEventTapEnable(self.__tap, True)
            return None

        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode)
        trigger = self.getQuasimodeKeycode(KEYCODE_QUASIMODE_START)

        if eventType == Quartz.kCGEventFlagsChanged:
            if keycode != trigger:
                return event
            # The trigger is a modifier-type key (CapsLock by default).
            # Consuming its events hides them from applications, but
            # the caps-lock toggle has already engaged in the HID
            # driver by the time the tap runs; undo it before it can
            # affect typing.
            if trigger == KEYCODE_CAPITAL:
                self.__capsToggle.clear()
            # CapsLock is a toggling modifier: macOS delivers a single
            # flagsChanged per physical press and nothing on release,
            # and CGEventSourceKeyState (from the session and the HID
            # source alike) reports the caps toggle state rather than
            # the physical key, so consulting it here swallowed every
            # other press.  An event for the trigger keycode therefore
            # simply means "the trigger was pressed".
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(
                    "Trigger flagsChanged: eventFlags=%#x capturing=%s "
                    "modal=%s",
                    Quartz.CGEventGetFlags(event),
                    self.__capturing, self.__currentlyModal)
            if not self.__capturing:
                self.__beginCapture()
            elif not self.__currentlyModal:
                # With no release events to end on, the non-modal
                # quasimode ends on the next trigger press instead of
                # on release (should a keyboard send a release
                # flagsChanged after all, it ends the capture here the
                # same way).
                self.__endCapture("quasimodeEnd")
            return None

        if eventType == Quartz.kCGEventKeyDown:
            if not self.__capturing:
                if keycode == trigger:
                    self.__beginCapture()
                    return None
                self.__postEvent("someKey")
                return event
            if self.__currentlyModal and keycode == \
                    self.getQuasimodeKeycode(KEYCODE_QUASIMODE_END):
                self.__endCapture("quasimodeEnd")
            elif self.__currentlyModal and keycode == \
                    self.getQuasimodeKeycode(KEYCODE_QUASIMODE_CANCEL):
                self.__endCapture("quasimodeCancel")
            elif keycode != trigger:
                self.__postEvent("keyDown", keycode)
            return None

        if eventType == Quartz.kCGEventKeyUp:
            if not self.__capturing:
                return event
            if keycode == trigger:
                if not self.__currentlyModal:
                    self.__endCapture("quasimodeEnd")
            else:
                self.__postEvent("keyUp", keycode)
            return None

        return event

    def __beginCapture(self):
        logging.debug("Quasimode capture begins (modal=%s)", self.__isModal)
        self.__capturing = True
        self.__currentlyModal = self.__isModal
        self.__postEvent("quasimodeStart")

    def __endCapture(self, eventName):
        logging.debug("Quasimode capture ends (%s)", eventName)
        self.__capturing = False
        self.__postEvent(eventName)

    def __postEvent(self, eventName, keycode=None):
        # Deliver outside the tap callback: core handlers redraw the
        # overlay, which is far too slow for a tap callback (macOS
        # disables taps that stall the event stream).
        AppHelper.callAfter(self._dispatchKeyEvent,
                            {"event": eventName, "keycode": keycode,
                             "posted": time.monotonic()})

    def _dispatchKeyEvent(self, info):
        """Delivers a tap event from the run loop, outside the tap."""
        try:
            event = info["event"]
            if event.startswith("quasimode"):
                # A long tap-to-dispatch delay means the run loop is
                # busy (slow overlay redraws), which is also what gets
                # the tap disabled by timeout.
                logging.debug("Dispatching %s (tap-to-dispatch %.1f ms)",
                              event,
                              (time.monotonic() - info["posted"]) * 1000)
            if event == "quasimodeStart":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_START)
            elif event == "quasimodeEnd":
                self.onKeypress(EVENT_KEY_QUASIMODE, KEYCODE_QUASIMODE_END)
            elif event == "quasimodeCancel":
                self.onKeypress(EVENT_KEY_QUASIMODE,
                                KEYCODE_QUASIMODE_CANCEL)
            elif event == "keyDown":
                self.onKeypress(EVENT_KEY_DOWN, info["keycode"])
            elif event == "keyUp":
                self.onKeypress(EVENT_KEY_UP, info["keycode"])
            elif event == "someKey":
                self.onSomeKey()
            else:
                logging.warning("Don't know what to do with event: %s"
                                % info)
        except Exception:
            logging.error("Exception in key event handler:\n%s"
                          % traceback.format_exc())

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
        # No grab to re-establish, unlike X11: the tap sees every key,
        # so a changed trigger takes effect immediately.
        self.__qmKeycodes[quasimodeKeycode] = keycode

    def setModality(self, isModal):
        self.__isModal = bool(isModal)

    def getModality(self):
        return self.__isModal

    def setCapsLockMode(self, capsLockEnabled):
        # Nothing to do: while CapsLock is the trigger, its toggle is
        # cleared on every press in the tap handler.
        pass

    def leaveQuasimode(self):
        if self.__capturing:
            self.__endCapture("quasimodeEnd")

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
