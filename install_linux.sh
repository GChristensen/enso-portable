#!/bin/sh
# Installs Enso's Linux dependencies into a venv and (optionally)
# registers an XDG autostart entry so Enso starts with the desktop
# session (works on KDE, LXQt and other freedesktop-compliant DEs).
#
# Usage: ./install_linux.sh [--autostart]
#
# The GTK/cairo/X11 bindings must come from the distribution (see
# README.linux.md); the venv shares them via --system-site-packages
# and only adds the pure-Python extras (flask for the web UI).

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$HOME/.enso/venv"
DESKTOP_FILE="$HOME/.config/autostart/enso.desktop"
LAUNCHER="$REPO_DIR/enso/scripts/run_enso.py"

if [ "$(uname)" != "Linux" ]; then
    echo "Error: this script is for Linux." >&2
    exit 1
fi

echo "Creating virtual environment at $VENV_DIR ..."
python3 -m venv --system-site-packages "$VENV_DIR"

echo "Installing dependencies ..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install flask python-xlib

if ! "$VENV_DIR/bin/python3" -c "import gi; gi.require_version('Gtk', '3.0'); import cairo" 2>/dev/null; then
    echo
    echo "Warning: the GTK3/cairo Python bindings are missing. On openSUSE:" >&2
    echo "  sudo zypper install python3-gobject python3-gobject-Gdk \\" >&2
    echo "      typelib-1_0-Gtk-3_0 python3-cairo xmodmap xset" >&2
fi

echo
echo "Done. Run Enso with:"
echo
echo "    $VENV_DIR/bin/python3 $LAUNCHER -l INFO"

if [ "$1" = "--autostart" ]; then
    echo
    echo "Registering autostart entry $DESKTOP_FILE ..."
    mkdir -p "$HOME/.config/autostart"
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Enso
Comment=Enso quasimodal launcher
Exec=$VENV_DIR/bin/python3 $LAUNCHER
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
EOF
    echo "Enso will start with the desktop session."
fi
