/* -*-Mode:C++; c-basic-indent:4; c-basic-offset:4; indent-tabs-mode:nil-*- */

/*
 Copyright (c) 2008, Humanized, Inc.
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
 
 THIS SOFTWARE IS PROVIDED BY Humanized, Inc. ``AS IS'' AND ANY
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL Humanized, Inc. BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

/*   Constants used by Enso's input manager. */

#ifndef INPUT_MANAGER_CONSTANTS_H
#define INPUT_MANAGER_CONSTANTS_H

/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Keypress events */
#define EVENT_KEY_UP 0
#define EVENT_KEY_DOWN 1
#define EVENT_KEY_QUASIMODE 2

/* Quasimode virtual key constants - valid only for keypress events of
 * type EVENT_KEY_QUASIMODE */
#define KEYCODE_QUASIMODE_START 1
#define KEYCODE_QUASIMODE_END 2
#define KEYCODE_QUASIMODE_CANCEL 3

/* Virtual key constants */
#define KEYCODE_LBUTTON 1
#define KEYCODE_RBUTTON 2
#define KEYCODE_CANCEL 3
#define KEYCODE_MBUTTON 4
#define KEYCODE_BACK 8
#define KEYCODE_TAB 9
#define KEYCODE_CLEAR 12
#define KEYCODE_RETURN 13
#define KEYCODE_SHIFT 16
#define KEYCODE_CONTROL 17
#define KEYCODE_MENU 18
#define KEYCODE_PAUSE 19
#define KEYCODE_CAPITAL 20
#define KEYCODE_KANA 21
#define KEYCODE_HANGUL 21
#define KEYCODE_JUNJA 23
#define KEYCODE_FINAL 24
#define KEYCODE_HANJA 25
#define KEYCODE_KANJI 25
#define KEYCODE_ESCAPE 27
#define KEYCODE_CONVERT 28
#define KEYCODE_NONCONVERT 29
#define KEYCODE_ACCEPT 30
#define KEYCODE_MODECHANGE 31
#define KEYCODE_SPACE 32
#define KEYCODE_PRIOR 33
#define KEYCODE_NEXT 34
#define KEYCODE_END 35
#define KEYCODE_HOME 36
#define KEYCODE_LEFT 37
#define KEYCODE_UP 38
#define KEYCODE_RIGHT 39
#define KEYCODE_DOWN 40
#define KEYCODE_SELECT 41
#define KEYCODE_PRINT 42
#define KEYCODE_EXECUTE 43
#define KEYCODE_SNAPSHOT 44
#define KEYCODE_INSERT 45
#define KEYCODE_DELETE 46
#define KEYCODE_HELP 47
#define KEYCODE_LWIN 91
#define KEYCODE_RWIN 92
#define KEYCODE_APPS 93
#define KEYCODE_NUMPAD0 96
#define KEYCODE_NUMPAD1 97
#define KEYCODE_NUMPAD2 98
#define KEYCODE_NUMPAD3 99
#define KEYCODE_NUMPAD4 100
#define KEYCODE_NUMPAD5 101
#define KEYCODE_NUMPAD6 102
#define KEYCODE_NUMPAD7 103
#define KEYCODE_NUMPAD8 104
#define KEYCODE_NUMPAD9 105
#define KEYCODE_MULTIPLY 106
#define KEYCODE_ADD 107
#define KEYCODE_SEPARATOR 108
#define KEYCODE_SUBTRACT 109
#define KEYCODE_DECIMAL 110
#define KEYCODE_DIVIDE 111
#define KEYCODE_F1 112
#define KEYCODE_F2 113
#define KEYCODE_F3 114
#define KEYCODE_F4 115
#define KEYCODE_F5 116
#define KEYCODE_F6 117
#define KEYCODE_F7 118
#define KEYCODE_F8 119
#define KEYCODE_F9 120
#define KEYCODE_F10 121
#define KEYCODE_F11 122
#define KEYCODE_F12 123
#define KEYCODE_F13 124
#define KEYCODE_F14 125
#define KEYCODE_F15 126
#define KEYCODE_F16 127
#define KEYCODE_F17 128
#define KEYCODE_F18 129
#define KEYCODE_F19 130
#define KEYCODE_F20 131
#define KEYCODE_F21 132
#define KEYCODE_F22 133
#define KEYCODE_F23 134
#define KEYCODE_F24 135
#define KEYCODE_NUMLOCK 144
#define KEYCODE_SCROLL 145
#define KEYCODE_LSHIFT 160
#define KEYCODE_RSHIFT 161
#define KEYCODE_LCONTROL 162
#define KEYCODE_RCONTROL 163
#define KEYCODE_LMENU 164
#define KEYCODE_RMENU 165
#define KEYCODE_PROCESSKEY 229
#define KEYCODE_ATTN 246
#define KEYCODE_CRSEL 247
#define KEYCODE_EXSEL 248
#define KEYCODE_EREOF 249
#define KEYCODE_PLAY 250
#define KEYCODE_ZOOM 251
#define KEYCODE_NONAME 252
#define KEYCODE_PA1 253
#define KEYCODE_OEM_CLEAR 254

/* Interval at which the timer goes off, in ms.  Note that this used
 * to be USER_TIMER_MINIMUM, but it was changed to a hardcoded value
 * since some people's win32 SDK installs didn't define this macro. */
#define TICK_TIMER_INTRVL  10

#endif
