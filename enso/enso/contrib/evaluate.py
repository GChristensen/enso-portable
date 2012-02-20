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
#   enso.contrib.evaluate
#
# ----------------------------------------------------------------------------

"""
    An Enso plugin that makes the 'evaluate' command available.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso.commands import CommandManager, CommandObject
from enso.utils import xml_tools


# ----------------------------------------------------------------------------
# The Evaluate command
# ---------------------------------------------------------------------------

class EvalCommand( CommandObject ):
    """
    The 'evaluate' command.
    """

    NAME = "evaluate"
    DESCRIPTION = "Evaluates the current selection as Python code."

    def __init__( self, displayMessage=None, selection=None ):
        super( EvalCommand, self ).__init__()
        self.setDescription( self.DESCRIPTION )
        self.setName( self.NAME )

        if displayMessage is None:
            from enso import messages
            displayMessage = messages.displayMessage
        if selection is None:
            import enso.selection
            selection = enso.selection

        self._selection = selection
        self._displayMessage = displayMessage

    def run( self, seldict=None ):
        if seldict is None:
            seldict = self._selection.get()

        text = seldict.get( "text", u"" ).strip()

        evalSuccessful = False
        append = False

        if text.endswith( "=" ):
            text = text[:-1].strip()
            append = True

        if not text:
            self._displayMessage( "<p>No code to evaluate!</p>" )
        else:
            try:
                code = compile( text, "<selected text>", "eval" )
                result = eval( code, {"__builtins__":None}, {} )
                evalSuccessful = True
            except Exception, e:
                self._displayMessage(
                    "<p>Error: %s</p>" % xml_tools.escape_xml(str(e))
                    )

        if evalSuccessful:
            resulttext = unicode( repr(result) )
            if append:
                newtext = "%s = %s" % (text, resulttext)
            else:
                newtext = resulttext
            self._selection.set( {"text" : newtext} )


# ----------------------------------------------------------------------------
# Plugin initialization
# ---------------------------------------------------------------------------

def load():
    CommandManager.get().registerCommand(
        EvalCommand.NAME,
        EvalCommand()
        )


# ----------------------------------------------------------------------------
# Doctests
# ---------------------------------------------------------------------------

def test_evaluate():
    """
    Set up mock objects:

      >>> def mockDisplayMessage( text ):
      ...   print "message: %s" % text

      >>> class MockSelection( object ):
      ...   def set( self, seldict ):
      ...     print "set selection: %s" % seldict

    Initialize our command with the mock objects:

      >>> ec = EvalCommand( mockDisplayMessage, MockSelection() )

    Ensure that the command works if nothing is selected:

      >>> ec.run( {} )
      message: <p>No code to evaluate!</p>

    Ensure that the command works in the general case:

      >>> ec.run( {'text' : u'5+3'} )
      set selection: {'text': u'8'}

    Ensure that the command works with syntax errors:

      >>> ec.run( {'text' : u'5+'} )
      message: <p>Error: unexpected EOF while parsing (&lt;selected text&gt;, line 1)</p>

    Ensure that the command doesn't allow standard Python builtins to be used:

      >>> ec.run( {'text' : u'open("secretfile", "w")'} )
      message: <p>Error: name 'open' is not defined</p>
    """

    pass

if __name__ == "__main__":
    import doctest

    doctest.testmod()
