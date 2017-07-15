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

/*   Header file for Enso's mouse/keyhook handlers. */

#include "WinSdk.h"

#ifdef __cplusplus
extern "C"
{
#endif

/* ------------------------------------------------------------------------
 * Installs the keyboard hook.
 * ........................................................................
 *
 * The hook will be dependent on the health of the thread owning the
 * AsyncEventWindow, meaning that if the thread ever behaves
 * abnormally (e.g., takes a long time to process some event), the
 * system's keyboard responsiveness will suffer as a result.
 *
 * "threadId" is the thread that the hook will send their generated
 * events to (as Windows messages).
 *
 * Returns true (nonzero) iff the operation was successful.
 *
 * ----------------------------------------------------------------------*/

int
installKeyboardHook( DWORD threadId );

/* ------------------------------------------------------------------------
 * Installs the mouse hook.
 * ........................................................................
 *
 * Behavior is analogous to installKeyboardHook(), only for mouse
 * instead.
 *
 * ----------------------------------------------------------------------*/

int
installMouseHook( DWORD threadId );

/* ------------------------------------------------------------------------
 * Removes the keyboard hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
removeKeyboardHook( void );

/* ------------------------------------------------------------------------
 * Removes the mouse hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
removeMouseHook( void );

/* ------------------------------------------------------------------------
 * Maps the given quasimode keycode to the given physical keycode.
 * ........................................................................
 *
 * The quasimodeKeycode should correspond to one of the
 * KEYCODE_QUASIMODE_* constants, and names the quasimode keycode
 * that should be set.
 *
 * The keycode will correspond to a KEYCODE_* constant.
 *
 * Once the quasimode begins, all keys pressed will be converted into
 * WM_USER_KEYPRESS events until the quasimode ends.  At all other
 * times, keystrokes are turned into WM_USER_SOMEKEY events.
 *
 * ----------------------------------------------------------------------*/

void
setQuasimodeKeycode( int quasimodeKeycode,
                     int keycode );

/* ------------------------------------------------------------------------
 * Returns the Quasimode keycode.
 * ........................................................................
 *
 * The returned keycode will correspond to a physical KEYCODE_*
 * constant that is currently mapped to the given quasimode
 * keycode constant.
 *
 * ----------------------------------------------------------------------*/

int
getQuasimodeKeycode( int quasimodeKeycode );

/* ------------------------------------------------------------------------
 * Pass true to make behavior modal, false to make it quasimodal (default).
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
setModality( int isModal );

/* ------------------------------------------------------------------------
 * Initializes this module.
 * ........................................................................
 *
 * This must be called before using any functions in this module.
 *
 * ----------------------------------------------------------------------*/

void
initHookHandlers( void );

/* ------------------------------------------------------------------------
 * Shuts down this module.
 * ........................................................................
 *
 * This must be called when finished using this module.
 *
 * ----------------------------------------------------------------------*/

void
shutdownHookHandlers( void );

#ifdef __cplusplus
};
#endif
