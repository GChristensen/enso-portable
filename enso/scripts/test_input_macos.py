#!/usr/bin/env python3

# Standalone bring-up test for the macOS InputManager (no Enso core).
#
# Captures the quasimode trigger key (Caps Lock) via a Quartz event tap
# and prints every event.  Hold Caps Lock and type to see keyDown/keyUp
# events; release to end the quasimode.  Run with --modal to test
# sticky mode (Caps Lock tap starts it, Return ends, Escape cancels).
# Ctrl+C to quit.
#
# Things to verify while it runs:
#   - the Caps Lock LED must never light up, and letter case in other
#     applications must be unaffected;
#   - keys typed during the quasimode must NOT reach the focused app.
#
# Requires the Input Monitoring permission (System Settings -> Privacy
# & Security); the first run should trigger the system prompt.

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.path.pardir)))

import logging
logging.basicConfig(level=logging.DEBUG, force=True)

from enso.platform.osx import input as osx_input

_EVENT_NAMES = {
    osx_input.EVENT_KEY_UP: "KEY_UP",
    osx_input.EVENT_KEY_DOWN: "KEY_DOWN",
    osx_input.EVENT_KEY_QUASIMODE: "QUASIMODE",
}

_QM_NAMES = {
    osx_input.KEYCODE_QUASIMODE_START: "START",
    osx_input.KEYCODE_QUASIMODE_END: "END",
    osx_input.KEYCODE_QUASIMODE_CANCEL: "CANCEL",
}


class TestInputManager(osx_input.InputManager):

    def onInit(self):
        mode = "modal" if self.getModality() else "quasimodal"
        print("Ready (%s mode). Hold Caps Lock and type; Ctrl+C to quit."
              % mode)

    def onKeypress(self, eventType, keyCode):
        if eventType == osx_input.EVENT_KEY_QUASIMODE:
            print("QUASIMODE %s" % _QM_NAMES.get(keyCode, keyCode))
        else:
            char = osx_input.CASE_INSENSITIVE_KEYCODE_MAP.get(keyCode, "")
            print("%s keycode=%s char=%r shift=%s"
                  % (_EVENT_NAMES.get(eventType, eventType), keyCode, char,
                     osx_input.getKeyState(osx_input.KEYCODE_SHIFT) < 0))


def main():
    manager = TestInputManager()
    if "--modal" in sys.argv:
        manager.setModality(True)
    print("Trigger keycode (Caps Lock): %s" % osx_input.KEYCODE_CAPITAL)
    print("Mapped printable keys: %d"
          % len(osx_input.CASE_INSENSITIVE_KEYCODE_MAP))
    manager.run()


if __name__ == "__main__":
    main()
