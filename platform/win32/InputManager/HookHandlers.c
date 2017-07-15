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

/*   Implementation for the key/mouse hook handlers. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "HookHandlers.h"
#include "InputManagerConstants.h"
#include "KeyhookDll.h"
#include "Input/AsyncEventProcessorRegistry.h"
#include "Logging/Logging.h"
#include "GlobalConstants.h"

#include <stdio.h>

/* ***************************************************************************
 * Private Module Variables
 * **************************************************************************/

/* Handle to Windows keyboard hook. */
static HHOOK _keyHook;

/* Handle to Windows mouse hook. */
static HHOOK _mouseHook;

/* Whether the quasimode key is currently pressed or not. */
static int _inQuasimode = 0;

/* Keycode to start the quasimode. */
static int _startQuasimodeKeycode;

/* Keycode to end the quasimode. */
static int _endQuasimodeKeycode;

/* Keycode to cancel the quasimode. */
static int _cancelQuasimodeKeycode;

/* If true, quasimode behaves modally. */
static int _isModal = FALSE;

/* If true, quasimode is currently behaving modally. */
static int _isCurrentlyModal = FALSE;

/* The thread that the key hook will send its generated events to. */
static DWORD _keyThreadId;

/* The thread that the mouse hook will send its generated events to. */
static DWORD _mouseThreadId;

/* Critical section held when we're in the keyboard hook; no data that
 * affects the keyhook should change while we're in this critical
 * section. */
static CRITICAL_SECTION _keyhookLock;


/* ***************************************************************************
 * Private Module Function Declarations
 * **************************************************************************/

static LRESULT
_hookHandlersEventProc( HWND theWindow,
                        UINT msg,
                        WPARAM wParam,
                        LPARAM lParam );

static int
_installKeyboardHook( void );

static int
_installMouseHook( void );

static int
_removeKeyboardHook( void );

static int
_removeMouseHook( void );

static void
_handlePostThreadMessageError( int errorCode,
                               int lineNum );

static int
_mouseEventProcessFunction( int event_type,
                            int x,
                            int y );

static int
_isKeyCodePassThrough( int vkCode,
                       int keypressType );

static int
_keyEventProcessFunction( int event_type,
                          int vkCode );


/* ***************************************************************************
 * Private Module Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * The hook handler Event Processing Function
 * ........................................................................
 * ----------------------------------------------------------------------*/

static LRESULT
_hookHandlersEventProc( HWND theWindow,
                        UINT msg,
                        WPARAM wParam,
                        LPARAM lParam )
{
    switch ( msg )
    {
    case WM_USER_KEYHOOK_INSTALL:
        return _installKeyboardHook();

    case WM_USER_MOUSEHOOK_INSTALL:
        return _installMouseHook();

    case WM_USER_KEYHOOK_UNINSTALL:
        return _removeKeyboardHook();

    case WM_USER_MOUSEHOOK_UNINSTALL:
        return _removeMouseHook();
    }

    /* This shouldn't happen, because this function should only be called
     * in response to the event types it was registered for. */
    errorMsg( "Bad event type message passed in." );
    return (LRESULT)0;
}

/* ------------------------------------------------------------------------
 * Installs the keyboard hook.
 * ........................................................................
 *
 * This is done by dynamically loading the keyhook DLL, locating the
 * hook procedure, and telling Windows to use it as a global
 * hook.
 *
 * LONGTERM TODO: When we are setting up the global input hooks, I
 * wonder if it's possible to detect whether any other program has
 * already installed similar hooks. And if they have, I wonder if we
 * could recognize potential incompatibilities this way and alert the
 * user of them. -Jono
 *
 * ----------------------------------------------------------------------*/

static int
_installKeyboardHook( void )
{
    int success = 0;
    HMODULE keyHookDLL;

    infoMsg( "In _installKeyboardHook()." );

    _removeKeyboardHook();
    keyHookDLL = LoadLibrary( "keyhook.dll" );

    if ( keyHookDLL )
    {
        FARPROC hookFunction = GetProcAddress( keyHookDLL,
                                               "_KH_KeyHookProc@12" );

        if ( hookFunction )
        {
            /* Set up the global keyhook. */

            _keyHook = SetWindowsHookEx(
                WH_KEYBOARD_LL,
                (HOOKPROC) hookFunction,
                (HINSTANCE) keyHookDLL,
                0
                );

            KH_SetKeyEventProcessFunction( _keyEventProcessFunction );

            if ( _keyHook )
            {
                success = 1;
            } else
                errorMsg( "SetWindowsHookEx() failed." );
        } else
            errorMsg( "GetProcAddress() failed." );
    } else
        errorMsg( "LoadLibrary() failed." );

    return success;
}

/* ------------------------------------------------------------------------
 * Installs the mouse hook.
 * ........................................................................
 *
 * See _installKeyboardHook() for implementation notes.
 *
 * ----------------------------------------------------------------------*/

static int
_installMouseHook( void )
{
    int success = 0;
    HMODULE keyHookDLL;

    _removeMouseHook();
    keyHookDLL = LoadLibrary( "keyhook.dll" );

    if ( keyHookDLL )
    {
        FARPROC mouseHookFunction = GetProcAddress( keyHookDLL,
                                                    "_KH_MouseHookProc@12" );

        if ( mouseHookFunction )
        {
            /* Set up the global keyhook. */

            _mouseHook = SetWindowsHookEx(
                WH_MOUSE_LL,
                (HOOKPROC) mouseHookFunction,
                (HINSTANCE) keyHookDLL,
                0
                );

            KH_SetMouseEventProcessFunction( _mouseEventProcessFunction );

            if ( _mouseHook )
            {
                success = 1;
            }
        }
    }

    return success;
}

/* ------------------------------------------------------------------------
 * Removes the keyboard hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

static int
_removeKeyboardHook( void )
{
    if ( _keyHook )
    {
        UnhookWindowsHookEx( _keyHook );
        _keyHook = NULL;
    }
    if ( _mouseHook )
    {
        UnhookWindowsHookEx( _mouseHook );
        _mouseHook = NULL;
    }

    return 1;
}

/* ------------------------------------------------------------------------
 * Removes the mouse hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

static int
_removeMouseHook( void )
{
    if ( _mouseHook )
    {
        UnhookWindowsHookEx( _mouseHook );
        _mouseHook = NULL;
    }

    return 1;
}

/* ------------------------------------------------------------------------
 * Processes error codes from the Windows system call PostThreadMessage.
 * ........................................................................
 *
 * After you call PostThreadMessage, you should pass its return value to
 * this function, which figures out if anything went wrong and if so,
 * logs an error message.
 *
 * Note that we would like to bail out if this contingency occurs, but
 * since PostThreadMessage is being called from a low-level keyboard
 * hook, trying to throw an exception or fail an assert would result
 * in Really Weird Stuff.
 *
 * ----------------------------------------------------------------------*/

static void
_handlePostThreadMessageError( int errorCode,
                               int lineNum )
{
    char errorText[256];
    
    if ( errorCode == 0 )
    {
        errorCode = GetLastError();
        sprintf( errorText, 
                 "PostThreadMessage failed with error %d on line %d.",
                 errorCode, lineNum );
        errorMsg( errorText );
    }
}

/* ------------------------------------------------------------------------
 * Process mouse events sent from the mouse hook.
 * ........................................................................
 *
 * This function is a callback from KeyhookDll, called whenever a user
 * mouse input event occurs.
 *
 * Posts the events to the main thread, where they will be handled by the
 * main loop of the message window.
 *
 * ----------------------------------------------------------------------*/

static int
_mouseEventProcessFunction( int event_type,
                            int x,
                            int y )
{
    int errorCode;

    if ( event_type == WM_MOUSEMOVE ) {
        errorCode = PostThreadMessage( _mouseThreadId,
                                       WM_USER_MOUSEMOVE,
                                       x, y );
        _handlePostThreadMessageError( errorCode, __LINE__ );
    } else {
        errorCode = PostThreadMessage( _mouseThreadId,
                                       WM_USER_SOMEMOUSEBTN,
                                       0, 0 );
        _handlePostThreadMessageError( errorCode, __LINE__ );
    }
    return HOOK_PASS_ON_EVENT;
}

/* ------------------------------------------------------------------------
 * Return whether the given key code is a pass-through key.
 * ........................................................................
 *
 * vkCode is a Windows VK_* constant.
 *
 * keypressType is WM_KEYUP or WM_KEYDOWN.
 *
 * When in the Quasimode, we want to pass modifier keys such as the
 * shift, control, and the alt (aka menu) keys back to the OS so other
 * applications can process them. This is done for a number of
 * reasons:
 * 
 * (1) On certain keyboards, such as Japanese keyboards, the
 * user has to hold down a modifier key and then press Caps
 * Lock and then release the modifier key to use Caps Lock as
 * a quasimode key.  Blocking the release of the modifier key
 * while in the quasimode would prevent the release of the
 * modifier key from ever being known to the rest of the
 * system, so the rest of the system would still think that
 * the modifier key was being pressed down, even if it was
 * released during the quasimode.
 *
 * (2) Some applications, such as Ventrilo and Teamspeak,
 * allow modifier keys to be used as system-wide quasimodes;
 * we want to allow such quasimodes to be used while Enso is
 * being used.
 *
 * NOTE: If the key is in fact a user-selected quasimode key,
 * we have to override this pass-through mechanism, and keep
 * the events for ourselves.
 *
 * NOTE: We're not going to pass through key down events for the alt
 * keys because this is used to make the quasimode "sticky", and
 * because this will, in most standard Windows applications,
 * inadvertently activate the menu bar, which will destroy our ability
 * to examine the current selection.
 * 
 * ----------------------------------------------------------------------*/

static int
_isKeyCodePassThrough( int vkCode,
                       int keypressType )
{
    return (( vkCode == VK_LSHIFT ||
              vkCode == VK_RSHIFT ||
              vkCode == VK_LCONTROL ||
              vkCode == VK_RCONTROL ||
              (vkCode == VK_LMENU && keypressType == WM_KEYUP) ||
              (vkCode == VK_RMENU && keypressType == WM_KEYUP) )
              && !(vkCode == _startQuasimodeKeycode) );
}

/* ------------------------------------------------------------------------
 * Process keypresses sent from the keyhook.
 * ........................................................................
 *
 * This function is a callback from KeyhookDll, called whenever a user
 * keypress occurs.
 *
 * This function intercepts and "eats" keypresses of the quasimode key
 * and any other keys pressed while the quasimode key is being held
 * down.  It then passes such keypresses on to the InputManager's event
 * loop for further processing.  When the quasimode key is not being held
 * down, keypresses become dismissal events instead.
 *
 * ----------------------------------------------------------------------*/

static int
_keyEventProcessFunction( int event_type,
                          int vkCode )
{
    /* This variable (our return value) determines whether we're going
     * to "eat" the keypress we've been given, or whether we'll pass
     * it on to the operating system. */
    int result = HOOK_PASS_ON_EVENT;
    int errorCode;

    EnterCriticalSection( &_keyhookLock );

    /* Note: In the following code, VK_SNAPSHOT means the "print
     * screen" key. We never eat, process, or interact with the print
     * screen key, because we want to be able to take screenshots of
     * Enso. */
    switch ( event_type )
    {
    case WM_KEYDOWN:
        if ( vkCode == _startQuasimodeKeycode && !_inQuasimode )
        {
            /* We are entering the quasimode. */
            _inQuasimode = TRUE;

            _isCurrentlyModal = _isModal;

            result = HOOK_EAT_EVENT;
            errorCode = PostThreadMessage( _keyThreadId,
                                           WM_USER_KEYPRESS,
                                           EVENT_KEY_QUASIMODE,
                                           KEYCODE_QUASIMODE_START );
            _handlePostThreadMessageError( errorCode, __LINE__ );
        } else if ( _inQuasimode &&
                    vkCode != VK_SNAPSHOT &&
                    !_isKeyCodePassThrough(vkCode, WM_KEYDOWN) )
        {
            /* A valid keypress occurred while in the quasimode. */
            result = HOOK_EAT_EVENT;

            if ( _inQuasimode && _isCurrentlyModal &&
                 ( (vkCode == _endQuasimodeKeycode) ||
                   (vkCode == _cancelQuasimodeKeycode) ) )
            {
                /* We are leaving the modal quasimode in some way. */
                int quasimodeEventType;

                _inQuasimode = FALSE;

                /* Now figure out if we're ending or cancelling it. */
                if (vkCode == _endQuasimodeKeycode)
                    quasimodeEventType = KEYCODE_QUASIMODE_END;
                else
                    quasimodeEventType = KEYCODE_QUASIMODE_CANCEL;

                errorCode = PostThreadMessage( _keyThreadId,
                                               WM_USER_KEYPRESS,
                                               EVENT_KEY_QUASIMODE,
                                               quasimodeEventType );
                _handlePostThreadMessageError( errorCode, __LINE__ );
            } else {
                /* Other key pressed while in quasimode: pass it on
                 * to be processed as part of a possible command name. */

                if ( _inQuasimode &&
                     (vkCode == VK_LMENU || vkCode == VK_RMENU) )
                    /* We may have been non-modal before, but it looks
                     * like alt has been pressed down while we're in
                     * the quasimode, so set ourselves to modal for
                     * the rest of this quasimode session. */
                    _isCurrentlyModal = TRUE;

                errorCode = PostThreadMessage( _keyThreadId,
                                               WM_USER_KEYPRESS,
                                               EVENT_KEY_DOWN,
                                               vkCode );
                _handlePostThreadMessageError( errorCode, __LINE__ );
            }
        } else if ( vkCode != VK_SNAPSHOT ) {
            /* We're not in the quasimode, or it's a passthrough key;
             * just pass the key on as a WM_USER_SOMEKEY event. */
            errorCode = PostThreadMessage( _keyThreadId, 
                                           WM_USER_SOMEKEY,
                                           0, 0 );
            _handlePostThreadMessageError( errorCode, __LINE__ );
        }
        break;
    case WM_KEYUP:
        if ( _inQuasimode &&
             vkCode != VK_SNAPSHOT &&
             !_isKeyCodePassThrough(vkCode, WM_KEYUP) )
        {
            /* A valid key release occurred while in the quasimode. */
            result = HOOK_EAT_EVENT;

            if ( vkCode == _startQuasimodeKeycode && !_isCurrentlyModal )
            {
                /* Leaving the quasimode, quasimodally. */
                _inQuasimode = FALSE;

                errorCode = PostThreadMessage( _keyThreadId,
                                               WM_USER_KEYPRESS,
                                               EVENT_KEY_QUASIMODE,
                                               KEYCODE_QUASIMODE_END );
                _handlePostThreadMessageError( errorCode, __LINE__ );
            } else {
                /* Other key released when in quasimode.  Pass it on 
                 * to be processed as part of a possible command name. */

                errorCode = PostThreadMessage( _keyThreadId,
                                               WM_USER_KEYPRESS,
                                               EVENT_KEY_UP,
                                               vkCode );
                _handlePostThreadMessageError( errorCode, __LINE__ );
            }
        } else if ( vkCode != VK_SNAPSHOT ) {
            /* Key released when not in quasimode, or it's a passthru
             * key: pass it on as a generic WM_USER_SOMEKEY keypress;
             * it will be used to dismiss Enso's transparent
             * message. */
            errorCode = PostThreadMessage( _keyThreadId,
                                           WM_USER_SOMEKEY,
                                           0, 0 );
            _handlePostThreadMessageError( errorCode, __LINE__ );
        }
        break;
    default:
        break;
    }

    LeaveCriticalSection( &_keyhookLock );

    return result;
}


/* ***************************************************************************
 * Public Module Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Sets the Quasimode keycode.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
setQuasimodeKeycode( int quasimodeKeycode,
                     int keycode )
{
    EnterCriticalSection( &_keyhookLock );

    switch ( quasimodeKeycode )
    {
    case KEYCODE_QUASIMODE_START:
        _startQuasimodeKeycode = keycode;
        break;
    case KEYCODE_QUASIMODE_END:
        _endQuasimodeKeycode = keycode;
        break;
    case KEYCODE_QUASIMODE_CANCEL:
        _cancelQuasimodeKeycode = keycode;
        break;
    default:
        errorMsg( "Invalid quasimodeKeycode." );
        break;
    }

    LeaveCriticalSection( &_keyhookLock );
}

/* ------------------------------------------------------------------------
 * Returns the Quasimode keycode.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
getQuasimodeKeycode( int quasimodeKeycode )
{
    int keycode;

    switch ( quasimodeKeycode )
    {
    case KEYCODE_QUASIMODE_START:
        keycode = _startQuasimodeKeycode;
        break;
    case KEYCODE_QUASIMODE_END:
        keycode = _endQuasimodeKeycode;
        break;
    case KEYCODE_QUASIMODE_CANCEL:
        keycode = _cancelQuasimodeKeycode;
        break;
    default:
        errorMsg( "Invalid quasimodeKeycode." );
        keycode = 0;
        break;
    }

    return keycode;
}

/* ------------------------------------------------------------------------
 * Pass true to make behavior modal, false to make it quasimodal (default).
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
setModality( int isModal )
{
    EnterCriticalSection( &_keyhookLock );
    _isModal = isModal;
    LeaveCriticalSection( &_keyhookLock );
}

/* ------------------------------------------------------------------------
 * Installs the keyboard/mouse hooks.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
installKeyboardHook( DWORD threadId )
{
    _keyThreadId = threadId;

    return sendMessageToAsyncEventWindow( WM_USER_KEYHOOK_INSTALL, 0, 0,
                                          _hookHandlersEventProc );
}

int
installMouseHook( DWORD threadId )
{
    _mouseThreadId = threadId;

    return sendMessageToAsyncEventWindow( WM_USER_MOUSEHOOK_INSTALL, 0, 0,
                                          _hookHandlersEventProc );
}

/* ------------------------------------------------------------------------
 * Removes the keyboard hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
removeKeyboardHook( void )
{
    return sendMessageToAsyncEventWindow( WM_USER_KEYHOOK_UNINSTALL, 0, 0,
                                          _hookHandlersEventProc );
}

/* ------------------------------------------------------------------------
 * Removes the mouse hook, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
removeMouseHook( void )
{
    return sendMessageToAsyncEventWindow( WM_USER_MOUSEHOOK_UNINSTALL, 0, 0,
                                          _hookHandlersEventProc );
}

/* ------------------------------------------------------------------------
 * Initializes this module.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
initHookHandlers( void )
{
    InitializeCriticalSection( &_keyhookLock );
}

/* ------------------------------------------------------------------------
 * Shuts down this module.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
shutdownHookHandlers( void )
{
    DeleteCriticalSection( &_keyhookLock );
}
