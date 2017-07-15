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

    /*   SWIG file for ClipboardBackend module. */

%module ClipboardBackend
%{
#include "ClipboardBackend.h"
#include "PythonClipboardFormatRenderer.h"

static void prepareForPastingWrapper(
    PyObject *renderFunc,
    const std::vector<int> &availableClipboardFormats
    )
{
    /* This wrapper allows Python to pass a python function (which
     * will return data to be pasted) as an argument to
     * prepareForPasting, and then sets up a
     * PythonClipboardFormatRenderer object wrapping that python
     * function. */
    prepareForPasting(
        new PythonClipboardFormatRenderer( renderFunc ),
        availableClipboardFormats
        );
}

static bool waitForClipboardToChangeWrapper( int msTimeout )
{
    /* Internally, we know that the function we're wrapping is waiting
     * on a mutex/event.  While we're waiting, allow Python time to
     * run its threads. */
    bool returnVal;
    Py_BEGIN_ALLOW_THREADS;
    returnVal = waitForClipboardToChange( msTimeout );
    Py_END_ALLOW_THREADS;
    return returnVal;
}

static void waitForPasteWrapper( int msTimeout )
{
    /* Internally, we know that the function we're wrapping is waiting
     * on a mutex/event.  While we're waiting, allow Python time to
     * run its threads. */
    Py_BEGIN_ALLOW_THREADS;
    waitForPaste( msTimeout );
    Py_END_ALLOW_THREADS;
}

%}

%include "std_vector.i"

namespace std {
   %template(IntVector) vector<int>;
};

/* Rename our wrapper functions and our initialize and shutdown functions
 * to have the names we want Python to see. */
%rename(init) initializeClipboardBackend;
void
initializeClipboardBackend( void );

%rename(shutdown) shutdownClipboardBackend;
void
shutdownClipboardBackend( void );

%rename(prepareForPasting) prepareForPastingWrapper;
void
prepareForPastingWrapper( PyObject *renderFunc,
                          const std::vector<int> &availableClipboardFormats );

%rename(waitForPaste) waitForPasteWrapper;
void
waitForPasteWrapper( int msTimeout );

bool
finalizePasting( void );

void
prepareForClipboardToChange( void );

bool
hasClipboardChanged( void );

%rename(waitForClipboardToChange) waitForClipboardToChangeWrapper;
bool
waitForClipboardToChangeWrapper( int msTimeout );
