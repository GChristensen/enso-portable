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

/*   TransparentWindow's SWIG interface file. */

%module TransparentWindow
%{
#include "TransparentWindow.h"
#include "pycairo.h"

static Pycairo_CAPI_t *Pycairo_CAPI = 0;

%}

/* Convert TransparentWindow exceptions to Python exceptions. */
%exception {
    try {
       $action
    } catch (FatalError &e) {
        /* Convert FatalErrors to Python RuntimeError exceptions. */
        PyErr_SetString( PyExc_RuntimeError, e.what() );
        return NULL;
    } catch (RangeError &e) {
        /* Convert RangeErrors to Python ValueError exceptions. */
        PyErr_SetString( PyExc_ValueError, e.what() );
        return NULL;
    }
}

/* Convert these two output parameters to a Python tuple. */
%include "typemaps.i"
%apply int *OUTPUT { int *width, int *height };

/* Use the TransparentWindow's header file to define our Python
 * interface. */
%include "TransparentWindow.h"

/* Define TransparentWindow.makeCairoSurface() for the Python
 * interface. This function will return a pycairo surface. */
%extend TransparentWindow {
    PyObject *makeCairoSurface( void ) {
        cairo_surface_t *surface;
        PyObject *pycairoSurface;

        if ( Pycairo_CAPI == 0 )
            Pycairo_IMPORT;

        surface = self->makeCairoSurface();
        
        pycairoSurface = PycairoSurface_FromSurface(
            surface,
            &PycairoWin32Surface_Type,
            NULL
            );

        if ( pycairoSurface == NULL )
            throw FatalError( "Couldn't init Pycairo surface." );
        else
            return pycairoSurface;
    }
};

