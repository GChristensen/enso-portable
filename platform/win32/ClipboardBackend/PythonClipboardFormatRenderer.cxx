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

    /*   Implementation file for the PythonClipboardFormatRenderer class. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include <Python.h>

#include "Logging/Logging.h"
#include "PythonClipboardFormatRenderer.h"


/* ***************************************************************************
 * Public Method Implementations
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Constructor.
 * ........................................................................
 *
 * Increments the reference count of the Python callable render function.
 *
 * ----------------------------------------------------------------------*/

PythonClipboardFormatRenderer::PythonClipboardFormatRenderer(
    PyObject *nRenderFunc
    ) :
    renderFunc( nRenderFunc )
{
    Py_INCREF( renderFunc );
}

/* ------------------------------------------------------------------------
 * Destructor.
 * ........................................................................
 *
 * Decrements the reference count of the Python callable render function.
 *
 * ----------------------------------------------------------------------*/

PythonClipboardFormatRenderer::~PythonClipboardFormatRenderer( void )
{
    if ( renderFunc != NULL )
    {
        Py_DECREF( renderFunc );
        renderFunc = NULL;
    }
}

/* ------------------------------------------------------------------------
 * Retrieves clipboard data in the given format.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
PythonClipboardFormatRenderer::renderFormat( int format,
                                             char **outputString,
                                             int *outputLength )
{
    int result;
    PyGILState_STATE gstate;
    PyObject *returnValue = NULL;

    *outputString = NULL;
    *outputLength = 0;

    gstate = PyGILState_Ensure();

    if ( !PyCallable_Check(renderFunc) )
    {
        /* The renderFunc isn't callable! */
        errorMsg( "Pycfr: renderFunc isn't callable." );
        goto errorOccurred;
    }

    /* The following line of C is equivalent to saying in Python:
     *   returnValue = renderFunc( formatCode )
     *
     * Note also that the following function returns a new
     * reference. */
    returnValue = PyObject_CallFunction(
        renderFunc,
        "i",
        format
        );

    if ( returnValue == NULL )
    {
        PyObject *exceptionType;

        /* A Python exception occurred. */
        errorMsg( "Pycfr: renderFunc raised an exception." );

        /* Since we're in the context of a win32 Window Procedure, we
         * can't raise an exception out to Python; instead, log the
         * exception and clear the Python error indicator. */
        exceptionType = PyErr_Occurred();
        if ( exceptionType != NULL )
        {
            PyErr_WriteUnraisable( exceptionType );
            PyErr_Clear();
        } else {
            errorMsg( "Pycfr: PyErr_Occurred() returned NULL." );
        }
        goto errorOccurred;
    }

    if ( !PyBytes_Check(returnValue) )
    {
        /* Return value is not a string. */
        errorMsg( "Pycfr: renderFunc didn't return a string." );
        goto errorOccurred;
    }
    
    /* Set the values of our out-parameters */
    *outputLength = PyBytes_Size( returnValue );
    *outputString = (char*) malloc( *outputLength );

    if ( *outputString == NULL )
    {
        /* Not enough memory. */
        errorMsg( "Pycfr: out of memory." );
        goto errorOccurred;
    }

    memcpy(
        *outputString,
        PyBytes_AsString( returnValue ),
        *outputLength
        );

    result = CFR_SUCCESS;

    goto done;

errorOccurred:
    result = CFR_ERROR;
    *outputLength = 0;

done:
    if ( returnValue != NULL )
        Py_DECREF( returnValue );

    PyGILState_Release( gstate );

    return result;
}
