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

#   Python Version - 2.4

"""
    Contains the maps that convert virtual key codes to characters.

    Each of the dictionaries maps windows vkCodes (which equals the
    ascii code, for alphanumerics) to one-character strings of the
    corresponding character.  Characters which we don't want as input
    during the quasimode have no entry in this map, and so will never
    appear in the quasimode or be part of a command name.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import InputManager


# ----------------------------------------------------------------------------
# The Standard map
# ----------------------------------------------------------------------------

# Our initial, Ameri-centric keycode map
STANDARD_ALLOWED_KEYCODES = {
    48: "0",
    49: "1",
    50: "2",
    51: "3",
    52: "4",
    53: "5",
    54: "6",
    55: "7",
    56: "8",
    57: "9",
    65: "a",
    66: "b",
    67: "c",
    68: "d",
    69: "e",
    70: "f",
    71: "g",
    72: "h",
    73: "i",
    74: "j",
    75: "k",
    76: "l",
    77: "m",
    78: "n",
    79: "o",
    80: "p",
    81: "q",
    82: "r",
    83: "s",
    84: "t",
    85: "u",
    86: "v",
    87: "w",
    88: "x",
    89: "y",
    90: "z",
    # Symbols:
    186: ";",
    187: "=",
    188: ",",
    189: "-",
    190: ".",
    191: "/",
    192: "`",
    219: "[",
    220: "\\",
    221: "]",
    222: "'",
    # Shift symbols:
    1048: ")",
    1049: "!",
    1050: "@",
    1051: "#",
    1052: "$",
    1053: "%",
    1054: "^",
    1055: "&",
    1056: "*",
    1057: "(",
    1186: ":",
    1187: "+",
    1188: "<",
    1189: "_",
    1190: ">",
    1191: "?",
    1192: "~",
    1219: "{",
    1220: "|",
    1221: "}",
    1222: "\"",
    InputManager.KEYCODE_SPACE: " ",
    # Keypad entry:
    InputManager.KEYCODE_NUMPAD0: "0",
    InputManager.KEYCODE_NUMPAD1: "1",
    InputManager.KEYCODE_NUMPAD2: "2",
    InputManager.KEYCODE_NUMPAD3: "3",
    InputManager.KEYCODE_NUMPAD4: "4",
    InputManager.KEYCODE_NUMPAD5: "5",
    InputManager.KEYCODE_NUMPAD6: "6",
    InputManager.KEYCODE_NUMPAD7: "7",
    InputManager.KEYCODE_NUMPAD8: "8",
    InputManager.KEYCODE_NUMPAD9: "9",
    InputManager.KEYCODE_DECIMAL: ".",
    InputManager.KEYCODE_DIVIDE: "/",
    InputManager.KEYCODE_MULTIPLY: "*",
    InputManager.KEYCODE_SUBTRACT: "-",
    InputManager.KEYCODE_ADD: "+"
    }
