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

/*   This header file defines the C API for the logging module.
 *   Include it wherever you want to use logging from C.
 *   Implementation is in Logging.cxx. */

#ifndef _LOGGING_H_
#define _LOGGING_H_

/* ***************************************************************************
 * Macros
 * **************************************************************************/

/* Define LOGGING_API to mean different things depending on whether
   Logging itself is including this file, or a client is including it.
   If the former, then we want to declare all Logging API functions as
   exported DLL functions; if the latter, we want to declare them as
   imported DLL functions. */

#ifdef LOGGING_USE_DL_EXPORT
#define LOGGING_API __declspec( dllexport ) extern
#else
#define LOGGING_API __declspec( dllimport ) extern
#endif

#include "LoggingConstants.h"


/* errorMsg, warnMsg, infoMsg, and debugMsg are macros which call
 * _logMessageImpl.  The magic macros __FILE__ and __LINE__ resolve to
 * the file name and line number where the macro is called from.  If
 * ENSO_DEBUG is turned off, debugMsg becomes a no-op.  */

/* errorMsg indicates a fatal error condition; it is the caller's
 * responsibility to terminate program execution after calling
 * errorMsg. */
#define errorMsg( string ) \
        _logMessageImpl( LOGGING_ERROR, string, __FILE__, __LINE__ )
#define warnMsg( string ) \
        _logMessageImpl( LOGGING_WARN, string, __FILE__, __LINE__ )
#define infoMsg( string ) \
        _logMessageImpl( LOGGING_INFO, string, __FILE__, __LINE__ )

#if ENSO_DEBUG == 1
#define debugMsg( string ) \
        _logMessageImpl( LOGGING_DEBUG, string, __FILE__, __LINE__ )
#else
#define debugMsg( string )
#endif

/* errorMsgInt, warnMsgInt, infoMsgInt, and debugMsgInt take a string
 * and an integer, and simply print the number after the end of the
 * string.  They're the same as errorMsg, warnMsg, infoMsg, and 
 * debugMsg in all other ways. */
#define errorMsgInt( string, variable ) _logMessageWithOneInt( \
                LOGGING_ERROR, string, __FILE__, __LINE__, variable );
#define warnMsgInt( string, variable ) _logMessageWithOneInt( \
                LOGGING_WARN, string, __FILE__, __LINE__, variable );
#define infoMsgInt( string, variable ) _logMessageWithOneInt( \
                LOGGING_INFO, string, __FILE__, __LINE__, variable );
#if ENSO_DEBUG == 1
#define debugMsgInt( string, variable ) _logMessageWithOneInt( \
                LOGGING_DEBUG, string, __FILE__, __LINE__, variable );
#else
#define debugMsgInt( string, variable )
#endif

#ifdef __cplusplus 
extern "C" {
#endif

/* ***************************************************************************
 * Public Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Initialize logging to a file.
 * ........................................................................
 * You must call either this function or initLoggingStdErr before you can
 * use any of the other logging functions.
 * 
 * minLevel is the severity threshold.  Should be one of 
 * (ERROR, WARN, INFO, or DEBUG).  No messages less severe than that
 * will be displayed.  filename is a string giving the name of the file,
 * which need not be open or exist yet.
 * If useStdErrToo is nonzero, logging output will go BOTH to the file
 * and to standard error.
 *
 * Returns LOGGING_RESULT_SUCCESS on success, LOGGING_RESULT_ERROR on
 * failure.
 * ----------------------------------------------------------------------*/

LOGGING_API int
initLoggingFile( int minLevel,
                 const char *filename,
                 int useStdErrToo);

/* ------------------------------------------------------------------------
 * Initialize logging to the standard error output.
 * ........................................................................
 * You must call either this function or initLoggingFile before you can
 * use any of the other logging functions.
 * 
 * minLevel has the same meaning as in initLoggingFile.  Only call one or
 * the other of initLoggingFile and initLoggingStdErr.
 * ----------------------------------------------------------------------*/

LOGGING_API void
initLoggingStdErr( int minLevel );

/* ------------------------------------------------------------------------
 * Ask whether logging subsytem is ready to use.
 * ........................................................................
 * Returns true if initialized, false if not initalized or already 
 * shutdown.
 * ----------------------------------------------------------------------*/

LOGGING_API int
isLoggingInitialized( void );

/* ------------------------------------------------------------------------
 * Change logging threshold on the fly.
 * ........................................................................
 * Pass in one of the LOGGING_ERROR, LOGGING_WARN, etc constants;
 * messages of that severity level and higher will be shown from this
 * point on.
 * ----------------------------------------------------------------------*/

LOGGING_API void
setLoggingThreshold( int newLevel );

/* ------------------------------------------------------------------------
 * Get the logging threshold.
 * ........................................................................
 * ----------------------------------------------------------------------*/

LOGGING_API int
getLoggingThreshold( void );

/* ------------------------------------------------------------------------
 * Shutdown the logging subsystem.
 * ........................................................................
 * You should call this function when you are done with logging, before
 * program termination, to ensure a clean exit.
 *
 * Returns LOGGING_RESULT_SUCCESS on success, LOGGING_RESULT_ERROR on
 * failure.
 * ----------------------------------------------------------------------*/

LOGGING_API int
shutdownLogging( void );

/* ------------------------------------------------------------------------
 * Returns true if logging output is currently going to a file.
 * ........................................................................
 * ----------------------------------------------------------------------*/

LOGGING_API int
isLoggingToFile( void );

/* ------------------------------------------------------------------------
 * Returns true if logging output is currently going to standard error.
 * ........................................................................
 * Note that this and isLoggingToFile are not mutually exclusive!
 * ----------------------------------------------------------------------*/

LOGGING_API int
isLoggingToStdErr( void );


/* ------------------------------------------------------------------------
 * Returns a reference to the string containing the logfile name, if any
 * ........................................................................
 * The return value is a pointer to this module's internal copy of the
 * string.  This data should not be modified; if you want to modify it,
 * make your own copy!
 * ----------------------------------------------------------------------*/

LOGGING_API const char*
getLoggingFileName( void );

/* ------------------------------------------------------------------------
 * Return whether an error has been logged.
 * ........................................................................
 * Returns 1 if an error has occurred, 0 if not.
 * ----------------------------------------------------------------------*/

LOGGING_API int
hasErrorBeenLogged( void );

/* ------------------------------------------------------------------------
 * Like printf, but for logging messages.
 * ........................................................................
 *
 * Unfortunately, you need to manually pass-in level (one of
 * LOGGING_DEBUG, etc.), filename, and line number information.
 * Ideally this would be done automatically by a variadic macro, but
 * Visual Studio 2005 is the earliest edition of MS Visual Studio that
 * supports them (at the time of this writing, we are using VS 2003).
 *
 * ----------------------------------------------------------------------*/

LOGGING_API void
logMessageWithVars( int level, 
                    const char *file, 
                    int line,
                    const char *msgString, 
                    ... );

/* ***************************************************************************
 * Private Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Generate the actual log messages.
 * ........................................................................
 * level is the severity level of the message, msgString is the
 * text, file is the name of the file where the message was logged,
 * and line is the line number in that file.
 *
 * msgString must be a C-style (null-terminated) string; if you have to
 * log Unicode use the Python API functions (see Logging.i.)
 * _logMessageImpl should never be called directly; use the Msg macros
 * above, instead.  The reason it is defined here is so the macros
 * here and the Python functions defined in the SWIG input file
 * Logging.i can use it.
 *
 * LOGGING_ERROR is intended to be a fatal error, but it is the caller's
 * responsibility to end the program.  After the caller does an 
 * errorMsg, the caller should produce bug reports or stack traces and
 * then terminate as soon as possible.
 * 
 * ----------------------------------------------------------------------*/

LOGGING_API void
_logMessageImpl( int level, 
                 const char *msgString,
                 const char *file,
                 int line );


/* ------------------------------------------------------------------------
 * Substitute integer variable into string and call _logMessageImpl
 * ........................................................................
 * 
 * Like _logMessageImpl in all respects except that it also takes an
 * integer variable ( called "variable" ) which is output after the
 * end of the msgString.
 * Defined here so that the macros above can use it.
 *
 * ----------------------------------------------------------------------*/

LOGGING_API void
_logMessageWithOneInt( int level, 
                       const char *msgString, 
                       const char *file, 
                       int line,
                       int variable );

#ifdef __cplusplus
}
#endif
#endif
