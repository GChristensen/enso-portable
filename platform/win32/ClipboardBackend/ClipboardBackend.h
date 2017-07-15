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

/*   Header file for Enso's clipboard backend.
 *
 *   The ClipboardBackend provides low-level methods which Python can
 *   use to interact with the Windows clipboard.  For instance, it
 *   provides a method of setting the clipboard text in preparation
 *   for pasting into an application, in such a way that we can then
 *   detect whether the subsequent paste operation was successful or
 *   not, using the delayed clipboard rendering feature of Win32.
 */

#ifndef _CLIPBOARDBACKEND_H_
#define _CLIPBOARDBACKEND_H_

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#ifndef SWIG
#include "WinSdk.h"
#include "Logging/Logging.h"
#include "Input/AsyncEventProcessorRegistry.h"
#include "Python.h"
#include "ClipboardFormatRenderer.h"
#endif

#include <vector>

/* ***************************************************************************
 * Public Function Declarations
 * **************************************************************************/

/* --------------------------------------------------------------------
 * Initialize the clipboard backend.
 * ....................................................................
 *
 * Call this exactly once before trying to use other functions in
 * this module.
 *
 * ------------------------------------------------------------------*/

void
initializeClipboardBackend( void );

/* --------------------------------------------------------------------
 * Shutdown the clipboard backend.
 * ....................................................................
 *
 * Call this exactly once after you are done using other functions in
 * this module.
 *
 * ------------------------------------------------------------------*/

void
shutdownClipboardBackend( void );

/* --------------------------------------------------------------------
 * Call this function before simulating a paste keystroke.
 * ....................................................................
 * 
 * The first argument is a ClipboardFormatRenderer object which
 * provides a method that will be used to retrieve the rendered data
 * when the time comes.
 *
 * The second argument is a list of the clipboard format codes
 * (CF_TEXT, CF_UNICODETEXT, etc) that you intend to support.  If you
 * include a format in this list, the ClipboardFormatRenderer you
 * provide MUST be prepared to actually render text in the appropriate
 * format!
 *
 * prepareForPasting() also puts a lock on ClipboardBackend which will
 * prevent any other threads from trying to use this module until the
 * lock is released in finalizePasting().
 *
 * ------------------------------------------------------------------*/

void
prepareForPasting( ClipboardFormatRenderer *clipFormRend,
                   const std::vector<int> &availableClipboardFormats );

/* --------------------------------------------------------------------
 * Waits until clipboard contents have been pasted or a timeout occurs.
 * ....................................................................
 * ------------------------------------------------------------------*/

void
waitForPaste( int msTimeout );

/* --------------------------------------------------------------------
 * Call this function after simulating a paste keystroke.
 * ....................................................................
 *
 * This function does any neccessary cleanup of resources allocated
 * during the paste-to-application process, returns ClipboardBackend
 * to its default state, and frees the lock.  The return value of this
 * function tells whether or not the paste operation was successful.
 *
 * ------------------------------------------------------------------*/

bool
finalizePasting( void );

/* --------------------------------------------------------------------
 * Prepares for the clipboard contents to change.
 * ....................................................................
 *
 * This function must be called prior to various other functions in
 * this module, such as hasClipboardChanged() and
 * waitForClipboardToChange().
 *
 * ------------------------------------------------------------------*/

void
prepareForClipboardToChange( void );

/* --------------------------------------------------------------------
 * Returns whether the clipboard contents have changed.
 * ....................................................................
 *
 * More specifically, this function returns whether the clipboard
 * contents have changed since the last call to
 * prepareForClipboardToChange().
 *
 * ------------------------------------------------------------------*/

bool
hasClipboardChanged( void );

/* --------------------------------------------------------------------
 * Waits until clipboard contents have changed or a timeout occurs.
 * ....................................................................
 *
 * More specifically, this function waits for clipboard contents to
 * change since the last call to prepareForClipboardToChange().
 *
 * Returns false if the clipboard contents didn't change inside
 * the specified timeout range.  Returns true of the contents
 * did actually change before the timeout kicked in.
 * ------------------------------------------------------------------*/

bool
waitForClipboardToChange( int msTimeout );

#endif
