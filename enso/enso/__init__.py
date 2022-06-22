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
from . import config

def run():
    """
    Initializes and runs Enso.
    """

    from . import messages, plugins, webui
    from .events import EventManager
    from .quasimode import layout, Quasimode

    eventManager = EventManager.get()
    Quasimode.install( eventManager )
    plugins.install( eventManager )

    def initEnso():
        msgXml = config.OPENING_MSG_XML
        if msgXml is not None and not config.ENSO_IS_QUIET:
            messages.displayMessage( msgXml )

        runTasks()

    if config.ENABLE_WEB_UI:
        webui.start()

    eventManager.registerResponder( initEnso, "init" )

    try:
        eventManager.run()
    except KeyboardInterrupt:
        webui.stop()
    except Exception as e:
        logging.error(e)
        print(e)
        webui.stop()

    if not config.ENSO_IS_QUIET:
        messages.displayMessage(config.CLOSING_MSG_XML)


def runTasks():
    class Tasks(threading.Thread):
        def run(self):
            tasksFilePath = os.path.join(config.ENSO_USER_DIR, "tasks.py")

            if os.path.exists(tasksFilePath):
                try:
                    with open( tasksFilePath, "r" ) as tasksFile:
                        contents = tasksFile.read()
                        compiled = compile( contents + "\n", tasksFilePath, "exec" )
                    exec(compiled, {}, {})
                except Exception:
                    from .contrib.scriptotron.tracebacks import TracebackCommand
                    TracebackCommand.setTracebackInfo()

    tasks = Tasks()
    tasks.daemon = True
    tasks.start()
