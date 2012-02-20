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
#   enso.providers
#
# ----------------------------------------------------------------------------

"""
    This module provides a simple Abstract Factory-like mechanism to
    that allows for platform-specific functionalities that conform to
    common interfaces to be implemented by different libraries.

    A provider is just a Python module or package with a single
    function in it, provideInterface(), which takes a single string
    argument that corresponds to the name of an interface.  If the
    provider has an implementation of the interface, it returns it; if
    not, it returns None.

    Providers are specified as their fully-qualified module or package
    names in the enso.config.PROVIDERS list.  For instance, if the
    provider "mypackage.myprovider" should be loaded when Enso is
    started, then the string "mypackage.myprovider" should be added to
    enso.config.PROVIDERS.

    Whenever an interface implementation is requested through this
    module's getInterface() function, each provider is consulted in
    the order listed in enso.config.PROVIDERS until an implementation
    is found.  In this way, it's possible for providers to be
    "layered" (in a variation of the Chain of Responsibility pattern)
    so that Enso attempts to load the most functional and
    feature-loaded implementation first, and if that fails, Enso's
    functionality is able to "gracefully degrade" until a working
    implementation of an interface is found.

    For instance, take the hypothetical example of an interface called
    "dictionary", which has a single function, lookupWord(), that
    looks up a particular word in a dictionary and presents the
    definition to the end-user.  Under Mac OS X, the ideal
    functionality would be to use the built-in dictionary that comes
    with the operating system.  Under Windows, the ideal functionality
    would be to see if the user has some kind of offline dictionary
    program installed, and if so, to use that.  If all of these fail,
    then the final alternative would be to open the user's web browser
    and look up the word online.  Each one of these mechanisms can be
    implemented by a different provider, and as long as the "most
    generic" ones are at the end of the provider chain, Enso's
    functionality will degrade gracefully.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

import enso.config


# ----------------------------------------------------------------------------
# Private module variables
# ----------------------------------------------------------------------------

# Dictionary mapping interface names to their implementations.
_interfaces = {}

# List of all provider objects.
_providers = []


# ----------------------------------------------------------------------------
# Private functions
# ----------------------------------------------------------------------------

def _initDefaultProviders():
    """
    Resolves all provider names in enso.config.PROVIDERS to actual
    Python objects.
    """

    for moduleName in enso.config.PROVIDERS:
        try:
            # Import the module; most of this code was taken from the
            # Python Library Reference documentation for __import__().
            module = __import__( moduleName, {}, {}, [] )
            components = moduleName.split( "." )
            for component in components[1:]:
                module = getattr( module, component )

            _providers.append( module )
            logging.info( "Added provider %s." % moduleName )
        except ProviderUnavailableError:
            logging.info( "Skipping provider %s." % moduleName )


# ----------------------------------------------------------------------------
# Public functions
# ----------------------------------------------------------------------------

def getInterface( name ):
    """
    Finds and returns an implementation that provides an interface
    with the given name.  If no interface exists that provides the
    given interface, this function raises a ProviderNotFoundError.
    """

    if not _providers:
        _initDefaultProviders()
    if name not in _interfaces:
        for provider in _providers:
            interface = provider.provideInterface( name )
            if interface:
                logging.info( "Obtained interface '%s' from provider '%s'."
                              % (name, provider.__name__) )
                _interfaces[name] = interface
                break
    if name in _interfaces:
        return _interfaces[name]
    else:
        raise ProviderNotFoundError( name )


# ----------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------

class ProviderUnavailableError( Exception ):
    """
    Exception raised when a provider is unavailable for use, even
    though its implementation exists; this may be because, for
    instance, the host system is unsupported by the provider, or the
    provider communcates with third-party software that isn't
    installed.
    """

    pass

class ProviderNotFoundError( Exception ):
    """
    Exception raised when an implementation for a particular interface
    is not found.
    """

    pass
