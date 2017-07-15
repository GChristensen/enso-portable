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

/*   Header file for Enso's asynchronous event processing thread.
 *
 *   This module contains a message-only window, along with a thread
 *   to run it, which handles all user input events at the system
 *   level by doing any necessary low-level processing, forwarding
 *   them to a parent thread, and returning immediately.  Doing this
 *   allows the low-level user interface and host operating system to
 *   remain completely responsive even if Enso hangs or takes a long
 *   time to process something.
 */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "Input/AsyncEventProcessorRegistry.h"
#include "Input/EnsoThread.h"
#include "WinSdk.h"



/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Window class name for the invisible window. */
#define ASYNC_EVENT_WINDOW_CLASS_NAME "MehitabelAsyncEventWindow"

/* Thread exit codes */
#define ASYNC_EVENT_THREAD_ABORTED      0
#define ASYNC_EVENT_THREAD_SUCCESSFUL   1   


/* ***************************************************************************
 * Class Declaration
 * **************************************************************************/

/* ===========================================================================
 * AsyncEventThread class
 * ...........................................................................
 *
 * This class encapsulates a message-only window which is used for all-purpose
 * asynchronous event handling.   It is a singleton.
 *
 * The thread's return code is ASYNC_EVENT_THREAD_ABORTED if it
 * failed, and ASYNC_EVENT_THREAD_SUCCESSFUL if it was successful.
 *
 * =========================================================================*/

class AsyncEventThread : public EnsoThread
{
public:

    /* ====================================================================
     * Construction and Destruction
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Constructor
     * ------------------------------------------------------------------*/

    AsyncEventThread( void );

    /* --------------------------------------------------------------------
     * Destructor
     * ------------------------------------------------------------------*/

    virtual
    ~AsyncEventThread( void );

    /* ====================================================================
     * Public Member Functions
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Stops the thread.
     * ....................................................................
     * ------------------------------------------------------------------*/

    void
    stop( void );

private:

    /* ====================================================================
     * Private Member Functions
     * ==================================================================*/

    bool
    _createMessageWindow( void );

    void
    _closeMessageWindow( void );

    static LRESULT CALLBACK
    _asyncMessageWindowProc( HWND theWindow,
                             UINT msg,
                             WPARAM wParam,
                             LPARAM lParam );

    static LRESULT
    _asyncEventProc( HWND theWindow,
                     UINT msg,
                     WPARAM wParam,
                     LPARAM lParam );

    virtual int
    _run( void );

    /* ====================================================================
     * Private Data Members
     * ==================================================================*/

    /* ID of the parent thread. */
    DWORD _parentThreadId;

    /* Invisible, message-only window handle to receive events. */
    HWND _asyncMessageWindow;

    /* Invisible window class. */
    static ATOM _asyncMessageWindowClass;

    /* Flag that is set to terminate the event thread. */
    volatile bool _terminating;
};
