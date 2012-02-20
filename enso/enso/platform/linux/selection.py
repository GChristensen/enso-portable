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

from time import sleep, time, clock

import Xlib
import Xlib.ext.xtest
from enso.platform.linux.utils import *

GET_TIMEOUT = 1.5
PASTE_STATE = Xlib.X.ShiftMask
PASTE_KEY = "^V"

def get_clipboard_text_cb (clipboard, text, userdata):
    '''Callback for clipboard fetch handling'''
    global selection_text
    selection_text = text

def get_focussed_window (display):
    '''Get the currently focussed window'''
    input_focus = display.get_input_focus ()
    window = Xlib.X.NONE
    if input_focus != None and input_focus.focus:
        window = input_focus.focus
    return window

def make_key (keycode, state, window, display):
    '''Build a data dict for a KeyPress/KeyRelease event'''
    root = display.screen ().root
    event_data = {
        "time": int (time ()),
        "root": root,
        "window": window,
        "same_screen": True,
        "child": Xlib.X.NONE,
        "root_x": 0,
        "root_y": 0,
        "event_x": 0,
        "event_y": 0,
        "state": state,
        "detail": keycode,
                 }
    return event_data

def fake_key_up (key, window, display):
    '''Fake a keyboard press event'''
    event = Xlib.protocol.event.KeyPress (**key)
    window.send_event (event, propagate = True)
    display.sync ()

def fake_key_down (key, window, display):
    '''Fake a keyboard release event'''
    event = Xlib.protocol.event.KeyRelease (**key)
    window.send_event (event, propagate = True)
    display.sync ()

def fake_key_updown (key, window, display):
    '''Fake a keyboard press/release events pair'''
    fake_key_up (key, window, display)
    fake_key_down (key, window, display)

def fake_paste (display = None):
    '''Fake a "paste" keyboard event'''
    if not display:
        display = get_display ()
    window = get_focussed_window (display)
    state = PASTE_STATE
    k = PASTE_KEY
    ctrl = False
    if k.startswith("^"):
      k = k[1:]
      ctrl = True
    keycode = get_keycode (key = k, display = display)
    key = make_key (keycode, state, window, display)
    ctrl_keycode = get_keycode (key = "Control_L", display = display)
    ctrl_key = make_key (ctrl_keycode, state, window, display)
    if ctrl: Xlib.ext.xtest.fake_input(display, Xlib.X.KeyPress, ctrl_keycode)
    Xlib.ext.xtest.fake_input(display, Xlib.X.KeyPress, keycode)
    Xlib.ext.xtest.fake_input(display, Xlib.X.KeyRelease, keycode)
    Xlib.ext.xtest.fake_input(display, Xlib.X.KeyRelease, ctrl_keycode)
    display.sync()

def get ():
    '''Fetch text from X PRIMARY selection'''
    global selection_text
    selection_text = None
    clipboard = gtk.clipboard_get (selection = "PRIMARY")
    clipboard.request_text (get_clipboard_text_cb)
    # Iterate until we actually received something, or we timed out waiting
    start = clock ()
    while not selection_text and (clock () - start) < GET_TIMEOUT:
        gtk.main_iteration (False)
    if not selection_text:
        selection_text = ""
    selection = {
                    "text": selection_text,
                }
    return selection

def set (seldict):
    '''Paste data into X CLIPBOARD selection'''
    if seldict.has_key ("text"):
        clipboard = gtk.clipboard_get (selection = "CLIPBOARD")
        clipboard.set_text (seldict["text"])
        primary = gtk.clipboard_get (selection = "PRIMARY")
        primary.set_text (seldict["text"])
        fake_paste()
        return True
    return False

