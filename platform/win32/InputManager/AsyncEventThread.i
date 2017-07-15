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

/*   SWIG interface file for the AsyncEventThread singleton. */

%module AsyncEventThread

%exception {
    try {
        $action
    } catch ( MehitabelException ) {
       PyErr_SetString( PyExc_RuntimeError,
                        "A MehitabelException occurred." );
       return NULL;
    }
}

%{
#include "Input/AsyncEventThread.h"
#include "Logging/Logging.h"
#include "InputManagerExceptions.h"

/* The AsyncEventThread singleton. */
static AsyncEventThread *_asyncEventThread = NULL;

/* Starts the async event thread. */
static void
startAsyncEventThread( void )
{
    if ( _asyncEventThread != NULL )
    {
        errorMsg( "Async event thread is already running." );
        throw MehitabelException();
    }

    _asyncEventThread = new AsyncEventThread();

    /* Initialize the async event thread. Note that it will throw an
     * exception if it isn't able to properly initialize itself. */
    _asyncEventThread->start();
}

/* Stops the async event thread. */
static void
stopAsyncEventThread( void )
{
    if ( _asyncEventThread == NULL )
    {
        errorMsg( "Async event thread is not running." );
        throw MehitabelException();
    }

    /* Clean up the async event thread. */
    _asyncEventThread->stop();
    if ( _asyncEventThread->waitForThreadExitCode() != \
         ASYNC_EVENT_THREAD_SUCCESSFUL )
    {
        errorMsg( "Async event thread didn't shutdown properly." );
        throw MehitabelException();
    }

    delete _asyncEventThread;
    _asyncEventThread = NULL;
}

%}

%rename(start) startAsyncEventThread;
void
startAsyncEventThread( void );

%rename(stop) stopAsyncEventThread;
void
stopAsyncEventThread( void );
