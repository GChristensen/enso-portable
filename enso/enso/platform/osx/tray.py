"""
Menu-bar icon for the macOS port (NSStatusItem).

The "Start at login" item toggles the same LaunchAgent that
install_macos.sh --autostart registers.
"""

import logging
import os
import plistlib
import subprocess
import sys

import AppKit
import Foundation

from enso import tray_actions

_LAUNCH_AGENT_LABEL = "com.ensoos.enso"
_LAUNCH_AGENT_PLIST = os.path.expanduser(
    "~/Library/LaunchAgents/%s.plist" % _LAUNCH_AGENT_LABEL)

# ObjC will not keep the Python-side delegate or status item alive for
# us; dropped references mean a silently dead menu.
_statusItem = None
_delegate = None


def _autostart_enabled():
    return os.path.isfile(_LAUNCH_AGENT_PLIST)


def _launchctl(*args):
    try:
        subprocess.run(["launchctl"] + list(args), capture_output=True)
    except OSError:
        logging.exception("launchctl invocation failed")


def _set_autostart(enabled):
    domain = "gui/%d" % os.getuid()
    if enabled:
        os.makedirs(os.path.dirname(_LAUNCH_AGENT_PLIST), exist_ok=True)
        with open(_LAUNCH_AGENT_PLIST, "wb") as f:
            plistlib.dump({
                "Label": _LAUNCH_AGENT_LABEL,
                "ProgramArguments": [sys.executable,
                                     tray_actions.get_launcher_path()],
                "RunAtLoad": True,
                "StandardErrorPath": "/tmp/enso.err.log",
            }, f)
        _launchctl("bootstrap", domain, _LAUNCH_AGENT_PLIST)
    elif os.path.isfile(_LAUNCH_AGENT_PLIST):
        _launchctl("bootout", domain, _LAUNCH_AGENT_PLIST)
        os.remove(_LAUNCH_AGENT_PLIST)


class _MenuDelegate(Foundation.NSObject):

    def onAbout_(self, sender):
        tray_actions.show_about()

    def onRestart_(self, sender):
        tray_actions.restart_enso()

    def onSettings_(self, sender):
        tray_actions.open_settings()

    def onAutostart_(self, sender):
        enable = not _autostart_enabled()
        _set_autostart(enable)
        # Re-read the state instead of assuming the toggle succeeded.
        sender.setState_(AppKit.NSControlStateValueOn
                         if _autostart_enabled()
                         else AppKit.NSControlStateValueOff)

    def onQuit_(self, sender):
        tray_actions.quit_enso()


def _addItem(menu, delegate, title, action, state=None):
    item = (AppKit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(title, action, ""))
    item.setTarget_(delegate)
    if state is not None:
        item.setState_(AppKit.NSControlStateValueOn if state
                       else AppKit.NSControlStateValueOff)
    menu.addItem_(item)
    return item


def install(enso_config):
    """Creates the menu-bar icon."""
    global _statusItem, _delegate

    _delegate = _MenuDelegate.alloc().init()

    menu = AppKit.NSMenu.alloc().init()
    menu.setAutoenablesItems_(False)

    _addItem(menu, _delegate, "About Enso", "onAbout:")
    _addItem(menu, _delegate, "Restart", "onRestart:")
    if tray_actions.settings_available():
        _addItem(menu, _delegate, "Settings...", "onSettings:")
    _addItem(menu, _delegate, "Start at login", "onAutostart:",
             state=_autostart_enabled())
    menu.addItem_(AppKit.NSMenuItem.separatorItem())
    _addItem(menu, _delegate, "Quit Enso", "onQuit:")

    _statusItem = (AppKit.NSStatusBar.systemStatusBar()
                   .statusItemWithLength_(
                       AppKit.NSVariableStatusItemLength))

    image = AppKit.NSImage.alloc().initWithContentsOfFile_(
        tray_actions.get_icon_path())
    if image is not None:
        image.setSize_(Foundation.NSMakeSize(18, 18))
        _statusItem.button().setImage_(image)
    else:
        logging.warning("Couldn't load the tray icon image; "
                        "using a text title instead.")
        _statusItem.button().setTitle_("Enso")

    _statusItem.setMenu_(menu)


def uninstall():
    global _statusItem, _delegate
    if _statusItem is not None:
        AppKit.NSStatusBar.systemStatusBar().removeStatusItem_(_statusItem)
        _statusItem = None
    _delegate = None
