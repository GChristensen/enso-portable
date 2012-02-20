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
#   enso.graphics.rounded_rect
#
# ----------------------------------------------------------------------------

"""
    Functions and constants for drawing rounded rectangles.
"""

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

LOWER_RIGHT = 0
UPPER_RIGHT = 1
LOWER_LEFT = 2
UPPER_LEFT = 3
ALL_CORNERS = [ LOWER_RIGHT, UPPER_RIGHT, LOWER_LEFT, UPPER_LEFT ]

# The radius of a corner of a rounded rectangle, in points.
CORNER_RADIUS = 5


# ----------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------

def drawRoundedRect( context, rect, softenedCorners ):
    """
    Draws a rectangle where each corner in softenedCorners has a
    CORNER_RADIUS-unit radius arc instead of a corner.
    """
    
    PI = 3.1415926535
    context.new_path()

    xPos,yPos,width,height = rect

    if LOWER_RIGHT in softenedCorners:
        context.arc( xPos+width-CORNER_RADIUS,
                     yPos+height-CORNER_RADIUS,
                     CORNER_RADIUS,
                     0,
                     .5*PI )
    else:
        context.move_to( xPos+width, yPos+height-CORNER_RADIUS )
        context.line_to( xPos+width, yPos+height )
    context.line_to( xPos+CORNER_RADIUS, yPos+height )

    if LOWER_LEFT in softenedCorners:
        context.arc( xPos+CORNER_RADIUS,
                     yPos+height-CORNER_RADIUS,
                     CORNER_RADIUS,
                     .5*PI,
                     PI )
    else:
        context.line_to( xPos, yPos+height )
    context.line_to( xPos, yPos+CORNER_RADIUS )

    if UPPER_LEFT in softenedCorners:
        context.arc( xPos+CORNER_RADIUS,
                     yPos+CORNER_RADIUS,
                     CORNER_RADIUS,
                     PI,
                     1.5*PI )
    else:
        context.line_to( xPos, yPos )
    context.line_to( xPos+width-CORNER_RADIUS, yPos )

    if UPPER_RIGHT in softenedCorners:
        context.arc( xPos+width-CORNER_RADIUS,
                     yPos+CORNER_RADIUS,
                     CORNER_RADIUS,
                     1.5*PI,
                     2*PI )
    else:
        context.line_to( xPos+width, yPos )
    context.line_to( xPos+width, yPos+height-CORNER_RADIUS )
