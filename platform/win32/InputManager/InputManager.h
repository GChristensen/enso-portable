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

/*   Header file for Enso's input manager.
 *
 *   Enso's input manager consists of a main event loop that
 *   provides input event notification to client code.  As such, the
 *   input manager offers a facade through which a higher-level
 *   frontend can build a robust user interface.
 */

#ifndef _INPUT_MANAGER_H_
#define _INPUT_MANAGER_H_

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#ifndef SWIG
#include "WinSdk.h"
#include "Logging/Logging.h"
#include "InputManagerConstants.h"
#include "InputManagerExceptions.h"
#include "Python.h"
#endif


/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Window class name for the message window. */
#define MESSAGE_WINDOW_CLASS_NAME "MehitabelMsgWindow"


/* ***************************************************************************
 * Class Declarations
 * **************************************************************************/

/* ===========================================================================
 * InputManager class
 * ...........................................................................
 *
 * The InputManager class encapsulates Mehitabel's input backend.  This
 * class is a singleton.
 *
 * =========================================================================*/

class InputManager
{
public:

    /* ====================================================================
     * Construction and Destruction
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Constructor
     * --------------------------------------------------------------------
     *
     * This constructor does not actually start the main event loop. It
     * also does not set the quasimode activation key, so client code
     * should call setQuasimodeKeycode() immediately after instantiation.
     *
     * ------------------------------------------------------------------*/

    InputManager( void );

    /* --------------------------------------------------------------------
     * Destructor
     * ------------------------------------------------------------------*/

    virtual
    ~InputManager( void );

    /* ====================================================================
     * Public Member Functions
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Runs the InputManager's event loop.
     * ....................................................................
     *
     * This is the primary loop of the module, and the place from which
     * most of Mehitabel's actions will originate from.
     *
     * ------------------------------------------------------------------*/

    void
    run( void );

    /* --------------------------------------------------------------------
     * Stops the InputManager's event loop.
     * ....................................................................
     *
     * This signals the InputManager's event loop to exit.  It
     * should be called while run() is executing.
     *
     * This method is thread-safe.
     *
     * ------------------------------------------------------------------*/

    void
    stop( void );

    /* --------------------------------------------------------------------
     * Sets whether mouse events are triggered.
     * ....................................................................
     *
     * If a false (zero) value is passed in, this enables mouse events
     * such as onMouseMove() and onSomeMouseButton().  If a true
     * (nonzero) value is passed in, these events will not be
     * triggered (possibly improving system performance).
     *
     * By default, mouse events are not enabled.
     *
     * ------------------------------------------------------------------*/

    void
    enableMouseEvents( int enabled );

    /* --------------------------------------------------------------------
     * Event handler for quasimodal keystrokes.
     * ....................................................................
     *
     * This is called on the keydown of the quasimode key, and on all
     * subsequent keypresses until we leave the quasimode.
     *
     * This method should be overridden by subclasses; the default
     * implementation simply checks to see if the 'q' key was pressed
     * and if so, stops the input manager (this default implementation
     * is provided purely for testing purposes only).
     *
     * eventType corresponds to an EVENT_KEY_* constant.
     *
     * vkCode is the virtual key code of the key pressed and
     * corresponds to a KEYCODE_* constant.
     *
     * LONGTERM TODO: We need to decide what our long-term keycode
     * mapping strategy is. Given that we won't, in general, be
     * dealing with internationalization, we should still be as
     * graceful as possible about it. Are we, for instance, requiring
     * that all command names involve a fixed set of allowed
     * characters (e.g., disallowing Japanese characters in command
     * names even if they are in the start menu shortcuts)? If so, how
     * do we interpret input when another keyboard/keyboard layout is
     * being used by the user? More generally, how do we transform
     * keystrokes into characters?  Our current technique is to use
     * the low-level KEYCODE_* codes and use their their ASCII
     * representation. It should be noted that, even on foreign
     * computers, these KEYCODE_* codes are exactly the same, i.e.,
     * Windows sees a Japanese input keyboard as a special layout of a
     * standard 101-key QWERTY keyboard. We should either adopt this
     * technique formally and eliminate this LONGTERM TODO, or decide on a
     * better one. -- Andrew
     *
     * ------------------------------------------------------------------*/

    virtual void
    onKeypress( int eventType,
                int vkCode ) {};

    /* --------------------------------------------------------------------
     * Event handler for non-quasimodal keystrokes.
     * ....................................................................
     *
     * This is called whenever the command quasimode is not active,
     * and when the user has not pressed or released the command
     * quasimode key.  For security purposes, we do not pass the
     * actual key pressed.
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onSomeKey( void ) {};

    /* --------------------------------------------------------------------
     * Event handler for system-wide mouseclicks.
     * ....................................................................
     *
     * The actual button pressed is not passed.  This method is also
     * called when the mouse wheel is scrolled.
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onSomeMouseButton( void ) {};

    /* --------------------------------------------------------------------
     * Event handler for interprocess-initiated exit requests.
     * ....................................................................
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onExitRequested( void ) {};

    /* --------------------------------------------------------------------
     * Event handler for system-wide mouse movement.
     * ....................................................................
     *
     * The absolute position of the cursor on-screen is passed.
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onMouseMove( int x,
                 int y ) {};

    /* --------------------------------------------------------------------
     * Returns the current keycode used to enable/disable the quasimode.
     * ....................................................................
     *
     * The returned keycode will correspond to a physical KEYCODE_*
     * constant that is currently mapped to the given quasimode
     * keycode constant.
     *
     * ------------------------------------------------------------------*/

    int
    getQuasimodeKeycode( int quasimodeKeycode );

    /* --------------------------------------------------------------------
     * Maps the given quasimode keycode to the given physical keycode.
     * ....................................................................
     *
     * The quasimodeKeycode should correspond to one of the
     * KEYCODE_QUASIMODE_* constants, and names the quasimode keycode
     * that should be set.
     *
     * The keycode should correspond to a KEYCODE_* constant, and names
     * the physical key that maps to the quasimodal keycode.
     *
     * ------------------------------------------------------------------*/

    void
    setQuasimodeKeycode( int quasimodeKeycode,
                         int keycode );

    /* --------------------------------------------------------------------
     * Sets behavior to be modal (pass in 1) or quasimodal (pass in 0).
     * ....................................................................
     * ------------------------------------------------------------------*/

    void
    setModality( int );

    /* --------------------------------------------------------------------
     * Sets the caps lock mode on the user's system.
     * ....................................................................
     *
     * If 'mode' is true, then Caps Lock will be enabled; otherwise,
     * it will be disabled.
     *
     * ------------------------------------------------------------------*/

    void
    setCapsLockMode( bool mode );

    /* --------------------------------------------------------------------
     * Event handler for timer events.
     * ....................................................................
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.  msPassed gives the number of
     * milliseconds passed since the previous onTick.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onTick( int msPassed ) {};

    /* --------------------------------------------------------------------
     * Event handler called upon initialization of the input manager.
     * ....................................................................
     *
     * This method should be overridden by subclasses; the default
     * implementation does nothing.
     *
     * ------------------------------------------------------------------*/

    virtual void
    onInit() {};

#ifndef SWIG
private:

    /* ====================================================================
     * Private Member Functions
     * ==================================================================*/

    void
    _registerTimer( void );

    void
    _unregisterTimer( void );

    void
    _handleThreadMessage( UINT msg,
                          WPARAM wParam,
                          LPARAM lParam );

    /* ====================================================================
     * Private Data Members
     * ==================================================================*/

    /* Thread ID of the main application thread. */
    DWORD _threadId;

    /* Timer ID of the tick timer. */
    UINT_PTR _timerId;

    /* Flag that is set to terminate the event thread. */
    volatile bool _terminating;
#endif
};

#endif
