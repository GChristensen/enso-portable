# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.2
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _TransparentWindow
else:
    import _TransparentWindow

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

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


BITS_PER_PIXEL = _TransparentWindow.BITS_PER_PIXEL
BYTES_PER_PIXEL = _TransparentWindow.BYTES_PER_PIXEL
MAX_OPACITY = _TransparentWindow.MAX_OPACITY
class TransparentWindowError(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, what):
        _TransparentWindow.TransparentWindowError_swiginit(self, _TransparentWindow.new_TransparentWindowError(what))

    def what(self):
        return _TransparentWindow.TransparentWindowError_what(self)
    __swig_destroy__ = _TransparentWindow.delete_TransparentWindowError

# Register TransparentWindowError in _TransparentWindow:
_TransparentWindow.TransparentWindowError_swigregister(TransparentWindowError)

class FatalError(TransparentWindowError):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, what):
        _TransparentWindow.FatalError_swiginit(self, _TransparentWindow.new_FatalError(what))
    __swig_destroy__ = _TransparentWindow.delete_FatalError

# Register FatalError in _TransparentWindow:
_TransparentWindow.FatalError_swigregister(FatalError)

class RangeError(TransparentWindowError):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, what):
        _TransparentWindow.RangeError_swiginit(self, _TransparentWindow.new_RangeError(what))
    __swig_destroy__ = _TransparentWindow.delete_RangeError

# Register RangeError in _TransparentWindow:
_TransparentWindow.RangeError_swigregister(RangeError)

class TransparentWindow(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, x, y, maxWidth, maxHeight):
        _TransparentWindow.TransparentWindow_swiginit(self, _TransparentWindow.new_TransparentWindow(x, y, maxWidth, maxHeight))
    __swig_destroy__ = _TransparentWindow.delete_TransparentWindow

    def update(self):
        return _TransparentWindow.TransparentWindow_update(self)

    def setOpacity(self, opacity):
        return _TransparentWindow.TransparentWindow_setOpacity(self, opacity)

    def getOpacity(self):
        return _TransparentWindow.TransparentWindow_getOpacity(self)

    def setPosition(self, x, y):
        return _TransparentWindow.TransparentWindow_setPosition(self, x, y)

    def getX(self):
        return _TransparentWindow.TransparentWindow_getX(self)

    def getY(self):
        return _TransparentWindow.TransparentWindow_getY(self)

    def setSize(self, width, height):
        return _TransparentWindow.TransparentWindow_setSize(self, width, height)

    def getWidth(self):
        return _TransparentWindow.TransparentWindow_getWidth(self)

    def getHeight(self):
        return _TransparentWindow.TransparentWindow_getHeight(self)

    def getMaxWidth(self):
        return _TransparentWindow.TransparentWindow_getMaxWidth(self)

    def getMaxHeight(self):
        return _TransparentWindow.TransparentWindow_getMaxHeight(self)

    def getHandle(self):
        return _TransparentWindow.TransparentWindow_getHandle(self)

    def setForeground(self):
        return _TransparentWindow.TransparentWindow_setForeground(self)

    def makeCairoSurface(self):
        return _TransparentWindow.TransparentWindow_makeCairoSurface(self)

# Register TransparentWindow in _TransparentWindow:
_TransparentWindow.TransparentWindow_swigregister(TransparentWindow)


def _getDesktopSize():
    return _TransparentWindow._getDesktopSize()

def _getDesktopOffset():
    return _TransparentWindow._getDesktopOffset()


