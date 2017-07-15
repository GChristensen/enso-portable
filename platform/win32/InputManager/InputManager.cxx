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

/*   Implementation for Mehitabel's input manager. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "InputManager.h"
#include "HookHandlers.h"
#include "ExitHandler.h"
#include "GlobalConstants.h"

#include <stdio.h>


/* ***************************************************************************
 * InputManager - Public Methods
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * This constructor initializes the InputManager.
 * ........................................................................
 * ----------------------------------------------------------------------*/

InputManager::InputManager( void ) :
    _terminating( false ),
    _timerId( 0 )
{
    _threadId = GetCurrentThreadId();

    /* LONGTERM TODO: The signature of this constructor is
     * inconsistent because it requires the client to pass in the
     * quasimode start keycode, but not the quasimode end or cancel
     * keycodes.  We should either hardcode all of them here or
     * require the client to pass them all in, not a mix of both. */

    /* Force the system to create a message queue for this thread, so
     * that PostThreadMessage() calls to our thread don't fail. */
    MSG msg;
    PeekMessage(&msg, NULL, WM_USER, WM_USER, PM_NOREMOVE);

    ::initHookHandlers();
    ::setQuasimodeKeycode( KEYCODE_QUASIMODE_START, VK_CAPITAL );
    ::setQuasimodeKeycode( KEYCODE_QUASIMODE_END, VK_RETURN );
    ::setQuasimodeKeycode( KEYCODE_QUASIMODE_CANCEL, VK_ESCAPE );
}


/* ------------------------------------------------------------------------
 * This destructor shuts down the InputManager.
 * ........................................................................
 * ----------------------------------------------------------------------*/

InputManager::~InputManager( void )
{
    ::shutdownHookHandlers();
}

/* ------------------------------------------------------------------------
 * Sets whether mouse events are triggered.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
InputManager::enableMouseEvents( int enabled )
{
    if ( enabled )
        installMouseHook(_threadId);
    else
        removeMouseHook();
}

/* ------------------------------------------------------------------------
 * Handles a message sent to the InputManager thread.
 * ........................................................................
 *
 * This is where all calls out to client code are made.
 *
 * ----------------------------------------------------------------------*/

void
InputManager::_handleThreadMessage( UINT msg,
                                    WPARAM wParam,
                                    LPARAM lParam )
{
    switch ( msg ) { 
    case WM_TIMER:
        if ( wParam == _timerId )
            onTick( TICK_TIMER_INTRVL );
        break;

    case WM_USER_MOUSEMOVE:
        onMouseMove( wParam, lParam );
        break;

    case WM_USER_SOMEMOUSEBTN:
        onSomeMouseButton();
        break;

    case WM_USER_SOMEKEY:
        onSomeKey();
        break;

    case WM_USER_KEYPRESS:
        onKeypress( wParam, lParam );
        break;

    case WM_USER_QUIT: 
        /* Sent by our owner when we're terminating.  We don't need to
         * do anything; this is just to kick the event loop. */
        debugMsg( "Message window thread: quit signal received." );
        break;

    case WM_USER_INIT:
        onInit();
        break;

    case WM_USER_EXIT_REQUESTED:
        onExitRequested();
        break;

    default:
        warnMsg( "Unhandled thread message in InputManager." );
        break;
    }
}

/* ------------------------------------------------------------------------
 * Sets the caps lock mode on the user's system.
 * ........................................................................
 *
 * This function will also need to temporarily uninstall the low-level
 * keyboard hooks, if caps lock is the current quasimode key, to
 * ensure that all simulated presses/releases of the caps lock key in
 * this code are not intercepted by the low-level keyboard hook.
 *
 * ----------------------------------------------------------------------*/

void
InputManager::setCapsLockMode( bool mode )
{
    int currState = GetKeyState( VK_CAPITAL );

    int desiredCapsLockState;

    int quasimodeKeycode = getQuasimodeKeycode( KEYCODE_QUASIMODE_START );

    if ( mode )
        desiredCapsLockState = 1;
    else
        desiredCapsLockState = 0;

    /* For help on what some of the literals associated with currState
     * mean, see the MSDN documentation for the GetKeyState()
     * function. */
    if ( (currState & 0x01) != desiredCapsLockState )
    {
        /* Looks like we need to toggle caps lock. */
        infoMsg( "Attempting to toggle caps lock mode." );

        /* Disable our low-level keyboard hook if necessary. */
        if ( quasimodeKeycode == VK_CAPITAL &&
             (!removeKeyboardHook()) )
        {
            errorMsg( "Couldn't remove keyboard/mouse hooks." );
            throw MehitabelException();
        } else {
            infoMsg( "Removed keyboard/mouse hooks." );
        }

        INPUT keypress;
        int errorOccurred = 0;

        keypress.type = INPUT_KEYBOARD;
        keypress.ki.wVk = VK_CAPITAL;

        if ( (currState & 0x80) == 0x80 )
        {
            /* Looks like the caps lock key is physically pressed
             * down.  Let's temporarily release it. */
            keypress.ki.dwFlags = KEYEVENTF_KEYUP;
            if ( SendInput( 1, &keypress, sizeof(INPUT) ) == 0 )
                errorOccurred = 1;
        }

        /* Press the caps lock key down. */
        keypress.ki.dwFlags = 0;
        if ( SendInput( 1, &keypress, sizeof(INPUT) ) == 0 )
            errorOccurred = 1;

        /* Now release the caps lock key, unless it was already being
         * pressed down. */
        if ( (currState & 0x80) != 0x80 )
        {
            keypress.ki.dwFlags = KEYEVENTF_KEYUP;
            if ( SendInput( 1, &keypress, sizeof(INPUT) ) == 0 )
                errorOccurred = 1;
        }

        if ( errorOccurred )
            warnMsg( "Warning: unable to toggle caps lock mode." );

        /* Re-enable our low-level keyboard hook if necessary. */
        if ( quasimodeKeycode == VK_CAPITAL &&
             (!installKeyboardHook(_threadId)) )
        {
            errorMsg( "installKeyboardHook() failed!" );
            throw MehitabelException();
        }
    }
}

/* ------------------------------------------------------------------------
 * Registers the Windows timer event source. 
 * ........................................................................
 *
 * Here we set up the timer.  Note that we're not passing an hwnd,
 * which means that the WM_TIMER messages will be handled by the main
 * thread; this guarantees that we will be processing the timer
 * messages in the main thread's main message loop.  We don't want to
 * register the timer with a window because there are some strange
 * situations, such as when using ShellExecute(), whereby the window
 * procedure can be called with a WM_TIMER message from outside code.
 *
 * ----------------------------------------------------------------------*/

void
InputManager::_registerTimer( void )
{
    _timerId = SetTimer( NULL, 0, TICK_TIMER_INTRVL, NULL );
    if ( _timerId == 0 )
    {
        errorMsg( "SetTimer() failed!" );
        throw MehitabelException();
    }
}

/* ------------------------------------------------------------------------
 * Unregisters the Windows timer event source. 
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
InputManager::_unregisterTimer( void )
{
    /* Stop and clean up the timer. */
    if ( _timerId )
    {
        KillTimer( NULL, _timerId );
        _timerId = 0;
    }
}

/* ------------------------------------------------------------------------
 * Runs the InputManager's event loop.
 * ........................................................................
 *
 * This is the main loop of the module; it also takes care of any
 * other necessary setup and teardown.
 *
 * ----------------------------------------------------------------------*/

void
InputManager::run( void )
{
    /* Queue the initialization message. */
    BOOL errorCode = PostThreadMessage( _threadId, WM_USER_INIT, 0, 0 );

    if ( errorCode == 0 )
    {
        errorMsg( "Posting of WM_USER_INIT failed." );
        throw MehitabelException();
    }

    _registerTimer();

    if ( !installExitHandler(_threadId) )
    {
        errorMsg( "installExitHandler() failed!" );
        throw MehitabelException();
    }
    else {
        infoMsg( "Installed exit handler." );
    }

    if ( !installKeyboardHook(_threadId) )
    {
        errorMsg( "installKeyboardHook() failed!" );
        throw MehitabelException();
    }
    else {
        infoMsg( "Installed keyboard/mouse hooks." );
    }

    bool pythonExceptionOccurred = false;

    /* Main event loop continues until _terminating becomes true
     * or until an exception occurs. */
    try {
        _terminating = false;

        while ( !_terminating )
        {
            MSG theMessage;
            int result;

            /* Get the next event to process.  While we're waiting for
             * an event, allow Python time to run its threads. */
            Py_BEGIN_ALLOW_THREADS;
            result = GetMessage( &theMessage, 0, 0, 0 );
            Py_END_ALLOW_THREADS;

            if ( result != -1 )
            {
                if ( theMessage.hwnd == NULL )
                {
                    _handleThreadMessage( theMessage.message,
                                          theMessage.wParam,
                                          theMessage.lParam );
                } else {
                    /* There's nothing in this module that this
                     * message is going to, because this module
                     * doesn't create any windows; we can only assume
                     * that some external client code in the same
                     * thread as us has created a window, so we'll do
                     * our best to try to service it. */

                    /* LONGTERM TODO: Remove this logging code at some
                     * point, once we've diagnosed exactly what
                     * windows are having messages sent to them. As of
                     * 1/23/07 we only seem to be getting an
                     * occassional message to a window of class
                     * OleMainThreadWndClass, which doesn't use up too
                     * much log file space. See ticket #366 for more
                     * information. */
                    char windowClassName[256] = "";

                    GetClassName( theMessage.hwnd, windowClassName, 256 );
                    infoMsg( "InputManager received a window message for"
                             "a window with class name:" );
                    infoMsg( windowClassName );

                    DispatchMessage( &theMessage );
                }
            } else {
                errorMsg( "GetMessage() error." );
                _terminating = true;
                throw MehitabelException();
            }
        }
    } catch ( MehitabelPythonException ) {
        infoMsg( "A Python exception occurred in an InputManager "
                 "event handler." );
        pythonExceptionOccurred = true;
    }

    if ( !removeKeyboardHook() )
    {
        errorMsg( "Couldn't remove keyboard/mouse hooks." );
        throw MehitabelException();
    } else {
        infoMsg( "Removed keyboard/mouse hooks." );
    }

    if ( !removeExitHandler() )
    {
        errorMsg( "Couldn't remove exit handler." );
        throw MehitabelException();
    } else {
        infoMsg( "Removed exit handler." );
    }

    /* LONGTERM TODO: This won't get called if an exception has been
     * thrown... Probably okay, though, since we're already up a creek
     * if an exception has been thrown. */
    _unregisterTimer();

    if ( pythonExceptionOccurred )
        throw MehitabelPythonException();
}


/* ------------------------------------------------------------------------
 * Stops the InputManager's event loop.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
InputManager::stop( void )
{
    int errorCode;

    /* Stop the message loop: setting this to true causes the while loop
     * in run() to terminate. */
    _terminating = true;

    /* Notify the thread that it should clean up window and quit */
    errorCode = PostThreadMessage( _threadId, WM_USER_QUIT, 0, 0 );

    if ( errorCode == 0 )
    {
        char errorText[256];

        errorCode = GetLastError();
        sprintf( errorText, 
                 "In InputManager::stop(): "
                 "PostThreadMessage failed with error %d.",
                 errorCode );
        errorMsg( errorText );
        
        throw MehitabelException();
    }
}

/* ------------------------------------------------------------------------
 * Returns the current keycode used to enable/disable the quasimode.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
InputManager::getQuasimodeKeycode( int quasimodeKeycode )
{
    return ::getQuasimodeKeycode( quasimodeKeycode );
}

/* --------------------------------------------------------------------
 * Maps the given quasimode keycode to the given physical keycode.
 * ....................................................................
 * ------------------------------------------------------------------*/

void
InputManager::setQuasimodeKeycode( int quasimodeKeycode,
                                   int keycode )
{
    ::setQuasimodeKeycode( quasimodeKeycode, keycode );
    if ( keycode == KEYCODE_CAPITAL ) {
        // Whenever the quasimode key is set to the capslock key,
        // disable the capslock mode.
        setCapsLockMode( 0 );
    }
}

/* ------------------------------------------------------------------------
 * Pass true to make behavior modal, false to make it quasimodal (default).
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
InputManager::setModality( int isModal )
{
    ::setModality( isModal );
}
