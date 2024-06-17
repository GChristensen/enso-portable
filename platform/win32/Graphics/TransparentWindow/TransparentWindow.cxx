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

/*   Implementation file for the TransparentWindow module.
 *
 *   The TransparentWindow class is implemented under Windows using a
 *   win32 Layered Window.
 */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include "TransparentWindow.h"

#include "cairo-win32.h"

#include "Logging/Logging.h"
#include "Input/AsyncEventProcessorRegistry.h"
#include "GlobalConstants.h"


#include <stdio.h>

/* ***************************************************************************
 * Module Variables
 * **************************************************************************/

ATOM TransparentWindow::_windowClass = 0;


/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Window class name for the transparent window. */
#define WINDOW_CLASS_NAME "EnsoTransparentWindow"

#define CREATE_WINDOW     0
#define DESTROY_WINDOW    1


/* ***************************************************************************
 * Public Class Methods
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Create an error with the given reason.
 * ........................................................................
 * ----------------------------------------------------------------------*/

TransparentWindowError::TransparentWindowError( const char *what )
{
    _what = (char *) what;
}

/* ------------------------------------------------------------------------
 * Returns the reason for the error.
 * ........................................................................
 * ----------------------------------------------------------------------*/

const char *
TransparentWindowError::what( void )
{
    return _what;
}

/* ------------------------------------------------------------------------
 * This constructor creates and initializes a TransparentWindow.
 * ........................................................................
 * ----------------------------------------------------------------------*/

TransparentWindow::TransparentWindow( int x,
                                      int y,
                                      int maxWidth,
                                      int maxHeight ) :
    _hDC( 0 ),
    _hBitmap( 0 ),
    _window( 0 ),
    _overallOpacity( MAX_OPACITY ),
    _x( x ),
    _y( y ),
    _maxWidth( maxWidth ),
    _maxHeight( maxHeight ),
    _currWidth( maxWidth ),
    _currHeight( maxHeight ),
    _cairoSurface( 0 )
{
    int screenWidth;
    int screenHeight;

    _getDesktopSize( &screenWidth, &screenHeight );

    if ( screenWidth < _maxWidth ||
         screenHeight < _maxHeight ||
         _maxWidth < 1 ||
         _maxHeight < 1 )
    {
        throw RangeError( "Size out of range." );
    }

    if ( !sendMessageToAsyncEventWindow( WM_USER_TRANSPARENT_WINDOW,
                                         (WPARAM) this, CREATE_WINDOW,
                                         TransparentWindow::_eventProc ) )
        throw FatalError( "Couldn't create transparent window." );
}


/* ------------------------------------------------------------------------
 * This destructor closes the TransparentWindow.
 * ........................................................................
 * ----------------------------------------------------------------------*/

TransparentWindow::~TransparentWindow( void )
{
    if ( _cairoSurface )
    {
        /* Make any cairo surfaces pointing at our TransparentWindow's
         * surface invalid. */
        cairo_surface_finish( _cairoSurface );

        /* Reduce the reference count of our private cairo surface by
         * 1.  Note that this doesn't necessarily deallocate the
         * memory used by it; that will be done when all references to
         * the cairo surface have been destroyed (including references
         * given to client code).*/
        cairo_surface_destroy( _cairoSurface );
        _cairoSurface = 0;
    }

    if ( !sendMessageToAsyncEventWindow( WM_USER_TRANSPARENT_WINDOW,
                                         (WPARAM) this, DESTROY_WINDOW,
                                         TransparentWindow::_eventProc ) )
        errorMsg( "Failed to destroy transparent window." );
}


/* ------------------------------------------------------------------------
 * Returns a Cairo surface representing the window's surface.
 * ........................................................................
 * ----------------------------------------------------------------------*/

cairo_surface_t *
TransparentWindow::makeCairoSurface( void )
{
    if ( !_cairoSurface )
    {
        /* Our private cairo surface doesn't exist yet; create it,
         * which also sets its reference count to 1. */

        /* Creating surface with cairo 1.16+ */

        _cairoSurface = cairo_win32_surface_create_with_format(_hDC, CAIRO_FORMAT_ARGB32);

        if ( cairo_surface_status(_cairoSurface) != CAIRO_STATUS_SUCCESS )
            throw FatalError( "Couldn't init Cairo surface." );
    }

    /* The cairo surface we give to the caller will be an additional
     * reference which the caller is responsible for destroying;
     * therefore, we need to increment the reference count of the
     * cairo surface by 1. */
    cairo_surface_reference( _cairoSurface );
    return _cairoSurface;
}


/* ------------------------------------------------------------------------
 * Draw the contents of the transparent window to the screen.
 * ........................................................................
 *
 * For more details on what's going on inside this function, see the
 * MSDN documentation on the UpdateLayeredWindow() function, and
 * follow its links to general documentation on Layered Windows.
 *
 * ----------------------------------------------------------------------*/

void
TransparentWindow::update( void )
{
    if (_cairoSurface)
        cairo_surface_flush(_cairoSurface);

    POINT srcPoint;
    BLENDFUNCTION bf;
    POINT destPoint;
    SIZE rectSize;
    BOOL result;
    HDC screenDc;

    srcPoint.x = 0;
    srcPoint.y = 0;
    
    destPoint.x = _x;
    destPoint.y = _y;

    rectSize.cx = _currWidth;
    rectSize.cy = _currHeight;

    /* Set up a BLENDFUNCTION structure to specify per-pixel alpha
     * transparency. */
    bf.BlendOp = AC_SRC_OVER;
    bf.BlendFlags = 0;
    bf.SourceConstantAlpha = _overallOpacity;
    bf.AlphaFormat = AC_SRC_ALPHA;

    screenDc = GetDC( NULL );

    /* Copy our device context's bitmap to the transparent window. */
    result = UpdateLayeredWindow(
        _window,            /* hwnd */
        screenDc,           /* hdcDst */
        &destPoint,         /* pptDst */
        &rectSize,          /* psize */
        _hDC,               /* hdcSrc */
        &srcPoint,          /* pptSrc */
        0,                  /* crKey */
        &bf,                /* pblend */
        ULW_ALPHA           /* dwFlags */
        );

    if ( !result )
    {
        DWORD lastError = GetLastError();

        /* This is a fix for #249. If the user has full-screened a
         * command prompt window, then UpdateLayeredWindow() will fail
         * with the reason ERROR_NOT_ENOUGH_MEMORY.  We need to deal
         * with this gracefully. */
        if ( lastError != ERROR_NOT_ENOUGH_MEMORY )
        {
            /* Try to clean up, ignore errors that occur b/c we're
             * already in an error state. */
            ReleaseDC( NULL, screenDc );

            infoMsgInt( "UpdateLayeredWindow() error code: ", lastError );
            throw FatalError( "Couldn't update transparent window." );
        }
    }

    if ( ReleaseDC(NULL, screenDc) != 1 )
        throw FatalError( "Couldn't release screen DC." );
}


/* ------------------------------------------------------------------------
 * Sets the overall opacity of the window.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
TransparentWindow::setOpacity( int opacity )
{
    if ( opacity > MAX_OPACITY || opacity < 0 )
        throw RangeError( "Opacity out of range." );
    
    _overallOpacity = opacity;
}


/* ------------------------------------------------------------------------
 * Returns the overall opacity of the window.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getOpacity( void )
{
    return _overallOpacity;
}


/* ------------------------------------------------------------------------
 * Sets the position of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
TransparentWindow::setPosition( int x,
                                int y )
{
    _x = x;
    _y = y;
}


/* ------------------------------------------------------------------------
 * Returns the X position of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getX( void )
{
    return _x;
}


/* ------------------------------------------------------------------------
 * Returns the Y position of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getY( void )
{
    return _y;
}


/* ------------------------------------------------------------------------
 * Sets the size of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
TransparentWindow::setSize( int width,
                            int height )
{
    if ( _maxWidth < width ||
         _maxHeight < height ||
         width < 1 ||
         height < 1 )
    {
        throw RangeError( "Size out of range." );
    }

    _currWidth = width;
    _currHeight = height;
}


/* ------------------------------------------------------------------------
 * Gets the current width of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getWidth( void )
{
    return _currWidth;
}


/* ------------------------------------------------------------------------
 * Gets the current height of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getHeight( void )
{
    return _currHeight;
}


/* ------------------------------------------------------------------------
 * Gets the maximum width of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getMaxWidth( void )
{
    return _maxWidth;
}


/* ------------------------------------------------------------------------
 * Gets the maximum height of the window, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
TransparentWindow::getMaxHeight( void )
{
    return _maxHeight;
}


/* ***************************************************************************
 * Private Class Methods
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Creates the TransparentWindow.
 * ........................................................................
 *
 * Returns true on success, false on failure.
 *
 * ----------------------------------------------------------------------*/

bool
TransparentWindow::_createWindow( void )
{
    bool success = false;

    /* Make the window class if needed */
    if ( !_windowClass )
    {
        WNDCLASSEX info;

        memset( &info, 0, sizeof(info) );

        info.cbSize = sizeof( info );
        info.hInstance = GetModuleHandle( NULL );
        info.lpszClassName = WINDOW_CLASS_NAME;

        info.style = 0;
        info.lpfnWndProc = DefWindowProc;
        info.hbrBackground = (HBRUSH) GetStockObject( HOLLOW_BRUSH );

        _windowClass = RegisterClassEx( &info );
    }

    if ( _windowClass )
    {
        /* Create a transparent window. */
        int windowExStyle;
        int windowStyle;

        windowExStyle = WS_EX_LAYERED |
            WS_EX_TOOLWINDOW |
            WS_EX_TOPMOST |
            WS_EX_TRANSPARENT;

        windowStyle = WS_VISIBLE |
            WS_POPUP;

        HWND oldForegroundWindow = GetForegroundWindow();

        _window = CreateWindowEx( 
            windowExStyle,                  /* dwExStyle    */
            WINDOW_CLASS_NAME,              /* lpClassName  */
            NULL,                           /* lpWindowName */
            windowStyle,                    /* dwStyle      */
            0,                              /* x            */
            0,                              /* y            */
            _maxWidth,                      /* nWidth       */
            _maxHeight,                     /* nHeight      */
            NULL,                           /* hWndParent   */
            NULL,                           /* hMenu        */
            GetModuleHandle( NULL ),        /* hInstance    */
            this                            /* lpParam      */
            );

        if ( _window )
        {
            /* Set the foreground window to the window that was in the
             * foreground just before we created our new overlay
             * window, to ensure that our new overlay window isn't the
             * foreground window. */
            /* LONGTERM TODO: This may not be necessary anymore, since this
             * mechanism has been carried over from some legacy code;
             * determine whether it is needed or not. */
            SetForegroundWindow( oldForegroundWindow );

            /* Create the device context that will hold the
             * transparent window's bitmap surface. */
            VOID *pvBits;
            BITMAPINFO bmi;
            _hDC = CreateCompatibleDC( NULL );

            if ( _hDC != NULL )
            {
                /* Create a device-independent bitmap surface with
                 * per-pixel alpha transparency. */

                ZeroMemory( &bmi, sizeof(BITMAPINFO) );

                bmi.bmiHeader.biSize = sizeof( BITMAPINFOHEADER );
                bmi.bmiHeader.biWidth = _maxWidth;
                bmi.bmiHeader.biHeight = -_maxHeight;
                bmi.bmiHeader.biPlanes = 1;
                bmi.bmiHeader.biBitCount = BITS_PER_PIXEL;
                bmi.bmiHeader.biCompression = BI_RGB;
                bmi.bmiHeader.biSizeImage = ( _maxWidth * _maxHeight *
                                              BYTES_PER_PIXEL );

                _hBitmap = CreateDIBSection(
                    _hDC,                        /* hdc */
                    &bmi,                        /* pbmi */
                    DIB_RGB_COLORS,              /* iUsage */
                    &pvBits,                     /* ppvBits */
                    NULL,                        /* hSection */
                    0x0                          /* dwOffset */
                    );

                if ( _hBitmap != NULL ) {
                    /*  Select the bitmap into our device context. */
                    if ( SelectObject(_hDC, _hBitmap) != NULL ) {
                        /* Show the transparent window. */
                        ShowWindow( _window, SW_SHOW );
                        UpdateWindow( _window );
                        
                        success = true;
                    }
                }
            }
        }
    }

    if ( !success )
        _closeWindow();

    return success;
}


/* ------------------------------------------------------------------------
 * Closes the TransparentWindow.
 * ........................................................................
 *
 * Because this method is called from functions that can't do anything
 * useful with exceptions (e.g., destructors), any of the (very
 * unlikely) errors it runs into will simply be logged as warnings
 * rather than thrown as exceptions.
 *
 * ----------------------------------------------------------------------*/

void
TransparentWindow::_closeWindow( void )
{
    if ( _window )
    {
        if ( _hDC != NULL ) 
        {
            /* Delete the device context. */
            if ( DeleteDC(_hDC) == 0 )
                warnMsg( "Couldn't delete device context." );
            _hDC = NULL;
            if ( _hBitmap != NULL )
            {
                /* Delete the bitmap surface. */
                if ( DeleteObject(_hBitmap) == 0 )
                    warnMsg( "Couldn't delete bitmap surface." );
                _hBitmap = NULL;
            }
        }
        /* Destroy the transparent window. */
        if ( DestroyWindow( _window ) == 0 )
            warnMsg( "Couldn't destroy window.\n" );
        _window = NULL;
    }
}


/* ------------------------------------------------------------------------
 * Event processing function for the TransparentWindow.
 * ........................................................................
 * ----------------------------------------------------------------------*/

LRESULT
TransparentWindow::_eventProc( HWND theWindow,
                               UINT msg,
                               WPARAM wParam,
                               LPARAM lParam )
{
    if ( msg != WM_USER_TRANSPARENT_WINDOW )
    {
        /* This shouldn't happen, because this function should only be called
         * in response to the event types it was registered for. */
        errorMsg( "Bad event type message passed in." );
        return (LRESULT) 0;
    }

    TransparentWindow *pThis = (TransparentWindow *) wParam;

    switch ( lParam )
    {
    case CREATE_WINDOW:
        LRESULT result;

        result = (LRESULT) pThis->_createWindow();
        return result;
    case DESTROY_WINDOW:
        pThis->_closeWindow();
        return (LRESULT) 1;
    default:
        errorMsg( "Unknown lParam." );
        return (LRESULT) 0;
    }
}


/* ***************************************************************************
 * Public Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Get the dimensions of the desktop, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
_getDesktopSize( int *width,
                 int *height )
{
    HWND hWndDesktop = GetDesktopWindow();
    RECT desktopRect;

    if ( GetWindowRect(hWndDesktop, &desktopRect) == 0 )
        throw FatalError( "Couldn't get desktop window size." );

    *width = desktopRect.right - desktopRect.left;
    *height = desktopRect.bottom - desktopRect.top;
}

/* ------------------------------------------------------------------------
 * Get the dimensions of the desktop, in pixels.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
_getDesktopOffset( int *left,
                 int *top )
{
    RECT rectWorkArea;

    if ( SystemParametersInfo(SPI_GETWORKAREA, 0, &rectWorkArea, 0) == 0 )
        throw FatalError( "Couldn't get desktop window size." );

    *left = rectWorkArea.left;
    *top = rectWorkArea.top;
}

long long TransparentWindow::getHandle() {
    return (long long)_window;
}