import mpcapi

from mpcapi import commands

import win32gui
import win32api
import win32con

from SendKeys import SendKeys

from enso import config

MPC_HOST = getattr(config, "MPC_HOST") if "MPC_HOST" in vars(config) else "127.0.0.1"
MPC_PORT = getattr(config, "MPC_PORT") if "MPC_PORT" in vars(config) else "13579"
MPC_ENABLED = getattr(config, "MPC_ENABLED") if "MPC_ENABLED" in vars(config) else False


def mpc_randomize():
    mpc_wnd = win32gui.FindWindow("MediaPlayerClassicW", None)
    navbar_wnd = win32gui.FindWindowEx(mpc_wnd, 0, None, "Navigation Bar")
    playlist_wnd = win32gui.FindWindowEx(navbar_wnd, 0, None, "Playlist")
    if playlist_wnd == 0:
        playlist_wnd = win32gui.FindWindowEx(mpc_wnd, 0, None, "Playlist")
    if playlist_wnd:
        rect = win32gui.GetWindowRect(playlist_wnd)
        win32api.SetCursorPos([rect[0] + 30, rect[1] + 40])
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN| \
                             win32con.MOUSEEVENTF_ABSOLUTE,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP| \
                             win32con.MOUSEEVENTF_ABSOLUTE,0,0)

        SendKeys("{UP}{UP}{UP}{UP}~{HOME}{SPACE}")


def get_mpc_commands():
    return [v["command_name"].replace("_", " ")
            for v in commands.command_mapping.values()]


def cmd_mpc(ensoapi, action):
    """Control Media Player Classic using Enso
    IMPORTANT: Web Interface should be enabled in MPC settings.
    <br>NOTE: the command is based on <a href="https://github.com/Grokzen/mpcapi">mpcapi</a>.
    <br>Due to the vast number of arguments the command is disabled by default.
    <br>Issue 'mpc enable' to make it available."""
    if action == "enable":
        config.MPC_ENABLED = True
        config.store_value("MPC_ENABLED", True)
        cmd_mpc.valid_args = ["disable", "randomize"] + get_mpc_commands()
    elif action == "disable":
        config.MPC_ENABLED = False
        config.store_value("MPC_ENABLED", False)
        cmd_mpc.valid_args = ["enable"]
    elif action == "randomize":
        mpc_randomize()
    else:
        getattr(mpcapi.MpcAPI(host=MPC_HOST, port=MPC_PORT), action.replace(" ", "_"))()


if MPC_ENABLED:
    cmd_mpc.valid_args = ["disable", "randomize"] + get_mpc_commands()
else:
    cmd_mpc.valid_args = ["enable"]
