"""
Shortcut backend for the 'open' commands on macOS.

Applications are found by scanning the standard Applications folders
for .app bundles; learned shortcuts are small JSON files in
LEARN_AS_DIR.  Everything is launched through /usr/bin/open.
"""

import json
import logging
import os
import subprocess

from enso import config

SHORTCUT_TYPE_EXECUTABLE = 'x'
SHORTCUT_TYPE_FOLDER = 'f'
SHORTCUT_TYPE_URL = 'u'
SHORTCUT_TYPE_DOCUMENT = 'd'
SHORTCUT_TYPE_CONTROL_PANEL = 'c'

LEARN_AS_DIR = os.path.join(config.ENSO_USER_DIR, "commands", "learned")

if not os.path.isdir(LEARN_AS_DIR):
    os.makedirs(LEARN_AS_DIR)

_APPLICATION_DIRS = [
    "/Applications",
    "/System/Applications",
    os.path.expanduser("~/Applications"),
]

_LEARNED_TYPES = {
    "url": SHORTCUT_TYPE_URL,
    "folder": SHORTCUT_TYPE_FOLDER,
    "file": SHORTCUT_TYPE_DOCUMENT,
}


def _learned_path(name):
    file_name = name.replace(":", "").replace("?", "").replace("/", "")
    return os.path.join(LEARN_AS_DIR, file_name + ".json")


class Shortcuts:
    _instance = None

    def __init__(self):
        self._shortcut_map = {}

    @classmethod
    def get(cls):
        if not cls._instance:
            cls._instance = Shortcuts()
            cls._instance.refresh_shortcuts()
        return cls._instance

    def _get_applications(self):
        shortcuts = []
        for base in _APPLICATION_DIRS:
            if not os.path.isdir(base):
                continue
            for root, dirs, _files in os.walk(base):
                # Scan two levels deep (e.g. /Applications/Utilities).
                if root.count(os.sep) - base.count(os.sep) > 1:
                    dirs[:] = []
                    continue
                for d in list(dirs):
                    if d.endswith(".app"):
                        dirs.remove(d)
                        name = os.path.splitext(d)[0].lower()
                        shortcuts.append((SHORTCUT_TYPE_EXECUTABLE, name,
                                          os.path.join(root, d)))
        return shortcuts

    def _get_learned(self):
        shortcuts = []
        for entry in os.listdir(LEARN_AS_DIR):
            if not entry.endswith(".json"):
                continue
            path = os.path.join(LEARN_AS_DIR, entry)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                shortcut_type = _LEARNED_TYPES.get(data.get("type"),
                                                   SHORTCUT_TYPE_DOCUMENT)
                name = os.path.splitext(entry)[0].lower()
                shortcuts.append((shortcut_type, name, data["target"]))
            except Exception:
                logging.exception("Bad learned shortcut file: %s" % path)
        return shortcuts

    def _reload_shortcuts_map(self):
        shortcuts = self._get_applications() + self._get_learned()
        return dict((s[1], s) for s in shortcuts)

    def add_shortcut(self, file_path):
        name = os.path.splitext(os.path.basename(file_path))[0].lower()
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        shortcut_type = _LEARNED_TYPES.get(data.get("type"),
                                           SHORTCUT_TYPE_DOCUMENT)
        self._shortcut_map[name] = (shortcut_type, name, data["target"])

    def remove_shortcut(self, name):
        if name in self._shortcut_map:
            del self._shortcut_map[name]

    def get_shortcuts(self):
        return self._shortcut_map

    def refresh_shortcuts(self):
        self._shortcut_map = self._reload_shortcuts_map()
        return self._shortcut_map


def run_shortcut(shortcut_type, name, target):
    """Launches the given shortcut; returns True on success."""
    try:
        if shortcut_type == SHORTCUT_TYPE_EXECUTABLE:
            subprocess.Popen(["open", "-a", target])
        else:
            subprocess.Popen(["open", target])
        return True
    except Exception:
        logging.exception("Error launching '%s'" % str(target))
        return False


def open_with_shortcut(executable_target, file):
    """Opens the given file with the given executable shortcut target."""
    try:
        subprocess.Popen(["open", "-a", executable_target, file])
    except Exception:
        logging.exception("Error opening '%s' with '%s'"
                          % (file, executable_target))


def learn_shortcut(name, target, is_url):
    """Persists a learned shortcut; returns its file path, or None if a
    shortcut with that name already exists."""
    path = _learned_path(name)
    if os.path.isfile(path):
        return None
    if is_url:
        entry_type = "url"
    elif os.path.isdir(target):
        entry_type = "folder"
    else:
        entry_type = "file"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": entry_type, "target": target}, f)
    return path


def unlearn_shortcut(name):
    """Removes a learned shortcut; returns an undo token, or None if no
    such shortcut exists."""
    path = _learned_path(name)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        contents = f.read()
    os.remove(path)
    return (name, path, contents)


def restore_shortcut(token):
    """Restores a shortcut removed by unlearn_shortcut(); returns its
    name."""
    name, path, contents = token
    with open(path, "w", encoding="utf-8") as f:
        f.write(contents)
    return name
