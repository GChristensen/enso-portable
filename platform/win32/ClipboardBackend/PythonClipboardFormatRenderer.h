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

/*   Header file for the PythonClipboardFormatRenderer class. This
 *   class provides a concrete implementation of the
 *   ClipboardFormatRenderer class which allows the clipboard data to
 *   be rendered in Python.
 */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include <Python.h>
#include "ClipboardFormatRenderer.h"


/* ***************************************************************************
 * Classes
 * **************************************************************************/

/* ===========================================================================
 * PythonClipboardFormatRenderer class
 * ...........................................................................
 *
 * Concrete implementation of ClipboardFormatRenderer that calls out
 * to a Python callable (function) to render the clipboard data in a
 * particular format.
 *
 * =========================================================================*/

class PythonClipboardFormatRenderer : public ClipboardFormatRenderer
{
public:
    /* --------------------------------------------------------------------
     * Constructor.
     * ....................................................................
     *
     * A Python callable object must be passed in of the form
     * renderFunc( formatCode ) where formatCode is an integer
     * corresponding to renderFormat()'s 'format' parameter.  The
     * function must return a Python string object containing the raw
     * data to be inserted into the clipboard.
     *
     * ------------------------------------------------------------------*/

    PythonClipboardFormatRenderer( PyObject *nRenderFunc );

    /* --------------------------------------------------------------------
     * Destructor.
     * ....................................................................
     * ------------------------------------------------------------------*/

    virtual ~PythonClipboardFormatRenderer( void );

    /* --------------------------------------------------------------------
     * Retrieves clipboard data in the given format.
     * ....................................................................
     * 
     * Concrete implementation of the abstract ClipboardFormatRenderer
     * method.
     *
     * ------------------------------------------------------------------*/

    virtual int
    renderFormat( int format,
                  char **outputString,
                  int *outputLength );

private:
    /* Python callable that renders the clipboard data. */
    PyObject *renderFunc;
};
