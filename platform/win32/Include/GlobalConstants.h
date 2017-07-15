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

/*   Global constants used by Enso; these need to be defined here
 *   because the values of these constants should never overlap, for
 *   code sanity and debugging purposes.
 */

#ifndef GLOBAL_CONSTANTS_H
#define GLOBAL_CONSTANTS_H

/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* User-defined window message constants used by various modules. */
#define WM_USER_KEYPRESS            ( WM_USER +  0 )
#define WM_USER_QUIT                ( WM_USER +  1 )
#define WM_USER_TRAY_ICON           ( WM_USER +  2 )
#define WM_USER_TRAY_MENU_ITEM      ( WM_USER +  3 )
#define WM_USER_SOMEKEY             ( WM_USER +  4 )
#define WM_USER_MOUSEMOVE           ( WM_USER +  5 )
#define WM_USER_SOMEMOUSEBTN        ( WM_USER +  6 )
#define WM_USER_INIT                ( WM_USER +  7 )
#define WM_USER_TRAY_ICON_INSTALL   ( WM_USER +  8 )
#define WM_USER_TRAY_ICON_UNINSTALL ( WM_USER +  9 )
#define WM_USER_KEYHOOK_INSTALL     ( WM_USER + 10 )
#define WM_USER_KEYHOOK_UNINSTALL   ( WM_USER + 11 )
#define WM_USER_TRANSPARENT_WINDOW  ( WM_USER + 12 )
#define WM_USER_MOUSEHOOK_INSTALL   ( WM_USER + 13 )
#define WM_USER_MOUSEHOOK_UNINSTALL ( WM_USER + 14 )
#define WM_USER_EXIT_REQUESTED      ( WM_USER + 15 )
#define WM_USER_CLIPBOARD_INSTALL   ( WM_USER + 16 )
#define WM_USER_CLIPBOARD_UNINSTALL ( WM_USER + 17 )

/* ***************************************************************************
 * MessageWindow Macros
 * **************************************************************************/

/* Custom message to indicate that the message window loop should
 * stop. It is not guaranteed that a message window will actually
 * receive this message; it's just used to kick the message loop if
 * necessary. */
#define WM_USER_MSGWND_QUIT         ( WM_USER + 50 )

/* Custom message to indicate that the message window loop is
 * starting. */
#define WM_USER_MSGWND_START        ( WM_USER + 51 )

/* ***************************************************************************
 * PyMessageWindow Macros
 * **************************************************************************/

/* Custom message to indicate that the message should be handled by
 * Python code. */
#define WM_USER_PYMSGWND_PYMSG      ( WM_USER + 70 )

/* Custom message to indicate that the message should be handled by
 * Python code, but is first processed by C code that converts its
 * integer parameter to a Python object. */
#define WM_USER_PYMSGWND_INTMSG    ( WM_USER + 71 )

/* The point at which any other code can define its own custom WM_USER
 * messages. */
#define WM_USER_GLOBALCONSTANTS_END ( WM_USER + 5000 )

#endif
