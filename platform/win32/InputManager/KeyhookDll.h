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

/*   Header file for the KeyhookDll module.
 *
 *   The KeyhookDll module provides global, low-level keyboard and
 *   mouse hooks for the Windows operating system.  All user
 *   keypresses and mouse events are intercepted by these hook
 *   procedures.
 *
 *   Standard Windows hook procedures may determine whether to pass
 *   the intercepted keypresses back to the operating system for
 *   processing by other processes. The keyhook module provides a
 *   callback mechanism which allows the client to determine what
 *   keypresses are intercepted and what aren't; the client may also
 *   use the callback function to gather information about keypresses
 *   and perform whatever functionality it needs to.
 */

#ifndef _KEYHOOK_DLL_H_
#define _KEYHOOK_DLL_H_

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "WinSdk.h"

/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Constant used when we want to pass an event on to the operating
 * system from a low-level input hook. */
#define HOOK_PASS_ON_EVENT    0

/* Constant used when we do not want to pass an event on to the
 * operating system from a low-level input hook. */
#define HOOK_EAT_EVENT        1

/* ***************************************************************************
 * Typedefs
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Key event process callback function.
 * ........................................................................
 *
 * This function is called whenever a keypress is intercepted; a
 * function of this type should be defined by the client and passed
 * into this module by the appropriate function.
 *
 * event_type will be either WM_KEYDOWN or WM_KEYUP.
 *
 * vkCode is the virtual key code and will be a Windows VK_* constant.
 *
 * This function should return HOOK_EAT_EVENT if the keyhook should
 * "eat" the keypress and not pass it on to other Windows processes,
 * HOOK_PASS_ON_EVENT otherwise.
 *
 * ----------------------------------------------------------------------*/

typedef int (*KEY_EVENT_PROCESS_FUNCTION)( int event_type, int vkCode );

/* ------------------------------------------------------------------------
 * Mouse event process callback function.
 * ........................................................................
 *
 * This function is called whenever a mouse event is intercepted; a
 * function of this type should be defined by the client and passed
 * into this module by the appropriate function.
 *
 * event_type will be any of WM_LBUTTONDOWN, WM_LBUTTONUP,
 * WM_MOUSEMOVE, WM_MOUSEWHEEL, WM_RBUTTONDOWN, or WM_RBUTTONUP..
 *
 * x and y specify the current coordinates of the mouse cursor
 * on-screen, in pixels.
 *
 * This function should return HOOK_EAT_EVENT if the mouse hook should
 * "eat" the mouse event and not pass it on to other Windows
 * processes, HOOK_PASS_ON_EVENT otherwise.
 *
 * ----------------------------------------------------------------------*/

typedef int (*MOUSE_EVENT_PROCESS_FUNCTION)( int event_type, int x, int y );

/* ***************************************************************************
 * Function Declarations
 * **************************************************************************/

#ifdef __cplusplus
extern "C"
{
#endif

/* ------------------------------------------------------------------------
 * Sets the key event process callback function.
 * ........................................................................
 *
 * Sets the callback function that is called whenever a keypress is
 * intercepted.
 *
 * ----------------------------------------------------------------------*/

DllExport void
KH_SetKeyEventProcessFunction( KEY_EVENT_PROCESS_FUNCTION f );

/* ------------------------------------------------------------------------
 * Sets the mouse event process callback function.
 * ........................................................................
 *
 * Sets the callback function that is called whenever a mouse event
 * occurs.
 *
 * ----------------------------------------------------------------------*/

DllExport void
KH_SetMouseEventProcessFunction( MOUSE_EVENT_PROCESS_FUNCTION f );

/* ------------------------------------------------------------------------
 * Windows low-level keyboard hook procedure.
 * ........................................................................
 *
 * This is the function that Windows will attach as a hook procedure
 * to intercept all user keypresses.
 *
 * NOTE: This gets mangled to _KH_KeyHookProc@12 due to stdcall name
 * mangling.
 *
 * ----------------------------------------------------------------------*/

DllExport LRESULT CALLBACK
KH_KeyHookProc( int type,
                WPARAM wParam,
                LPARAM lParam );

/* ------------------------------------------------------------------------
 * Windows low-level mouse hook procedure.
 * ........................................................................
 *
 * This is the function that Windows will attach as a hook procedure
 * to intercept all user mouse events.
 *
 * NOTE: This gets mangled to _KH_MouseHookProc@12 due to stdcall name
 * mangling.
 *
 * ----------------------------------------------------------------------*/

DllExport LRESULT CALLBACK
KH_MouseHookProc( int nCode,
                  WPARAM wParam,
                  LPARAM lParam );

#ifdef __cplusplus
};
#endif

#endif
