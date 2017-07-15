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
 *   defined in InputManager.h, and allows you to extend some of the
 *   classes in Python through the use of SWIG directors.
 */

%module( directors="1" ) InputManager
%include "std_string.i"

%define MAKE_CLASS_EXTENDABLE( CLASSNAME )
%feature( "director" ) CLASSNAME;
%enddef

%feature( "director:except" ) {
    if ( $error != NULL ) {
        throw MehitabelPythonException();
    }
}

%exception {
    try {
        $action
    } catch ( MehitabelPythonException ) {
        SWIG_fail;
    } catch ( MehitabelException ) {
       PyErr_SetString( PyExc_RuntimeError,
                        "A MehitabelException occurred." );
       return NULL;
    }
}

%{
#include "InputManager.h"
%}

MAKE_CLASS_EXTENDABLE( InputManager );

%include "InputManager.h"
%include "InputManagerConstants.h"
