import os
import re
import time
import random
import subprocess

COMMON_ARGS = ['what', 'prev', 'next', 'all']

probe_registry = {}


def open_player(cmd, api, basedir, cat, player, findfirst=False):
    global probe_registry

    cmd = probe_registry[cmd]

    if cat == 'what':
        api.display_message(", ".join(cmd.valid_args[3:]))
        return
    elif cat == 'next':
        idx = cmd.valid_args.index(cmd.cat) if hasattr(cmd, 'cat') else 3
        cat = cmd.valid_args[idx + 1] if idx < len(cmd.valid_args) - 1 else cmd.valid_args[4]
    elif cat == 'prev':
        idx = cmd.valid_args.index(cmd.cat) if hasattr(cmd, 'cat') else len(cmd.valid_args) - 1
        cat = cmd.valid_args[idx - 1] if idx > 4 else cmd.valid_args[len(cmd.valid_args) - 1]

    cmd.cat = cat

    if basedir:
        if os.path.isdir(basedir):
            os.chdir(basedir)
        item = basedir if cat == "all" else cmd.arg2dir[cat]
    else:
        if cat == "all":
            api.display_message("Nothing to play")
            return
        else:
            item = cmd.arg2dir[cat]

    if findfirst:
        items = os.listdir(item)
        for i in items:
            path = os.path.join(item, i)
            if os.path.isfile(path):
                item = path
                break

    if player:
        subprocess.Popen([player, item])
    else:
        os.startfile(item)


def dictionary_probe(category, dictionary, player="", all="", findfirst=False):
    """Sends values found in the dictionary (may be directory paths) to player by the corresponding arguments.
    The category parameter specifies the name of command argument.
    if findfirst is true and the value is a directory path, the first file found
    in the directory is sent into the player instead of the item.
    If player is empty string, the default shell application is used.
    The 'all' command argument value is substituted by the 'all' function parameter.
    """

    global probe_registry

    cmd_name = "fun" + str(int(time.time() * 1000000)) + str(random.randint(0, 1000))
    cmd_text = """
def {0}(ensoapi, {1}):
    open_player('{0}', ensoapi, '{2}', {1}, '{3}', {4})    
"""

    cmd_text = cmd_text.format(cmd_name, category, all, player, findfirst)
    allLocals = {}

    exec(cmd_text, globals(), allLocals)
    func = allLocals[cmd_name]

    func.arg2dir = dictionary
    func.valid_args = COMMON_ARGS + list(func.arg2dir.keys())
    probe_registry[cmd_name] = func
    return func


def collect_descendants(directory):
    pattern = re.compile("(^\d+\.? ?)?(.*)")
    dirs = os.listdir(directory)
    args = [pattern.match(name)[2] for name in dirs]
    arg2dir = {}

    for i, val in enumerate(dirs):
        arg2dir[args[i]] = os.path.join(directory, dirs[i])

    return arg2dir


def directory_probe(category, directory, player="", additional=None):
    """Sends directory entries found in the 'directory' to 'player',
    makes command arguments from the directory entries."""

    dictionary = collect_descendants(directory)

    if additional:
        dictionary.update(additional)

    return dictionary_probe(category, dictionary, player, directory)


def findfirst_probe(category, dictionary, player=""):
    """Uses the default shell program to open a first **file** in the directory
    designated by the 'dictionary' argument, or uses player if specified."""
    return dictionary_probe(category, dictionary, player, findfirst=True)
