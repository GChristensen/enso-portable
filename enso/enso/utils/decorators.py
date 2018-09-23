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
#   enso.utils.decorators
#
# ----------------------------------------------------------------------------

"""
    Contains utility functions for decorators.  Note that this module
    does not contain actual decorators, but rather *utilities* for
    decorators to use.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import inspect
import sys


# ----------------------------------------------------------------------------
# Functionality
# ----------------------------------------------------------------------------

def finalizeWrapper( origFunc, wrappedFunc, decoratorName ):
    """
    Makes some final modifications to the decorated or 'wrapped'
    version of a function by making the wrapped version's name and
    docstring match those of the original function.

    'decoratorName' is the string name for the decorator,
    e.g. 'Synchronized'.

    Assuming that the original function was of the form 'myFunc( self,
    foo = 1 )' and the decorator name is 'Synchronized', the new
    docstring for the wrapped function will be of the form:

        Synchronized wrapper for:
        myFunc( self, foo = 1 )

        <myFunc's docstring>
    
    Returns the wrapped function.
    """

    if "pychecker" in sys.modules:
        # If pychecker is in sys.modules, then we can assume that our
        # code is being checked by pychecker.  If this is the case,
        # then we just want to return the original function, because
        # pychecker doesn't like decorators.
        return origFunc

    # Get a prettified representation of the argument list.
    args, varargs, varkw, defaults = inspect.getargspec( origFunc )
    argspec = inspect.formatargspec(
        args,
        varargs,
        varkw,
        defaults
        )

    callspec = "%s%s" % ( origFunc.__name__, argspec )

    # Generate a new docstring.
    newDocString = "%s wrapper for:\n%s\n\n%s" % \
                   ( decoratorName, callspec, origFunc.__doc__ )

    # Set the appropriate attributes on the wrapped function and pass
    # it back.
    wrappedFunc.__doc__ = newDocString
    wrappedFunc.__name__ = origFunc.__name__
    wrappedFunc.__module__ = origFunc.__module__
    return wrappedFunc
