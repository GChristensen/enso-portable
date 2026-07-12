# Enso on Linux (X11)

Experimental Linux port of the Enso launcher, targeting X11 sessions
(tested desktops: KDE Plasma and LXQt on openSUSE). Wayland sessions are
not supported: Enso's global key grab only works under X11.

## Prerequisites

On openSUSE:

```
sudo zypper install python3-gobject python3-gobject-Gdk \
    typelib-1_0-Gtk-3_0 python3-cairo python3-xlib setxkbmap xset
```

Optional:

- `python3-Flask` — enables the web UI (settings page). Without it, Enso
  runs with the web UI disabled.
- `typelib-1_0-AyatanaAppIndicator3-0_1` — enables the tray icon
  (About/Restart/Start at login/Quit). Without it, Enso runs without a
  tray.
- `picom` — a compositing manager, required for transparent overlays on
  desktops that don't composite by default (LXQt). KDE's KWin always
  composites, so nothing extra is needed there. On LXQt, start it with
  `picom -b` (or enable it in the LXQt session settings); without a
  compositor Enso still works, but the overlays are drawn on an opaque
  background.

## Installing

After the distro packages above are in place, the install script sets
up a virtual environment at `~/.enso/venv` (sharing the system GTK
bindings) with the pure-Python extras (flask for the web UI), and can
optionally register an XDG autostart entry so Enso starts with the
desktop session:

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

(This is the same launcher script used on Windows and macOS; it detects
the OS at runtime and behaves accordingly.)

Hold **Caps Lock** and type a command name (e.g. `help`), then release.
While Enso runs, the Caps Lock toggle action is disabled via
`setxkbmap -option caps:none` and the original XKB options are
restored on exit.

User files live in `~/.enso` (configuration `ensorc.py`, user commands in
`~/.enso/commands`). The bundled commands ship in the repository's
`enso/commands` directory; Windows-only ones are skipped automatically.

## Bring-up test scripts

To test the two platform layers separately, before running the whole
launcher:

```
python3 enso/scripts/test_transparent_window_linux.py   # graphics
python3 enso/scripts/test_input_linux.py [--modal]      # key grabbing
```

The first draws a translucent rounded rectangle that fades, moves, and
is click-through. The second prints quasimode/key events while Caps Lock
is held, and must restore the Caps Lock toggle and key repeat on exit
(check with `xmodmap -pm`: the `lock` row should list `Caps_Lock` again).

## Notes on specific commands

- `open {name}` lists installed applications (desktop entries) plus
  anything learned via `learn as open`.
- `go {window}` and the window commands (maximize, minimize, close,
  fullscreen, ...) use EWMH and work on KDE, LXQt and other
  standards-compliant window managers.
- `shutdown`/`reboot`/`suspend`/`hibernate` use systemctl; `logoff`
  uses loginctl.

## Known limitations

- Text-only selection support: commands see the PRIMARY selection
  (highlighted text); inserting text is done by setting the clipboard
  and synthesizing Ctrl+V (applications with different paste shortcuts,
  e.g. terminals, won't receive it).
- The Windows `open`/`open with` commands have no Linux equivalent yet
  (planned: freedesktop `.desktop` scanning).
- Localized keyboard input (`LOCALIZED_INPUT`) is not implemented; the
  command line accepts the characters of the primary keyboard layout.
