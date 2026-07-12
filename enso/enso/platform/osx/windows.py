"""
Application enumeration and activation for the macOS port, used by the
'go' command (app-level only), plus Accessibility-based manipulation of
the frontmost window, used by the window commands.
"""

import AppKit

# The AXUIElement API lives in the ApplicationServices bindings, which
# are a separate PyObjC package (pyobjc-framework-ApplicationServices)
# not pulled in by Cocoa/Quartz; the window commands degrade gracefully
# without it, everything else here works regardless.
try:
    import ApplicationServices as _AX
except ImportError:
    _AX = None


def get_windows():
    """Returns a list of (application, label) for the running
    applications with regular activation policy."""
    result = []
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    for app in workspace.runningApplications():
        if app.activationPolicy() != \
                AppKit.NSApplicationActivationPolicyRegular:
            continue
        name = app.localizedName()
        if name:
            result.append((app, str(name).lower()))
    return result


def activate(app):
    """Brings the given application to the foreground."""
    app.activateWithOptions_(
        AppKit.NSApplicationActivateAllWindows
        | AppKit.NSApplicationActivateIgnoringOtherApps)


def ax_available():
    """Whether the Accessibility API can be used: the bindings are
    installed and the process holds the Accessibility permission (the
    same grant Enso's event tap already needs)."""
    return _AX is not None and _AX.AXIsProcessTrusted()


def _ax_attribute(element, attribute):
    err, value = _AX.AXUIElementCopyAttributeValue(element, attribute,
                                                   None)
    if err != _AX.kAXErrorSuccess:
        return None
    return value


def _front_window():
    """Returns the AXUIElement of the frontmost application's focused
    window (falling back to its main window), or None."""
    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if app is None:
        return None
    axApp = _AX.AXUIElementCreateApplication(app.processIdentifier())
    window = _ax_attribute(axApp, _AX.kAXFocusedWindowAttribute)
    if window is None:
        window = _ax_attribute(axApp, _AX.kAXMainWindowAttribute)
    return window


def close_front_window():
    """Presses the close button of the frontmost application's focused
    window -- the exact equivalent of clicking the red titlebar button.
    Returns True if the button was pressed; False if there is no window
    or it has no close button (e.g. a system dialog)."""
    window = _front_window()
    if window is None:
        return False
    button = _ax_attribute(window, _AX.kAXCloseButtonAttribute)
    if button is None:
        return False
    return (_AX.AXUIElementPerformAction(button, _AX.kAXPressAction)
            == _AX.kAXErrorSuccess)
