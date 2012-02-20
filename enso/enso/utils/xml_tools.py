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
#   enso.utils.xml_tools
#
# ----------------------------------------------------------------------------

"""
    XML utility functions.  This module is called "xml_tools" instead
    of simply "xml" because that would cause a namespace conflict due
    to Python 2.x's default prioritization of relative imports over
    absolute imports (this will change in Py3k, though).
"""

# ----------------------------------------------------------------------------
# Public Constants
# ----------------------------------------------------------------------------

# Invalid control character ordinals that can't be included in
# well-formed XML text.  These were determined by examining the ASCII
# characters with the BT_NONXML type in the asciitab.h file of the
# expat library.
INVALID_CONTROL_CHARACTERS = [
    0x00,
    0x01,
    0x02,
    0x03,
    0x04,
    0x05,
    0x06,
    0x07,
    0x08,
    0x0b,
    0x0c,
    0x0e,
    0x0f,
    0x10,
    0x11,
    0x12,
    0x13,
    0x14,
    0x15,
    0x16,
    0x17,
    0x18,
    0x19,
    0x1a,
    0x1b,
    0x1c,
    0x1d,
    0x1e,
    0x1f
]


# ----------------------------------------------------------------------------
# Private Constants
# ----------------------------------------------------------------------------

# Unicode translation table to remove invalid control characters.
_UNICODE_INVALID_CONTROL_CHARACTERS_TRANSLATION_TABLE = {}

for _char in INVALID_CONTROL_CHARACTERS:
    _UNICODE_INVALID_CONTROL_CHARACTERS_TRANSLATION_TABLE[_char] = None

_TEMPCHARS = []
for _char in range(256):
    _TEMPCHARS.append( chr(_char) )

# Identity transformation string for the str.translate() method.
_STRING_IDENTITY_TRANSLATION = "".join( _TEMPCHARS )

_TEMPCHARS = []
for _char in INVALID_CONTROL_CHARACTERS:
    _TEMPCHARS.append( chr(_char) )

# Deletechars string for the str.translate() method, used to remove
# invalid control characters.
_STRING_INVALID_CONTROL_CHARACTERS_DELETECHARS = "".join( _TEMPCHARS )

del _char
del _TEMPCHARS


# ----------------------------------------------------------------------------
# DOM Node functions
# ----------------------------------------------------------------------------

def get_inner_text( dom_node ):
    """
    Returns a unicode string that is the amalgamation of all the text
    interior to node dom_node.  Recursively grabs the inner text from
    all descendent (child, grandchild, etc.) nodes.
    """

    text_strings = []
    for node in  dom_node.childNodes:
        if node.nodeType == dom_node.TEXT_NODE \
               or node.nodeType == dom_node.CDATA_SECTION_NODE:
            text_strings.append( node.data )
        else:
            text_strings.append( get_inner_text( node ) )
        
    return "".join( text_strings ).strip()


def remove_invalid_control_chars( string ):
    """
    Removes invalid control characters from the given string.  The
    string can be a standard Python string or a unicode object.

    Returns the string with the control characters removed; the
    returned string is always of the same type as the string passed
    in.
    """

    if isinstance( string, str ):
        string = string.translate(
            _STRING_IDENTITY_TRANSLATION,
            _STRING_INVALID_CONTROL_CHARACTERS_DELETECHARS
            )
    elif isinstance( string, unicode ):
        string = string.translate(
            _UNICODE_INVALID_CONTROL_CHARACTERS_TRANSLATION_TABLE
            )
    else:
        raise AssertionError( "string must be a string or unicode object." )
    return string


def escape_xml( xml_data ):
    """
    Returns a string in which all the xml characters of xml_data have
    been escaped once (e.g., "&" -> "&amp;", and "<" -> "&lt;"), and
    also removes any invalid control characters from xml_data.
    """
    
    xml_data = xml_data.replace( "&", "&amp;" )
    xml_data = xml_data.replace( "<", "&lt;" )
    # This is needed to escape the sequence "]]>"
    xml_data = xml_data.replace( ">", "&gt;" )
    return remove_invalid_control_chars( xml_data )
