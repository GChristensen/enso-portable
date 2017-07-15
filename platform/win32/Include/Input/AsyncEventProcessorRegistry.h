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

/*   Header file for AsyncEventProcessorRegistry.
 *
 *   This module provides a public interface by which various and sundry
 *   modules can register their message-processing functions so that the
 *   functions will be called in response to events in the Async Event
 *   Thread.
 */

#ifndef ASYNC_EVENT_PROCESSOR_REGISTRY_H
#define ASYNC_EVENT_PROCESSOR_REGISTRY_H

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "WinSdk.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifdef ASYNC_EVENT_USE_DL_EXPORT
#define ASYNC_EVENT_API __declspec( dllexport ) 
#else
#define ASYNC_EVENT_API __declspec( dllimport ) 
#endif

/* ***************************************************************************
 * Typedefs
 * **************************************************************************/

/* Define eventProcessorFunc as a pointer to a function that takes hwnd, msg, 
   wparam, lparam, and returns nothing. */

typedef LRESULT (*EVENT_PROCESSOR_FUNC)( HWND, UINT, WPARAM, LPARAM );

/* ***************************************************************************
 * Public Function Declarations
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Call code in the thread of the async event window by sending a message.
 * ........................................................................
 *
 * Utility function that temporarily registers the given Event
 * Processor Function with a certain message ID, sends a message to
 * the Async Event Window with that message ID and returns the result.
 *
 * Returns NULL if the function fails.  Note that this means that if
 * this function returns NULL, it may be ambiguous as to whether the
 * function itself failed, or if the Async Event Window's window
 * procedure returned NULL.
 * 
 * Precondition: the caller must own the Python Global Interprerer
 * Lock (GIL).
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API LRESULT
sendMessageToAsyncEventWindow( UINT msg,
                               WPARAM wParam,
                               LPARAM lParam,
                               EVENT_PROCESSOR_FUNC eventProc );


/* ------------------------------------------------------------------------
 * Dispatches an event to the appropriate registered function
 * ........................................................................
 *
 * When the async event window has an event to process, it passes the
 * event to this function.  This function decides which registered callback
 * function is appropriate and dispatches the event there.
 * It calls only one function -- the one that was registered last.
 * The registered function will be called with all the system arguments
 * that it would get if it were the sole window proc.
 * If a message comes in for which there is no registered handler function,
 * DefWindowProc (default) is called.  (Specifically, this happens during
 * window creation.)
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API LRESULT
dispatchAsyncEvent( HWND hwnd, 
            UINT msg, 
            WPARAM wParam, 
            LPARAM lParam );


/* ------------------------------------------------------------------------
 * Registers an event-processing function for callback
 * ........................................................................
 * 
 * When client code wants to process events of a certain type 
 * asynchronously, it should pass a pointer to its event-processor
 * function to registerAsyncEventProc.  The registered callback function
 * will be called whenever an event with type msg is received.
 * 
 * Only one event-processor function may be registered per event
 * type.
 *
 * Returns true (nonzero) iff the operation was successful.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API int
registerAsyncEventProc( int msg, 
            EVENT_PROCESSOR_FUNC callback );


/* ------------------------------------------------------------------------
 * Removes the function for the msg type from the map.
 * ........................................................................
 *
 * Returns true (nonzero) iff the operation was successful.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API int
unregisterAsyncEventProc( int msg );


/* ------------------------------------------------------------------------
 * Get the handle to the Async Event Window
 * ........................................................................
 *
 * If client code has an event that it wants to post to the async event
 * thread for asynchronous processing, the client code should call this
 * function to retrieve a handle to the async event window, then pass the
 * handle along with the event to PostMessage().
 * 
 * Returns NULL if an error occurred or no window has yet been
 * registered.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API HWND
getAsyncEventWindow( void );


/* ------------------------------------------------------------------------
 * Sets the handle to the Async Event Window
 * ........................................................................
 *
 * When the AsyncEventThread has created its async message window, it
 * should call this function, to set the module-level window handle in
 * AsyncEventProcessorRegistry, which clients can then access.  There is
 * no reason for this function to be called by anybody else ever.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API void
setAsyncEventWindow( HWND hwnd );


/* ------------------------------------------------------------------------
 * Returns whether or not the module is initialized.
 * ........................................................................
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API int
isAsyncEventProcessorRegistryInitialized( void );


/* ------------------------------------------------------------------------
 * Initializes the Async Event Processor Registry.
 * ........................................................................
 *
 * This must be called before any other functions in this module are
 * used.
 *
 * Return value is true (nonzero) iff the operation was successful.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API int
initAsyncEventProcessorRegistry( void );


/* ------------------------------------------------------------------------
 * Shuts down the Async Event Processor Registry.
 * ........................................................................
 *
 * This must be called after the client is finished using this module.
 *
 * Return value is true (nonzero) iff the operation was successful.
 *
 * ----------------------------------------------------------------------*/

ASYNC_EVENT_API int
shutdownAsyncEventProcessorRegistry( void );


#ifdef __cplusplus
}
#endif

#endif


