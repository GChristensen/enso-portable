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

/*   Implementation file for AsyncEventProcessorRegistry. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "Input/AsyncEventProcessorRegistry.h"
#include "Logging/Logging.h"

#include "Python.h"

#include <map>


/* ***************************************************************************
 * Typedefs
 * **************************************************************************/

/* Define an STL map in which the map keys are integers corresponding
 * to values of msg, and map values are pointers to event processor
 * functions.  A map entry means that this type of msg should be
 * processed by this function. */

typedef std::map<int, EVENT_PROCESSOR_FUNC> FunctionMap;


/* ***************************************************************************
 * Static Module Variables
 * **************************************************************************/

/* Single instance of the function map */
static FunctionMap _functionMap;

/* Critical section used to ensure the function map is accessed in a
 * thread-safe way. */
static CRITICAL_SECTION _functionMapLock;

/* There is only one async event window in the program, and it is created and
 * destroyed not in this module, but by the AsyncEventThread.  This module
 * maintains a reference to this window for the convenience of client code,
 * which can be accessed with get and set methods. */
static HWND _asyncEventWindowHandle = NULL;

/* Whether our module is initialized or not. */
static int _isInitialized = 0;


/* ***************************************************************************
 * Public Function Definitions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Call code in the thread of the async event window by sending a message.
 * ........................................................................
 * ----------------------------------------------------------------------*/

LRESULT
sendMessageToAsyncEventWindow( UINT msg,
                               WPARAM wParam,
                               LPARAM lParam,
                               EVENT_PROCESSOR_FUNC eventProc )
{
    LRESULT returnValue;

    if ( _asyncEventWindowHandle == NULL )
    {
        errorMsg( "_asyncEventWindowHandle is NULL." );
        return 0;
    }

    int wasSuccessful = registerAsyncEventProc(
        msg,
        eventProc
        );

    if ( !wasSuccessful )
    {
        errorMsg( "registerAsyncEventProc() failed.\n" );
        return 0;
    }

    /* Release our lock on the GIL, because we have no idea how long
     * SendMessage will take. */

    Py_BEGIN_ALLOW_THREADS;
    returnValue = SendMessage(
        _asyncEventWindowHandle,
        msg,
        wParam,
        lParam );
    Py_END_ALLOW_THREADS;

    unregisterAsyncEventProc( msg );

    return returnValue;
}


/* ------------------------------------------------------------------------
 * Given a message, finds and calls the appropriate registered function.
 * ........................................................................
 * 
 * This function uses the msg type of the event as a key into the map
 * to decide which of the registered functions to call.
 *
 * ----------------------------------------------------------------------*/

LRESULT
dispatchAsyncEvent( HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return (LRESULT) 0;
    }

    EnterCriticalSection( &_functionMapLock );

    FunctionMap::iterator iter = _functionMap.find( msg );
    if ( iter != _functionMap.end() )
    {
        EVENT_PROCESSOR_FUNC callback = iter->second;

        LeaveCriticalSection( &_functionMapLock );
        return callback( hwnd, msg, wParam, lParam );        
    }

    LeaveCriticalSection( &_functionMapLock );
    return DefWindowProc( hwnd, msg, wParam, lParam );
}

/* ------------------------------------------------------------------------
 * Adds the given function to the map, with the msg type as its key.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
registerAsyncEventProc( int msg, EVENT_PROCESSOR_FUNC callback )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return 0;
    }

    int success = 0;

    EnterCriticalSection( &_functionMapLock );

    FunctionMap::iterator iter = _functionMap.find( msg );
    if ( iter != _functionMap.end() )
    {
        errorMsg( "registerAsyncEventProc(): msg already registered." );
    } else {
        _functionMap[msg] = callback;
        success = 1;
    }

    LeaveCriticalSection( &_functionMapLock );

    return success;
}

/* ------------------------------------------------------------------------
 * Removes the function for the msg type from the map.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
unregisterAsyncEventProc( int msg )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return 0;
    }

    int success = 0;

    EnterCriticalSection( &_functionMapLock );

    FunctionMap::iterator iter = _functionMap.find( msg );
    if ( iter == _functionMap.end() )
    {
        errorMsg( "registerAsyncEventProc(): msg not registered." );
    } else {
        _functionMap.erase( msg );
        success = 1;
    }

    LeaveCriticalSection( &_functionMapLock );

    return success;
}

/* ------------------------------------------------------------------------
 * Gets the module-level reference to the async event window instance
 * ........................................................................
 * ----------------------------------------------------------------------*/

HWND
getAsyncEventWindow( void )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return NULL;
    }

    return _asyncEventWindowHandle;
}

/* ------------------------------------------------------------------------
 * Sets the module-level reference to the async event window instance
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
setAsyncEventWindow( HWND hwnd )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return;
    }

    _asyncEventWindowHandle = hwnd;
}

/* ------------------------------------------------------------------------
 * Returns whether or not the module is initialized.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
isAsyncEventProcessorRegistryInitialized( void )
{
    return _isInitialized;
}

/* ------------------------------------------------------------------------
 * Initializes the Async Event Processor Registry.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
initAsyncEventProcessorRegistry( void )
{
    if ( _isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry already inited." );
        return 0;
    }

    /* Initialize critical section */
    InitializeCriticalSection( &_functionMapLock );

    _functionMap.clear();
    _asyncEventWindowHandle = NULL;

    _isInitialized = 1;

    return 1;
}

/* ------------------------------------------------------------------------
 * Shuts down the Async Event Processor Registry.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
shutdownAsyncEventProcessorRegistry( void )
{
    if ( !_isInitialized )
    {
        errorMsg( "AsyncEventProcessorRegistry not inited." );
        return 0;
    }

    DeleteCriticalSection( &_functionMapLock );

    _functionMap.clear();
    _asyncEventWindowHandle = NULL;

    _isInitialized = 0;

    return 1;
}
