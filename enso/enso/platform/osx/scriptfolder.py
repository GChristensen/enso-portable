"""
macOS implementation of the Enso "scripts_folder" provider.
"""

import os

from enso import config


def get_script_folder_name():
    """Returns the folder where the bundled Enso commands are found
    (the same location the win32 provider uses; per-user commands are
    loaded separately from ~/.enso/commands)."""
    return os.path.join(config.ENSO_DIR, "commands")
