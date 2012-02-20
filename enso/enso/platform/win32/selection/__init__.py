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

"""
    Win32 implementation of the Selection interface: provides get()
    and set() methods that take/return selection dictionaries.
    The heavy lifting is delegated to TextSelection.py and
    FileSelection.py.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging
import atexit

import ClipboardArchive 
import TextSelection 
import FileSelection 


# ----------------------------------------------------------------------------
# Module variables
# ----------------------------------------------------------------------------

_isInitialized = False


def get():
    _init()
    fileSelContext = FileSelection.get()
    textSelContext = TextSelection.get()

    sel_dict = textSelContext.getSelection()

    files = fileSelContext.getSelectedFiles()
    if files:
        sel_dict[ "files" ] = files

    return sel_dict

def set( sel_dict ):
    _init()
    textSelContext = TextSelection.get()
    
    # Trying to "set" a file selection doesn't do anything.
    textSelContext.replaceSelection( sel_dict )


# ----------------------------------------------------------------------------
# Package Initialization
# ----------------------------------------------------------------------------

def _init():
    """
    Import and initalize ClipboardBackend and any context sub-modules
    that need initialization, if they haven't already been initialized.
    Register their shutdown functions to run at exit time as well.
    """
    global _isInitialized    
    if not _isInitialized:
        logging.info( "Now initializing ClipboardBackend." )
        import ClipboardBackend
        ClipboardBackend.init()
        atexit.register( ClipboardBackend.shutdown )
        _isInitialized = True
