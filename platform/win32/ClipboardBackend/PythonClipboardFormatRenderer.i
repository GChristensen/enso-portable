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

/*   Input file for SWIG.  Creates wrappers for the C++ classes
 *   defined in PythonClipboardFormatRenderer.h, and allows you to
 *   extend some of the classes in Python through the use of SWIG
 *   directors.
 *
 *   This SWIG interface file will generate a Python module that will be
 *   used for TESTING PURPOSES ONLY.
 */

%module PythonClipboardFormatRenderer

%{
#include "PythonClipboardFormatRenderer.h"
%}

%include "cstring.i"

#define CFR_SUCCESS        0
#define CFR_ERROR          1

/* See section 8.3.4 of the SWIG documentation for help on what this
 * does. */

%cstring_output_allocate_size( char **outputString,
                               int *outputLength,
                               free(*$1) );

class PythonClipboardFormatRenderer
{
public:
    /* LONGTERM TODO: If the PyObject passed in here contains a
     * reference back to its "parent" PythonClipboardFormatRenderer,
     * then a cyclic reference will exist.  At present this class
     * isn't being built with any support for cyclic garbage
     * collection (we'll have to hack SWIG a bit for that), which
     * means that neither the PyObject passed in nor its parent
     * PythonClipboardFormatRenderer will ever be GC'd.  If there's
     * only one PythonClipboardFormatRenderer in the whole application
     * (i.e., if it's a singleton) then this shoudn't be a big
     * problem, though. */
    PythonClipboardFormatRenderer( PyObject *nRenderFunc );
    virtual ~PythonClipboardFormatRenderer( void );

    virtual int
    renderFormat( int format,
                  char **outputString,
                  int *outputLength );
};
