# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.2
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _InputManager
else:
    import _InputManager

import builtins as __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


import weakref

MESSAGE_WINDOW_CLASS_NAME = _InputManager.MESSAGE_WINDOW_CLASS_NAME
class InputManager(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self):
        if self.__class__ == InputManager:
            _self = None
        else:
            _self = self
        _InputManager.InputManager_swiginit(self, _InputManager.new_InputManager(_self, ))
    __swig_destroy__ = _InputManager.delete_InputManager

    def run(self):
        return _InputManager.InputManager_run(self)

    def stop(self):
        return _InputManager.InputManager_stop(self)

    def enableMouseEvents(self, enabled):
        return _InputManager.InputManager_enableMouseEvents(self, enabled)

    def onKeypress(self, eventType, vkCode):
        return _InputManager.InputManager_onKeypress(self, eventType, vkCode)

    def onSomeKey(self):
        return _InputManager.InputManager_onSomeKey(self)

    def onSomeMouseButton(self):
        return _InputManager.InputManager_onSomeMouseButton(self)

    def onExitRequested(self):
        return _InputManager.InputManager_onExitRequested(self)

    def onMouseMove(self, x, y):
        return _InputManager.InputManager_onMouseMove(self, x, y)

    def getQuasimodeKeycode(self, quasimodeKeycode):
        return _InputManager.InputManager_getQuasimodeKeycode(self, quasimodeKeycode)

    def setQuasimodeKeycode(self, quasimodeKeycode, keycode):
        return _InputManager.InputManager_setQuasimodeKeycode(self, quasimodeKeycode, keycode)

    def setModality(self, arg2):
        return _InputManager.InputManager_setModality(self, arg2)

    def setCapsLockMode(self, mode):
        return _InputManager.InputManager_setCapsLockMode(self, mode)

    def onTick(self, msPassed):
        return _InputManager.InputManager_onTick(self, msPassed)

    def onInit(self):
        return _InputManager.InputManager_onInit(self)

    def leaveQuasimode(self):
        print("leaving")
        return _InputManager.InputManager_leaveQuasimode(self)
    def __disown__(self):
        self.this.disown()
        _InputManager.disown_InputManager(self)
        return weakref.proxy(self)

# Register InputManager in _InputManager:
_InputManager.InputManager_swigregister(InputManager)

EVENT_KEY_UP = _InputManager.EVENT_KEY_UP
EVENT_KEY_DOWN = _InputManager.EVENT_KEY_DOWN
EVENT_KEY_QUASIMODE = _InputManager.EVENT_KEY_QUASIMODE
KEYCODE_QUASIMODE_START = _InputManager.KEYCODE_QUASIMODE_START
KEYCODE_QUASIMODE_END = _InputManager.KEYCODE_QUASIMODE_END
KEYCODE_QUASIMODE_CANCEL = _InputManager.KEYCODE_QUASIMODE_CANCEL
KEYCODE_LBUTTON = _InputManager.KEYCODE_LBUTTON
KEYCODE_RBUTTON = _InputManager.KEYCODE_RBUTTON
KEYCODE_CANCEL = _InputManager.KEYCODE_CANCEL
KEYCODE_MBUTTON = _InputManager.KEYCODE_MBUTTON
KEYCODE_BACK = _InputManager.KEYCODE_BACK
KEYCODE_TAB = _InputManager.KEYCODE_TAB
KEYCODE_CLEAR = _InputManager.KEYCODE_CLEAR
KEYCODE_RETURN = _InputManager.KEYCODE_RETURN
KEYCODE_SHIFT = _InputManager.KEYCODE_SHIFT
KEYCODE_CONTROL = _InputManager.KEYCODE_CONTROL
KEYCODE_MENU = _InputManager.KEYCODE_MENU
KEYCODE_PAUSE = _InputManager.KEYCODE_PAUSE
KEYCODE_CAPITAL = _InputManager.KEYCODE_CAPITAL
KEYCODE_KANA = _InputManager.KEYCODE_KANA
KEYCODE_HANGUL = _InputManager.KEYCODE_HANGUL
KEYCODE_JUNJA = _InputManager.KEYCODE_JUNJA
KEYCODE_FINAL = _InputManager.KEYCODE_FINAL
KEYCODE_HANJA = _InputManager.KEYCODE_HANJA
KEYCODE_KANJI = _InputManager.KEYCODE_KANJI
KEYCODE_ESCAPE = _InputManager.KEYCODE_ESCAPE
KEYCODE_CONVERT = _InputManager.KEYCODE_CONVERT
KEYCODE_NONCONVERT = _InputManager.KEYCODE_NONCONVERT
KEYCODE_ACCEPT = _InputManager.KEYCODE_ACCEPT
KEYCODE_MODECHANGE = _InputManager.KEYCODE_MODECHANGE
KEYCODE_SPACE = _InputManager.KEYCODE_SPACE
KEYCODE_PRIOR = _InputManager.KEYCODE_PRIOR
KEYCODE_NEXT = _InputManager.KEYCODE_NEXT
KEYCODE_END = _InputManager.KEYCODE_END
KEYCODE_HOME = _InputManager.KEYCODE_HOME
KEYCODE_LEFT = _InputManager.KEYCODE_LEFT
KEYCODE_UP = _InputManager.KEYCODE_UP
KEYCODE_RIGHT = _InputManager.KEYCODE_RIGHT
KEYCODE_DOWN = _InputManager.KEYCODE_DOWN
KEYCODE_SELECT = _InputManager.KEYCODE_SELECT
KEYCODE_PRINT = _InputManager.KEYCODE_PRINT
KEYCODE_EXECUTE = _InputManager.KEYCODE_EXECUTE
KEYCODE_SNAPSHOT = _InputManager.KEYCODE_SNAPSHOT
KEYCODE_INSERT = _InputManager.KEYCODE_INSERT
KEYCODE_DELETE = _InputManager.KEYCODE_DELETE
KEYCODE_HELP = _InputManager.KEYCODE_HELP
KEYCODE_LWIN = _InputManager.KEYCODE_LWIN
KEYCODE_RWIN = _InputManager.KEYCODE_RWIN
KEYCODE_APPS = _InputManager.KEYCODE_APPS
KEYCODE_NUMPAD0 = _InputManager.KEYCODE_NUMPAD0
KEYCODE_NUMPAD1 = _InputManager.KEYCODE_NUMPAD1
KEYCODE_NUMPAD2 = _InputManager.KEYCODE_NUMPAD2
KEYCODE_NUMPAD3 = _InputManager.KEYCODE_NUMPAD3
KEYCODE_NUMPAD4 = _InputManager.KEYCODE_NUMPAD4
KEYCODE_NUMPAD5 = _InputManager.KEYCODE_NUMPAD5
KEYCODE_NUMPAD6 = _InputManager.KEYCODE_NUMPAD6
KEYCODE_NUMPAD7 = _InputManager.KEYCODE_NUMPAD7
KEYCODE_NUMPAD8 = _InputManager.KEYCODE_NUMPAD8
KEYCODE_NUMPAD9 = _InputManager.KEYCODE_NUMPAD9
KEYCODE_MULTIPLY = _InputManager.KEYCODE_MULTIPLY
KEYCODE_ADD = _InputManager.KEYCODE_ADD
KEYCODE_SEPARATOR = _InputManager.KEYCODE_SEPARATOR
KEYCODE_SUBTRACT = _InputManager.KEYCODE_SUBTRACT
KEYCODE_DECIMAL = _InputManager.KEYCODE_DECIMAL
KEYCODE_DIVIDE = _InputManager.KEYCODE_DIVIDE
KEYCODE_F1 = _InputManager.KEYCODE_F1
KEYCODE_F2 = _InputManager.KEYCODE_F2
KEYCODE_F3 = _InputManager.KEYCODE_F3
KEYCODE_F4 = _InputManager.KEYCODE_F4
KEYCODE_F5 = _InputManager.KEYCODE_F5
KEYCODE_F6 = _InputManager.KEYCODE_F6
KEYCODE_F7 = _InputManager.KEYCODE_F7
KEYCODE_F8 = _InputManager.KEYCODE_F8
KEYCODE_F9 = _InputManager.KEYCODE_F9
KEYCODE_F10 = _InputManager.KEYCODE_F10
KEYCODE_F11 = _InputManager.KEYCODE_F11
KEYCODE_F12 = _InputManager.KEYCODE_F12
KEYCODE_F13 = _InputManager.KEYCODE_F13
KEYCODE_F14 = _InputManager.KEYCODE_F14
KEYCODE_F15 = _InputManager.KEYCODE_F15
KEYCODE_F16 = _InputManager.KEYCODE_F16
KEYCODE_F17 = _InputManager.KEYCODE_F17
KEYCODE_F18 = _InputManager.KEYCODE_F18
KEYCODE_F19 = _InputManager.KEYCODE_F19
KEYCODE_F20 = _InputManager.KEYCODE_F20
KEYCODE_F21 = _InputManager.KEYCODE_F21
KEYCODE_F22 = _InputManager.KEYCODE_F22
KEYCODE_F23 = _InputManager.KEYCODE_F23
KEYCODE_F24 = _InputManager.KEYCODE_F24
KEYCODE_NUMLOCK = _InputManager.KEYCODE_NUMLOCK
KEYCODE_SCROLL = _InputManager.KEYCODE_SCROLL
KEYCODE_LSHIFT = _InputManager.KEYCODE_LSHIFT
KEYCODE_RSHIFT = _InputManager.KEYCODE_RSHIFT
KEYCODE_LCONTROL = _InputManager.KEYCODE_LCONTROL
KEYCODE_RCONTROL = _InputManager.KEYCODE_RCONTROL
KEYCODE_LMENU = _InputManager.KEYCODE_LMENU
KEYCODE_RMENU = _InputManager.KEYCODE_RMENU
KEYCODE_PROCESSKEY = _InputManager.KEYCODE_PROCESSKEY
KEYCODE_ATTN = _InputManager.KEYCODE_ATTN
KEYCODE_CRSEL = _InputManager.KEYCODE_CRSEL
KEYCODE_EXSEL = _InputManager.KEYCODE_EXSEL
KEYCODE_EREOF = _InputManager.KEYCODE_EREOF
KEYCODE_PLAY = _InputManager.KEYCODE_PLAY
KEYCODE_ZOOM = _InputManager.KEYCODE_ZOOM
KEYCODE_NONAME = _InputManager.KEYCODE_NONAME
KEYCODE_PA1 = _InputManager.KEYCODE_PA1
KEYCODE_OEM_CLEAR = _InputManager.KEYCODE_OEM_CLEAR
TICK_TIMER_INTRVL = _InputManager.TICK_TIMER_INTRVL


