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
    The Win32 clipboard uses a special format for handling HTML. The basic
    problem that the special format is trying to solve is that the user can
    select an arbitrary chunk of formatted text that might not be valid HTML.
    For instance selecting half-way through a bolded word would contain no </b>
    tag. The solution is to encase the fragment in a valid HTML document.

    You can read more about this at:
    http://msdn.microsoft.com/workshop/networking/clipboard/htmlclipboard.asp

    This module deals with converting between the clipboard HTML format and
    standard HTML format.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import re

# ----------------------------------------------------------------------------
# Private Functions
# ----------------------------------------------------------------------------

def _findFirst( pattern, src ):
    """
    A helper function that simplifies the logic of using regex to find
    the first match in a string.
    """
    
    results = re.findall( pattern, src )
    if len(results) > 0:
        return results[0]
    return None


# ----------------------------------------------------------------------------
# HtmlClipboardFormat Object
# ----------------------------------------------------------------------------

class HtmlClipboardFormat:
    """
    Encapsulates the conversation between the clipboard HTML
    format and standard HTML format.
    """

    # The 1.0 HTML clipboard header format.
    HEADER_FORMAT = \
        "Version:1.0\r\n" \
        "StartHTML:%(htmlStart)09d\r\n" \
        "EndHTML:%(htmlEnd)09d\r\n" \
        "StartFragment:%(fragmentStart)09d\r\n" \
        "EndFragment:%(fragmentEnd)09d\r\n" \
        "StartSelection:%(fragmentStart)09d\r\n" \
        "EndSelection:%(fragmentEnd)09d\r\n" \
        "SourceURL:Enso\r\n"

    # A generic HTML page.
    HTML_PAGE = \
        "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 3.2//EN\">\n" \
        "<html>\n<head><title></title></head>\n" \
        "<body>%s</body>\n" \
        "</html>"

    # These regexps find the character offsets of the fragment strings (see
    # below) from the HTML clipboard format header.
    START_RE = "StartFragment:(\d+)"
    END_RE = "EndFragment:(\d+)"

    # The Clipboard HTML format uses the following comment strings to mark
    # the beginning and end of the text fragment which represents the user's
    # actual selection; everything else is envelope.
    START_FRAG = "<!-- StartFragment -->"
    END_FRAG   = "<!-- EndFragment -->"

    def __init__( self, html ):
        """
        Initializes the class to represent html.
        """

        # Preconditions:
        assert( type( html ) == unicode )

        # The internal storage format is platonic unicode.
        self.html = html

    @classmethod
    def fromClipboardHtml( cls, clipboardHtml ):
        """
        Instantiates the class given a string containing the Win32 Html 
        Clipboard format.  The given clipboardHtml is expected to be in
        utf-8 and is expected to contain the special start-fragment and
        end-fragment markers as defined in the class constants.  If it's
        not utf-8 or if it doesn't have the right delimiters, this function
        logs a warning message and creates an instance empty of text.
        """
        # Preconditions:
        assert( type( clipboardHtml ) == str )

        try:
            html = clipboardHtml.decode( "utf-8" )
        except UnicodeDecodeError:
            # input can't be decoded from utf-8:
            logging.warn( "Non-Utf-8 string in fromClipboardHtml." )
            return cls( u"" )

        start = _findFirst( cls.START_RE, clipboardHtml )
        end = _findFirst( cls.END_RE, clipboardHtml )
        
        if start and end:
            html = clipboardHtml[ int(start): int(end) ]
            html = html.decode( "utf-8" )
            return cls( html )
        else:
            # Start and end not found in input:
            logging.warn( "Missing delimiters in fromClipboardHtml." )
            return cls( u"" )
        
    @classmethod
    def fromHtml( cls, html ):
        """
        Instantiates the class given a string containing plain Html.
        """
        # Preconditions:
        assert( isinstance( html, unicode ) )

        return cls( html )

    def toClipboardHtml( self ):
        """
        Returns the contents in the Win32 Html format.
        """
        
        return self._encodeHtmlFragment( self.html )

    def toHtml( self ):
        """
         Returns the contents in the plain Html format.
        """
        
        return self.html

    def _createHtmlPage( self, fragment ):
        """
        Takes an Html fragment and encloses it in a full Html page.
        """
        
        return self.HTML_PAGE % fragment      

    def _encodeHtmlFragment(self, sourceHtml):
        """
        Join all our bits of information into a string formatted as per the 
        clipboard HTML format spec.

        The return value of this function is a Python string
        encoded in UTF-8.
        """

        # Preconditions:
        assert( type( sourceHtml ) == unicode )

        # LONGTERM TODO: The above contract statement involving
        # .encode().decode() could have damaging performance
        # repercussions.

        # NOTE: Every time we construct a string, we must encode it to
        # UTF-8 *before* we do any position-sensitive operations on
        # it, such as taking its length or finding a substring
        # position.  

        if "<body>" in sourceHtml:
            htmlheader, fragment = sourceHtml.split( "<body>" )
            fragment, footer = fragment.split( "</body>" )
            htmlheader = htmlheader + "<body>"
            footer = "</body>" + footer
            fragment = "".join( [self.START_FRAG,
                                 fragment,
                                 self.END_FRAG] )
            html = "".join([ htmlheader, fragment, footer ])
        else:
            fragment = sourceHtml
            html = self._createHtmlPage( fragment )
        fragment = fragment.encode( "utf-8" )
        html = html.encode( "utf-8" )
        assert html == html.decode( "utf-8" ).encode( "utf-8" ), \
               "Encoding got out of whack in HtmlClipboardFormat."
        
        # How long is the header going to be?
        dummyHeader = self.HEADER_FORMAT % dict( htmlStart = 0,
                                                 htmlEnd   = 0,
                                                 fragmentStart = 0,
                                                 fragmentEnd = 0 )
        dummyHeader = dummyHeader.encode( "utf-8" )
        headerLen = len(dummyHeader)

        fragmentStart = html.find( fragment )
        fragmentEnd   = fragmentStart + len( fragment )

        positions = dict( htmlStart     = headerLen,
                          htmlEnd       = headerLen + len(html),
                          fragmentStart = headerLen + fragmentStart,
                          fragmentEnd   = headerLen + fragmentEnd )
        header = self.HEADER_FORMAT % positions
        header = header.encode( "utf-8" )

        result = header + html

        # Postconditions:
        assert( type( result ) == str )
        assert( result == result.decode( "utf-8" ).encode( "utf-8" ) )
        return result

