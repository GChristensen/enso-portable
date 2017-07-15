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

/*   Header file for the ClipboardFormatRenderer class. This class
 *   provides an abstract interface which encapsulates the part of the
 *   ClipboardBackend that renders the clipboard data in a particular
 *   format.
 */

#ifndef _CLIPBOARD_FORMAT_RENDERER_H_
#define _CLIPBOARD_FORMAT_RENDERER_H_ 1


/* ***************************************************************************
 * Constants
 * **************************************************************************/

#define CFR_SUCCESS        0
#define CFR_ERROR          1


/* ***************************************************************************
 * Classes
 * **************************************************************************/

/* ===========================================================================
 * ClipboardFormatRenderer class
 * ...........................................................................
 *
 * An abstract base class which defines an interface for retreiving string or
 * binary data rendered into a specified clipboard format.
 *
 * =========================================================================*/

class ClipboardFormatRenderer
{
public:

    /* --------------------------------------------------------------------
     * Destructor.
     * ....................................................................
     * ------------------------------------------------------------------*/

    virtual ~ClipboardFormatRenderer() { }

    /* --------------------------------------------------------------------
     * Retrieves clipboard data in the given format.
     * ....................................................................
     * 
     * format is the desired ClipboardFormat code, as a win32 CF_*
     * constant.
     * 
     * outputString and outputLength are out-parameters containing a
     * pointer to the raw clipboard data and its length, in bytes. The
     * caller is responsible for freeing outputString. 
     * 
     * If successful, this function returns CFR_SUCCESS; otherwise, 
     * CFR_ERROR is returned.
     *
     * ------------------------------------------------------------------*/

    virtual int
    renderFormat( int format,
                  char **outputString,
                  int *outputLength ) = 0;
};

#endif

