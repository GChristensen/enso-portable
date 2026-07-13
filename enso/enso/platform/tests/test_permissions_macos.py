#!/usr/bin/env python3

# Diagnoses the macOS permission state for Enso's event tap.
# Run it the same way you run Enso (same terminal, same venv python)
# and it reports what TCC actually grants this process.

import os
import sys

import Quartz

print("executable:      ", sys.executable)
print("resolved binary: ", os.path.realpath(sys.executable))

try:
    print("Input Monitoring (CGPreflightListenEventAccess):",
          bool(Quartz.CGPreflightListenEventAccess()))
except AttributeError:
    print("Input Monitoring: preflight API unavailable (macOS < 10.15?)")

try:
    print("Post events      (CGPreflightPostEventAccess):  ",
          bool(Quartz.CGPreflightPostEventAccess()))
except AttributeError:
    print("Post events: preflight API unavailable")

try:
    from ApplicationServices import AXIsProcessTrusted
    print("Accessibility    (AXIsProcessTrusted):          ",
          bool(AXIsProcessTrusted()))
except ImportError:
    print("Accessibility: ApplicationServices not importable "
          "(pip install pyobjc-framework-ApplicationServices)")

mask = (Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged))


def try_tap(name, option):
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap, Quartz.kCGHeadInsertEventTap,
        option, mask, lambda proxy, type_, event, refcon: event, None)
    print("%s tap creation: %s" % (name, "OK" if tap else "FAILED"))
    return tap


try_tap("Listen-only (needs Input Monitoring)",
        Quartz.kCGEventTapOptionListenOnly)
try_tap("Active      (needs Accessibility)   ",
        Quartz.kCGEventTapOptionDefault)

print()
print("If the active tap FAILED but Accessibility shows True, check that")
print("'Secure Keyboard Entry' is disabled in the Terminal/iTerm2 menu.")
print("If a grant shows False although System Settings shows it enabled,")
print("fully quit the terminal app (Cmd+Q) and reopen it; if it persists,")
print("run 'tccutil reset Accessibility' and 'tccutil reset ListenEvent',")
print("then re-grant when prompted.")
