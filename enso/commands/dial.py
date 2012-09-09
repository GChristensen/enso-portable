import win32ras
import threading
from ctypes import *
from enso.commands import CommandManager, CommandObject

class RASDIALDLG(Structure):
    _fields_ = [("dwSize", c_ulong),
                ("hwndOwner", c_ulong),
                ("dwFlags", c_ulong),
                ("xDlg", c_long),
                ("yDlg", c_long),
                ("dwSubEntry", c_ulong),
                ("dwError", c_ulong),
                ("reserved", c_ulong),
                ("reserved2", c_ulong)]

class HangupCommand(object):
    """ Disconnect a remote connection """
    def hangup(self, ensoapi, entryName):
        try:
            conn = (i for i in win32ras.EnumConnections() if i[1] == entryName).next()
            win32ras.HangUp(conn[0])
        except:
            print "Couldn't hangup: %s" % entryName
    def __call__(self, ensoapi, connection):
        self.hangup(ensoapi, connection)
    def on_quasimode_start(self):
        self.valid_args = win32ras.EnumEntries()

class DialCommand(object):
    """ Connect to a remote connection """
    def connect(self, ensoapi, entryName):
        try:
            info = RASDIALDLG()
            info.dwSize = sizeof(info)
            windll.rasdlg.RasDialDlgA(0, entryName, 0, byref(info))
        except:
            print "Couldn't connect: %s" % entryName
    def __call__(self, ensoapi, connection):
        def thread_proc():
            self.connect(ensoapi, connection)
        t = threading.Thread(target = thread_proc)
        t.start()        
    def on_quasimode_start(self):
        self.valid_args = win32ras.EnumEntries()

cmd_dial = DialCommand()
cmd_dial.valid_args = []

cmd_hangup = HangupCommand()
cmd_hangup.valid_args = []
