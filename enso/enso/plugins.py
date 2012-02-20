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
#   enso.plugins
#
# ----------------------------------------------------------------------------

"""
    This module provides a simple mechanism to extend Enso's
    functionality.

    A plugin is just a Python module or package with a single function
    in it, load(), which takes no parameters, and is called when the
    Enso quasimode is about to start itself.

    Plugins are specified as their fully-qualified module or package
    names in the enso.config.PLUGINS list.  For instance, if the
    plugin "mypackage.myplugin" should be loaded when Enso is started,
    then the string "mypackage.myplugin" should be added to
    enso.config.PLUGINS.

    Plugins are loaded in the order specified by enso.config.PLUGINS.

    There is currently no mechanism to unload a plugin, because
    plugins are assumed to have the same lifespan as Enso itself.  If
    a plugin needs to perform any cleanup, it should register a
    handler with Python's 'atexit' module.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import logging

import enso.config


# ----------------------------------------------------------------------------
# Public functions
# ----------------------------------------------------------------------------

def install( eventManager ):
    """
    Installs the plugin system into the given enso.events.EventManager
    instance.
    """

    eventManager.registerResponder( _init, "init" )


# ----------------------------------------------------------------------------
# Private functions
# ----------------------------------------------------------------------------

def _init():
    """
    Responder for the EventManager's init event that loads all
    registered plugins.
    """

    for moduleName in enso.config.PLUGINS:
        try:
            # Import the module; most of this code was taken from the
            # Python Library Reference documentation for __import__().
            module = __import__( moduleName, {}, {}, [] )
            components = moduleName.split( "." )
            for component in components[1:]:
                module = getattr( module, component )

            module.load()
        except:
            logging.warn( "Error while loading plugin '%s'." % moduleName )
            raise
        logging.info( "Loaded plugin '%s'." % moduleName )
