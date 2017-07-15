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

/*   Implementation for the exit handler. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "Input/AsyncEventProcessorRegistry.h"
#include "Logging/Logging.h"
#include "GlobalConstants.h"


/* ***************************************************************************
 * Private Module Variables
 * **************************************************************************/

/* The parent thread to send generated events to. */
static DWORD _parentThreadId;


/* ***************************************************************************
 * Private Module Function Declarations
 * **************************************************************************/

static LRESULT
_exitHandlerEventProc( HWND theWindow,
                       UINT msg,
                       WPARAM wParam,
                       LPARAM lParam );


/* ***************************************************************************
 * Private Module Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * The hook handler Event Processing Function
 * ........................................................................
 * ----------------------------------------------------------------------*/

static LRESULT
_exitHandlerEventProc( HWND theWindow,
                       UINT msg,
                       WPARAM wParam,
                       LPARAM lParam )
{
    switch ( msg )
    {
    case WM_CLOSE:
        PostThreadMessage( _parentThreadId,
                           WM_USER_EXIT_REQUESTED,
                           0, 0 );
        return (LRESULT)0;
    }

    /* This shouldn't happen, because this function should
     * only be called in response to the event types it was
     * registered for. */
    errorMsg( "Bad event type message passed in." );
    return (LRESULT)0;
}


/* ***************************************************************************
 * Public Module Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Installs the exit handler.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
installExitHandler( DWORD threadId )
{
    int wasSuccessful;

    _parentThreadId = threadId;

    wasSuccessful = registerAsyncEventProc(
        WM_CLOSE,
        _exitHandlerEventProc
        );

    if ( !wasSuccessful )
    {
        errorMsg( "Registering WM_CLOSE failed.\n" );
        return 0;
    }

    return 1;
}

/* ------------------------------------------------------------------------
 * Removes the exit handler, if it's currently active.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
removeExitHandler( void )
{
    if ( !unregisterAsyncEventProc( WM_CLOSE ) )
    {
        errorMsg( "Unregistering WM_CLOSE failed.\n" );
        return 0;
    }

    return 1;
}
