"""
Author : Guillaume "iXce" Seguin
Email  : guillaume@segu.in

Copyright (C) 2008, Guillaume Seguin <guillaume@segu.in>.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

  3. Neither the name of Enso nor the names of its contributors may
     be used to endorse or promote products derived from this
     software without specific prior written permission.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys

import enso.platform

platforms = [
    "linux",
    "openbsd",
    "freebsd",
    "netbsd",
]
if not True in map (lambda s: sys.platform.startswith (s), platforms):
    raise enso.platform.PlatformUnsupportedError()

def provideInterface (name):
    '''Plug into Enso core'''
    if name == "input":
        import enso.platform.linux.input
        return enso.platform.linux.input
    elif name == "graphics":
        import enso.platform.linux.graphics
        return enso.platform.linux.graphics
    elif name == "cairo":
        import cairo
        return cairo
    elif name == "selection":
        import enso.platform.linux.selection
        return enso.platform.linux.selection
    elif name == "scripts_folder":
        from enso.platform.linux.scriptfolder import get_script_folder_name
        return get_script_folder_name
    else:
        return None
