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

#   Python Version - 2.4

"""
    Module for XML text layout.

    This module implements a high-level XML-based interface to the
    TextLayout module.  It also provides a simple style mechanism that
    is heavily based on the Cascading Style Sheets (CSS) system.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import xml.sax
import xml.sax.handler

import Environment
import Measurement
import TextLayout
import Font


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Ordinarily, we'd use the unicodedata module for this, but it's a
# hefty file so we'll just define values here.
NON_BREAKING_SPACE = u"\u00a0"


# ----------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------

@memoized
def colorHashToRgba( colorHash ):
    """
    Converts the given HTML-style color hash (e.g., '#aabbcc') or
    HTML-with-alpha color hash (e.g. '#aabbccdd') to a quad-color (r,
    g, b, a) tuple and returns the result.

    Examples:

    >>> colorHashToRgba( '#ffffff' )
    (1.0, 1.0, 1.0, 1.0)

    >>> colorHashToRgba( '#ff000000' )
    (1.0, 0.0, 0.0, 0.0)
    """
    
    colorHash = colorHash[1:]
    if len(colorHash) == 6:
        # It's a RGB hash.
        alphaHex = "FF"
    elif len(colorHash) == 8:
        # It's a RGBA hash.
        alphaHex = colorHash[6:8]
    else:
        raise ValueError("Can't parse color hash for '#%s'" % colorHash)

    redHex = colorHash[0:2]
    greenHex = colorHash[2:4]
    blueHex = colorHash[4:6]

    red = float( int(redHex, 16) )
    green = float( int(greenHex, 16) )
    blue = float( int(blueHex, 16) )
    alpha = float( int(alphaHex, 16) )

    return ( red / 255.0, green / 255.0, blue / 255.0, alpha / 255.0 )


def stringToBool( string ):
    """
    Converts a string with the contents 'true' or 'false' to the
    appropriate boolean value.

    Examples:

    >>> stringToBool( 'true' )
    True

    >>> stringToBool( 'false' )
    False

    >>> stringToBool( 'True' )
    Traceback (most recent call last):
    ...
    ValueError: can't convert to boolean: True
    """

    if string == "true":
        return True
    elif string == "false":
        return False
    else:
        raise ValueError( "can't convert to boolean: %s" % string )


# ----------------------------------------------------------------------------
# Style Properties
# ----------------------------------------------------------------------------

# Style properties that are inherited from a parent element to a child
# element.
STYLE_INHERITED_PROPERTIES = [
    # The following properties are identical to the CSS properties of
    # the same name, with the exception that any underscores should be
    # replaced by hyphens.
    "width",
    "text_align",
    "line_height",
    "color",
    "font_style",
    "font_family",
    "font_size",

    # This property defines the maximum number of lines that the
    # element can contain, and is only valid for Block elements; if
    # the element's lines exceed this number and the 'ellipsify'
    # property is false, a TextLayout.MaxLinesExceededError is raised.
    "max_lines",

    # This property defines whether or not to truncate a Block element
    # with an ellipsis ('...') if the Block's number of lines exceeds
    # that prescribed by the "max_lines" property.
    "ellipsify"
    ]


# Style properties that are uninherited from a parent element to a
# chid element.
STYLE_UNINHERITED_PROPERTIES = [
    # The following properties are identical to the CSS properties of
    # the same name, with the exception that any underscores should be
    # replaced by hyphens.
    "margin_top",
    "margin_bottom"
    ]


# All possibilities of styles defined by this module.
STYLE_PROPERTIES = (
    STYLE_INHERITED_PROPERTIES +
    STYLE_UNINHERITED_PROPERTIES
    )


# ----------------------------------------------------------------------------
# Style Registry
# ----------------------------------------------------------------------------

class StyleRegistry:
    """
    Registry of styles used by XML text layout markup.  Note that this
    class is not a singleton; rather, one StyleRegistry instance
    exists for each document that the client wants to layout.
    """
    
    def __init__( self ):
        """
        Creates an empty StyleRegistry object.
        """
        
        self._styleDict = {}

    def __validateKeys( self, dict ):
        """
        Makes sure that the keys of dict are the names of valid style
        properties.
        """

        invalidKeys = [ key for key in dict.keys() \
                        if key not in STYLE_PROPERTIES ]
        if len( invalidKeys ) > 0:
            raise InvalidPropertyError( str(invalidKeys) )


    def add( self, selector, **properties ):
        """
        Adds the given style selector with the given properties to the
        style registry.  If any of the properties are invalid, an
        InvalidPropertyError is thrown.

        Examples:

        >>> styles = StyleRegistry()
        >>> styles.add( 'document', width = '1000pt' )
        >>> styles.add( 'p', foo = '1000pt' )
        Traceback (most recent call last):
        ...
        InvalidPropertyError: ['foo']

        It should also be noted that the same style selector can't be
        defined more than once, e.g.:

        >>> styles.add( 'foo', width = '1000pt' )
        >>> styles.add( 'foo', width = '1000pt' )
        Traceback (most recent call last):
        ...
        ValueError: Style 'foo' already exists.
        """

        if self._styleDict.has_key( selector ):
            raise ValueError( "Style '%s' already exists." % selector )
        
        self.__validateKeys( properties )
        self._styleDict[ selector ] = properties

    def findMatch( self, selector ):
        """
        Given a selector, returns the style dictionary corresponding
        to it.  If no match is found, this method returns None.

        Each key of the returned style dictionary corresponds to a
        style property, while each value corresponds to the value of
        the style property.

        Examples:

        >>> styles = StyleRegistry()
        >>> styles.add( 'document', width = '1000pt' )
        >>> styles.findMatch( 'document' )
        {'width': '1000pt'}

        >>> styles.findMatch( 'mystyle' ) == None
        True
        """
        
        return self._styleDict.get( selector, None )

    @contractify
    def update( self, selector, **properties ):
        """
        Updates the styles for selector to those described by
        properties.

        Examples:

        >>> styles = StyleRegistry()
        >>> styles.add( 'document', width = '1000pt' )
        >>> styles.update( 'document', margin_top = '24pt' )
        >>> styles.findMatch( 'document' )
        {'width': '1000pt', 'margin_top': '24pt'}

        Preconditions:
          selector in self._styleDict.keys()
        End Contract
        """

        self.__validateKeys( properties )
        self._styleDict[ selector ].update( properties )
        
        
class InvalidPropertyError( Exception ):
    """
    Exception raised by the StyleRegistry when a style with invalid
    properties is added to the registry.
    """
    
    pass


# ----------------------------------------------------------------------------
# Cascading Style Stack
# ----------------------------------------------------------------------------

class CascadingStyleStack:
    """
    Encapsulates the CSS-like 'cascading' style mechanism supported by
    the XML text layout markup.
    """

    # This is just a set version of STYLE_UNINHERITED_PROPERTIES.
    uninheritedProps = set( STYLE_UNINHERITED_PROPERTIES )

    def __init__( self ):
        """
        Creates an empty stack.
        """
        
        self.__stack = []

    def push( self, newStyle ):
        """
        Push a new style onto the Cascading Style Stack, making it the
        current style.
        """
        
        if len( self.__stack ) > 0:
            # "Cascade" the new style by combining it with our current
            # style, removing any uninherited properties first.

            currStyle = self.__stack[-1].copy()
            props = self.uninheritedProps.intersection( currStyle.keys() )

            for key in props:
                del currStyle[key]

            currStyle.update( newStyle )
            self.__stack.append( currStyle )
        else:
            # Set this style as our current style.
            
            self.__stack.append( newStyle )

    def pop( self ):
        """
        Remove the current style from the Cascading Style Stack.
        """

        self.__stack.pop()

    def _strToPoints( self, unitsStr ):
        """
        Converts from a string such as '1em', '2pt', '3in', '5pc', or
        '20px' into a floating-point value measured in points.
        """

        if unitsStr.endswith( "em" ):
            currEmSizeStr = self.__stack[-1]["font_size"]
            currEmSize = self._strToPoints( currEmSizeStr )
            units = float( unitsStr[:-2] )
            return units * currEmSize
        else:
            return Measurement.strToPoints( unitsStr )

    def _propertyToPoints( self, propertyName ):
        """
        Converts the value of the given property name into a
        floating-point value measured in points.
        """
        
        propertyStr = self.__stack[-1][propertyName]
        return self._strToPoints( propertyStr )

    def _propertyToInt( self, propertyName ):
        """
        Converts the value of the given property name into an integer
        value.
        """
        
        return int( self.__stack[-1][propertyName] )

    def _propertyToBool( self, propertyName ):
        """
        Converts the value of the given property name into a boolean
        value.
        """
        
        return stringToBool( self.__stack[-1][propertyName] )

    def _propertyToColor( self, propertyName ):
        """
        Converts the value of the given property name into a (r, g, b,
        a) color tuple.
        """
        
        return colorHashToRgba( self.__stack[-1][propertyName] )

    def _property( self, propertyName ):
        """
        Returns the value of the given property name as a string.
        """
        
        return self.__stack[-1][propertyName]

    def makeNewDocument( self ):
        """
        Makes a new document with the current style.
        """

        document = TextLayout.Document(
            width = self._propertyToPoints("width"),
            marginTop = self._propertyToPoints("margin_top"),
            marginBottom = self._propertyToPoints("margin_bottom"),
            )

        return document

    def makeNewBlock( self ):
        """
        Makes a new block with the current style.
        """

        block = TextLayout.Block(
            width = self._propertyToPoints("width"),
            lineHeight = self._propertyToPoints("line_height"),
            marginTop = self._propertyToPoints("margin_top"),
            marginBottom = self._propertyToPoints("margin_bottom"),
            textAlign = self._property("text_align"),
            maxLines = self._propertyToInt("max_lines"),
            ellipsify = self._propertyToBool("ellipsify")
            )
        
        return block
    
    def makeNewGlyphs( self, characters ):
        """
        Makes new glyphs with the current style.
        """

        glyphs = []
        
        font = Font.theFontRegistry.get(
            self._property( "font_family" ),
            self._propertyToPoints( "font_size" ),
            self._property( "font_style" ) == "italic"
            )

        color = self._propertyToColor( "color" )

        for char in characters:
            fontGlyph = font.getGlyph( char )
            glyph = TextLayout.Glyph(
                fontGlyph,
                color,
                )
            glyphs.append( glyph )

        return glyphs


# ----------------------------------------------------------------------------
# XML Markup Tag Aliases
# ----------------------------------------------------------------------------

class XmlMarkupTagAliases:
    """
    Implementation of XML markup tag aliases, a simple feature that
    allows one tag name to be aliased as another tag name.
    """
    
    def __init__( self ):
        """
        Creates an empty set of tag aliases.
        """
        
        self._aliases = {}

    def add( self, name, baseElement ):
        """
        Adds a tag alias; 'name' will now be an alias for
        'baseElement'.

        The following example sets up tag aliases for <p> and
        <caption> tags:

        >>> tagAliases = XmlMarkupTagAliases()
        >>> tagAliases.add( 'p', baseElement = 'block' )
        >>> tagAliases.add( 'caption', baseElement = 'block' )

        It should also be noted the same tag alias can't be defined
        more than once, e.g.:
        
        >>> tagAliases.add( 'foo', baseElement = 'inline' )
        >>> tagAliases.add( 'foo', baseElement = 'block' )
        Traceback (most recent call last):
        ...
        ValueError: Tag alias 'foo' already exists.
        """

        if self._aliases.has_key( name ):
            raise ValueError( "Tag alias '%s' already exists." % name )

        self._aliases[name] = baseElement

    def get( self, name ):
        """
        Retrieves the tag that the given name is an alias for.

        Example:

        >>> tagAliases = XmlMarkupTagAliases()
        >>> tagAliases.add( 'p', baseElement = 'block' )
        >>> tagAliases.get( 'p' )
        'block'
        >>> tagAliases.get( 'caption' )
        Traceback (most recent call last):
        ...
        KeyError: 'caption'
        """
        
        return self._aliases[name]

    def has( self, name ):
        """
        Returns whether or not the given name is an alias for a tag.

        Example:

        >>> tagAliases = XmlMarkupTagAliases()
        >>> tagAliases.add( 'p', baseElement = 'block' )
        >>> tagAliases.has( 'p' )
        True
        >>> tagAliases.has( 'caption' )
        False
        """
        
        return self._aliases.has_key( name )


# ----------------------------------------------------------------------------
# XML Markup Content Handler
# ----------------------------------------------------------------------------

class _XmlMarkupHandler( xml.sax.handler.ContentHandler ):
    """
    XML content handler for XML text layout markup.
    """
    
    def __init__( self, styleRegistry, tagAliases=None ):
        """
        Initializes the content handler with the given style registry
        and tag aliases.
        """
        
        xml.sax.handler.ContentHandler.__init__( self )
        self.styleRegistry = styleRegistry

        if not tagAliases:
            tagAliases = XmlMarkupTagAliases()
        self.tagAliases = tagAliases

    def startDocument( self ):
        """
        Called by the XML parser at the beginning of parsing the XML
        document.
        """
        
        self.style = CascadingStyleStack()
        self.document = None
        self.block = None
        self.glyphs = None

    def _pushStyle( self, name, attrs ):
        """
        Sets the current style to the style defined by the "style"
        attribute of the given tag.  If that style doesn't exist, we
        use the style named by the tag.
        """

        styleDict = None

        styleAttr = attrs.get( "style", None )
        if styleAttr:
            styleDict = self.styleRegistry.findMatch( styleAttr )

        if styleDict == None:
            styleDict = self.styleRegistry.findMatch( name )

        if styleDict == None:
            raise ValueError, "No style found for: %s, %s" % (
                name,
                str( styleAttr )
                )

        self.style.push( styleDict )

    def startElement( self, name, attrs ):
        """
        Handles the beginning of an XML element.
        """
        
        if name == "document":
            self._pushStyle( name, attrs )
            self.document = self.style.makeNewDocument()
        elif name == "block":
            if not self.document:
                raise XmlMarkupUnexpectedElementError(
                    "Block element encountered outside of document element."
                    )
            self._pushStyle( name, attrs )
            self.block = self.style.makeNewBlock()
            self.glyphs = []
        elif name == "inline":
            if not self.block:
                raise XmlMarkupUnexpectedElementError(
                    "Inline element encountered outside of block element."
                    )
            self._pushStyle( name, attrs )
        elif self.tagAliases.has( name ):
            baseElement = self.tagAliases.get( name )
            self.startElement( baseElement, { "style" : name } )
        else:
            raise XmlMarkupUnknownElementError( name )

    def endElement( self, name ):
        """
        Handles the end of an XML element.
        """
        
        if name == "document":
            self.style.pop()
            self.document.layout()
        elif name == "block":
            ellipsisGlyph = self.style.makeNewGlyphs( u"\u2026" )[0]
            self.block.setEllipsisGlyph( ellipsisGlyph )
            
            self.style.pop()
            self.block.addGlyphs( self.glyphs )
            self.document.addBlock( self.block )
            self.block = None
            self.glyphs = None
        elif name == "inline":
            self.style.pop()
        else:
            baseElement = self.tagAliases.get( name )
            self.endElement( baseElement )

    def characters( self, content ):
        """
        Handles XML character data.
        """

        if self.glyphs != None:
            self.glyphs.extend( self.style.makeNewGlyphs(content) )
        else:
            # Hopefully, the content is just whitespace...
            content = content.strip()
            if content:
                raise XmlMarkupUnexpectedCharactersError( content )


class XmlMarkupUnknownElementError( Exception ):
    """
    Exception raised when an unknown XML text layout markup element is
    encountered.
    """
    
    pass


class XmlMarkupUnexpectedElementError( Exception ):
    """
    Exception raised when a recognized, but unexpected XML text layout
    markup element is encountered.
    """
    
    pass


class XmlMarkupUnexpectedCharactersError( Exception ):
    """
    Exception raised when characters are encountered in XML text
    layout in a place where they're not expected.
    """
    
    pass


# ----------------------------------------------------------------------------
# XML Markup to Document Conversion
# ----------------------------------------------------------------------------

def xmlMarkupToDocument( text, styleRegistry, tagAliases=None ):
    """
    Converts the given XML text into a TextLayout.Document object that
    has been fully laid out and is ready for rendering, using the
    given style registry and tag alises.
    """

    import re
    
    # Convert all occurrences of multiple contiguous whitespace
    # characters to a single space character.
    text = re.sub( r"\s+", " ", text )

    # Convert all occurrences of the non-breaking space character
    # entity reference into its unicode equivalent (the SAX XML parser
    # doesn't recognize this one on its own, sadly).
    text = text.replace( "&nbsp;", NON_BREAKING_SPACE )

    xmlMarkupHandler = _XmlMarkupHandler( styleRegistry, tagAliases )
    xml.sax.parseString( text, xmlMarkupHandler )
    return xmlMarkupHandler.document
