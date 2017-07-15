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

/*   Implemenation file for the KeyhookDll module. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "WinSdk.h"
#include "KeyhookDll.h"

/* ***************************************************************************
 * Global and Static Variables
 * **************************************************************************/

/* The handle to the DLL module. */
HANDLE g_instance;

/* The current key event process callback function. */
KEY_EVENT_PROCESS_FUNCTION g_KeyEventProcessFunction = NULL;

/* The current mouse event process callback function. */
MOUSE_EVENT_PROCESS_FUNCTION g_MouseEventProcessFunction = NULL;

/* ***************************************************************************
 * Private Function Implementations
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * DllMain() entry point function.
 * ........................................................................
 *
 * This function doesn't do very much; it just saves the handle to the
 * DLL module for future use.
 *
 * ----------------------------------------------------------------------*/

BOOL WINAPI
DllMain( HINSTANCE theInstance,
         DWORD reason,
         LPVOID reserved )
{
    BOOL result = TRUE;

    if ( theInstance )
        g_instance = theInstance;

    switch ( reason )
    {
        case DLL_PROCESS_ATTACH:
            break;

        case DLL_PROCESS_DETACH:
            break;
    }

    return result;
}

/* ***************************************************************************
 * Public Function Implementations
 * **************************************************************************/

#ifdef __cplusplus
extern "C"
{
#endif

/* ------------------------------------------------------------------------
 * Sets the key event process callback function.
 * ........................................................................
 * ----------------------------------------------------------------------*/

DllExport void
KH_SetKeyEventProcessFunction( KEY_EVENT_PROCESS_FUNCTION f )
{
    g_KeyEventProcessFunction = f;
}

/* ------------------------------------------------------------------------
 * Sets the mouse event process callback function.
 * ........................................................................
 * ----------------------------------------------------------------------*/

DllExport void
KH_SetMouseEventProcessFunction( MOUSE_EVENT_PROCESS_FUNCTION f )
{
    g_MouseEventProcessFunction = f;
}

/* ------------------------------------------------------------------------
 * Windows low-level keyboard hook procedure.
 * ........................................................................
 * ----------------------------------------------------------------------*/

DllExport LRESULT CALLBACK
KH_KeyHookProc( int type,
                WPARAM wParam,
                LPARAM lParam )
{
    LRESULT result = HOOK_PASS_ON_EVENT;
    KBDLLHOOKSTRUCT *info = (KBDLLHOOKSTRUCT *) lParam;

    /* Should we process this? */
    if ( type >= 0 )
    {
        switch ( wParam )
        {
        case WM_SYSKEYDOWN:
        case WM_SYSKEYUP:
        case WM_KEYDOWN:
        case WM_KEYUP:
            /* This, bizarrely, occurs if alt is pressed down. */
            if ( wParam == WM_SYSKEYDOWN )
                wParam = WM_KEYDOWN;

            /* This, bizarrely, occurs if alt and caps lock are
             * pressed down and caps lock is released. */
            else if ( wParam == WM_SYSKEYUP )
                wParam = WM_KEYUP;

            if ( g_KeyEventProcessFunction )
                result = g_KeyEventProcessFunction( wParam, info->vkCode );
            break;

        default:
            break;
        }
    }

    /* call the next hook */
    if ( result == HOOK_PASS_ON_EVENT )
        result = CallNextHookEx( NULL, type, wParam, lParam );

    return result;
}

/* ------------------------------------------------------------------------
 * Windows low-level mouse hook procedure.
 * ........................................................................
 * ----------------------------------------------------------------------*/

DllExport LRESULT CALLBACK
KH_MouseHookProc( int nCode,
                  WPARAM wParam,
                  LPARAM lParam )
{
    if ( nCode < 0 ) {
        return CallNextHookEx( NULL, nCode, wParam, lParam );
    } else {
        /* LONGTERM TODO: Assert that nCode == HC_ACTION.  See ticket
         * #367. */
        LRESULT result = HOOK_PASS_ON_EVENT;
        MSLLHOOKSTRUCT *info = (MSLLHOOKSTRUCT *) lParam;
        int x = 0;
        int y = 0;

        x = info->pt.x;
        y = info->pt.y;

        if ( g_MouseEventProcessFunction )
            result = g_MouseEventProcessFunction( wParam, x, y );

        /* call the next hook */
        if ( result == HOOK_PASS_ON_EVENT )
            result = CallNextHookEx( NULL, nCode, wParam, lParam );

        return result;
    }
}

#ifdef __cplusplus
};
#endif
