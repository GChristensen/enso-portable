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


/*   Header file for the TransparentWindow module.
 *
 *   The TransparentWindow module offers a single eponymous class that
 *   allows the client to create a semi-transparent desktop window
 *   with per-pixel alpha transparency. The window does not have any
 *   decoration (e.g., widgets or borders), and offers a bitmap
 *   surface that can be drawn on. The window can be moved and resized
 *   (up to a maximum size, defined at creation), and aside from the
 *   per-pixel alpha transparency defined by the pixels on the
 *   surface, it also has an overall opacity that is further applied
 *   to its surface as a whole (useful, for instance, in fading
 *   animations).
 */

#ifndef _TRANSPARENTWINDOW_H_
#define _TRANSPARENTWINDOW_H_

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#ifndef SWIG

#include "WinSdk.h"

#include "cairo.h"

#endif


/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Bits per pixel used by the transparent window's bitmap surface. */
#define BITS_PER_PIXEL 32

/* Bytes per pixel used by the transparent window's bitmap surface. */
#define BYTES_PER_PIXEL ( BITS_PER_PIXEL / 8 )

/* Maximum opacity value for the transparent window. */
#define MAX_OPACITY 0xff


/* ***************************************************************************
 * Class Declarations
 * **************************************************************************/

/* ===========================================================================
 * Exception classes
 * ...........................................................................
 * =========================================================================*/

/* Base exception class for all transparent window errors. */
class TransparentWindowError
{
public:
    /* Create an error with the given reason. */
    TransparentWindowError( const char *what );

    /* Returns the reason for the error. */
    const char *
    what( void );

private:
    /* Pointer to const char string containing a description of the
     * error.  This is a char pointer and not a const char pointer
     * because the C++ compiler raises a warning if a const pointer
     * exists as a class variable, compliaining that it could cause
     * memory leaks. */
    char *_what;
};

/* Exception thrown when a fatal error has occurred, and the process
 * must be shut down. */
class FatalError : public TransparentWindowError
{
public:
    FatalError( char *what ) : TransparentWindowError(what) {}    
};

/* Exception thrown when an out-of-range parameter was passed in. */
class RangeError : public TransparentWindowError {
public:
    RangeError( char *what ) : TransparentWindowError(what) {}    
};


/* ===========================================================================
 * TransparentWindow class
 * ...........................................................................
 *
 * The TransparentWindow class encapsulates a widgetless window with
 * per-pixel alpha transparency.
 *
 * =========================================================================*/

class TransparentWindow
{
public:

    /* ====================================================================
     * Construction and Destruction
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Constructor
     * --------------------------------------------------------------------
     *
     * The constructor takes as parameters the location of the window
     * on the screen and its maximum size, in pixels. The current size
     * is set to the maximum size by default.
     *
     * If maxWidth or maxHeight is larger than the desktop's or either
     * dimension is less than 1, a RangeError exception is thrown.
     *
     * ------------------------------------------------------------------*/

    TransparentWindow( int x,
                       int y,
                       int maxWidth,
                       int maxHeight );

    /* --------------------------------------------------------------------
     * Destructor
     * ------------------------------------------------------------------*/

    ~TransparentWindow( void );

    /* ====================================================================
     * Public Member Functions
     * ==================================================================*/

    /* --------------------------------------------------------------------
     * Draw the contents of the transparent window to the screen.
     * ....................................................................
     *
     * This method should be used after you've drawn everything you
     * need to the window's surface and want to display it on the
     * screen.
     *
     * Note that this function actually immediately draws the contents
     * of the window's surface to the screen; it does not simply
     * "mark" the window to be drawn at a later time, so it should be
     * called as sparingly as possible.
     *
     * ------------------------------------------------------------------*/

    void
    update( void );

#ifndef SWIG
    /* --------------------------------------------------------------------
     * Returns a Cairo surface representing the window's surface.
     * ....................................................................
     *
     * Note that any changes made to this surface won't take effect
     * until TransparentWindow.update() is called. Once finished with
     * the surface, cairo_surface_destroy() should be called.
     *
     * ------------------------------------------------------------------*/

    cairo_surface_t *
    makeCairoSurface( void );
#endif

    /* --------------------------------------------------------------------
     * Sets the overall opacity of the window.
     * ....................................................................
     *
     * The opacity value can range from 0 to MAX_OPACITY, where 0 is
     * fully transparent and MAX_OPACITY is fully opaque.
     *
     * If the opacity value is out of range, a RangeError is thrown.
     *
     * ------------------------------------------------------------------*/

    void
    setOpacity( int opacity );

    /* --------------------------------------------------------------------
     * Returns the overall opacity of the window.
     * ....................................................................
     *
     * The opacity value can range from 0 to MAX_OPACITY, where 0 is
     * fully transparent and MAX_OPACITY is fully opaque.
     *
     * ------------------------------------------------------------------*/

    int
    getOpacity( void );

    /* --------------------------------------------------------------------
     * Sets the position of the window, in pixels.
     * ....................................................................
     *
     * TransparentWindow.update() must subsequently be called for
     * changes to take effect.
     * 
     * ------------------------------------------------------------------*/

    void
    setPosition( int x,
                 int y );

    /* --------------------------------------------------------------------
     * Returns the X position of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getX( void );

    /* --------------------------------------------------------------------
     * Returns the Y position of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getY( void );

    /* --------------------------------------------------------------------
     * Sets the size of the window, in pixels.
     * ....................................................................
     *
     * The given size cannot be larger than the maximum size of the
     * window. This effectively "crops" the window that's displayed
     * on-screen.
     *
     * If width or height is larger than the window's maximum size or
     * either dimension is less than 1, a RangeError exception is
     * thrown.
     *
     * TransparentWindow.update() must subsequently be called for
     * changes to take effect.
     * 
     * ------------------------------------------------------------------*/

    void
    setSize( int width,
             int height );

    /* --------------------------------------------------------------------
     * Gets the current width of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getWidth( void );

    /* --------------------------------------------------------------------
     * Gets the current height of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getHeight( void );

    /* --------------------------------------------------------------------
     * Gets the maximum width of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getMaxWidth( void );

    /* --------------------------------------------------------------------
     * Gets the maximum height of the window, in pixels.
     * ....................................................................
     * ------------------------------------------------------------------*/

    int
    getMaxHeight( void );

    long long getHandle();
    void setForeground();

#ifndef SWIG
private:

    /* ====================================================================
     * Private Member Functions
     * ==================================================================*/

    bool
    _createWindow( void );

    void
    _closeWindow( void );

    static LRESULT
    _eventProc( HWND theWindow,
                UINT msg,
                WPARAM wParam,
                LPARAM lParam );

    /* ====================================================================
     * Private Data Members
     * ==================================================================*/

    /* X position of window on screen, in pixels. */
    int _x;

    /* Y position of window on screen, in pixels. */
    int _y;

    /* Maximum width of window on screen, in pixels. */
    const int _maxWidth;

    /* Maximum height of window on screen, in pixels. */
    const int _maxHeight;

    /* Current width of window on screen, in pixels. */
    int _currWidth;

    /* Current height of window on screen, in pixels. */
    int _currHeight;

    /* Overall opacity of window on screen, from 0 to MAX_OPACITY; 0
     * is fully transparent, MAX_OPACITY is fully opaque. */
    int _overallOpacity;

    /* A Cairo surface pointing to the window's surface. If
     * TransparentWindow.makeCairoSurface() has not yet been called,
     * this value is 0. */
    cairo_surface_t *_cairoSurface;

    /* A win32 handle to the window's surface as a memory device
     * context. */
    HDC _hDC;

    /* A win32 handle to a device-independent bitmap (DIB) that
     * represents the window's surface. */
    HBITMAP _hBitmap;

    /* A win32 handle to the transparent window as a layered
     * window. */
    HWND _window;

    /* A win32 handle to the transparent window's window class. */
    static ATOM _windowClass;
#endif
};


/* ***************************************************************************
 * Public Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Get the dimensions of the desktop, in pixels.
 * ........................................................................
 *
 * The arguments here are out-parameters.
 *
 * Note that this function is put in here for convenience; it really
 * belongs in the Graphics module, but since it's just one function
 * and creating an entire SWIG setup for a module with one function is
 * such a pain in the neck, we're just defining it here.
 *
 * ----------------------------------------------------------------------*/

extern void
_getDesktopSize( int *width,
                 int *height );

extern void
_getDesktopOffset( int *left,
                 int *top );

#endif
