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
#   enso.utils.memoize
#
# ----------------------------------------------------------------------------

"""
    A memoizing decorator for caching the results of a function.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import inspect

from enso.utils.decorators import finalizeWrapper


# ----------------------------------------------------------------------------
# Memoized Decorator
# ----------------------------------------------------------------------------

_memoizedFunctions = []

class _MemoizedFunction:
    """
    Encapsulates all information about a function that is memoized.
    """
    
    def __init__( self, function ):
        self.function = function
        self.cache = {}
        _memoizedFunctions.append( self )


def _generateArgWrapper( function, wrappedFunction ):
    """
    Given any function and a wrappedFunction of the form
    wrappedFunction(*args), creates an argument-wrapper function that
    guarantees that function's arguments will be passed into
    wrappedFunction() as a single tuple with no keyword arguments;
    furthermore, the default values of any absent arguments will be
    inserted into the tuple in their appopriate positions.

    The function is very useful for creating wrappers that memoize
    functions, because it ensures that the wrapped function's
    arguments are always passed in to the memoizing wrapper as a
    hashable data structure (a tuple) in a very consistent way. See
    the following primitive example:

      >>> timesCalled = 0
      >>> cachedResults = {}

      >>> def myFunction( a, b=1 ):
      ...   'Simple function that returns the sum of the two arguments.'
      ...   global timesCalled
      ...   timesCalled += 1
      ...   return a+b

      >>> def memoizedMyFunction( *args ):
      ...   'Simple wrapper that memoizes myFunction().'
      ...   if not cachedResults.has_key( args ):
      ...     cachedResults[args] = myFunction( *args )
      ...   return cachedResults[args]

    Note that memoizedFunction() isn't very flexible; for instance,
    calling it in two different ways that are semantically identical
    erroneously causes myFunction() to be called twice:

      >>> memoizedMyFunction( 1 )
      2
      >>> memoizedMyFunction( 1, 1 )
      2
      >>> timesCalled
      2

    Note further that the function can't be used with keyword
    arguments, partly because allowing memoizedMyFunction() to take
    keyword arguments would require us to convert a **kwargs dictionary
    into a hashable object, which is inefficient.  See the following:

      >>> memoizedMyFunction( 1, b=5 )
      Traceback (most recent call last):
      ...
      TypeError: memoizedMyFunction() got an unexpected keyword argument 'b'

    To solve these problems, let's try using _generateArgWrapper() on
    our memoized function:
    
      >>> f = _generateArgWrapper( myFunction, memoizedMyFunction )

    Now the function 'f' can be used just like myFunction():

      >>> timesCalled = 0
      >>> cachedResults = {}

      >>> f( 1, 1 )
      2
      >>> f( a=1 )
      2
      >>> f( 1 )
      2
      >>> f( a=1, b=1 )
      2

    Furthermore, note that myFunction() has still only been called
    once:

      >>> timesCalled
      1
    """

    args, varargs, varkw, defaults = inspect.getargspec( function )

    assert varkw == None, "Memoized functions cannot take ** arguments."

    argspecString = inspect.formatargspec( args, varargs, None, defaults )
    argspecStringNoDefaults = inspect.formatargspec( args,
                                                     varargs,
                                                     None,
                                                     None )

    codeString = "\n".join( [
        "def argWrapperGenerator( wrappedFunction ):",
        "    def argWrappedFunction%(argspecString)s:",
        "        return wrappedFunction%(argspecStringNoDefaults)s",
        "    return argWrappedFunction",
        ] )

    codeString = codeString % {
        "argspecString" : argspecString,
        "argspecStringNoDefaults" : argspecStringNoDefaults,
        }

    fakeFileName = "<Memoize-generated code for '%s'>" % function.__name__

    codeObj = compile(
        codeString,
        fakeFileName,
        "exec"
    )

    localsDict = {}
    globalsDict = function.func_globals

    exec codeObj in globalsDict, localsDict

    argWrapperGenerator = localsDict["argWrapperGenerator"]

    return argWrapperGenerator( wrappedFunction )


def memoized( function ):
    """
    'Memoizes' the function, causing its results to be cached based on
    the called arguments.  When subsequent calls to function are made
    using the same arguments, the cached value is returned rather than
    calling the function to re-compute the result.  For instance:

      >>> timesCalled = 0
      >>> @memoized
      ... def addNumbers( a, b ):
      ...   global timesCalled
      ...   timesCalled += 1
      ...   return a + b

    We can show that the above function is only called once for each
    unique pair of arguments like so:

      >>> addNumbers( 50, 20 )
      70
      >>> timesCalled
      1
      >>> addNumbers( a=50, b=20 )
      70
      >>> timesCalled
      1

    Using different arguments calls the function again, of course:

      >>> addNumbers( 20, 50 )
      70
      >>> timesCalled
      2

    The memoized function cannot take any arguments that are
    non-hashable; this means that the memoized function cannot take
    dicts or lists, among others.  For instance:

      >>> @memoized
      ... def myFunc( myDict ):
      ...   myDict.update( {'bar':2} )
      ...   return myDict
      >>> myFunc( {'foo':1} )
      Traceback (most recent call last):
      ...
      TypeError: dict objects are unhashable

    The memoized function also cannot take a ** argument, since this
    constitutes a dict.

    This decorator should only be used on functions which have a small
    number of relatively simple input arguments, and which are called
    a fantastic number of times.

    The memoized decorator is most effective in helping performance
    when used on factory functions, as the instantiated object
    (assuming that it should only be instantiated once) can be reused
    rather than re-instantiated (effectively providing the services of
    a flyweight pool).
    """

    mfWrap = _MemoizedFunction( function )

    # For efficiency purposes, let's make it as easy to look up
    # mfWrap.cache as possible.
    cache = mfWrap.cache

    def memoizedFunctionWrapper( *args ):
        # We're using a try-except clause here instead of testing
        # whether the dictionary has a key because we believe that it
        # is more efficient; it's preferable to speed up the most
        # common scenario where a cached value already exists by
        # simply assuming that it *does* exist.

        try:
            return cache[args]
        except KeyError:
            cache[args] = function( *args )
            return cache[args]
    
    finalWrapper = _generateArgWrapper( function, memoizedFunctionWrapper )

    return finalizeWrapper( function,
                            finalWrapper,
                            "Memoized" )


def getMemoizeStats():
    """
    Returns a string describing the memoize usage dictionary.
    """

    STAT_STRING = \
        "Number of functions which used memoizing:  %(numFuncs)s\n" \
        "Number of unique function values recorded: %(numValues)s"

    info = STAT_STRING % dict(
        numFuncs = len( _memoizedFunctions ),
        numValues = sum( [ len(i.cache.keys()) \
                           for i in _memoizedFunctions ] ),
        )

    return info
