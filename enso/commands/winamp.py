import win32api
import win32gui

from enso.commands import CommandManager, CommandObject
from enso.commands.factories import ArbitraryPostfixFactory
from enso import selection
from enso.messages import displayMessage
from enso.contrib.scriptotron import ensoapi

WM_COMMAND = 0x0111
WM_USER    = 0x400
 
 
class WinampCommand():
   
    def __init__(self):
        self.winampCommands = {"prev"      :40044,
                                "next"      :40048,
                                "play"      :40045,
                                "pause"     :40046,
                                "stop"      :40047,
                                "forward"   :40157,
                                "rewind"    :40148,
                                "raisevol"  :40058,
                                "lowervol"  :40059,
                                "+"         :40058,
                                "-"         :40059}
        
    #Command Methods
    def __call__(self, command, param = None):
        hWinamp = win32gui.FindWindow('Winamp v1.x', None)

        if command == 'volume':
            if param == '+':
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['raisevol'], 0)
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['raisevol'], 0)
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['raisevol'], 0)
                return
            else:
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['lowervol'], 0)
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['lowervol'], 0)
                win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands['lowervol'], 0)
                return

        if self.winampCommands.has_key(command):
            return win32api.SendMessage(hWinamp, WM_COMMAND, self.winampCommands[command], 0)
        else:
            raise AssertionError("Unknown Winamp Command, try again")


wc = WinampCommand()

def cmd_next_track(ensoapi):
    """ Go to next track in audio player """
    wc('next')

def cmd_previous_track(ensoapi):
    """ Go to previous track in audio player """
    wc('prev')

def cmd_play_track(ensoapi):
    """ Play current track in audio player """
    wc('play')

def cmd_pause_track(ensoapi):
    """ Pause/play current track in audio player """
    wc('pause')

def cmd_stop_track(ensoapi):
    """ Stop current track in audio player """
    wc('stop')

def cmd_volume(ensoapi, param):
    """ Raise/lower volume in audio player """
    wc('volume', param)

cmd_volume.valid_args = ['+', '-']

