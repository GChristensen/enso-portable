# Enso on macOS

Experimental macOS port of the Enso launcher, with the same feature set
as the Linux port (see `README.linux.md`). Pure Python — no native
components to compile; global key capture uses a Quartz event tap.

## Prerequisites

macOS 12 or newer, with Python 3 (system, Homebrew, or python.org),
and [Homebrew](https://brew.sh) — pycairo has no macOS wheels on PyPI,
so pip builds it from source and needs the cairo library and
pkg-config:

```
brew install cairo pkg-config
```

Install the Python dependencies into a virtual environment at a
**stable path** — macOS privacy permissions attach to the python
binary, so recreating the venv elsewhere means granting them again:

```
python3 -m venv ~/.enso/venv
~/.enso/venv/bin/pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pycairo
```

Optional: `pip install flask` — enables the web UI (settings page).
Without it, Enso runs with the web UI disabled.

## Permissions (important)

Enso's key capture requires two permissions in System Settings →
Privacy & Security:

- **Input Monitoring** — required; without it Enso cannot see the
  quasimode key at all (there is no crash — it just sees nothing).
- **Accessibility** — needed for simulated copy/paste (selection
  commands).

macOS attributes these permissions to the *responsible application* at
the root of the process tree, so **which entry to enable depends on how
Enso is launched**:

- Launched from a terminal: the grant goes to the terminal app
  (Terminal, iTerm2, ...). The permission prompt names it accordingly —
  enable it, restart Enso from the same terminal.
- Launched at login via the LaunchAgent (see below): the grant goes to
  the python installation itself, as a separate entry. macOS prompts
  again on the first login launch; if no prompt appears, add it
  manually with the "+" button.

Tips for the "+" file dialog:

- It only accepts app bundles, not bare command-line binaries. For
  python, select the **Python.app** bundle inside the framework, e.g.
  `/usr/local/opt/python@3.13/Frameworks/Python.framework/Versions/3.13/Resources/Python.app`
  (adjust prefix/version; `/opt/homebrew/...` on Apple Silicon). This
  entry covers python no matter where it is launched from, so adding
  it to both panes is the most robust option.
- Terminal.app lives in `/System/Applications/Utilities/`. If the
  dialog refuses it, drag it there from Finder instead.
- Press Cmd+Shift+G to type a path directly, and Cmd+Shift+. to show
  hidden directories (like `~/.enso`).

If key capture still fails with the grants in place: fully quit the
terminal app (Cmd+Q) and reopen it (grants are read at launch), make
sure "Secure Keyboard Entry" is disabled in the Terminal/iTerm2 menu,
and diagnose with:

```
~/.enso/venv/bin/python3 enso/scripts/test_permissions_macos.py
```

These are two independent grants — testing from Terminal does not
pre-authorize the autostart, and vice versa.

## Running

From a checkout of this repository:

```
~/.enso/venv/bin/python3 enso/scripts/run_enso.py -l INFO
```

(This is the same launcher script used on Windows and Linux; it detects
the OS at runtime.)

Hold **Caps Lock** and type a command name (e.g. `help`), then release.
While Enso runs, Caps Lock does not toggle: the event tap consumes the
key so applications never see it, and the system-level caps toggle
(which engages in the HID driver regardless) is reset on every press,
so the LED and letter case stay unaffected.

An Enso icon appears in the menu bar with About/Restart/Quit and a
"Start at login" toggle (which manages the same LaunchAgent as
`install_macos.sh --autostart`).

User files live in `~/.enso` (configuration `ensorc.py`, user commands
in `~/.enso/commands`). The bundled commands ship in the repository's
`enso/commands` directory; Windows-only ones are skipped automatically.

## Bring-up test scripts

To test the two platform layers separately, before running the whole
launcher:

```
~/.enso/venv/bin/python3 enso/scripts/test_transparent_window_macos.py   # graphics
~/.enso/venv/bin/python3 enso/scripts/test_input_macos.py [--modal]      # key capture
```

The first draws a translucent rounded rectangle that fades, moves, and
is click-through (and its colors must be correct: green rectangle,
white text — swapped colors indicate a pixel-format bug worth
reporting). The second prints quasimode/key events while Caps Lock is
held; the Caps Lock LED must never light up, and keys typed during the
quasimode must not reach the focused application.

## Starting Enso at login

Create `~/Library/LaunchAgents/com.ensoos.enso.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.ensoos.enso</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOU/.enso/venv/bin/python3</string>
    <string>/path/to/checkout/enso/scripts/run_enso.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>/tmp/enso.err.log</string>
</dict>
</plist>
```

Then: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ensoos.enso.plist`

Note the two-step flow: the permissions must have been granted during a
manual Terminal run first; only then does the login launch work.

## Notes on specific commands

- `shutdown`, `reboot`, `logoff` use AppleScript (System Events); the
  first use triggers an Automation permission prompt — grant it once.
- `go {name}` switches between running applications (not individual
  windows).
- `close` closes the frontmost window via the Accessibility API
  (equivalent to clicking the red titlebar button); it needs the
  `pyobjc-framework-ApplicationServices` package and the Accessibility
  permission Enso already uses.
- `open {name}` finds applications from /Applications,
  /System/Applications and ~/Applications.

## Known limitations

- Text-only selection support: commands read the selection by
  simulating Cmd+C (clobbering the clipboard) and insert text by
  setting the clipboard and simulating Cmd+V.
- The Windows `open`/`open with` commands have no macOS equivalent yet
  (planned: NSWorkspace application scanning).
- Caps Lock press-and-hold detection relies on Quartz flags-changed
  events; if your keyboard misbehaves, set a different trigger key in
  `~/.enso/ensorc.py` (e.g. `QUASIMODE_START_KEY = "KEYCODE_F19"`).
