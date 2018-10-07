# Copyright (c) 2008, Humanized, Inc.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Enso nor the names of its contributors may
#       be used to endorse or promote products derived from this
#       software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY Humanized, Inc. ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Humanized, Inc. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ----------------------------------------------------------------------------
#
#   enso
#
# ----------------------------------------------------------------------------

import os, threading, logging
from enso import config

def run_tasks():
    class Tasks(threading.Thread):
        def run(self):
            tasks_file = os.path.join(config.ENSO_USER_DIR, "tasks.py")
            if os.path.exists(tasks_file):
                try:
                    logging.info( "Executing tasks" )
                    contents = open( tasks_file, "r" ).read()
                    compiled = compile( contents + "\n", tasks_file, "exec" )
                    exec(compiled, {}, {})
                except Exception as e:
                    from enso.contrib.scriptotron.tracebacks import TracebackCommand
                    logging.exception("Error executing tasks file")
                    TracebackCommand.setTracebackInfo()

    tasks = Tasks()
    tasks.setDaemon(True)
    tasks.start()


def run():
    """
    Initializes and runs Enso.
    """

    from enso.events import EventManager
    from enso.quasimode import Quasimode
    from enso import plugins, webui
    from enso.quasimode import layout

    # Set color theme before quasimode is loaded to capture font styles
    layout.setColorTheme(config.COLOR_THEME)

    eventManager = EventManager.get()
    Quasimode.install( eventManager )
    plugins.install( eventManager )
    def initEnso():
        msgXml = config.OPENING_MSG_XML
        if msgXml != None:
            messages.displayMessage( msgXml )

        run_tasks()

    if config.ENABLE_WEB_UI:
        webui.start(eventManager)

    eventManager.registerResponder( initEnso, "init" )
    eventManager.run()