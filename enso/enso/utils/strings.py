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
#   enso.utils.strings
#
# ----------------------------------------------------------------------------

"""
    Various string utility methods.
"""

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Double "smart quotes".
OPEN_QUOTE = "\u201C"
CLOSE_QUOTE = "\u201D"

# Single "smart quotes".
OPEN_SINGLE_QUOTE = "\u2018"
CLOSE_SINGLE_QUOTE = "\u2019"


# ----------------------------------------------------------------------------
# String utility functions
# ----------------------------------------------------------------------------

def smartQuote( text ):
    """
    Replaces regular quotes in text with "smart quotes", i.e., left and right
    facing quotes, and returns the result as a unicode object.

    NOTE: This uses a very simple algorithm; if you are trying to quote
    an arbitrary chunk of text, it would be best to use this function
    on your formatting string, e.g., use this on:
        ' %s ' - output from blah command
    before you apply the formatting operation that dumps unknown text.
    """

    text = _smartDoubleQuote( text )
    text = _smartSingleQuote( text )

    return text


def _smartSingleQuote( inText ):
    """
    Replaces single quotes with "smart quotes", i.e., forward
    and back facing quotes, except for single quotes that are
    parts of certain contractions.
    """
    
    # Explicitly copy the text and cast it to unicode.
    outText = str( inText[:] )

    # There are two usages of single quote marks; for
    # quotations, and for contractions.

    # First, we escape the contraction cases.  Then,
    # without those pesky apostrophes, we will be free
    # and clear to replace the remaining single quotes
    # with smart quotes.

    cases = [ "'s", "'t", "'nt", "I'm", "'ve", "'re", ]
    for case in cases:
        tempText = "<<|%s|>>" % case.replace( "'", "" )
        outText = outText.replace( case, tempText )

    # Now that there are no apostrophes, we can run through
    # the text, replacing each pair of single quotes with
    # opening and closing 'smart single quotes'.
    while outText.count( "'" ) > 0:
        outText = outText.replace( "'", OPEN_SINGLE_QUOTE, 1)
        outText = outText.replace( "'", CLOSE_SINGLE_QUOTE, 1)

    # Now we have to replace the contraction escape sequences
    # with the original contractions.
    for case in cases:
        tempText = "<<|%s|>>" % case.replace( "'", "" )
        outText = outText.replace( tempText, case )

    return outText


def _smartDoubleQuote( inText ):
    """
    Replaces double quotes with "smart quotes", i.e., forward
    and back facing quotes.
    """
    
    # Explicitly copy the text and cast it to unicode.
    outText = str( inText[:] )
    while outText.count( "\"" ) > 0:
        outText = outText.replace( "\"", OPEN_QUOTE, 1)
        outText = outText.replace( "\"", CLOSE_QUOTE, 1)
    return outText
    

def stringRatio( a, b ):
    """
    Calculates the string ratio of a to b.

    If the strings are equal, returns 1.0.  If they have no similarity
    whatsoever, returns 0.0.  Otherwise, returns a number in-between.
    """

    if a == b:
        return 1.0
    elif a in b:
        return float( len(a) ) / len(b)
    elif b in a:
        return float( len(b) ) / len(a)
    else:
        # The following code is actually identical to this code:
        #
        #  import difflib
        #  seqMatch = difflib.SequenceMatcher( False, a, b )
        #  ratio = seqMatch.real_quick_ratio()
        #  return ratio
        #
        # But has been copied from difflib and pasted inline here for
        # efficiency purposes.
        
        la, lb = len(a), len(b)

        length = la + lb
        if length:
            return 2.0 * (min(la, lb)) / length
        return 1.0


def stringRatioBestMatch( item, sequence ):
    """
    Uses a string ratio algorithm to find to the best match
    to item among the elements of sequence.
    """

    ratios = [ stringRatio( item, element ) \
               for element in sequence ]

    return sequence[ ratios.index( min(ratios) ) ]
