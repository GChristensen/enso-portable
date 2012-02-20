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
#   enso.quasimode.layout
#
# ----------------------------------------------------------------------------

"""
    Classes for laying out the Quasimode's transparent display.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import graphics
from enso.graphics import xmltextlayout
from enso.utils.xml_tools import escape_xml


# ----------------------------------------------------------------------------
# Layout Constants
# ----------------------------------------------------------------------------

# Constants determining the "rag-smoothing" process.  The delta is how
# close two rags need to be to require "smoothing" (i.e., widening one
# to match the other), and the max cycles is the maximum number of
# times to "smooth" the rags.
RAG_DELTA = 5
MAX_CYCLES = 8

# Left and right margins (in points)
L_MARGIN = 5
R_MARGIN = 7

# Top and bottom margins, in proportion to the relevant font size; i.e.,
# for a line with font size 20 and a top margin factor of .2, the top margin
# will be 4 (in whatever units).
TOP_MARGIN_FACTOR = .3
BOTTOM_MARGIN_FACTOR = .20

# A useful factor for determining the total height of the line, i.e.,
# the height of a given line is the global height factor times the font
# size.
HEIGHT_FACTOR = 1 + TOP_MARGIN_FACTOR + BOTTOM_MARGIN_FACTOR

# Colors
WHITE = "#ffffff"
DESIGNER_GREEN = "#9fbe57"
DARK_GREEN = "#7f9845"
BLACK = "#000000"

# Add alpha values to get transparent backgrounds.
DESCRIPTION_BACKGROUND_COLOR = DESIGNER_GREEN + "cc"
MAIN_BACKGROUND_COLOR = BLACK + "d8"

SMALL_SCALE = [ 12, 18, 24 ]
LARGE_SCALE = [ 24, 28, 32, 36, 40, 44, 48 ]
DESCRIPTION_SCALE = SMALL_SCALE
AUTOCOMPLETE_SCALE = LARGE_SCALE
SUGGESTION_SCALE = SMALL_SCALE


# ----------------------------------------------------------------------------
# Style Registries
# ----------------------------------------------------------------------------

def _newLineStyleRegistry():
    """
    Creates a new style registry for laying out one of the quasimode's
    text lines.
    """
    
    styles = xmltextlayout.StyleRegistry()
    styles.add( 
        "document",
        font_family = "Gentium",
        font_style = "normal",
        max_lines = "1",
        )
    styles.add(
        "line",
        text_align = "left",
        color = WHITE,
        margin_top = "0pt",
        margin_bottom = "0pt",
        )
    styles.add(
        "help",
        font_style = "italic",
        color = "#999999",
        )
    styles.add( "ins" )
    styles.add( "alt" )
    return styles

    
_AUTOCOMPLETE_STYLES = _newLineStyleRegistry()
_SUGGESTION_STYLES   = _newLineStyleRegistry()
_DESCRIPTION_STYLES  = _newLineStyleRegistry()
_DESCRIPTION_STYLES.update( "ins", color = DESIGNER_GREEN )
_DESCRIPTION_STYLES.update( "alt", color = BLACK )

XML_ALIASES = xmltextlayout.XmlMarkupTagAliases()
XML_ALIASES.add( "line", baseElement = "block" )
XML_ALIASES.add( "ins", baseElement = "inline" )
XML_ALIASES.add( "alt", baseElement = "inline" )
XML_ALIASES.add( "help", baseElement = "inline" )

def _updateStyleSizes( styles, size ):
    """
    Updates all size-related style elements to those suggested
    when the font is of 'size' points.

    styles should be a style registry.
    """

    width = graphics.getDesktopSize()[0]
    styles.update(
        "document",
        font_size = "%fpt" % size,
        width = "%fpt" % width,
        margin_top = "%fpt" % (TOP_MARGIN_FACTOR * size),
        margin_bottom = "%fpt" % (BOTTOM_MARGIN_FACTOR *size),
        line_height = "%fpt" % size,
        )


def _updateSuggestionColors( styles, active ):
    """
    Sets the color scheme in styles ( a style registry )
    to the correct one for active or inactive suggestions,
    depending on the value of active ( a boolean ).
    """

    if active:
        styles.update( "line", color = WHITE )
        styles.update( "ins", color = DARK_GREEN )
        styles.update( "alt", color = WHITE )
    else:
        styles.update( "line", color = DESIGNER_GREEN )
        styles.update( "ins", color = DARK_GREEN )
        styles.update( "alt", color = DESIGNER_GREEN )


def _updateStyles( styles, scale, size ):
    """
    Updates size and ellipsification styling information for
    the style registry 'styles', based on 'size' (a font size
    in points) and 'scale' (a list of usable font sizes in points).
    """
    
    _updateStyleSizes( styles, size )
    if size == scale[0]:
        # We're at the smallest possible size.  Ellispify if needed.
        styles.update( "document", ellipsify = "true" )
    else:
        styles.update( "document", ellipsify = "false" )
    return styles

def retrieveDescriptionStyles( size = DESCRIPTION_SCALE[-1] ):
    """
    LONGTERM TODO: Document this.
    """
    
    return _updateStyles( _DESCRIPTION_STYLES, DESCRIPTION_SCALE, size )


def retrieveAutocompleteStyles( active = True, size = LARGE_SCALE[-1] ):
    """
    LONGTERM TODO: Document this.
    """
    
    styles =  _updateStyles( _AUTOCOMPLETE_STYLES, AUTOCOMPLETE_SCALE, size )
    _updateSuggestionColors( styles, active )
    return styles


def retrieveSuggestionStyles( active = True, size = SMALL_SCALE[-1] ):
    """
    LONGTERM TODO: Document this.
    """
    
    styles = _updateStyles( _SUGGESTION_STYLES, SUGGESTION_SCALE, size )
    _updateSuggestionColors( styles, active )
    return styles


def layoutXmlLine( xml_data, styles, scale ):
    """
    Performs a layout of a line using xml_data and styles, doing
    its best to display all of the text of xml_data at the largest
    size allowed by scale (a list of font sizes).  If the text will
    not fit even at the smallest size of scale, then ellipsifies
    the text at that size.
    """
    
    document = None
    for size in reversed( scale ):
        try:
            _updateStyles( styles, scale, size )
            document = xmltextlayout.xmlMarkupToDocument(
                xml_data,
                styles,
                XML_ALIASES,
                )
            usedSize = size
            break
        except Exception:
            # NOTE: If the error is fundamental (not size-related),
            # then it will be raised again below

            # TODO: Figure out what exact types of exceptions are
            # "non-fundamental" and catch those instead of using
            # a blanket catch like this.

            pass

    if document == None:
        # no size above worked; use the smallest size
        _updateStyles( styles, scale, scale[0] )
        document = xmltextlayout.xmlMarkupToDocument(
            xml_data,
            styles,
            XML_ALIASES,
            )
        usedSize = scale[0]
    document.shrinkOffset = scale[-1] - usedSize
    return document


# ----------------------------------------------------------------------------
# Layout Classes
# ----------------------------------------------------------------------------

class QuasimodeLayout:
    """
    Class for calculating and storing layout metrics of the quasimode
    window.
    """

    LINE_XML = "<document><line>%s</line></document>"
    
    def __init__( self, quasimode ):
        """
        Computes and stores the layout metrics for the quasimode.
        """

        self.newLines = self.__newCreateLines( quasimode )
        self.__newSmoothRags()
        self.__newRoundCorners()
        self.__setBackgroundColors()
        
    def __newCreateLines( self, quasimode ):
        """
        LONGTERM TODO: Document this.
        """
    
        lines = []

        suggestionList = quasimode.getSuggestionList()
        description = suggestionList.getDescription()
        description = escape_xml( description )
        suggestions = suggestionList.getSuggestions()
        activeIndex = suggestionList.getActiveIndex()

        lines.append( layoutXmlLine(
            xml_data = self.LINE_XML % description, 
            styles = retrieveDescriptionStyles(),
            scale = DESCRIPTION_SCALE,
            ) )

        if len(suggestions[0].toXml()) == 0:
            text = suggestions[0].getSource()
            text = escape_xml( text )
        else:
            text = suggestions[0].toXml()

        lines.append( layoutXmlLine(
            xml_data = self.LINE_XML % text,
            styles = retrieveAutocompleteStyles( active = (activeIndex==0) ),
            scale = AUTOCOMPLETE_SCALE,
            ) )

        for index in range( 1, len(suggestions) ):
            isActive = (activeIndex==index)
            lines.append( layoutXmlLine(
                xml_data = self.LINE_XML % suggestions[index].toXml(),
                styles = retrieveSuggestionStyles( active = isActive ),
                scale = SUGGESTION_SCALE,
                ) )
            
        return lines
            

    def __setBackgroundColors( self ):
        """
        LONGTERM TODO: Document this.
        """
    
        self.newLines[0].background = \
             xmltextlayout.colorHashToRgba( DESCRIPTION_BACKGROUND_COLOR )
        for i in range( 1, len(self.newLines) ):
            self.newLines[i].background = \
                xmltextlayout.colorHashToRgba( MAIN_BACKGROUND_COLOR )
                
    
    def __newSmoothRags( self ):
        """
        Uses the computed size metrics to smooth the rags of the
        extended suggestions.
        """

        # To "smooth the rags" of the suggestion windows, we
        # repeatedly check for adjacent lines that differ in width by
        # less than a constant, and extend the smaller one to meet the
        # larger one.

        # By doing this multiple times with a small constant rather
        # than once or twice with a large constant, we get much better
        # results.  Only those lines that are nearly the same width
        # get corrected, and in the case that multiple lines are near
        # each other in size, the repetition causes a single smooth
        # edge to emerge.

        # LONGTERM TODO:Ideally, perhaps, this algorithm should simply
        # continue until all adjacent windows are either equal in
        # width or have widths greater than the constant.

        def _computeWidth( doc ):
            lines = []
            for b in doc.blocks:
                lines.extend( b.lines )
            if len( lines ) == 0:
                return 0
            return max( [ l.xMax for l in lines ] )

        for l in self.newLines:
            l.ragWidth = _computeWidth( l )
            
        for i in range( MAX_CYCLES ):
            widths = [ l.ragWidth for l in self.newLines ]
            for i in range( len(widths) - 1 ):
                if abs(widths[i]-widths[i+1]) < RAG_DELTA:
                    # If the widths of two adjacent windows are near
                    # each other, then set both to be the width of the
                    # wider one.
                    outsideWidth = max( widths[i], widths[i+1] )
                    self.newLines[i].ragWidth = outsideWidth
                    self.newLines[i+1].ragWidth = outsideWidth


    def __newRoundCorners( self ):
        """
        Sets all the appropriate corners to be rounded.
        """

        for l in self.newLines:
            l.roundLowerRight = False
            l.roundUpperRight = False

        lines = self.newLines
        for i in range( len(lines)-1 ):
            if lines[i+1].ragWidth < lines[i].ragWidth:
                lines[i].roundLowerRight = True

        for i in range( len(lines)-1 ):
            if lines[i].ragWidth < lines[i+1].ragWidth:
                lines[i+1].roundUpperRight = True

        lines[-1].roundLowerRight = True
        self.newLines = lines
