"""
Author : Guillaume "iXce" Seguin
Email  : guillaume@segu.in
Contributions from:
  Stuart "aquarius" Langridge, sil@kryogenix.org

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

import logging
import subprocess
import os
import atexit

from threading import Thread
from time import sleep
import gobject
import gtk
from Xlib import X
from utils import *

gtk.gdk.threads_init ()

# Timer interval in seconds.
_TIMER_INTERVAL = 0.010

# Timer interval in milliseconds.
_TIMER_INTERVAL_IN_MS = int (_TIMER_INTERVAL * 1000)

# Input modes
QUASI_MODAL = 0
MODAL       = 1

KEYCODE_CAPITAL = -1
KEYCODE_SPACE = -1
KEYCODE_LSHIFT = -1
KEYCODE_RSHIFT = -1
KEYCODE_LCONTROL = -1
KEYCODE_RCONTROL = -1
KEYCODE_LWIN = -1
KEYCODE_RWIN = -1
KEYCODE_RETURN = -1
KEYCODE_ESCAPE = -1
KEYCODE_TAB = -1
KEYCODE_BACK = -1
KEYCODE_DOWN = -1
KEYCODE_UP = -1

EVENT_KEY_UP = 0
EVENT_KEY_DOWN = 1
EVENT_KEY_QUASIMODE = 2

KEYCODE_QUASIMODE_START = 0
KEYCODE_QUASIMODE_END = 1
KEYCODE_QUASIMODE_CANCEL = 2

QUASIMODE_TRIGGER_KEYS = ["Caps_Lock"]

CASE_INSENSITIVE_KEYCODE_MAP = {}

def fill_keymap ():
    '''Fill keymap'''
    global EXTRA_KEYCODES
    EXTRA_KEYCODES = []
    special_keycodes = {}
    display = get_display ()
    for i in range (0, 255):
        keyval = display.keycode_to_keysym (i, 0)
        if int (keyval) > 0x110000:
            continue
        if keyval == gtk.keysyms.Return:
            special_keycodes["KEYCODE_RETURN"] = i
        elif keyval == gtk.keysyms.Escape:
            special_keycodes["KEYCODE_ESCAPE"] = i
        elif keyval == gtk.keysyms.Tab:
            special_keycodes["KEYCODE_TAB"] = i
        elif keyval == gtk.keysyms.BackSpace:
            special_keycodes["KEYCODE_BACK"] = i
        elif keyval == gtk.keysyms.Up:
            special_keycodes["KEYCODE_UP"] = i
        elif keyval == gtk.keysyms.Down:
            special_keycodes["KEYCODE_DOWN"] = i
        else:
            char = unichr (int (keyval))
            if len (char) > 0 and ord (char) > 0:
                CASE_INSENSITIVE_KEYCODE_MAP[i] = str (char)
    vars = globals ()
    for i in special_keycodes:
        vars[i] = special_keycodes[i]
        EXTRA_KEYCODES.append (special_keycodes[i])

fill_keymap ()

class _KeyListener (Thread):
    '''Keyboard input handling thread'''

    __parent    = None
    __callback  = None

    __display   = None

    __terminate = False
    __restart   = False

    __capture   = False

    __lock      = False

    __caps_lock = None
    __num_lock_mod = None
    __key_mod   = None

    def __init__ (self, parent, callback):
        '''Initialize object'''
        Thread.__init__ (self)
        self.__parent = parent
        self.__callback = callback

    def run (self):
        '''Main keyboard event loop'''
        def make_event (type, keycode = None):
            return {
                    "event": type,
                    "keycode": keycode,
                   }
        self.__display = get_display ()
        self.__display.set_error_handler (self.error_handler)
        '''Outter loop, used for configuration handling'''
        while not self.__terminate:
            trigger_key, trigger_keycode = self.grab (QUASIMODE_TRIGGER_KEYS)
            events = [X.KeyPress]
            if not self.__parent.getModality ():
                events += [X.KeyRelease]
            self.__restart = False
            '''Inner loop, used for event processing'''
            while not self.__restart:
                event = self.__display.next_event ()
                self.__lock = True
                gtk.gdk.threads_enter ()
                if hasattr (event,"detail") \
                   and event.detail == trigger_keycode \
                   and event.type in events:
                    if self.__parent.getModality ():
                        continue
                    elif event.type == X.KeyPress:
                        self.__callback (make_event ("quasimodeStart"))
                        self.__capture = True
                    elif event.type == X.KeyRelease:
                        self.__callback (make_event ("quasimodeEnd"))
                        self.__capture = False
                elif not self.__parent.getModality () and self.__capture \
                     and event.type in events:
                    modifiers_mask = gtk.gdk.MODIFIER_MASK
                    if self.__key_mod:
                        mod_str = self.__key_mod.upper ()
                        mod = eval ("gtk.gdk.%s_MASK" % mod_str)
                        modifiers_mask &= ~mod
                    state = event.state & modifiers_mask
                    keyval = self.__display.keycode_to_keysym (event.detail,
                                                               state)
                    if not keyval and self.__num_lock_mod:
                        mod_str = self.__num_lock_mod.upper ()
                        mod = eval ("gtk.gdk.%s_MASK" % mod_str)
                        modifiers_mask &= ~mod
                        state = event.state & modifiers_mask
                        keyval = \
                            self.__display.keycode_to_keysym (event.detail,
                                                              state)
                    if event.detail in EXTRA_KEYCODES \
                       or sanitize_char (keyval):
                        if event.type == X.KeyPress:
                            self.__callback (make_event ("keyDown",
                                                         event.detail))
                        else:
                            self.__callback (make_event ("keyUp",
                                                         event.detail))
                gtk.gdk.threads_leave ()
                self.__lock = False
            self.ungrab (grabbedKey)

    def unlock (self):
        '''Unlock GDK threading lock'''
        if self.__lock:
            gtk.gdk.threads_leave ()

    def stop (self):
        '''Halt thread: restart inner loop and kill outter loop'''
        self.__restart = True
        self.__terminate = True

    def restart (self):
        '''Restart inner loop to use latest options'''
        self.__restart = True

    def error_handler (self, error, *args):
        '''Catch Xlib errors'''
        logging.critical ("X protocol error caught : %s" % error)
        self.__parent.stop ()

    def grab (self, keys):
        '''Grab a specific key'''
        root_window = self.__display.screen ().root
        keycode = 0
        xset_command = ["which", "xset"]
        which_process = subprocess.Popen (xset_command,
                                          stdout = subprocess.PIPE)
        which_stdout = which_process.stdout
        has_xset = (len (which_stdout.readlines ()) > 0)
        xmodmap_command = ["which", "xmodmap"]
        which_process = subprocess.Popen (xmodmap_command,
                                          stdout = subprocess.PIPE)
        which_stdout = which_process.stdout
        has_xmodmap = (len (which_stdout.readlines ()) > 0)
        if not has_xset:
            logging.warn ("xset not found, you might experience some bad \
key-repeat problems")
        for key in keys:
            keycode = get_keycode (key)
            if not keycode:
                continue
            if has_xset:
                os.system ("xset -r %d" % keycode) # FIXME: revert on exit
            if has_xmodmap:
                xmodmap_command = ["xmodmap","-pm"]
                xmodmap_process = subprocess.Popen (xmodmap_command,
                                                    stdout = subprocess.PIPE)
                xmodmap_stdout = xmodmap_process.stdout
                lines = xmodmap_stdout.readlines ()
                lock_line = filter (lambda l: l.startswith ("lock"), lines)
                num_line = filter (lambda l: "Num_Lock" in l, lines)
                key_line = filter (lambda l: key in l, lines)
                if lock_line:
                    parts = lock_line[0].strip ().split ()
                    if len (parts) > 1:
                        self.__caps_lock = parts[1]
                if num_line:
                    parts = num_line[0].strip ().split ()
                    if len (parts) > 1:
                        self.__num_lock_mod = parts[0]
                if key_line:
                    parts = key_line[0].strip ().split ()
                    if len (parts) > 1:
                        self.__key_mod = parts[0]
            if key == "Caps_Lock":
                if not self.__caps_lock:
                    logging.debug ("Caps Lock already disabled!")
                else:
                    self.disable_caps_lock ()
                    atexit.register (self.enable_caps_lock)
            ownev = not self.__parent.getModality ()
            root_window.grab_key (keycode, X.AnyModifier, ownev,
                                  X.GrabModeAsync, X.GrabModeAsync)
            return key, keycode
        logging.critical ("Couldn't find quasimode key")
        self.__parent.stop ()
        return None, None

    def ungrab (self, keycode):
        '''Ungrab a specific key'''
        root_window = self.__display.screen ().root
        root_window.ungrab_key (keycode, 0)
        
    def disable_caps_lock (self):
        '''Disable Caps Lock'''
        if self.__caps_lock:
            logging.debug ("Using xmodmap to disable Caps Lock")
            os.system ('xmodmap -e "clear Lock"')
        
    def enable_caps_lock (self):
        '''Enable Caps Lock'''
        if self.__caps_lock:
            logging.debug ("Using xmodmap to enable Caps Lock")
            os.system ('xmodmap -e "add Lock = %s"' % self.__caps_lock)

class InputManager (object):
    '''Input event manager object'''

    __mouseEventsEnabled = False
    __qmKeycodes = [0, 0, 0]
    __isModal = False
    __inQuasimode = False

    __keyListener = None

    def __init__ (self):
        '''Initialize object'''
        pass

    def __timerCallback (self):
        '''Handle gobject timeout'''
        try:
            self.onTick (_TIMER_INTERVAL_IN_MS)
        except KeyboardInterrupt:
            gtk.main_quit ()
        return True # Return true to keep the timeout running 

    def __keyCallback (self, info):
        '''Handle callbacks from KeyListener'''
        if info["event"] == "quasimodeStart":
            self.onKeypress (EVENT_KEY_QUASIMODE,
                             KEYCODE_QUASIMODE_START)
        elif info["event"] == "quasimodeEnd":
            self.onKeypress (EVENT_KEY_QUASIMODE,
                             KEYCODE_QUASIMODE_END)
        elif info["event"] == "someKey":
            self.onSomeKey ()
        elif info["event"] in ["keyUp", "keyDown"]:
            keycode = info["keycode"]
            if info["event"] == "keyUp":
                eventType = EVENT_KEY_UP
            else:
                eventType = EVENT_KEY_DOWN
            self.onKeypress (eventType, keycode)
        else:
            logging.warn ("Don't know what to do with event: %s" % info)

    def run (self):
        '''Main input events processing loop'''
        logging.info( "Entering InputManager.run ()" )

        timeout_source = gobject.timeout_add (_TIMER_INTERVAL_IN_MS,
                                              self.__timerCallback)

        self.__keyListener = _KeyListener (self, self.__keyCallback)
        self.__keyListener.start ()

        try:
            try:
                self.onInit ()
                gtk.main ()
            except KeyboardInterrupt:
                pass
        finally:
            self.__keyListener.stop ()
            gobject.source_remove (timeout_source)

        logging.info ("Exiting InputManager.run ()")
        exit (1)

    def stop (self):
        '''Stop main loop by exiting from gtk mainloop'''
        try:
            self.__keyListener.unlock ()
            gtk.main_quit ()
        except:
            pass

    def enableMouseEvents (self, isEnabled):
        # TODO: Implementation needed.
        self.__mouseEventsEnabled = isEnabled

    def onKeypress (self, eventType, vkCode):
        pass

    def onSomeKey (self):
        pass

    def onSomeMouseButton (self):
        pass

    def onExitRequested (self):
        pass

    def onMouseMove (self, x, y):
        pass

    def getQuasimodeKeycode (self, quasimodeKeycode):
        return self.__qmKeycodes[quasimodeKeycode]

    def setQuasimodeKeycode (self, quasimodeKeycode, keycode):
        # TODO: Implementation needed.
        self.__qmKeycodes[quasimodeKeycode] = keycode

    def setModality (self, isModal):
        # TODO: Implementation needed.
        if self.__isModal != isModal:
            self.__isModal = isModal
            self.__keyListener.restart ()

    def getModality (self):
        return self.__isModal

    def setCapsLockMode (self, caps_lock_enabled):
        if caps_lock_enabled:
            self.__keyListener.enable_caps_lock ()
        else:
            self.__keyListener.disable_caps_lock ()

    def onTick (self, msPassed):
        pass

    def onInit (self):
        pass
