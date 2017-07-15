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

/*   Implementation for Enso's custom thread class. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include <stdio.h>

#include "Input/EnsoThread.h"
#include "Logging/Logging.h"
#include "InputManagerExceptions.h"


/* ***************************************************************************
 * Public Methods
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * This constructor initializes the EnsoThread.
 * ........................................................................
 * ----------------------------------------------------------------------*/

EnsoThread::EnsoThread( void )
{
    _threadHandle = CreateThread(
        NULL,                          /* lpThreadAttributes */
        0,                             /* dwStackSize */
        EnsoThread::_threadProc,       /* lpStartAddress */
        this,                          /* lpParameter */
        CREATE_SUSPENDED,              /* dwCreationFlags */
        &_threadId                     /* lpThreadId */
        );

    if ( _threadHandle == NULL )
    {
        errorMsg( "CreateThread() failed." );
        throw MehitabelException();
    }

    _threadInitializedEvent = CreateEvent(
        NULL,                          /* lpEventAttributes */
        TRUE,                          /* bManualReset */
        FALSE,                         /* bInitialState */
        NULL                           /* lpName */
        );

    if ( _threadInitializedEvent == NULL )
    {
        CloseHandle( _threadHandle );

        errorMsg( "CreateEvent() failed." );
        throw MehitabelException();        
    }
}

/* ------------------------------------------------------------------------
 * This destructor shuts down the EnsoThread.
 * ........................................................................
 * ----------------------------------------------------------------------*/

EnsoThread::~EnsoThread( void )
{
    if ( CloseHandle(_threadHandle) == 0 )
        errorMsg( "CloseHandle() failed for thread handle." );

    if ( CloseHandle(_threadInitializedEvent) == 0 )
        errorMsg( "CloseHandle() failed for thread-initialized event." );
}

/* ------------------------------------------------------------------------
 * Starts the thread.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
EnsoThread::start( void )
{
    if ( ResumeThread(_threadHandle) == (DWORD) (-1) )
    {
        errorMsg( "ResumeThread() failed." );
        throw MehitabelException();
    }

    HANDLE handles[2];

    handles[0] = _threadHandle;
    handles[1] = _threadInitializedEvent;

    DWORD waitResult = WaitForMultipleObjects(
        2,                                     /* nCount */
        handles,                               /* lpHandles */
        FALSE,                                 /* bWaitAll */
        THREAD_WAIT_TIMEOUT                    /* dwMilliseconds */
        );

    if ( waitResult != (WAIT_OBJECT_0 + 1) )
    {
        DWORD lastError = GetLastError();

        errorMsg( "Thread did not initialize properly." );
        infoMsgInt( "WaitForMultipleObjects() returned: ", waitResult );
        if ( waitResult == WAIT_FAILED )
            infoMsgInt( "  GetLastError(): ", lastError );
        throw MehitabelException();
    }
}

/* ------------------------------------------------------------------------
 * Waits for the thread to exit and returns its exit code.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
EnsoThread::waitForThreadExitCode( void )
{
    DWORD waitResult = WaitForSingleObject( _threadHandle,
                                            THREAD_WAIT_TIMEOUT );

    if ( waitResult != WAIT_OBJECT_0 )
    {
        errorMsg( "WaitForSingleObject() failed." );
        throw MehitabelException();
    }

    DWORD exitCode;

    if ( GetExitCodeThread(_threadHandle, &exitCode) == 0 )
    {
        errorMsg( "GotExitCodeThread() failed." );
        throw MehitabelException();
    }

    return exitCode;
}

/* ------------------------------------------------------------------------
 * Returns whether the thread is still running or not.
 * ........................................................................
 * ----------------------------------------------------------------------*/

bool
EnsoThread::isAlive( void )
{
    DWORD exitCode;
    BOOL retVal;

    retVal = GetExitCodeThread( _threadHandle, &exitCode );
    if ( retVal == 0 )
    {
        errorMsg( "GotExitCodeThread() failed." );
        throw MehitabelException();
    }

    return ( exitCode == STILL_ACTIVE );
}

/* ------------------------------------------------------------------------
 * Wrapper for starting the thread.
 * ........................................................................
 * ----------------------------------------------------------------------*/

DWORD WINAPI
EnsoThread::_threadProc( LPVOID lpParameter )
{
    EnsoThread *thread = (EnsoThread *) lpParameter;

    return thread->_run();
}

/* ------------------------------------------------------------------------
 * Signal that initializing is complete.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
EnsoThread::_signalInitializingFinished( void )
{
    if ( SetEvent(_threadInitializedEvent) == 0 )
        /* LONGTERM TODO: Is there some way we can bail out here?
         * Otherwise we'll hang... */
        errorMsg( "SetEvent() failed." );
}
