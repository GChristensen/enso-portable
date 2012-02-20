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
#   enso.graphics.measurement
#
# ----------------------------------------------------------------------------

"""
   Screen measurement-related functionality.

   This module handles coordinate conversion calculations and
   maintains information on the pixel density of the screen.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from enso.utils.memoize import memoized


# ----------------------------------------------------------------------------
# Pixels-Per-Inch (PPI) Getter/Setter
# ----------------------------------------------------------------------------

DEFAULT_PPI = 96.0

_ppi = DEFAULT_PPI

def setPixelsPerInch( ppi ):
    """
    Sets the current PPI of the screen in the Measurement module. This
    alters the state of the module, in that any functions depending on
    the PPI of the screen will use the value passed into this
    function.

    It is further assumed that the screen has square pixels (i.e., the
    horizontal and vertical PPI of the screen are the same).
    """
    
    global _ppi
    _ppi = float(ppi)

def getPixelsPerInch():
    """
    Returns the current PPI of the screen in the Measurement module.
    """
    
    return _ppi


# ----------------------------------------------------------------------------
# Unit-of-Measurement Conversion Functions
# ----------------------------------------------------------------------------

def pointsToPixels( points ):
    """
    Converts the given number of points to pixels, using the current
    PPI settings.
    """
    
    return points * getPixelsPerInch() / 72.0

def pixelsToPoints( pixels ):
    """
    Converts the given number of pixels to points, using the current
    PPI settings.
    """
    
    return pixels * 72.0 / getPixelsPerInch() 

def inchesToPoints( inches ):
    """
    Converts the given number of inches to points.
    """
    
    return inches * 72.0

def picasToPoints( picas ):
    """
    Converts the given number of picas to points.
    """
    
    return picas * 12.0

def calculateScreenPpi( screenDiagonal, hres, vres ):
    """
    Given a screen's diagonal in inches, and the horizontal &
    vertical resolution in pixels, calculates the pixels per inch of
    the screen.
    """

    import math
    diagonalInPixels = math.sqrt( hres**2 + vres**2 )
    return int( diagonalInPixels / screenDiagonal )

def convertUserSpaceToPoints( cairoContext ):
    """
    Modifies the CTM of a Cairo Context so that all future drawing
    operations on it can be specified in units of points rather than
    pixels.

    It is assumed that prior to this call, the Cairo Context's CTM is
    the identity matrix.
    """
    
    scaleFactor = getPixelsPerInch() / 72.0
    cairoContext.scale( scaleFactor, scaleFactor )

@memoized
def strToPoints( unitsStr ):
    """
    Converts from a string such as '2pt', '3in', '5pc', or '20px' into
    a floating-point value measured in points.

    Examples:

      >>> setPixelsPerInch( 72 )
      >>> strToPoints( '1in' )
      72.0
      >>> strToPoints( '1pt' )
      1.0
      >>> strToPoints( '5pc' )
      60.0
      >>> strToPoints( '72px' )
      72.0
      >>> strToPoints( '125em' )
      Traceback (most recent call last):
      ...
      ValueError: Bad measurement string: 125em
    """

    units = float( unitsStr[:-2] )
    if unitsStr.endswith( "pt" ):
        return units
    elif unitsStr.endswith( "in" ):
        return inchesToPoints( units )
    elif unitsStr.endswith( "pc" ):
        return picasToPoints( units )
    elif unitsStr.endswith( "px" ):
        return pixelsToPoints( units )
    else:
        raise ValueError( "Bad measurement string: %s" % unitsStr )
