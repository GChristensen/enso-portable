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

/*   Header file for Windows software development.
 *
 *   This header file is mostly just a wrapper for the standard
 *   Windows include file, Windows.h. It also defines a few necessary
 *   macros needed by our software. This file should always be used in 
 *   original Humanized code instead of including Windows.h directly.
 */

#ifndef _WINSDK_H_
#define _WINSDK_H_

/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Use strict type checking for all Windows data types and API
 * calls. Must be defined before including Windows.h. */
#define STRICT

/* Assume we're using Windows NT 5.0 (Windows 2000) or above. This
 * will enable certain API calls that are only availale under NT 5.0
 * or above. Must be defined before including Windows.h. */
#define _WIN32_WINNT 0x0500

/* More readable definition for a DLL exported function under MSVC++. */
#define DllExport __declspec(dllexport)

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include <Windows.h>

#endif
