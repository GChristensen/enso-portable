import os
import sys
import operator
import time
import logging
import subprocess

import enso.config
from enso.messages import displayMessage

def cmd_enso(ensoapi, cmd):
    """ Enso system command """
    if cmd == 'quit':
        displayMessage(u"<p>Closing <command>Enso</command>...</p><caption>enso</caption>")
        time.sleep(1)
        sys.exit(0)
    if cmd == 'restart':
        subprocess.Popen(["run-enso.exe", "--restart " + str(os.getpid())])
        displayMessage(u"<p>Closing <command>Enso</command>...</p><caption>enso</caption>")
        time.sleep(1)
        sys.exit(0)
    elif cmd == 'about':
        displayMessage(enso.config.ABOUT_BOX_XML)
    elif cmd == "commands":
        ensoapi.display_message("Enso commands", "enso")

cmd_enso.valid_args = ['about', 'help', 'quit', 'restart', 'commands']

# vim:set tabstop=4 shiftwidth=4 expandtab:
