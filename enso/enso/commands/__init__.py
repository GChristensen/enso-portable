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
#   enso.commands
#
# ----------------------------------------------------------------------------

"""
    The command subsystem.

    Defines interfaces for command objects and factories, interfaces for
    objects that describe command name expressions, and objects for
    suggestions (including autocompletions).

    Also implements a command manager class, which is used to maintain the
    available commands (including dynamically generated commands from
    command factories).

    This module is reponsible for initializing and maintaining the command
    manager singleton.  It also exposes several objects from submodules
    directly.
"""

# ----------------------------------------------------------------------------
# This file contains trade secrets of Humanized, Inc. No part
# may be reproduced or transmitted in any form by any means or for any purpose
# without the express written permission of Humanized, Inc.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso.commands.manager import CommandManager
from enso.commands.interfaces import CommandObject, AbstractCommandFactory
from enso.commands.suggestions import Suggestion, AutoCompletion
