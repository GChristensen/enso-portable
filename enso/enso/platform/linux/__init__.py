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

import os
import sys
import logging

import enso.platform

platforms = [
    "linux",
    "openbsd",
    "freebsd",
    "netbsd",
]
if not any (sys.platform.startswith (s) for s in platforms):
    raise enso.platform.PlatformUnsupportedError()

from enso.platform.linux import detect

# Pin GDK to the display protocol matching the chosen backend before
# anything imports Gtk: under Wayland, GTK would otherwise be free to
# pick XWayland (or the other way round with GDK_BACKEND set), and the
# input/graphics code must talk to the same display server the backend
# was chosen for.  setdefault keeps an explicit user override working.
BACKEND = detect.get_backend()
os.environ.setdefault(
    "GDK_BACKEND", "wayland" if BACKEND == "kwayland" else "x11")

_BACKEND_PACKAGE = "enso.platform.linux." + \
    ("kwayland" if BACKEND == "kwayland" else "x11")


def _backend_module (name):
    module = __import__ (_BACKEND_PACKAGE + "." + name,
                         fromlist = [name])
    return module


def provideInterface (name):
    '''Plug into Enso core'''
    if BACKEND == "x11" and name in ("input", "graphics") \
            and not os.environ.get ("DISPLAY"):
        logging.error ("DISPLAY is not set; the X11 backend requires an "
                       "X11 session.")
    if name in ("input", "graphics", "selection"):
        return _backend_module (name)
    elif name == "cairo":
        import cairo
        return cairo
    elif name == "scripts_folder":
        from enso.platform.linux.scriptfolder import get_script_folder_name
        return get_script_folder_name
    else:
        return None
