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
#   enso.contrib.google
#
# ----------------------------------------------------------------------------

"""
    An Enso plugin that makes the 'google' command available.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import urllib.request, urllib.parse, urllib.error
import locale
import webbrowser

import enso.config
from enso.commands import CommandManager, CommandObject
from enso.commands.factories import ArbitraryPostfixFactory
from enso import selection
from enso.messages import displayMessage
from enso.contrib.scriptotron.tracebacks import safetyNetted


# ----------------------------------------------------------------------------
# The Google command
# ---------------------------------------------------------------------------

class GoogleCommand( CommandObject ):
    """
    Implementation of the 'google' command.
    """
    
    def __init__( self, parameter = None ):
        """
        Initializes the google command.
        """
    
        CommandObject.__init__( self )

        self.parameter = parameter

        if parameter != None:
            self.setDescription( "Performs a Google web search for "
                                 "\u201c%s\u201d." % parameter )
        
    @safetyNetted
    def run( self ):
        """
        Runs the google command.
        """

        # Google limits their search requests to 2048 bytes, so let's be
        # nice and not send them anything longer than that.
        #
        # See this link for more information:
        #
        #   http://code.google.com/apis/soapsearch/reference.html

        MAX_QUERY_LENGTH = 2048

        if self.parameter != None:
            text = self.parameter.decode()
            # '...' gets replaced with current selection
            if "..." in text:
                seldict = selection.get()
                text = text.replace(
                    "...", seldict.get( "text", "" ).strip().strip("\0"))
        else:
            seldict = selection.get()
            text = seldict.get( "text", "" )

        text = text.strip().strip("\0")
        if not text:
            displayMessage( "<p>No text was selected.</p>" )
            return

        BASE_URL = "http://www.google.com/search?q=%s"

        if enso.config.PLUGIN_GOOGLE_USE_DEFAULT_LOCALE:
            # Determine the user's default language setting.  Google
            # appears to use the two-letter ISO 639-1 code for setting
            # languages via the 'hl' query argument.
            languageCode, encoding = locale.getdefaultlocale()
            if languageCode:
                language = languageCode.split( "_" )[0]
            else:
                language = "en"
            BASE_URL = "%s&hl=%s" % (BASE_URL, language)

        # The following is standard convention for transmitting
        # unicode through a URL.
        text = urllib.parse.quote_plus( text.encode("utf-8") )

        finalQuery = BASE_URL % text

        if len( finalQuery ) > MAX_QUERY_LENGTH:
            displayMessage( "<p>Your query is too long.</p>" )
        else:
            # Catch exception, because webbrowser.open sometimes raises exception
            # without any reason
            try:
                webbrowser.open_new_tab( finalQuery )
            except WindowsError as e:
                logging.warning(e)


class GoogleCommandFactory( ArbitraryPostfixFactory ):
    """
    Generates a "google {search terms}" command.
    """

    HELP_TEXT = "search terms"
    PREFIX = "google "
    NAME = "google {search terms}"
    
    def _generateCommandObj( self, postfix ):
        if postfix:
            # TODO: postfix never seems to be used. Perhaps this command
            # could be simplified.
            cmd = GoogleCommand( postfix )
        else:
            cmd = GoogleCommand()
            cmd.setDescription(
                "Performs a Google web search on the selected or typed text."
            )
        return cmd


# ----------------------------------------------------------------------------
# Plugin initialization
# ---------------------------------------------------------------------------

def load():
    cmd = GoogleCommandFactory()
    cmd.setDescription(
        "Performs a Google web search on the selected or typed text."
    )
    CommandManager.get().registerCommand(
        GoogleCommandFactory.NAME,
        cmd
        )

# vim:set tabstop=4 shiftwidth=4 expandtab:
