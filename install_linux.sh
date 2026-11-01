#!/bin/sh
# Installs Enso's Linux dependencies into a venv and (optionally)
# registers an XDG autostart entry so Enso starts with the desktop
# session (works on KDE, LXQt and other freedesktop-compliant DEs).
#
# Usage: ./install_linux.sh [--autostart] [--wayland]
#
# --wayland installs the evdev module needed by the KDE Wayland backend
# (done automatically when the script runs inside a Wayland session).
#
# The GTK/cairo/X11 bindings must come from the distribution (see
# README.linux.md); the venv shares them via --system-site-packages
# and only adds the pure-Python extras (flask for the web UI).

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$HOME/.enso/venv"
DESKTOP_FILE="$HOME/.config/autostart/enso.desktop"
# Repository checkout: <repo>/enso/scripts; unix archive: <root>/scripts.
if [ -f "$REPO_DIR/enso/scripts/run_enso.py" ]; then
    LAUNCHER="$REPO_DIR/enso/scripts/run_enso.py"
else
    LAUNCHER="$REPO_DIR/scripts/run_enso.py"
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Error: this script is for Linux." >&2
    exit 1
fi

AUTOSTART=0
WANT_WAYLAND=0
if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    WANT_WAYLAND=1
fi
for arg in "$@"; do
    case "$arg" in
        --autostart) AUTOSTART=1 ;;
        --wayland) WANT_WAYLAND=1 ;;
        *) echo "Usage: $0 [--autostart] [--wayland]" >&2; exit 1 ;;
    esac
done

echo "Creating virtual environment at $VENV_DIR ..."
python3 -m venv --system-site-packages "$VENV_DIR"

echo "Installing dependencies ..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install flask python-xlib

# evdev is only needed by the KDE Wayland backend, so it is installed
# only from a Wayland session (or with --wayland). It has no prebuilt
# wheels, so pip compiles it (needs gcc, Python headers and kernel
# headers); prefer the distro package, which the venv sees through
# --system-site-packages. A failure here must not abort the install.
if [ "$WANT_WAYLAND" = 1 ] && \
   ! "$VENV_DIR/bin/python3" -c "import evdev" 2>/dev/null; then
    if ! "$VENV_DIR/bin/pip" install evdev; then
        echo
        echo "Warning: could not build the evdev module (only needed for KDE" >&2
        echo "Wayland sessions; X11 works without it). On openSUSE either:" >&2
        echo "  sudo zypper install python3-evdev" >&2
        echo "or install the build tools and re-run this script:" >&2
        echo "  sudo zypper install gcc python3-devel linux-glibc-devel" >&2
    fi
fi

if ! "$VENV_DIR/bin/python3" -c "import gi; gi.require_version('Gtk', '3.0'); import cairo" 2>/dev/null; then
    echo
    echo "Warning: the GTK3/cairo Python bindings are missing. On openSUSE:" >&2
    echo "  sudo zypper install python3-gobject python3-gobject-Gdk \\" >&2
    echo "      typelib-1_0-Gtk-3_0 python3-cairo" >&2
fi

echo
echo "Done. Run Enso with:"
echo
echo "    $VENV_DIR/bin/python3 $LAUNCHER -l INFO"

if [ "$AUTOSTART" = 1 ]; then
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
