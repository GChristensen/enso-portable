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
#   enso.selection
#
# ----------------------------------------------------------------------------

"""
    This module provides access to manipulating the current selection
    on the end-user's system.

    A selection is represented by a Python dictionary-like object
    called a "Selection Dictionary", or "seldict" for short.  The keys
    in a seldict are strings that correspond to different formats that
    the current selection can be interpreted as; each value contains
    the selection in a particular format.

    The three most common formats are:

      'text'  -- Unicode text.
      'html'  -- Unicode HTML.
      'files' -- A tuple of absolute file paths.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import enso.providers


# ----------------------------------------------------------------------------
# Module variables
# ----------------------------------------------------------------------------

# Actual implementation provider for this module.
__impl = enso.providers.getInterface( "selection" )


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

def get():
    """
    Returns the current selection, as a seldict.  If no selection
    could be retrieved, an empty dictionary is returned.
    """

    return __impl.get()

def set( seldict ):
    """
    Sets the current selection to the given seldict.  Returns True if
    at least one format of the seldict could be applied as the current
    selection, False otherwise.

    Note also that this function overwrites the current selection,
    whatever it may be.
    """

    return __impl.set( seldict )
