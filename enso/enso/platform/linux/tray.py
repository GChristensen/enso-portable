"""
Tray icon for the Linux port, as a StatusNotifierItem via
AyatanaAppIndicator3 (native on KDE Plasma and LXQt).

If the AppIndicator typelib is not installed, Enso runs without a
tray; on openSUSE it is provided by
typelib-1_0-AyatanaAppIndicator3-0_1.
"""

import logging
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

from enso import config, tray_actions

_AUTOSTART_FILE = os.path.expanduser("~/.config/autostart/enso.desktop")

# The indicator must stay referenced or the icon disappears.
_indicator = None
_menu = None


def _load_indicator_namespace():
    for namespace in ("AyatanaAppIndicator3", "AppIndicator3"):
        try:
            gi.require_version(namespace, "0.1")
            return __import__("gi.repository." + namespace,
                              fromlist=[namespace])
        except (ValueError, ImportError):
            continue
    logging.warning(
        "No AppIndicator typelib found; running without a tray icon. "
        "On openSUSE: sudo zypper install "
        "typelib-1_0-AyatanaAppIndicator3-0_1")
    return None


def _ensure_icon():
    """Converts the themed .ico to a PNG in an icon dir AppIndicator
    can use; returns (theme_dir, icon_name) or None."""
    icon_dir = os.path.join(config.ENSO_USER_DIR, "icons")
    # The PNG is named after the source icon, so switching the color
    # theme picks up a different file instead of reusing a stale one.
    icon_name = os.path.splitext(tray_actions.get_icon_name())[0]
    png_path = os.path.join(icon_dir, icon_name + ".png")
    if not os.path.isfile(png_path):
        try:
            os.makedirs(icon_dir, exist_ok=True)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                tray_actions.get_icon_path())
            pixbuf.savev(png_path, "png", [], [])
        except Exception:
            logging.exception("Couldn't prepare the tray icon PNG; "
                              "running without a tray icon.")
            return None
    return icon_dir, icon_name


def _autostart_enabled():
    return os.path.isfile(_AUTOSTART_FILE)


def _set_autostart(enabled):
    if enabled:
        os.makedirs(os.path.dirname(_AUTOSTART_FILE), exist_ok=True)
        with open(_AUTOSTART_FILE, "w") as f:
            f.write("[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=Enso\n"
                    "Comment=Enso quasimodal launcher\n"
                    "Exec=%s %s\n"
                    "X-GNOME-Autostart-enabled=true\n"
                    "X-KDE-autostart-after=panel\n"
                    % (sys.executable, tray_actions.get_launcher_path()))
    elif os.path.isfile(_AUTOSTART_FILE):
        os.remove(_AUTOSTART_FILE)


def install(enso_config):
    """Creates the tray icon; returns quietly (with a log message) if
    the AppIndicator bindings or the icon are unavailable."""
    global _indicator, _menu

    indicator_mod = _load_indicator_namespace()
    if indicator_mod is None:
        return

    icon = _ensure_icon()
    if icon is None:
        return
    icon_dir, icon_name = icon

    _menu = Gtk.Menu()

    about_item = Gtk.MenuItem(label="About")
    about_item.connect("activate",
                       lambda item: tray_actions.show_about())
    _menu.append(about_item)

    restart_item = Gtk.MenuItem(label="Restart")
    restart_item.connect("activate",
                         lambda item: tray_actions.restart_enso())
    _menu.append(restart_item)

    if tray_actions.settings_available():
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate",
                              lambda item: tray_actions.open_settings())
        _menu.append(settings_item)

    autostart_item = Gtk.CheckMenuItem(label="Start at login")
    autostart_item.set_active(_autostart_enabled())
    autostart_item.connect(
        "toggled", lambda item: _set_autostart(item.get_active()))
    _menu.append(autostart_item)

    _menu.append(Gtk.SeparatorMenuItem())

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda item: tray_actions.quit_enso())
    _menu.append(quit_item)

    _menu.show_all()

    _indicator = indicator_mod.Indicator.new(
        "enso", icon_name,
        indicator_mod.IndicatorCategory.APPLICATION_STATUS)
    _indicator.set_icon_theme_path(icon_dir)
    _indicator.set_title("Enso Open-Source")
    _indicator.set_menu(_menu)
    _indicator.set_status(indicator_mod.IndicatorStatus.ACTIVE)
