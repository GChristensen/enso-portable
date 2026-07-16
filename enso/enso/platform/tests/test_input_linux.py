#!/usr/bin/env python3

# Standalone bring-up test for the Linux InputManager (no Enso core).
#
# Works with whichever backend enso.platform.linux.detect selects
# (X11 grab or KDE Wayland evdev/layer-shell); ENSO_LINUX_BACKEND
# overrides the choice.
#
# Grabs the quasimode trigger key (Caps Lock) and prints every event.
# Hold Caps Lock and type to see keyDown/keyUp events; release to end
# the quasimode.  Run with --modal to test sticky mode (Caps Lock tap
# starts it, Return ends, Escape cancels).  Ctrl+C to quit; on X11,
# afterwards check that 'xmodmap -pm' shows Caps_Lock restored on the
# lock row.

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.path.pardir)))

import logging
logging.basicConfig(level=logging.DEBUG, force=True)

import enso.platform.linux
linux_input = enso.platform.linux.provideInterface("input")

_EVENT_NAMES = {
    linux_input.EVENT_KEY_UP: "KEY_UP",
    linux_input.EVENT_KEY_DOWN: "KEY_DOWN",
    linux_input.EVENT_KEY_QUASIMODE: "QUASIMODE",
}

_QM_NAMES = {
    linux_input.KEYCODE_QUASIMODE_START: "START",
    linux_input.KEYCODE_QUASIMODE_END: "END",
    linux_input.KEYCODE_QUASIMODE_CANCEL: "CANCEL",
}


class TestInputManager(linux_input.InputManager):

    def onInit(self):
        mode = "modal" if self.getModality() else "quasimodal"
        print("Ready (%s mode). Hold Caps Lock and type; Ctrl+C to quit."
              % mode)

    def onKeypress(self, eventType, keyCode):
        if eventType == linux_input.EVENT_KEY_QUASIMODE:
            print("QUASIMODE %s" % _QM_NAMES.get(keyCode, keyCode))
        else:
            char = linux_input.CASE_INSENSITIVE_KEYCODE_MAP.get(keyCode, "")
            print("%s keycode=%s char=%r shift=%s"
                  % (_EVENT_NAMES.get(eventType, eventType), keyCode, char,
                     linux_input.getKeyState(linux_input.KEYCODE_SHIFT) < 0))


def main():
    manager = TestInputManager()
    if "--modal" in sys.argv:
        manager.setModality(True)
    print("Trigger keycode (Caps_Lock): %s" % linux_input.KEYCODE_CAPITAL)
    print("Mapped printable keys: %d"
          % len(linux_input.CASE_INSENSITIVE_KEYCODE_MAP))
    manager.run()


if __name__ == "__main__":
    main()
