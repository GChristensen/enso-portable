"""
KDE Wayland backend of the Enso Linux port.

Wayland's security model rules out the X11 techniques (global key
grabs, keyboard capture, override-redirect windows placed in global
coordinates), so this backend composes different mechanisms:

  * graphics  -- overlays are wlr-layer-shell surfaces (gtk-layer-shell)
                 on the overlay layer, positioned with layer margins.
  * input     -- the quasimode trigger key is watched on the raw evdev
                 devices (requires membership in the 'input' group);
                 while the quasimode is active an invisible layer-shell
                 surface takes exclusive keyboard focus, so keystrokes
                 arrive as ordinary GTK key events and never reach the
                 application below.
  * selection -- wl-clipboard for reading/writing selections, a uinput
                 virtual keyboard for synthesizing the paste.
  * windows   -- window enumeration and manipulation via KWin's
                 scripting interface over D-Bus.

Targets KDE Plasma (KWin implements layer-shell since 5.20); the
graphics and input parts also work on other wlr-layer-shell
compositors, while windows/xkb degrade gracefully off Plasma.
"""
