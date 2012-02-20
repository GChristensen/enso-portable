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
    This module provides a high-level interface for registering and
    accessing fonts, including their font metrics information, their
    glyphs, and their rendering.

    This module requires no initialization or shutdown.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import cairo

import Environment
import Humanized.Platform as Platform


# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------

class Font:
    """
    Encapsulates a font face, which describes both a given typeface
    and style.
    """
    
    def __init__( self, fileName, size, cairoContext ):
        """
        Creates a Font from the given filename pointing to a TrueType
        font file, at the given size (in points).
        """
        
        import os

        if not os.path.exists( fileName ):
            raise IOError( "file not found: %s" % fileName )

        self.fileName = fileName
        self.size = size
        self.cairoContext = cairoContext

        cairoContext.save()

        self.loadInto( cairoContext )

        # Make our font metrics information visible to the client.
        
        ( self.ascent,
          self.descent,
          self.height,
          self.maxXAdvance,
          self.maxYAdvance ) = cairoContext.font_extents()
        
        cairoContext.restore()

    @memoized
    def getGlyph( self, char ):
        """
        Returns a glyph of the font corresponding to the given Unicode
        character.
        """

        return FontGlyph( char, self, self.cairoContext )

    def getKerningDistance( self, charLeft, charRight ):
        """
        Returns the kerning distance (in points) between the two
        Unicode characters for this font face.
        """

        # LONGTERM TODO: Get this to work. This may involve modifying
        # the source code of Cairo.
        return 0.0

    def loadInto( self, cairoContext ):
        """
        Sets the cairo context's current font to this font.
        """

        # Note that we are using our own modified 'interpretation' of
        # the select_font_face() function here, as outlined in our
        # modified version of the Cairo FreeType 2 Font Module; see
        # the file 'cairo-ft-font.c' in our modified version of the
        # Cairo library for more information.
        fileName = Platform.toLegacyFilesystemEncoding( self.fileName )
        cairoContext.select_font_face(
            fileName,
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL
            )
        cairoContext.set_font_size( self.size )


# ----------------------------------------------------------------------------
# Font Glyphs
# ----------------------------------------------------------------------------

class FontGlyph:
    """
    Encapsulates a glyph of a font face.
    """
    
    def __init__( self, char, font, cairoContext ):
        """
        Creates the font glyph corresponding to the given Unicode
        character, using the font specified by the given Font object
        and the given cairo context.
        """
        
        # Encode the character to UTF-8 because that's what the cairo
        # API uses.
        self.charAsUtf8 = char.encode("UTF-8")
        self.char = char
        self.font = font

        cairoContext.save()
        
        self.font.loadInto( cairoContext )

        # Make our font glyph metrics information visible to the client.

        ( xBearing,
          yBearing,
          width,
          height,
          xAdvance,
          yAdvance ) = cairoContext.text_extents( self.charAsUtf8 )

        # The xMin, xMax, yMin, yMax, and advance attributes are used
        # here to correspond to their values in this image:
        # http://freetype.sourceforge.net/freetype2/docs/glyphs/Image3.png

        self.xMin = xBearing
        self.xMax = xBearing + width
        self.yMin = -yBearing + height
        self.yMax = -yBearing
        self.advance = xAdvance
        
        cairoContext.restore()


# ----------------------------------------------------------------------------
# The Font Registry
# ----------------------------------------------------------------------------

class FontRegistry:
    """
    This singleton represents a registry of font faces, allowing for a
    client to simply retrieve a Font object in a particular size and
    style rather without having to know the location of a specific
    TrueType file.
    """
    
    def __init__( self ):
        """
        Initializes the font registry.
        """
        
        self._registry = {}

        dummySurface = cairo.ImageSurface( cairo.FORMAT_ARGB32, 1, 1 )
        self.cairoContext = cairo.Context( dummySurface )


    def register( self, fileName, name, italic=False ):
        """
        Registers the given TrueType font filename as representing the
        given font name with the given style.
        """
        
        registryKey = (name, italic)

        if self._registry.has_key( registryKey ):
            raise FontAlreadyRegisteredError( registryKey )
        else:
            self._registry[registryKey] = fileName

    @memoized
    def get( self, name, size, italic=False ):
        """
        Retrieves a Font object corresponding to the given font name
        at the given size and style.
        """
        
        registryKey = (name, italic)

        fileName = self._registry[registryKey]
        return Font( fileName, size, self.cairoContext )


class FontAlreadyRegisteredError( Exception ):
    """
    Exception raised when the client attempts to register a font when
    that font has already been registered.
    """

    pass


# ----------------------------------------------------------------------------
# Singleton Instance
# ----------------------------------------------------------------------------

# The font registry singleton instance.
# LONGTERM TODO: SingletonWrap-ify this?
theFontRegistry = FontRegistry()
