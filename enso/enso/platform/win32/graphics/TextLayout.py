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
    Module for text layout.

    Text layout is accomplished by first laying-out the text one wants
    to render, and then rendering it.  Layout entities are
    heirarchically organied: the root layout element is the Document,
    which is made up of Blocks; Blocks are made up of Lines; and Lines
    are made up of Glyphs.

    The parameters used by this text layout interface is loosely based
    on CSS.  To fully understand this module's interface, consider
    reading the introduction to 'CSS Pocket Reference', 2nd edition.

    This system is fairly standard as far as text layout engines go;
    to fully understand its implementation, you should first
    understand the basics of font glyph conventions.  A great tutorial
    on this can be found here:

      http://freetype.sourceforge.net/freetype2/docs/glyphs/index.html
"""

# ----------------------------------------------------------------------------
# The Document Element
# ----------------------------------------------------------------------------

class Document:
    """
    Encapsulates a contiguous two-dimensional area of text layout.
    The Document is made up of Blocks, each of which corresponds to a
    vertical section of text with its own alignment and margins (e.g.,
    the <p> tag in HTML).
    """
    
    def __init__( self, width, marginTop, marginBottom ):
        """
        Creates a Document with the given width and margins, all in
        points.
        """

        # Standard style properties, taken directly from the
        # constructor parameters.
        self.width = width
        self.marginTop = marginTop
        self.marginBottom = marginBottom

        # List of blocks in the document.
        self.blocks = []

        # Total height of the block, in points.
        self.height = None
        
    def addBlock( self, block ):
        """
        Adds the given Block object to the document.
        """
        
        self.blocks.append( block )

    def layout( self ):
        """
        Lays out the Document; must always be caled before drawing the
        document and after all the blocks have been added.
        """
        
        blocksHeight = 0
        for block in self.blocks:
            block.layout()
            blocksHeight += block.height
        self.height = self.marginTop + blocksHeight + self.marginBottom

    def draw( self, x, y, cairoContext ):
        """
        Draws the document with its top-left corner at the given
        position (in points), using the given cairo context.
        """
        
        y += self.marginTop
        for block in self.blocks:
            block.draw( x, y, cairoContext )
            y += block.height


# ----------------------------------------------------------------------------
# The Block Element
# ----------------------------------------------------------------------------

class Block:
    """
    The Block element, which a Document is made of.  A Block consists
    of individual lines, and cannot have any layout elements to its
    sides.
    """
    
    def __init__( self, width, lineHeight, marginTop, marginBottom, textAlign,
                  maxLines, ellipsify ):
        """
        Creates a Block object with the given width, line height, and
        margins, all in points.  Also sets the alignment of the text
        block--this can be any one of 'left', right', 'center', or
        'justify'.

        If 'maxLines' is set, then the Block cannot exceed the given
        number of lines in length.  If 'ellipsify' is set, then the
        text is truncated with an ellipsis character if it exceeds
        that number of lines; otherwise, if the maximum number of
        lines is exceeded, a MaxLinesExceededError is thrown.
        """

        # Standard style properties, taken directly from the
        # constructor parameters.
        self.lineHeight = lineHeight
        self.marginTop = marginTop
        self.marginBottom = marginBottom
        self.width = width
        self.textAlign = textAlign
        self.maxLines = maxLines
        self.ellipsify = ellipsify

        # Temporary list of glyphs that need to be laid out into
        # lines.
        self.__glyphs = []

        # List of lines in the block.
        self.lines = []

        # Glyph that will be used as an ellipsis character if
        # necessary.
        self.ellipsisGlyph = None

        # Total height of the block, in points.
        self.height = None

    def setEllipsisGlyph( self, ellipsisGlyph ):
        """
        Sets the ellipsis glyph for the block; this is the glyph
        inserted at the end of the final line of a block if maxLines
        has been exceeded and ellipsify is set.
        """
        
        self.ellipsisGlyph = ellipsisGlyph

    def addGlyphs( self, glyphs ):
        """
        Adds the given glyphs to the block.
        """
        
        self.__glyphs.extend( glyphs )

    def __addLine( self, line, isPartialLine = False ):
        """
        Private method that adds the given line to the block.
        'isPartialLine' should be set to true if the line being added
        is not full--i.e., if the line doesn't have enough characters
        on it that it needs to be word-wrapped.
        """
        
        if isPartialLine and self.textAlign == "justify":
            # A partial line (e.g., the last line) of justified text
            # shouldn't be justified (or else it'll be "force
            # justify".
            alignment = "left"
        else:
            alignment = self.textAlign
        line.layout( alignment, self.width, self.lineHeight )
        self.lines.append( line )

    def layout( self ):
        """
        Lays out the block. This method should be called before the
        block is drawn, yet after all glyphs have been added to the
        block.
        """
        
        currLineLength = 0
        currWordStartIndex = 0
        currWordLength = 0
        currLine = Line()
        for i in range( len(self.__glyphs) ):
            assert( currLineLength >= currWordLength )

            glyph = self.__glyphs[i]
            advance = glyph.fontGlyph.advance

            if currLineLength + advance > self.width:
                # If we don't have *any* characters on this line yet,
                # that means the glyph advance is greater than this
                # block's width--we're in big trouble!
                if currLineLength == 0:
                    raise GlyphWiderThanBlockError(glyph)

                # Time to make a new line.

                if len( self.lines ) == self.maxLines-1:
                    # We've hit the max # of lines!
                    if not self.ellipsify:
                        raise MaxLinesExceededError()
                    else:
                        # We'll put an ellipsis at the end of this
                        # line and then break out of this loop,
                        # ignoring the rest of the glyphs.
                        currLine.addGlyphs(
                            self.__glyphs[currWordStartIndex:i]
                            )
                        currWordLength = 0
                        currLine.ellipsify( self.ellipsisGlyph,
                                            self.width )
                        break

                # Determine whether our current line has a word in it.
                currLineHasWord = (currLineLength != currWordLength)

                # If our current line has no words in it, just add
                # what we've got so far (not including the glyph we're
                # looking at) and count it as a "word".
                
                # Alternatively, if this character is whitespace, then
                # we're at the end of a word; we'll effectively
                # replace the whitespace with a newline.
                if not currLineHasWord or glyph.isWhitespace:
                    currLine.addGlyphs(
                        self.__glyphs[currWordStartIndex:i]
                        )

                    # If the current character we're looking at is
                    # whitespace, pretend it doesn't exist because
                    # we're at the end of a line.
                    if glyph.isWhitespace:
                        currWordStartIndex = i+1
                        currWordLength = 0
                    else:
                        currWordStartIndex = i
                        currWordLength = advance
                else:
                    # This character is part of a word.
                    currWordLength += advance

                # Now, create a new line.
                self.__addLine( currLine )
                currLineLength = currWordLength
                currLine = Line()
            elif glyph.isWhitespace:
                # We've reached the end of our word, and the beginning
                # of another.  Add this word, including this
                # whitespace character, to the current line.
                currLine.addGlyphs(
                    self.__glyphs[currWordStartIndex:i+1]
                    )
                currLineLength += advance
                currWordStartIndex = i+1
                currWordLength = 0
            else:
                # We're still building a word.
                currLineLength += advance
                currWordLength += advance

            assert( currLineLength >= currWordLength )

        assert( currLineLength >= currWordLength )

        # Now that we're done looking through all the glyphs, we can
        # safely add the last remaining word to the current line.
        if currWordLength > 0:
            currLine.addGlyphs(
                self.__glyphs[currWordStartIndex:]
                )

        # If our current (i.e., last) line has anything on it, we're
        # going to add it to the block.
        if currLineLength > 0:
            self.__addLine( currLine, isPartialLine = True )

        self.__glyphs = None
        self.height = self.marginTop + \
                      self.lineHeight * len(self.lines) + \
                      self.marginBottom

    def draw( self, x, y, cairoContext ):
        """
        Draws the block with its upper-left corner at the given
        coordinates (in points), using the given cairo context.
        """
        
        for line in self.lines:
            line.draw( x, y, cairoContext )
            y += self.lineHeight


class GlyphWiderThanBlockError( Exception ):
    """
    Exception raised when a glyph is wider than a block and therefore
    can't be added to the block.
    """

    pass


class MaxLinesExceededError( Exception ):
    """
    Exception thrown by a Block object when the maximum number of
    lines for the block has been exceeded.
    """
    
    pass


# ----------------------------------------------------------------------------
# The Line Element
# ----------------------------------------------------------------------------

class Line:
    """
    Encapsulates a line, made up of glyphs.

    Note that some of the documentation for this class uses
    terminology taken from Cascading Style Sheets; in particular, see
    'CSS Pocket Reference', 2nd edition, pgs. 12-13.
    """
    
    def __init__( self ):
        """
        Creates an empty line.
        """
        
        self.glyphs = []

        # Current cursor position at which next glyph will be placed
        # on line.
        self.__cursorPos = 0.0

        # X-offset for alignment (left, right, centered, etc.).
        self.__alignOfs = 0.0

        # Offset per space for justified text.
        self.__ofsPerSpace = 0.0

        # Ascent of the line above the baseline, in points.
        self.ascent = None

        # Descent of the line below the baseline, in points.
        self.descent = None

        # Height of the line's line box, in points.
        self.lineHeight = None

        # External leading of the line (the leading minus the line's
        # ascent and descent).
        self.externalLeading = None

        # Distance from the top of the line's line box to its baseline.
        self.distanceToBaseline = None
        
        # The bounding box in screen coordinates, relative to the
        # top-left of the line's line box.
        self.xMin = None
        self.yMin = None
        self.xMax = None
        self.yMax = None

    def layout( self, alignment, width, lineHeight ):
        """
        Lays out the glyphs on the line; this should be called after
        adding all glyphs to the line, but before drawing it.

        Takes as parameters the alignment of the line ('left',
        'right', 'center', or 'justify'), the width of the line in
        points, and the line height in points.
        """
        
        # Local variables xMin, xMax, yMin, and yMax are used here to
        # correspond to their values in this image:
        # http://freetype.sourceforge.net/freetype2/docs/glyphs/Image3.png
        
        # Cut off a trailing whitespace character, if it exists.
        if len( self.glyphs ) > 1 and self.glyphs[-1].isWhitespace:
            self.glyphs = self.glyphs[:-1]

        # Determine our bounding box.
        INFINITY = 999999999
        
        xMin = INFINITY
        xMax = -INFINITY
        yMin = INFINITY
        yMax = -INFINITY

        # Calculate the line's bounding box relative to the baseline
        # origin of the line.
        for glyph in self.glyphs:
            glyphXMin = glyph.pos + glyph.fontGlyph.xMin
            glyphXMax = glyph.pos + glyph.fontGlyph.xMax
            glyphYMin = glyph.fontGlyph.yMin
            glyphYMax = glyph.fontGlyph.yMax

            if glyphXMin < xMin:
                xMin = glyphXMin
            if glyphXMax > xMax:
                xMax = glyphXMax
            if glyphYMin < yMin:
                yMin = glyphYMin
            if glyphYMax > yMax:
                yMax = glyphYMax

        bboxWidth = xMax - xMin
        if alignment == "left":
            self.__alignOfs = -xMin
        elif alignment == "right":
            self.__alignOfs = width - xMax
        elif alignment == "center":
            self.__alignOfs = (width / 2) - (bboxWidth / 2)
        elif alignment == "justify":
            # First, left align our text.
            self.__alignOfs = -xMin
            # Next, figure out how much extra padding we need per
            # space character.
            spaceCount = 0
            for glyph in self.glyphs:
                if glyph.isWhitespace:
                    spaceCount += 1
            if spaceCount == 0:
                # No spaces in this line!  We'll just have to
                # left-align this one.
                self.__alignOfs = -xMin
            else:
                widthNeeded = width - bboxWidth
                self.__ofsPerSpace = widthNeeded / spaceCount
                xMax = width
        else:
            raise InvalidAlignmentError( alignment )

        # Determine some line metrics information.
        self.ascent = max( [glyph.font.ascent for glyph in self.glyphs] )
        self.descent = max( [glyph.font.descent for glyph in self.glyphs] )

        self.lineHeight = lineHeight
        self.externalLeading = ( self.lineHeight -
                                 (self.ascent +
                                  self.descent) )
        self.distanceToBaseline = ( self.externalLeading / 2.0 ) + \
                                  self.ascent
        
        # Set the bounding box in screen coordinates, relative to the
        # top-left of the line's line box.
        self.xMin = xMin + self.__alignOfs
        self.yMin = -yMax + self.distanceToBaseline
        self.xMax = xMax + self.__alignOfs
        self.yMax = -yMin + self.distanceToBaseline

    def addGlyphs( self, glyphs ):
        """
        Adds the given glyphs to the end of the line.
        """
        
        if len( self.glyphs ) > 0:
            lastGlyph = self.glyphs[-1]
        else:
            lastGlyph = None

        for glyph in glyphs:
            if lastGlyph:
                # Perform kerning, if possible.
                if ( glyph.font == lastGlyph.font ):
                    kernDist = glyph.font.getKerningDistance(
                        lastGlyph.char, glyph.char
                        )
                    self.__cursorPos += kernDist
            glyph.pos = self.__cursorPos
            self.__cursorPos += glyph.fontGlyph.advance
            lastGlyph = glyph
        self.glyphs.extend( glyphs )

    def removeGlyph( self ):
        """
        Removes the last glyph from the line.
        """

        removedGlyph = self.glyphs.pop()
        self.__cursorPos = removedGlyph.pos

    def ellipsify( self, ellipsisGlyph, maxWidth ):
        """
        'Ellipsifies' this line by removing its current glyphs until
        this line with the given ellipsis glyph appended is shorter
        than the given maximum width.  Then, the ellipsis glyph is
        appended to the line.
        """
        
        ellipsisWidth = ellipsisGlyph.fontGlyph.advance

        # Remove glyphs (if necessary) until there's enough room on
        # this line for an ellipsis.
        while self.__cursorPos + ellipsisWidth > maxWidth:
            self.removeGlyph()

        # Add the ellipsis to the end of this line.
        self.addGlyphs( [ellipsisGlyph] )

    def draw( self, x, y, cairoContext ):
        """
        Draws the line to the given cairo context so that the top-left
        of the line's line box is at the given coordinates, in points.
        """
        
        y += self.distanceToBaseline
        spaceOfs = 0.0
        glyphX = 0.0
        currFont = None
        for glyph in self.glyphs:
            glyphX = spaceOfs + \
                     self.__alignOfs + \
                     x + \
                     glyph.pos

            if not glyph.isWhitespace:
                if currFont != glyph.font:
                    currFont = glyph.font
                    currFont.loadInto( cairoContext )
                cairoContext.set_source_rgba( *glyph.color )
                cairoContext.move_to( glyphX, y )

                cairoContext.show_text( glyph.charAsUtf8 )
            else:
                spaceOfs += self.__ofsPerSpace


class InvalidAlignmentError( Exception ):
    """
    Exception raised when an invalid alignment is used as an argument
    to a function or method.
    """
    
    pass


# ----------------------------------------------------------------------------
# The Glyph Element
# ----------------------------------------------------------------------------

class Glyph:
    """
    The smallest element of text layout, the glyph encapsulates a
    single character on a line, including its font, style, size, and
    color.
    """


    def __init__( self, fontGlyph, color ):
        """
        Creates the glyph from the given font glyph and color.
        """
        
        self.fontGlyph = fontGlyph
        self.color = color
        self.pos = 0.0

        # These are just copies of attributes from fontGlyph to make
        # their lookup easier.
        self.char = fontGlyph.char
        self.charAsUtf8 = fontGlyph.charAsUtf8
        self.font = fontGlyph.font

        # Whether this glyph represents valid, breaking whitespace.
        self.isWhitespace = (self.char == " ")

    def __repr__( self ):
        """
        Returns a textual representation of this glyph for debugging.
        """

        char = self.char.encode( "ascii", "replace" )
        return "<TextLayout Glyph '%s'>" % char
