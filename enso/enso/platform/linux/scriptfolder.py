import os


def get_script_folder_name():
    """Returns the folder where Enso commands are found. This function
       is responsible for ensuring that this folder exists: it must not
       return a path that is not present! It is expected to place this
       folder in some platform-specific logical location."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, "enso", "commands")
    os.makedirs(path, exist_ok=True)
    return path
