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
   This module provides an object representing a clipboard state, and
   maintains a stack of these objects.  When client code wants to save
   the clipboard state, it can push a state onto the stack by calling
   ClipboardArchive.pushState().  When the client code is done messing
   with the clipboard, it can restore the most recently saved state by
   calling ClipboardArchive.popState().
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

import win32con
import win32clipboard

from enso.utils.decorators import finalizeWrapper
import _ContextUtils as ContextUtils


# ----------------------------------------------------------------------------
# Module Variables
# ----------------------------------------------------------------------------

# A LIFO array of ClipboardState objects.  The most recent clipboard state
# is on the top of the stack.
_archiveStack = []


# ----------------------------------------------------------------------------
# Private Classes
# ----------------------------------------------------------------------------

class ClipboardState:
    """
    A class that encapsulates a state of the clipboard.  Upon
    intialization it stores the current state of the clipboard.
    """

    # List of clipboard formats that we save.  (We whitelist, rather
    # than blacklist, formats.)  This is far from all the clipboard
    # formats that there are, but Unicode, RTF, and Device Independent
    # Bitmap cover most of the bases.  It should be noted that a
    # number of similar formats, such as CF_TEXT and CF_BITMAP, are
    # automatically synthesized by Windows from some of the clipboard
    # formats we save, which means that we don't need to explicitly
    # save them ourselves.
    
    # LONGTERM TODO: Add more formats here when it is determined that
    # we have the need and the ability to save them.
    _SAVED_FORMATS = [
        win32con.CF_UNICODETEXT,
        win32con.CF_DIB,
        win32clipboard.RegisterClipboardFormat( "Rich Text Format" )
        ]

    # LONGTERM TODO: If a user is running, say, Photoshop, and they
    # copy some massive chunk of graphics, Photoshop is probably doing
    # delayed clipboard rendering.  If this class is then called on to
    # save the clipboard state, it will force Photoshop to actually
    # render the massive chunk of graphics, which takes lots of time
    # and memory.  So this may become a performance issue at some
    # point.  OTOH, there may not be any other alternative; more
    # research needs to be done.

    # LONGTERM TODO: When saving the clipboard state, we're not
    # currently preserving the order in which the clipboard formats
    # were put on the clipboard.  This may be something we want to do
    # in the future, since some programs may rely on it to figure out
    # what the most 'useful' or 'high-priority' clipboard format is.

    @ContextUtils.clipboardDependent
    def __init__( self ):
        """
        Reads current state of clipboard, creates a ClipboardState
        object duplicating that state.
        """

        logging.debug( "Attempting to save clipboard data in \
                   ClipboardState object" )

        self.__formatData = {}

        for format in self._SAVED_FORMATS:
            if win32clipboard.IsClipboardFormatAvailable( format ):
                try:
                    dataHandle = win32clipboard.GetClipboardDataHandle( format )
                except win32clipboard.error, e:
                    # This is a fix for ticket #414.
                    if e.args[0] == 0:
                        logging.info( "GetClipboardData error suppressed." )
                        continue
                    else:
                        raise

                rawData = win32clipboard.GetGlobalMemory( dataHandle )
                self.__formatData[ format ] = rawData


    @ContextUtils.clipboardDependent
    def restore( self ):
        """
        Puts the data contained in this object back into the
        clipboard.
        """

        logging.debug( "Attempting to restore clipboard data from"
                          " ClipboardState object" )
        
        win32clipboard.EmptyClipboard()

        for format in self.__formatData.keys():
            rawData = self.__formatData[format]
            win32clipboard.SetClipboardData( format, rawData )

        ContextUtils.setClipboardDataViewerIgnore()


    def __getClipboardFormatList( self ):
        """
        Returns a list of strings corresponding to the formats
        currently contained in the clipboard, useful for debugging
        purposes.

        Precondition: the clipboard is open.
        Postcondition: the clipboard is open.
        """

        format = 0
        done = False
        formatNames = []
        while not done:
            format = win32clipboard.EnumClipboardFormats( format )
            if format == 0:
                done = True
            else:
                formatName = ContextUtils.interpretFormatCode( format )
                if not formatName:
                    formatName = "Unknown format %d" % format
                formatNames.append( formatName )
        return formatNames


# ----------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------

def clipboardPreserving( function ):
    """
    A decorator which pushes the clipboard state before running the function,
    and pops it afterwards, whether or not the function raises an error.
    """

    def wrapperFunc( *args, **kwargs ):
        pushState()
        try:
            result = function( *args, **kwargs )
        finally:
            popState()
        return result

    return finalizeWrapper( function,
                            wrapperFunc,
                            "clipboardPreserving" )


def pushState():
    """
    Saves the current clipboard state, and pushes it onto the
    archive stack.  Does not change current clipboard contents.
    Returns nothing.
    """

    state = ClipboardState()
    _archiveStack.append( state )

def popState():
    """
    Restores the most recently pushed clipboard state, and removes it
    from the archive stack.  Replaces current clipboard contents.
    Returns nothing.  Stack must not be empty.
    """

    # Preconditions:
    assert( len( _archiveStack ) > 0 )
    state = _archiveStack.pop()
    state.restore()

def restoreLastState():
    """
    Restores the most recently pushed clipboard state, but does not
    remove it from the archive stack.  Replaces current clipboard contents.
    Returns nothing.  Stack must not be empty.
    """
    
    # Preconditions:
    assert( len( _archiveStack ) > 0 )
    
    state = _archiveStack[ -1 ]
    state.restore()
