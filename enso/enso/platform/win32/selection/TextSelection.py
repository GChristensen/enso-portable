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
    Contains all the methods for dealing with text selections.
    
    Usage: Contexts.TextSelection.get() returns a TextSelection object
    ( one of AbstractTextSelection's subclasses as appropriate to the
    front application ).  The client code can then use the various
    methods of the object to get and set text.

    If nothing is selected, this module is supposed to return a TextSelection
    object containing no text.  It should NOT return None.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import win32clipboard
import win32con
import logging

import ClipboardBackend
import ClipboardArchive
import _ContextUtils as ContextUtils
from HtmlClipboardFormat import HtmlClipboardFormat

# Internal aliases for external names
clipboardDependent = ContextUtils.clipboardDependent
clipboardPreserving = ClipboardArchive.clipboardPreserving

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Time to wait after issuing a shortcut-key command to an application
# LONGTERM TODO: Figure out the best time; the standard time was not
# long enough for long HTML documents.
STANDARD_WAIT_TIME = 600

# Import all of the clipboard format constants for ease of use
CF_RTF = ContextUtils.CF_RTF
CF_HTML = ContextUtils.CF_HTML
CF_CLIPBOARD_VIEWER_IGNORE = ContextUtils.CF_CLIPBOARD_VIEWER_IGNORE
CF_UNICODETEXT = win32con.CF_UNICODETEXT
CF_TEXT = win32con.CF_TEXT
                                   

# List of the clipboard formats in which we are able to output text
SUPPORTED_FORMATS = [ CF_HTML,
                      # CF_RTF, # We don't support this yet.
                      CF_TEXT,
                      CF_UNICODETEXT,
                      CF_CLIPBOARD_VIEWER_IGNORE,
                      ]

# ----------------------------------------------------------------------------
# Private Utility Functions
# ----------------------------------------------------------------------------

def _concatenate( currentTextDict, additionalTextDict ):
    """
    Returns a new textDict containing the text
    from currentTextDict appended with the text from additionalTextDict.
    """

    # The plaintext contents can be combined simply:
    newPlainText = currentTextDict.get( "text", u"" ) + \
                   additionalTextDict.get( "text", u"" )

    newHtml = currentTextDict.get( "html", u"" ) + \
              currentTextDict.get( "html", u"" )    

    newDict = {}
    
    if len( newPlainText ) > 0:
        newDict[ "text" ] = newPlainText
    if len( newHtml ) > 0:
        newDict[ "html" ] = newHtml

def _textDictToAscii( textDict ):
    text = textDict.get( "text", u"" )
    return text.encode( "ascii", "replace" )

def _textDictToUtf16( textDict ):
    text = textDict.get( "text", u"" )
    return text.encode( "utf-16-le" )

def _textDictToClipboardHtml( textDict ):
    html = textDict.get( "html", u"" )
    clipFormat = HtmlClipboardFormat.fromHtml( html )
    return clipFormat.toClipboardHtml()


# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------

class AbstractTextSelection:
    """
    As an abstract class, this should never be instantiated; it
    defines the interface that all TextSelection objects should
    follow.
    
    This class can also contain protected methods which are utility
    functions shared between different subclasses.
    """

    @clipboardPreserving
    def getSelection( self ):
        """
        Returns a textDict ( with, potentially, "text" and "html" keys )
        containing the text that is selected in the application.
        Attempts to do so without clobbering the clipboard.
        """
        
        ContextUtils.clearClipboard()

        ClipboardBackend.prepareForClipboardToChange()
        self.simulateCopyKeystroke()
        ClipboardBackend.waitForClipboardToChange( STANDARD_WAIT_TIME )

        result = self._getClipboardText()
        return result


    def replaceSelection( self, textDict ):
        """
        Abstract method that must be overridden by subclasses.
        Replaces current selection with given textDict.  (textDict is
        expected to contain "text" and/or "html" keys.)  If there is
        no selection, inserts textObject at the insertion point.
        Returns True if this operation succeeded, False if it did not.
        """

        unusedArgs( textDict )
        raise NotImplementedError()

    def insertAtCursor( self, textDict ):
        """
        Abstract method that must be overridden by subclasses.
        Appends textDict to the end of the selection.  If there is
        no selection, inserts textDict at the insertion point.
        Returns True if this operation succeeded, False if it did not.
        """

        unusedArgs( textDict )
        raise NotImplementedError()


    @clipboardDependent
    def _getClipboardText( self ):
        """
        Attempts to get text from clipboard, create a textDict
        wrapping it, and return the dictionary; takes care of opening and
        closing the clipboard.

        If nothing is available, returns an empty dict.
        """

        # We attempt to get two pieces of information from the clipboard:
        # the formatted text and the plain text.
        
        # Try to get plaintext from unicode text in clipboard; this
        # is likely to be a better version of the unformatted text than
        # what we could produce by stripping out format tags, and it's
        # also easier to use.
        if win32clipboard.IsClipboardFormatAvailable( CF_UNICODETEXT ):
            try:
                plainText = win32clipboard.GetClipboardData( CF_UNICODETEXT )
            except win32clipboard.error, e:
                # This is a fix for ticket #415.
                if e.args[0] == 0:
                    logging.info( "GetClipboardData() error suppressed." )
                    return {}
                else:
                    raise
            assert isinstance( plainText, unicode ), \
                   "GetClipboardData returned not-a-unicode object!!"
        else:
            # If UNICODETEXT is not available, then all other
            # plain-text formats are unavailable; however,
            # we can fall back on getting the plaintext by stripping
            # formatting info out of the formatted text.
            plainText = None

        # Try to get HTML from clipboard:
        if win32clipboard.IsClipboardFormatAvailable( CF_HTML ):
            logging.debug( "HTML is available, getting it." )
            formatText = win32clipboard.GetClipboardData( CF_HTML )
        else:
            formatText = None


        # TODO if plainText is none and formatText is not none, then
        # try to create plainText from formatText by stripping the HTML --
        # see how this is done in EnsoTextObject.

        newTextDict = {}
        if plainText != None:
            newTextDict[ "text" ] = plainText
        if formatText != None:
            newTextDict[ "html" ] = formatText                

        return newTextDict

    def simulateCopyKeystroke( self ):
        """
        Abstract method that must be overridden by subclasses.
        Simulate Ctrl-C or whatever keystroke causes a copy
        action in the current context.
        """
        
        raise NotImplementedError

    def simulateCutKeystroke( self ):
        """
        Abstract method that must be overridden by subclasses.
        Simulate Ctrl-X or whatever keystroke causes a cut
        action in the current context.
        """
        
        raise NotImplementedError

    def simulatePasteKeystroke( self ):
        """
        Abstract method that must be overridden by subclasses.
        Simulate Ctrl-V or whatever keystroke causes a paste
        action in the current context.
        """
        
        raise NotImplementedError

    def _renderClipboardFormat( self, textDict, format ):
        """
        Interprets a given clipboard format code and returns contents
        rendered into the corresponding format, and explicitly
        terminated with null bytes: in other words, the text returned
        from this function is ready to be put into the Windows
        Clipboard.
          """
        # Precondition:
        assert( format in [ CF_TEXT, CF_UNICODETEXT, CF_HTML ] )

        if format == CF_TEXT:
            text = _textDictToAscii( textDict )
            terminator = "\0"
        elif format == CF_UNICODETEXT:
            # For CF_UNICODETEXT we must provide double-null-terminated
            # Utf-16:
            text = _textDictToUtf16( textDict )
            terminator = "\0\0"
        elif format == CF_HTML:
            text = _textDictToClipboardHtml( textDict )
            # No terminator should be used on clipboard html format.
            terminator = ""

        result = text + terminator
        # Postcondition:
        assert( type( result ) == str )
        return result
          

    def _pasteText( self, textDict ):
        """
        Puts the given textObject into the clipboard, then simulates
        a paste keystroke in the application.  If all goes well, the
        text will be inserted into the application, and this function
        returns True.  If the attempt fails, returns False.
        """

        # Create the function which will be used for callback
        def getPendingData( formatCode ):
            try:
                if formatCode == ContextUtils.CF_CLIPBOARD_VIEWER_IGNORE:
                    return "HumanizedEnsoTextSelectionContext\0"
                else:
                    return self._renderClipboardFormat( textDict, formatCode )
            except Exception:
                import traceback
                logging.error( "Traceback in getPendingData():\n%s" %
                                  traceback.format_exc() )
                raise

        # Give the above function to clipboard backend, along with the
        # list of formats in which we can support pasting
        ClipboardBackend.prepareForPasting( getPendingData,
                                            SUPPORTED_FORMATS )
        # then type the paste command key, which will cause the app to
        # draw the data out of getPendingData.
        self.simulatePasteKeystroke()

        ClipboardBackend.waitForPaste( STANDARD_WAIT_TIME )

        success = ClipboardBackend.finalizePasting()
        return success


class DefaultTextSelection( AbstractTextSelection ):
    """
    This subclass encapsulates the default methods for getting text
    from and putting text into an application, based on Ctrl-C for
    copy and Ctrl-V for paste.  It is returned by TextSelection.get()
    if the currently active application is not one that we have a
    special subclass for.
    """
    
    def simulateCopyKeystroke( self ):
        """
        Simulate Ctrl-C, which is the copy command in most
        applications.
        """
        
        ContextUtils.typeCommandKey( "c" )

    def simulateCutKeystroke( self ):
        """
        Simulate Ctrl-X, which is the cut command in most
        applications.
        """
        
        ContextUtils.typeCommandKey( "x" )

    def simulatePasteKeystroke( self ):
        """
        Simulate Ctrl-V, which is the paste command in most
        applications.
        """
        
        ContextUtils.typeCommandKey( "v" )

    @clipboardPreserving
    def replaceSelection( self, textDict ):
        """
        Replace the selected text with the given textObject by doing a
        paste operation.  In most applications, a paste operation
        replaces any selected text, so this is the behavior we want.
        For applications where this is not the case, see
        NonReplacingTextSelection.
        Returns a boolean telling whether replacement succeeded.
        """

        return self._pasteText( textDict )


    @clipboardPreserving
    def insertAtCursor( self, textDict ):
        """
        Inserts the given text at the cursor position without
        replacing anything.
        Returns a boolean telling whether insertion succeeded.
        """

        # LONGTERM TODO:
        # find a better way to do this? It's currently not really inserting
        # at cursor, it's replacing text selection with text selection + new
        # text.  This means that, for instance, if I do an insert when
        # the cursor is at the beginning of the selection, my new text
        # will actually appear at the end of the selection.
        #
        # If there were a programmatic way to deselect the selection without
        # changing the text or moving the cursor, we could do that, then
        # issue paste... but I don't know of a way to do this.

        # Try to do a copy:
        ClipboardBackend.prepareForClipboardToChange()
        self.simulateCopyKeystroke()
        changed = ClipboardBackend.waitForClipboardToChange( STANDARD_WAIT_TIME )

        if not changed:
            # There was no selection to copy; just paste the text:
            return self._pasteText( textDict )
        else:
            # There was an existing selection: Concatenate it with
            # the new text:
            currentText = self._getClipboardText()
            newText = _concatenate( currentText, textDict )
            return self._pasteText( newText )
        
        
class NonReplacingTextSelection( DefaultTextSelection ):
    """
    In some applications, notably MoonEdit and Emacs, a paste
    does not replace selected tet: it inserts
    at the cursor.  This is the selection context to use for
    those applications.
    """
    
    @clipboardPreserving
    def replaceSelection( self, textDict ):
        """
        Replace the selected text with the given text by first
        cutting and discarding the selected text, then pasting in
        the new text.
        Returns a boolean telling whether replacement succeeded.
        """
        ClipboardBackend.prepareForClipboardToChange()
        self.simulateCutKeystroke()
        ClipboardBackend.waitForClipboardToChange( STANDARD_WAIT_TIME )

        return self._pasteText( textDict )

    @clipboardPreserving
    def insertAtCursor( self, textDict ):
        """
        Insert text at cursor position in MoonEdit by doing a paste
        operation.
        Returns a boolean telling whether insertion succeeded.
        """

        return self._pasteText( textDict )



class EmacsTextSelection( NonReplacingTextSelection ):
    """
    The subclass to use if the currently active application is Emacs.
    """

    # LONGTERM TODO: Figure out what an appropriate behavior
    # is if "transient-mark mode" is turned on in emacs.
    # (and how we can detect this.)

    # A note on replaceSelection in this context:
    # the "selection" in Emacs is everything between the point and the
    # mark, so it's fairly easy to have stuff selected without
    # realizing it, and then lose it because of this function, but I
    # don't see a good solution.

    def simulatePasteKeystroke( self ):
        ContextUtils.typeCommandKey( "y" )

    def simulateCopyKeystroke( self ):
        ContextUtils.typeSequence( "ESC W" )

    def simulateCutKeystroke( self ):
        ContextUtils.typeCommandKey( "w" )




class CommandPromptTextSelection( DefaultTextSelection ):
    """
    Returned if the currently active application is a Windows
    Command Prompt.  There is very little that we can do to
    interact with the text in a command prompt, so most of
    these functions are no-ops.
    """

    def getSelection( self ):
        """
        Always blank.
        """
        return {}

    def replaceSelection( self, textDict ):
        """
        Text in the command prompt window is immutable, so
        the replacement behavior is impossible to achieve.
        Return False to indicate failure.
        """
        return False

    def simulatePasteKeystroke( self ):
        # Alt-space pops up the window menu (the thing you get
        # by clicking in the upper-left corner).  Then typing
        # e and then p selects edit->paste.
        ContextUtils.typeAltKey( " " )
        ContextUtils.typeSequence( "e p" )

    def simulateCopyKeystroke( self ):
        pass
    
    def simulateCutKeystroke( self ):
        pass

    @clipboardPreserving
    def insertAtCursor( self, textDict ):
        """
        Attempts to insert text into the command prompt window.
        Returns a boolean telling whether insertion succeeded.
        """
        return self._pasteText( textDict )

    
# ----------------------------------------------------------------------------
# Public Function
# ----------------------------------------------------------------------------

def get():
    """
    Creates and returns a TextSelection object of a subclass
    appropriate to the currently active application.

    If no text is selected, this must return a TextSelection object with
    no text in it -- NOT a None.
    """

    className = ContextUtils.getForegroundClassNameUnicode()

    if className == u"Emacs":
        tsContext = EmacsTextSelection()
    elif className == u"MoonEdit":
        tsContext = NonReplacingTextSelection()
    elif className == u"ConsoleWindowClass":
        tsContext = CommandPromptTextSelection()
    else:
        tsContext = DefaultTextSelection()

    return tsContext
