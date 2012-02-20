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
#   enso.graphics.font
#
# ----------------------------------------------------------------------------

"""
    This module provides a high-level interface for registering and
    accessing fonts, including their font metrics information, their
    glyphs, and their rendering.

    This module requires no initialization or shutdown.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso import cairo

from enso.utils.memoize import memoized


# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------

class Font:
    """
    Encapsulates a font face, which describes both a given typeface
    and style.
    """

    _cairoContext = None

    def __init__( self, name, size, isItalic ):
        """
        Creates a Font with the given properties.
        """

        self.name = name
        self.size = size
        self.isItalic = isItalic

        if self.isItalic:
            self.slant = cairo.FONT_SLANT_ITALIC
        else:
            self.slant = cairo.FONT_SLANT_NORMAL

        if not Font._cairoContext:
            dummySurface = cairo.ImageSurface( cairo.FORMAT_ARGB32, 1, 1 )
            Font._cairoContext = cairo.Context( dummySurface )

        self.cairoContext = Font._cairoContext

        self.cairoContext.save()

        self.loadInto( self.cairoContext )

        # Make our font metrics information visible to the client.
        
        ( self.ascent,
          self.descent,
          self.height,
          self.maxXAdvance,
          self.maxYAdvance ) = self.cairoContext.font_extents()
        
        self.cairoContext.restore()

    @classmethod
    @memoized
    def get( cls, name, size, isItalic ):
        """
        Retrieves the Font object with the given properties.

        The fact that this class method is memoized effectively makes
        this mechanism a flyweight pool of Font objects.
        """

        return cls( name, size, isItalic )

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


        # TODO THE WINDOWS SPECIAL CASE WITH THE HARD-CODED PATH TO ARIAL
        # IS A HORRIBLE HACK AND MUST BE FIXED ASAP (besides, Arial is
        # ugly).
        import sys
        if sys.platform.startswith( "win" ):
            cairoContext.select_font_face(
                "c:/WINDOWS/Fonts/arial.ttf",
                self.slant,
                cairo.FONT_WEIGHT_NORMAL
                )
        else:
            cairoContext.select_font_face(
                self.name,
                self.slant,
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
