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
    Contains methods for determining which files, if any, are selected
    in the Windows Explorer.  This module uses the Abstract Factory
    pattern common to all of the Contexts modules:
    Contexts.FileSelection.get() returns a FileSelection object ( a
    subclass of AbstractFileSelection, as appropriate to the front
    application ).
    At present, there are only two subclasses -- one for the Windows
    Explorer, and one (no-op) subclass for all other applications. 

    LONGTERM TODO: Create a subclass which can read the selected file from
    Windows Open File dialog boxen and Save File dialog boxen.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import win32con
import win32clipboard
import pywintypes
import logging

import _ContextUtils as ContextUtils
import ClipboardArchive
import ClipboardBackend

# Internal aliases for external names
clipboardPreserving = ClipboardArchive.clipboardPreserving


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Max amount of time to wait for a file copy to occur, in ms.
FILE_COPY_WAIT_TIME = 2000


# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------

class AbstractFileSelectionContext:
    """
    The abstract base class that defines the interface to
    FileSelectionContext objects.
    """
    
    def getSelectedFiles( self ):
        """
        Returns a list of the names of the files that are selected.
        Each element of the list is an absolute path.  If no files are
        selected, it returns None (not an empty list).
        """

        raise NotImplementedError()


class NullFileSelectionContext( AbstractFileSelectionContext ):
    """
    A FileSelectionContext that always reports that no files are
    selected.  This should be used when we know that the current
    application can't possibly have any notion of 'file selection'.
    """
    
    def getSelectedFiles( self ):
        """
        Returns a list of the names of the files that are selected.
        Each element of the list is an absolute path.  If no files are
        selected, it returns None (not an empty list).
        """
        
        return None


class DefaultFileSelectionContext( AbstractFileSelectionContext ):
    """
    The default subclass to use when in most applications.  It simply
    simulates performing a copy operation, then checks to see if the
    clipboard contains data in the CF_HDROP format.
    """

    @clipboardPreserving
    def getSelectedFiles( self ):
        """
        Returns a list of the names of the files that are selected.
        Each element of the list is an absolute path.  If no files are
        selected, it returns None (not an empty list).
        """

        ClipboardBackend.prepareForClipboardToChange()
        ContextUtils.typeCommandKey( "C" )
        success = ClipboardBackend.waitForClipboardToChange(
            FILE_COPY_WAIT_TIME
            )

        if not success:
            return None

        return self.__getHdropFiles()


    @ContextUtils.clipboardDependent
    def __getHdropFiles( self ):
        """
        Private method for fetching the clipboard format CF_HDROP,
        which represents file targets.
        """
        
        formatAvailable = win32clipboard.IsClipboardFormatAvailable(
            win32con.CF_HDROP
            )
        if formatAvailable:
            try:
                value = win32clipboard.GetClipboardData(
                    win32con.CF_HDROP
                    )
            except pywintypes.error, e:
                logging.warn( "Error getting CF_HDROP from clipboard: %s" \
                                 % ( str(e) ) )
                value = None
        else:
            logging.info( "Clipboard type CF_HDROP not in clipboard." )
            value = None
            # LONGTERM TODO: See whether there are other clipboard
            # formats that could give us the information we need
            # when CF_HDROP is not available.
            
        return value

# ----------------------------------------------------------------------------
# Public getter
# ----------------------------------------------------------------------------

def get():
    """
    Create and return an instance of the FileSelectionContext
    subclass which is appropriate to the currently active application.
    """
    
    windowClass = ContextUtils.getForegroundClassNameUnicode()

    if windowClass == u"ConsoleWindowClass":
        fsContext = NullFileSelectionContext()
    elif windowClass == u"Emacs":
        fsContext = NullFileSelectionContext()
    else:
        fsContext = DefaultFileSelectionContext()

    return fsContext
