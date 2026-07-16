# Enso on Linux

Experimental Linux port of the Enso launcher, supporting two display
backends:

- **X11** sessions (tested desktops: KDE Plasma and LXQt on openSUSE).
- **Wayland** sessions on **KDE Plasma** (tested on Plasma 6).

The backend is detected automatically at startup (`WAYLAND_DISPLAY`
wins over `DISPLAY`, since Wayland sessions usually run XWayland too);
set `ENSO_LINUX_BACKEND=x11` or `ENSO_LINUX_BACKEND=kwayland` to
override the detection.

## Prerequisites

Common, on openSUSE:

```
sudo zypper install python3-gobject python3-gobject-Gdk \
    typelib-1_0-Gtk-3_0 python3-cairo
```

For **X11** sessions:

```
sudo zypper install python3-xlib setxkbmap xset
```

For **KDE Wayland** sessions:

```
sudo zypper install typelib-1_0-GtkLayerShell-0_1 wl-clipboard
```

plus the `evdev` Python module (the install script puts it into the
venv; otherwise `pip install evdev`), and two one-time permission
steps:

```
# let Enso watch the trigger key (Caps Lock) on the raw input devices
sudo usermod -a -G input $USER

# let Enso synthesize the Ctrl+V paste keystroke via uinput
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | \
    sudo tee /etc/udev/rules.d/99-enso-uinput.rules
sudo udevadm control --reload && sudo udevadm trigger --name-match=uinput
```

Log out and back in afterwards for the group membership to take
effect.

> **Security note:** membership in the `input` group grants read
> access to all input devices — to Enso and to every other process
> running as your user. This is inherent to how a hold-a-key launcher
> must work on Wayland, whose security model forbids global key grabs;
> skip the Wayland setup if that trade-off is not acceptable to you.

Optional:

- `typelib-1_0-AyatanaAppIndicator3-0_1` - enables the tray icon
  (About/Restart/Start at login/Quit). Without it, Enso runs without a
  tray.
- `picom` - a compositing manager, required for transparent overlays on
  X11 desktops that don't composite by default (LXQt). KDE's KWin always
  composites, so nothing extra is needed there — and Wayland is always
  composited. On LXQt, start it with `picom -b` (or enable it in the
  LXQt session settings); without a compositor Enso still works, but
  the overlays are drawn on an opaque background.
- `python3-Flask` - enables the web UI (settings page). Without it, Enso
  runs with the web UI disabled.

## Installing

After the distro packages above are in place, the install script sets
up a virtual environment at `~/.enso/venv` (sharing the system GTK
bindings) with the pure-Python extras (flask for the web UI, evdev for
the Wayland backend).
The install script also can optionally register an XDG autostart entry
so Enso starts with the desktop session:

```
./install_linux.sh              # venv + dependencies only
./install_linux.sh --autostart  # also start Enso at login
```

## Running

From a checkout of this repository:

```
python3 enso/scripts/run_enso.py -l INFO
```

or, if installed via the script:

```
~/.enso/venv/bin/python3 enso/scripts/run_enso.py -l INFO
```

Hit **Caps Lock** and type a command name (e.g. `help`).

User files live in `~/.enso` (configuration `ensorc.py`, user commands in
`~/.enso/commands`). The bundled commands ship in the repository's
`enso/commands` directory.

## How the Wayland backend works

Wayland's security model rules out the X11 techniques (global key
grabs, keyboard capture, windows positioned in global coordinates), so
on KDE the port composes different mechanisms:

- The Caps Lock trigger is watched on the raw evdev devices (hence the
  `input` group), the only way to see both its press and its release
  regardless of window focus.
- While the quasimode is held, an invisible layer-shell surface takes
  *exclusive keyboard focus*, so your keystrokes go to Enso and never
  reach the application below — the Wayland counterpart of the X11
  keyboard grab.
- The overlays are wlr-layer-shell surfaces on the overlay layer,
  which keeps them above all windows, including fullscreen ones.
- Caps Lock's toggle action is suppressed for the session via the
  `caps:none` XKB option in `~/.config/kxkbrc` (restored on exit),
  the Plasma equivalent of what `setxkbmap` does on X11.
- `go {window}` and the window commands run small KWin scripts over
  D-Bus, which see native Wayland and XWayland windows alike.
- Selections are read/written with `wl-clipboard`, and the paste
  keystroke is typed by a uinput virtual keyboard (hence the udev
  rule), since XTEST reaches only XWayland applications.

## Notes on specific commands

- `open {name}` lists installed applications (desktop entries) plus
  anything learned via `learn as open`.
- `go {window}` and the window commands (maximize, minimize, close,
  fullscreen, ...) use EWMH on X11 and work on KDE, LXQt and other
  standards-compliant window managers; on Wayland they use KWin
  scripting and therefore require KDE.
- `shutdown`/`reboot`/`suspend`/`hibernate` use systemctl; `logoff`
  uses loginctl.

## Known limitations

Both backends:

- Text-only selection support: commands see the PRIMARY selection
  (highlighted text); inserting text is done by setting the clipboard
  and synthesizing Ctrl+V (applications with different paste shortcuts,
  e.g. terminals, won't receive it).
- The Windows `open`/`open with` commands have no Linux equivalent yet
  (but theoretically achievable with freedesktop `.desktop` scanning).
- Localized keyboard input (`LOCALIZED_INPUT`) is not implemented; the
  command line accepts the characters of the primary keyboard layout.

Wayland only (inherent to Wayland's pointer/window privacy):

- Overlays appear on the primary monitor instead of the monitor under
  the mouse pointer.
- Messages are dismissed on any mouse activity; the mouse-over effects
  of the message mini-windows are unavailable (the global pointer
  position is not observable).
- `APPEAR_OVER_TASKBAR = False` is ignored; overlays may cover panels.
- Non-KDE Wayland desktops are untested: the overlays and the trigger
  work on any compositor implementing wlr-layer-shell (GNOME does
  not), while the window commands and the Caps Lock suppression are
  KDE-specific and degrade gracefully elsewhere.
