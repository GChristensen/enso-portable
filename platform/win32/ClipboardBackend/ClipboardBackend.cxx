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

    /*   Implementation for Enso's clipboard backend. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "ClipboardBackend.h"
#include "GlobalConstants.h"

#include "Python.h"


/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Amount of time to wait between attempts to open the clipboard, in
 * ms. */
#define CLIPBOARD_OPEN_WAIT_INTERVAL   10

/* Total amount of time we can wait for the clipboard to become
 * available for opening, in ms. */
#define CLIPBOARD_OPEN_WAIT_AMOUNT     1000


/* ***************************************************************************
 * Static Module Variables
 * **************************************************************************/

/* Critical section lock for the clipboard.  This should only be
 * locked and unlocked when the clipboard is open, to prevent
 * deadlocks from occurring. */
static CRITICAL_SECTION _clipboardLock;

/* Mutex to ensure only one thread can be in the Pasting Ritual at a time */
static HANDLE _pastingRitualExclusionLock;

/* Keep track of when clipboard is open, to help avoid sequence errors */
static volatile bool _clipboardIsOpen = false;

/* Set to true when pasting succeeds, reset when a new operation begins */
static volatile bool _pasteSuccess = false;

/* The object which will provide us with the text to be pasted. */
static ClipboardFormatRenderer * _rendererObject = NULL;

/* The next clipboard viewer in the clipboard viewer chain. */
static HWND _nextClipboardViewer = NULL;

/* Window handle to the clipboard viewer we've registered. */
static HWND _ourClipboardViewer = NULL;

/* Event that indicates whether the clipboard contents have been changed. */
static HANDLE _clipboardChangedEvent;

/* Event that indicates whether the clipboard contents have been pasted. */
static HANDLE _clipboardPastedEvent;

/* Clipboard format code for ThornSoft's CF_CLIPBOARD_VIEWER_IGNORE
 * format.  For more information, see
 * http://www.thornsoft.com/developer_ignore.htm. */
static UINT CF_CLIPBOARD_VIEWER_IGNORE = 0;


/* ***************************************************************************
 * Private Function Declarations
 * **************************************************************************/

/* The private functions declared in the following header file need to
 * have public visibility for use by testing suites and other private
 * submodules. */
#include "ClipboardBackendPrivateFunctions.h"

static void
_installClipboardViewer( void );

static void
_uninstallClipboardViewer( void );

static int
_openClipboard( void );

static int
_closeClipboard( void );

static LRESULT
_renderSingleFormat( int formatCode );

static LRESULT
_clipboardBackendWindProc( HWND hwnd,
                           UINT msg,
                           WPARAM wParam,
                           LPARAM lParam );


/* ***************************************************************************
 * Private Function Implementations
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Installs the ClipboardBackend's clipboard viewer.
 * ........................................................................
 *
 * Logs an error if anything goes amiss.
 *
 * ----------------------------------------------------------------------*/

static void
_installClipboardViewer( void )
{
    HWND asyncEventWindow;

    /* Now register ourselves as a clipboard viewer. */
    asyncEventWindow = getAsyncEventWindow();

    if ( asyncEventWindow == NULL )
    {
        errorMsg( "getAsyncEventWindow() returned NULL." );
    } else {
        /* For some reason, SetClipboardViewer() does not clear the error
         * message for SetLastError(). */
        SetLastError( ERROR_SUCCESS );

        HWND oldClipboardViewer = SetClipboardViewer( asyncEventWindow );

        if ( oldClipboardViewer == NULL )
        {
            DWORD errorCode = GetLastError();

            /* The return value of SetClipboardViewer() is overloaded,
             * so we have to figure out if it was successful and there
             * was no previous clipboard viewer, or if the function
             * call actually failed.  See the MSDN documentation for
             * more information. */
            if ( errorCode != ERROR_SUCCESS )
            {
                errorMsgInt( "SetClipboardViewer() failed with code: ",
                             errorCode );
                return;
            }
        } else if ( oldClipboardViewer == asyncEventWindow ) {
            /* This *should* never happen, because our code never
             * attempts to install the clipboard viewer twice, but
             * apparently it ends up happening in some rare,
             * unproduceable circumstances--see #496.  We can't set
             * our next clipboard viewer to the old one at this point
             * or we will end up going in infinite recursion whenever
             * a WM_DRAWCLIPBOARD message is received, so we're just
             * going to set the next clipboard viewer to NULL. */
            warnMsg( "Clipboard viewer is already installed." );
            oldClipboardViewer = NULL;
        }

        _nextClipboardViewer = oldClipboardViewer;
        _ourClipboardViewer = asyncEventWindow;
    }
}


/* ------------------------------------------------------------------------
 * Uninstalls the ClipboardBackend's clipboard viewer.
 * ........................................................................
 *
 * If the ClipboardBackend's clipboard viewer wasn't already installed,
 * this function does nothing.
 *
 * This function must be called from the thread that owns the
 * clipboard viewer window, or it will do nothing.
 *
 * ----------------------------------------------------------------------*/

static void
_uninstallClipboardViewer( void )
{
    if ( _ourClipboardViewer )
    {
        /* ChangeClipboardChain() must be called from the thread that
         * owns the clipboard viewer window being removed or it won't
         * do anything.  Annoyingly, I had to discover this through
         * trial and error: the MSDN documentation doesn't even
         * mention the possibility of this function failing, and
         * GetLastError() doesn't yield anything useful either.
         * - Atul */
        ChangeClipboardChain( _ourClipboardViewer,
                              _nextClipboardViewer );
        _ourClipboardViewer = NULL;
        _nextClipboardViewer = NULL;
    }
}


/* ------------------------------------------------------------------------
 * Immediately puts arbitrary data into the clipboard in given format.
 * ........................................................................
 *
 * This function is the final step in our delayed-rendering strategy,
 * which finally puts the promised data into the clipboard.  Since the
 * data is provided as a void pointer and a number of bytes, absolutely
 * any type of data can be used.
 *
 * Precondition: Clipboard is already open by another application.
 * Postcondition: data is in the clipboard for format given by
 * formatCode, clipboard is still open.
 *
 * Note that this function is not static because it needs to be
 * publicly visible for use by this module's testing suite and/or private
 * submodules.
 *
 * ----------------------------------------------------------------------*/

bool
_insertDataIntoClipboard( void *sourceData,
                          long numBytes,
                          int formatCode )
{
    /* The plan goes like this: We allocate a global memory handle,
     * lock it, copy numBytes into it from sourceData, unlock it, and
     * use it to set the clipboard data for the given format code.
     * The rest of this function is error handling, because there are
     * many many things that can go wrong. */
    HGLOBAL hGlobal;
    void *dataPointer;
    int locks;
    DWORD errorCode;
    bool hGlobalAllocated = false;
    bool success = false;

    debugMsgInt( "_insertDataIntoClipboard format code ", formatCode );

    /* Sanity check on arguments */
    if ( sourceData == NULL )
        errorMsg( "ASSERTION FAILED: sourceData is a null pointer." );
    if ( numBytes <= 0 )
        errorMsg( "ASSERTION FAILED: Invalid number of bytes" );

    /* Before we can set the clipboard data, we need to put the text
     * into globally allocated memory.  It's a quirk of Windows.  You
     * may see some code using the GMEM_DDESHARE flag here, but this
     * is officially obsolete and ignored by win32.  See
     * http://msdn.microsoft.com/library/default.asp?
     * url=/library/en-us/memory/base/globalalloc.asp for
     * details. */
    hGlobal = GlobalAlloc( GMEM_MOVEABLE,
                           numBytes );
    if ( hGlobal == NULL ) {
        errorMsg( "Trying to set clipboard data, GlobalAlloc() failed." );
        goto cleanUpAndExit;
    }
    hGlobalAllocated = true;
 
    /* Lock the global handle to get a pointer, and copy the source
     * data into it. */
    dataPointer = (void *) GlobalLock( hGlobal );
    if ( dataPointer == NULL )
    {
        errorMsg( "Trying to set clipboard data, locking failed." );
        goto cleanUpAndExit;
    }
    CopyMemory( dataPointer, sourceData, numBytes );

    /* The call after this one may or may not modify the last-error
     * variable; to ensure that we don't have a stale last-error
     * variable, reset it here. */
    SetLastError( NO_ERROR );

    /* Unlock the handle and handle handle errors */
    locks = GlobalUnlock( hGlobal );
    if ( locks )
    {
        errorMsg( "Couldn't release handle after copying memory." );
        goto cleanUpAndExit;
    }
    errorCode = GetLastError();
    if ( errorCode != NO_ERROR )
    {
        errorMsgInt( "GlobalUnlock failed, with error ", errorCode );
        goto cleanUpAndExit;
    }

    /* Finally, use the global handle to set clipboard data,
     * and handle errors */
    HANDLE returnValue = SetClipboardData( formatCode, hGlobal );
    if ( returnValue == NULL )
    {
        errorCode = GetLastError();
        errorMsgInt( "SetClipboardData failed, with error ",
                     errorCode );
        goto cleanUpAndExit;
    }
    success = true;

cleanUpAndExit:
    if ( hGlobalAllocated && ! success )
    {
        /* If we have allocated the global handle, but failed to put
         * it into the clipboard, then it is our responsibility to
         * free it. If we successfully put it into the clipboard, the
         * clipboard now has ownership of the handle and will deal
         * with freeing the memory later.*/
        GlobalFree( hGlobal );
    }

    return success;
}


/* ------------------------------------------------------------------------
 * Replacement for OpenClipboard with built-in error checking
 * ........................................................................
 *
 * This and _closeClipboard maintain a module-level state variable
 * _clipboardIsOpen which makes it easier to track down sequence errors:
 * if these functions are used consistently, we can check the variable
 * to see whether the clipboard is open or not.  Fails an assertion
 * if the clipboard is already open.
 *
 * ----------------------------------------------------------------------*/

static int
_openClipboard( void )
{
    HWND windowHandle = getAsyncEventWindow();

    /* Make some assertions. */
    if ( windowHandle == NULL )
        errorMsg( "ASSERTION FAILED: Attempted to use _openClipboard before "
                  "asyncEventWindow initialized." );
    if ( _clipboardIsOpen )
        errorMsg( "ASSERTION FAILED: Attempted to open already-open "
                  "clipboard." );

    /* Now we'll try repeatedly to open the clipboard.  The reason we
     * make multiple attempts is because it's entirely possible for
     * another process to have the clipboard open, and Windows offers
     * no synchronization mechanism for clipboard access. */
    int msPassed = 0;
    int success = 0;

    /* Yes, the following conditional does include an assignment--it's
     * not a coding error. */
    while ( !(success = OpenClipboard( windowHandle )) &&
            (msPassed <= CLIPBOARD_OPEN_WAIT_AMOUNT) )
    {
        Py_BEGIN_ALLOW_THREADS;
        Sleep( CLIPBOARD_OPEN_WAIT_INTERVAL );
        Py_END_ALLOW_THREADS;

        msPassed += CLIPBOARD_OPEN_WAIT_INTERVAL;
    }

    if ( success )
    {
        _clipboardIsOpen = true;
    } else {
        int errorCode = GetLastError();
        errorMsgInt( "OpenClipboard failed with error ", errorCode );
        if ( errorCode = ERROR_INVALID_WINDOW_HANDLE )
        {
            errorMsg( "OpenClipboard failed with "
                      "ERROR_INVALID_WINDOW_HANDLE (another application "
                      "may be holding on to the clipboard for too long)." );
        }
    }
    return success;
}


/* ------------------------------------------------------------------------
 * Replacement for CloseClipboard with built-in error checking.
 * ........................................................................
 * ------------------------------------------------------------------------*/

static int
_closeClipboard( void )
{
    if ( !_clipboardIsOpen )
        errorMsg( "ASSERTION FAILED: Attempted to close not-open "
                  "clipboard." );

    int success = CloseClipboard();
    if ( success )
    {
        _clipboardIsOpen = false;
    } else {
        int errorCode = GetLastError();
        errorMsgInt( "CloseClipboard failed with error ", errorCode );
    }
    return success;
}


/* ------------------------------------------------------------------------
 * Render a single clipboard format.
 * ........................................................................
 *
 * Called in response to a WM_RENDERFORMAT message.  This means that
 * an application has requested data from the clipboard to paste it,
 * and has told us which format it wants.  We respond by getting the
 * data from the _rendererObject and passing it into
 * _insertDataIntoClipboard.
 *
 * ----------------------------------------------------------------------*/

static LRESULT
_renderSingleFormat( int formatCode )
{
    char *pendingData;
    int dataSize;
    int renderSuccess;

    EnterCriticalSection( &_clipboardLock );

    if ( _rendererObject == NULL )
        errorMsg( "ASSERTION FAILED: RendererObject is null in "
                  "_clipboardBackendWindProc." );

    renderSuccess = _rendererObject->renderFormat( formatCode,
                                                   &pendingData,
                                                   &dataSize );
    if ( renderSuccess == CFR_SUCCESS )
    {
        debugMsg( "In ClipBackWindProc: renderFormat returned true." );
        _pasteSuccess = _insertDataIntoClipboard( pendingData,
                                                  dataSize,
                                                  formatCode );
        if ( _pasteSuccess )
        {
            debugMsg( "_insertDataIntoClipboard() returned true." );
            if ( SetEvent(_clipboardPastedEvent) == 0 )
                errorMsg( "SetEvent() failed." );
        } else {
            errorMsgInt( "Failed to put format into clipboard! ",
                         formatCode );
        }
        free( pendingData );
    } else {
        /* Otherwise, we have no data waiting to be pasted, so there
         * is nothing to do. */
        warnMsg( "Got a WM_RENDERFORMAT when there is no pending "
                 "string." );
    }

    LeaveCriticalSection( &_clipboardLock );

    return (LRESULT)0;
}


/* ------------------------------------------------------------------------
 * Callback function to process delayed clipboard rendering events.
 * ........................................................................
 *
 * This function is registered with the AsyncEventProcessorRegistry,
 * so it will be called when our program gets one of the clipboard-
 * related messages such as WM_RENDERFORMAT, etc.  Dispatches to the
 * appropriate function.
 *
 * ----------------------------------------------------------------------*/

static LRESULT
_clipboardBackendWindProc( HWND hwnd,
                           UINT msg,
                           WPARAM wParam,
                           LPARAM lParam )
{

    switch ( msg )
    {
    case WM_DESTROYCLIPBOARD:
        /* Windows will pass us this message when Enso is shutting
         * down.  Currently Enso doesn't need to do anything special
         * in response to this situation. */
        debugMsg( "WM_DESTROYCLIPBOARD received." );
        return (LRESULT)0;

    case WM_RENDERFORMAT:
        /* Another application has requested a single delayed-rendering format
         * from the clipboard.  The wParam tells us which format has been
         * requested. */
        debugMsgInt( "WM_RENDERFORMAT received with wParam ", wParam );
        return _renderSingleFormat( (int)wParam );

    case WM_RENDERALLFORMATS:
        /* Typically Windows sends this message to a program that is
         * shutting down, in order to tell the program to immediately
         * render any delayed-clipboard-rendering data it may be
         * hanging on to.  In the very rare case that this is called
         * when Enso exits, we want to empty the clipboard so that
         * there are no longer any delayed clipboard rendering hooks
         * contained in it. */
        debugMsg( "WM_RENDERALLFORMATS received." );
        OpenClipboard( hwnd );
        EmptyClipboard();
        CloseClipboard();
        return (LRESULT)0;

    case WM_DRAWCLIPBOARD:
        /* The clipboard has just been altered; as a registered
         * clipboard viewer, we're being notified of this change so we
         * can draw its new content. However, what we'll do instead is
         * set _clipboardChangedEvent; by checking the status of this
         * event, another thread can determine whether a copy command
         * passed to another application has made anything change yet
         * or not.*/
        debugMsg( "WM_DRAWCLIPBOARD received." );

        if ( !IsClipboardFormatAvailable(CF_CLIPBOARD_VIEWER_IGNORE) )
        {
            /* We're not supposed to ignore this change of the
             * clipboard contents, so we'll set our clipboard-changed
             * event. */
            if ( SetEvent( _clipboardChangedEvent ) == 0 )
                errorMsg( "SetEvent() failed." );
        } else {
            debugMsg( "Clipboard contains CF_CLIPBOARD_VIEWER_IGNORE." );
        }

        if ( _nextClipboardViewer != NULL )
            SendMessage( _nextClipboardViewer, msg, wParam, lParam );

        return (LRESULT)0;

    case WM_CHANGECBCHAIN:
        /* The clipboard viewer chain has been altered. */
        debugMsg( "WM_CHANGECBCHAIN received." );

        if ( (HWND) wParam == _nextClipboardViewer )
        {
            /* Looks like our next clipboard viewer just dropped
             * itself out of the chain; we'll have to pass all
             * WM_DRAWCLIPBOARD messages on to a new clipboard viewer
             * now. */
            _nextClipboardViewer = (HWND) lParam;
        } else {
            /* Some clipboard viewer further down the chain dropped
             * out, so pass this message on to our next clipboard
             * viewer. */

            SendMessage( _nextClipboardViewer, msg, wParam, lParam );
        }

        return (LRESULT)0;

    case WM_USER_CLIPBOARD_INSTALL:
        _installClipboardViewer();
        return (LRESULT)0;

    case WM_USER_CLIPBOARD_UNINSTALL:
        _uninstallClipboardViewer();
        return (LRESULT)0;
    }

    errorMsg( "Received an invalid message." );
    return (LRESULT)0;
}


/* ***************************************************************************
 * Public Function Implementations
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Initializer
 * ........................................................................
 *
 * Initialize clipboard backend by registering event processor
 * functions, initializing event objects, registering ourself as a
 * clipboard viewer, and getting pointer to the async event window.
 * This function must be called from before other functions in this
 * module can be used.
 *
 * ----------------------------------------------------------------------*/

void
initializeClipboardBackend()
{
    debugMsg( "In initializeClipboardBackend." );
    
    /* Create our critical sections and mutexen */
    InitializeCriticalSection( &_clipboardLock );
    /* The false argument means that no thread initially owns this
     * mutex: */
    _pastingRitualExclusionLock = CreateMutex( NULL, false, NULL );
    if ( _pastingRitualExclusionLock == NULL )
    {
        int errorCode = GetLastError();
        errorMsgInt( "Pasting ritual mutex can't be created ", errorCode );
    }

    CF_CLIPBOARD_VIEWER_IGNORE = RegisterClipboardFormat(
        "Clipboard Viewer Ignore"
        );

    if ( CF_CLIPBOARD_VIEWER_IGNORE == 0 )
    {
        errorMsg( "RegisterClipboardFormat() failed." );
    }

    int wasSuccessful;

    /* Set up asyncEventProcessorRegistry so that the async event thread
     * will call our function clipboardBackendWindProc when getting any
     * of the event types WM_RENDERFORMAT, WM_RENDERALLFORMATS,
     * WM_DESTROYCLIPBOARD, WM_DRAWCLIPBOARD, or WM_CHANGECBCHAIN. */
    wasSuccessful = registerAsyncEventProc( WM_RENDERFORMAT,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_RENDERFORMAT failed." );

    wasSuccessful = registerAsyncEventProc( WM_RENDERALLFORMATS,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_RENDERALLFORMATS failed." );

    wasSuccessful = registerAsyncEventProc( WM_DESTROYCLIPBOARD,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_DESTROYCLIPBOARD failed." );

    wasSuccessful = registerAsyncEventProc( WM_DRAWCLIPBOARD,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_DRAWCLIPBOARD failed." );

    wasSuccessful = registerAsyncEventProc( WM_CHANGECBCHAIN,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_CHANGECBCHAIN failed." );

    wasSuccessful = registerAsyncEventProc( WM_USER_CLIPBOARD_INSTALL,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_USER_CLIPBOARD_INSTALL failed." );

    wasSuccessful = registerAsyncEventProc( WM_USER_CLIPBOARD_UNINSTALL,
                                            &_clipboardBackendWindProc );
    if ( !wasSuccessful )
        errorMsg( "Registering WM_USER_CLIPBOARD_UNINSTALL failed." );

    /* Initialize our event objects. */
    _clipboardChangedEvent = CreateEvent(
        NULL,                          /* lpEventAttributes */
        TRUE,                          /* bManualReset */
        FALSE,                         /* bInitialState */
        NULL                           /* lpName */
        );

    if ( _clipboardChangedEvent == NULL )
        errorMsg( "CreateEvent() failed." );

    _clipboardPastedEvent = CreateEvent(
        NULL,                          /* lpEventAttributes */
        TRUE,                          /* bManualReset */
        FALSE,                         /* bInitialState */
        NULL                           /* lpName */
        );

    if ( _clipboardPastedEvent == NULL )
        errorMsg( "CreateEvent() failed." );
}


/* ------------------------------------------------------------------------
 * Shutdown the module.
 * ........................................................................
 *
 * This should be called when you are done using this module.
 *
 * ----------------------------------------------------------------------*/

void
shutdownClipboardBackend( void )
{
    if ( _rendererObject != NULL )
    {
        errorMsg( "ClipboardBackend shut down without finalizePasting." );
        delete _rendererObject;
        _rendererObject = NULL;
    }

    SendMessage( getAsyncEventWindow(), WM_USER_CLIPBOARD_UNINSTALL, 0, 0 );

    if ( CloseHandle(_clipboardChangedEvent) == 0 )
    {
        errorMsg( "CloseHandle() failed for clipboard-changed event." );
    }
    _clipboardChangedEvent = NULL;

    if ( CloseHandle(_clipboardPastedEvent) == 0 )
    {
        errorMsg( "CloseHandle() failed for clipboard-pasted event." );
    }
    _clipboardPastedEvent = NULL;

    if ( CloseHandle( _pastingRitualExclusionLock ) == 0 )
    {
        errorMsg( "CloseHandle() failed for pasting mutex." );
    }
    _pastingRitualExclusionLock = NULL;
    

    unregisterAsyncEventProc( WM_RENDERFORMAT );
    unregisterAsyncEventProc( WM_RENDERALLFORMATS );
    unregisterAsyncEventProc( WM_DESTROYCLIPBOARD );
    unregisterAsyncEventProc( WM_DRAWCLIPBOARD );
    unregisterAsyncEventProc( WM_CHANGECBCHAIN );
    unregisterAsyncEventProc( WM_USER_CLIPBOARD_INSTALL );
    unregisterAsyncEventProc( WM_USER_CLIPBOARD_UNINSTALL );

    DeleteCriticalSection( &_clipboardLock );
}


/* ------------------------------------------------------------------------
 * Prepares for pasting of text by setting up clipboard hooks.
 * ........................................................................
 *
 * clipFormRend is a pointer to an object supporting the
 * ClipboardFormatRenderer interface, basically a callback object,
 * which will supply us with the data to be pasted.
 * availableClipboardFormats is a list (std::vector) of the clipboard
 * format codes for those formats Enso is promising to support.
 *
 * This function goes through the list and, for each clipboard format,
 * it does a SetClipboardData( NULL ) in order to create the clipboard
 * delayed-rendering hook.
 *
 * Precondition: clipboard is not open.
 * Postcondition: clipboard is not open.
 *
 * ----------------------------------------------------------------------*/

void
prepareForPasting( ClipboardFormatRenderer *clipFormRend,
                   const std::vector<int> &availableClipboardFormats )
{
    int errorCode;
    bool enteredCriticalSection = false;
    DWORD doWaitResult;

    /* Reality check on arguments */
    if ( clipFormRend == NULL )
        errorMsg( "ASSERTION FAILED: Null object passed to "
                  "prepareForPasting!" );

    /* Get the mutex, which we will hold until finalizePasting is called.
     * This ensures that no more than one thread can try to paste things
     * at the same time.  Since there's only one thread that should be
     * attempting to paste, we're not going to wait for the mutex --
     * if we can't get it immediately, it must be a sequence error. */
    doWaitResult = WaitForSingleObject( _pastingRitualExclusionLock,
                                        0 );
    if ( doWaitResult != WAIT_OBJECT_0 )
    {
        errorMsg( "prepareForPasting can't aquire pasting mutex." );
        goto cleanUpAndExit;
    }

    /* Before using the clipboard, we must open it and empty it.
     * When we open it, we pass the handle to the window, so that Windows
     * can identify that it is our thread that has the clipboard open
     * and our thread that should be called back for delayed rendering.
     * Also, we have to make sure that every exit path from this function
     * closes the clipboard! */
    if ( !_openClipboard() )
    {
        errorMsg( "_openClipboard() failed." );
        goto cleanUpAndExit;
    }

    EnterCriticalSection( &_clipboardLock );
    enteredCriticalSection = true;

    /* set up the object we are given as the rendererObject, to be
     * called in order to get the text. */
    _rendererObject = clipFormRend;

    if ( ResetEvent( _clipboardPastedEvent ) == 0 )
    {
        errorMsg( "ResetEvent() failed." );
        goto cleanUpAndExit;
    }

    if ( EmptyClipboard() == 0 )
    {
        errorMsg( "EmptyClipboard() failed." );
        goto cleanUpAndExit;
    }

    for ( unsigned int i = 0; i < availableClipboardFormats.size(); i ++ )
    {
        /* The call after this one may or may not modify the last-error
         * variable; to ensure that we don't have a stale last-error
         * variable, reset it here. */
        SetLastError( NO_ERROR );

        /* Passing NULL to SetClipboardData sets up the
         * delayed-rendering clipboard hook.  Note also that there is
         * no use in looking at the return value from this function,
         * since it will return NULL whether or not an error
         * occurred. */
        SetClipboardData( availableClipboardFormats[i], NULL );

        errorCode = GetLastError();

        /* Handle errors */
        if ( errorCode != NO_ERROR )
        {
            errorMsgInt( "SetClipboardData failed when setting format ",
                         availableClipboardFormats[i] );
            errorMsgInt( "SetClipboardData failed, with error ",
                         errorCode );
        }
    }

cleanUpAndExit:
    if ( enteredCriticalSection )
        LeaveCriticalSection( &_clipboardLock );

    if ( _clipboardIsOpen )
        /* Release lock on clipboard. */
        if ( _closeClipboard() == 0 )
            errorMsg( "_closeClipboard() failed." );
}

/* --------------------------------------------------------------------
 * Waits until clipboard contents have been pasted or a timeout occurs.
 * ....................................................................
 * ------------------------------------------------------------------*/

void
waitForPaste( int msTimeout )
{
    DWORD result = WaitForSingleObject( _clipboardPastedEvent, msTimeout );

    switch ( result )
    {
    case WAIT_ABANDONED:
        errorMsg( "WaitForSingleObject() returned WAIT_ABANDONED." );
        break;
    case WAIT_FAILED:
        errorMsg( "WaitForSingleObject() returned WAIT_FAILED." );
        break;
    }
}

/* --------------------------------------------------------------------
 * Call this function after simulating a paste keystroke.
 * ....................................................................
 *
 * Clears out any clipboard hooks which are leftover from
 * prepareForTextPasting.  Returns the value of _pasteSuccess ( so,
 * true if the paste finished succesfully) and resets the variable.
 *
 * Precondition: Clipboard is not open.
 * Postcondition: Clipboard is closed and empty, _pasteSuccess is
 * false.
 *
 * ------------------------------------------------------------------*/

bool
finalizePasting( void )
{
    bool returnValue;
    bool enteredCriticalSection = false;

    /* Empty the clipboard of any hooks that might be lingering */
    if ( !_openClipboard() )
    {
        errorMsg( "_openClipboard() failed." );
    } else {
        EnterCriticalSection( &_clipboardLock );
        enteredCriticalSection = true;

        if ( EmptyClipboard() == 0 )
        {
            errorMsg( "EmptyClipboard() failed." );
        }
    }

    /* free up the rendererObject we were given */
    if ( _rendererObject != NULL )
    {
        delete _rendererObject;
        _rendererObject = NULL;
    }

    /* Check success and reset the variable */
    returnValue = _pasteSuccess;
    _pasteSuccess = false;

    if ( enteredCriticalSection )
        LeaveCriticalSection( &_clipboardLock );

    if ( _clipboardIsOpen )
        /* Release lock on clipboard. */
        if ( _closeClipboard() == 0 )
            errorMsg( "_closeClipboard() failed." );

    /* We are done with the Pasting Ritual, so we can
     * release the mutex now and allow other threads to start
     * their own Pasting Ritual.*/
    if ( !ReleaseMutex( _pastingRitualExclusionLock ) )
    {
        int errorCode = GetLastError();
        errorMsgInt( "Can't release pastingRitual mutex.", errorCode );
    }

    return returnValue;
}

/* --------------------------------------------------------------------
 * Prepares for the clipboard contents to change.
 * ....................................................................
 * ------------------------------------------------------------------*/

void
prepareForClipboardToChange( void )
{
    /* Here we'll uninstall and then reinstall our clipboard viewer
     * just in case an ill-behaved application corrupted the chain.
     * This is meant as a fix for #261. */
    SendMessage( getAsyncEventWindow(), WM_USER_CLIPBOARD_UNINSTALL, 0, 0 );
    SendMessage( getAsyncEventWindow(), WM_USER_CLIPBOARD_INSTALL, 0, 0 );

    /* Reset the _clipboardChangedEvent; if the clipboard changes,
     * we will be notified through the clipboard viewer interface
     * ( see _clipboardBackendWindProc ) and will set this event. */
    if ( ResetEvent( _clipboardChangedEvent ) == 0 )
        errorMsg( "ResetEvent() failed." );
}

/* --------------------------------------------------------------------
 * Returns whether the clipboard contents have changed.
 * ....................................................................
 * ------------------------------------------------------------------*/

bool
hasClipboardChanged( void )
{
    /* The 0 argument to WaitForSingleObject means we do not wait, but
     * do an immediate check on the event's status. */
    DWORD result = WaitForSingleObject( _clipboardChangedEvent, 0 );

    switch ( result )
    {
    case WAIT_TIMEOUT:
        return false;
    case WAIT_OBJECT_0:
        return true;
    case WAIT_ABANDONED:
        errorMsg( "WaitForSingleObject() returned WAIT_ABANDONED." );
        return false;
    case WAIT_FAILED:
        errorMsg( "WaitForSingleObject() returned WAIT_FAILED." );
        return false;
    default:
        errorMsg( "Unexpected return value from WaitForSingleObject()." );
        return false;
    }
}

/* --------------------------------------------------------------------
 * Waits until clipboard contents have changed or a timeout occurs.
 * ....................................................................
 * ------------------------------------------------------------------*/

bool
waitForClipboardToChange( int msTimeout )
{
    DWORD result = WaitForSingleObject( _clipboardChangedEvent, msTimeout );

    switch ( result )
    {
    case WAIT_ABANDONED:
        errorMsg( "WaitForSingleObject() returned WAIT_ABANDONED." );
        return false;
    case WAIT_FAILED:
        errorMsg( "WaitForSingleObject() returned WAIT_FAILED." );
        return false;
    case WAIT_TIMEOUT:
        return false;
    default:
        return true;
    }
}
