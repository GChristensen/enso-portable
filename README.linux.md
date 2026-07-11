# Enso on Linux (X11)

Experimental Linux port of the Enso launcher, targeting X11 sessions
(tested desktops: KDE Plasma and LXQt on openSUSE). Wayland sessions are
not supported: Enso's global key grab only works under X11.

## Prerequisites

On openSUSE:

```
sudo zypper install python3-gobject python3-gobject-Gdk \
    typelib-1_0-Gtk-3_0 python3-cairo python3-xlib xmodmap xset
```

Optional:

- `python3-Flask` — enables the web UI (settings page). Without it, Enso
  runs with the web UI disabled.
- `picom` — a compositing manager, required for transparent overlays on
  desktops that don't composite by default (LXQt). KDE's KWin always
  composites, so nothing extra is needed there. On LXQt, start it with
  `picom -b` (or enable it in the LXQt session settings); without a
  compositor Enso still works, but the overlays are drawn on an opaque
  background.

## Running

From a checkout of this repository:

```
python3 enso/scripts/run_enso.py -l INFO
```

(This is the same launcher script used on Windows; it detects the OS at
runtime and behaves accordingly.)

Hold **Caps Lock** and type a command name (e.g. `help`), then release.
While Enso runs, the Caps Lock toggle is disabled via `xmodmap` and
restored on exit.

User files live in `~/.enso` (configuration `ensorc.py`, user commands in
`~/.enso/commands`); command scripts are also loaded from
`~/.local/share/enso/commands`.

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

## Known limitations

- Text-only selection support: commands see the PRIMARY selection
  (highlighted text); inserting text is done by setting the clipboard
  and synthesizing Ctrl+V (applications with different paste shortcuts,
  e.g. terminals, won't receive it).
- No tray icon yet (planned: StatusNotifierItem via AyatanaAppIndicator3).
- The Windows `open`/`open with` commands have no Linux equivalent yet
  (planned: freedesktop `.desktop` scanning).
- Localized keyboard input (`LOCALIZED_INPUT`) is not implemented; the
  command line accepts the characters of the primary keyboard layout.
