#!/bin/sh
# Installs Enso's macOS dependencies into a venv and (optionally)
# registers a LaunchAgent so Enso starts at login.
#
# Usage: ./install_macos.sh [--autostart]
#
# See README.macos.md for the permission-granting flow: run Enso once
# manually from Terminal before relying on the autostart.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$HOME/.enso/venv"
PLIST="$HOME/Library/LaunchAgents/com.ensoos.enso.plist"
LAUNCHER="$REPO_DIR/enso/scripts/run_enso.py"

if [ "$(uname)" != "Darwin" ]; then
    echo "Error: this script is for macOS." >&2
    exit 1
fi

# pycairo has no macOS wheels on PyPI; pip builds it from source, which
# needs the cairo library and pkg-config (Homebrew).
if ! command -v brew >/dev/null 2>&1; then
    echo "Error: Homebrew is required to install the cairo library" >&2
    echo "(pycairo builds from source on macOS). Install it first:" >&2
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"' >&2
    exit 1
fi

echo "Installing cairo and pkg-config via Homebrew ..."
brew install cairo pkg-config

echo "Creating virtual environment at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"

echo "Installing dependencies ..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install \
    pyobjc-framework-Cocoa pyobjc-framework-Quartz pycairo flask

echo
echo "Done. Run Enso manually once to grant the required permissions:"
echo
echo "    $VENV_DIR/bin/python3 $LAUNCHER -l INFO"
echo
echo "(System Settings -> Privacy & Security -> Input Monitoring and"
echo "Accessibility must list and enable the venv's python3.)"

if [ "$1" = "--autostart" ]; then
    echo
    echo "Registering LaunchAgent $PLIST ..."
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.ensoos.enso</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV_DIR/bin/python3</string>
    <string>$LAUNCHER</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>/tmp/enso.err.log</string>
</dict>
</plist>
EOF
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
    echo "Enso will start at login (after the manual permission run)."
fi
