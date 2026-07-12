"""
Application enumeration and activation for the macOS port, used by the
'go' command.  App-level only (no per-window switching, which would
require the Accessibility AX API).
"""

import AppKit


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
