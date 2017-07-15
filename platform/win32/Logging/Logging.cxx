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

/*   Implementation of the C logging functions defined in Logging.h. */

/* ***************************************************************************
 * Include Files
 * **************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
#include "WinSdk.h"
#include "Logging/Logging.h"


/* ***************************************************************************
 * Module-Level Variables
 * **************************************************************************/

/* A file handle to which logging output will be written.  Will
 * point to either stderr or an open file, once initialized. */
static FILE *_fileHandle = NULL;

/* If logging is going to a file, this will store the file name. */
static char *_logFileName = NULL;

/* One of LOGGING_ERROR through LOGGING_DEBUG; messages of lower
 * priority than _minimumLevel will not be displayed. */
static int _minimumLevel;

/* Critical section used to ensure log messages are serialized and
 * not interleaved even if multiple threads call logging. */
static CRITICAL_SECTION _loggingLock;

/* If this is 1, then output goes both to _fileHandle and to stdErr.*/
static int _logToBoth = 0;

/* If this is 1, then an error has been logged. */
static volatile int _hasErrorOccurred = 0;

/* ***************************************************************************
 * Private Constants
 * **************************************************************************/

/* String constants which will be displayed in the logging output to describe
 * the levels of severity: */
static const char *errorText = "ERROR  ";
static const char *warningText = "WARNING";
static const char *infoText = "INFO   ";
static const char *debugText = "DEBUG  ";

/* The length in characters of the date produced by _createTimestamp */
static const int LONGEST_DATE = 25;

/* The length in characters of the longest 4-byte int, expressed in base-10 */
static const int LONGEST_INT = 12;

/* Maximum number of characters that variables can take up in a
 * printf-formatted-style string.  This value is arbitrary. */
static const int MAX_VARS_STRING_LEN = 1024;


/* ***************************************************************************
 * Private Function Declarations
 * **************************************************************************/

void
_formattedOutput( FILE *fileHandle,
                  const char *levelString,
                  char *timeStampString,
                  const char *file,
                  int line,
                  const char *msgString );

void
_createTimeStamp( char *timeStampString );

/* ***************************************************************************
 * Public Functions
 * **************************************************************************/

/* ------------------------------------------------------------------------
 * Initialize Logging to a File
 * ........................................................................
 * Opens the file described by filename for appending, and gives fatal
 * error if this is not possible.
 * ----------------------------------------------------------------------*/

int
initLoggingFile( int minLevel, 
                 const char *filename, 
                 int useStdErrToo ) 
{
    /* This function should never be called twice in a row, but just
       in case: */
    if ( isLoggingInitialized() ) 
    {
        fprintf( _fileHandle, "WARNING in initLoggingFile: " );
        fprintf( _fileHandle, 
                 "Attempted to initialize logging more than once.\n" );
        return LOGGING_RESULT_SUCCESS;
    }

    /* Initialize module variables, and open the file: */
    _logFileName = ( char* )malloc( strlen( filename ) + 1 );
    if ( _logFileName == NULL )
        return LOGGING_RESULT_ERROR;

    strncpy( _logFileName, filename, strlen( filename ) + 1 );
    _fileHandle = fopen( filename, "a" );

    /* If we can't open the file, return an error code. */
    if ( _fileHandle == 0 ) 
    {
        free( _logFileName );
        _logFileName = NULL;
        _fileHandle = NULL;
        return LOGGING_RESULT_ERROR;
    }

    _minimumLevel = minLevel;
    _logToBoth = useStdErrToo;

    /* Initialize critical section */
    InitializeCriticalSection( &_loggingLock );

    _hasErrorOccurred = 0;

    return LOGGING_RESULT_SUCCESS;
}


/* ------------------------------------------------------------------------
 * Initialize Logging to Standard Error
 * ........................................................................
 * Works by setting to _fileHandle to stderr, so that we can write to it
 * like any filehandle and have the output go to the terminal.
 * ----------------------------------------------------------------------*/

void
initLoggingStdErr( int minLevel ) 
{
    /* Should never be called more than once, but just in case: */
    if ( isLoggingInitialized() ) 
    {
        fprintf( _fileHandle, "WARNING in initLoggingStdErr: " );
        fprintf( _fileHandle, 
                 "Attempted to initialize logging more than once.\n" );
        return;
    }

    /* Set minimum logging level and open the file: */
    _minimumLevel = minLevel;
    _fileHandle = stderr;

    /* Initialize critical section */
    InitializeCriticalSection( &_loggingLock );

    _hasErrorOccurred = 0;
}


/* ------------------------------------------------------------------------
 * Ask whether logging subsytem is ready to use.
 * ........................................................................
 * Returns true if initialized, false if not initalized, or already 
 * shutdown.
 * ----------------------------------------------------------------------*/

int
isLoggingInitialized() 
{
    return ( _fileHandle != 0 );
}


/* ------------------------------------------------------------------------
 * Change logging threshold on the fly.
 * ........................................................................
 * Sets the threshold to newLevel; subsequent calls to _logMessageImpl
 * will be affected.
 * ----------------------------------------------------------------------*/

void
setLoggingThreshold( int newLevel )
{
    _minimumLevel = newLevel;
}


/* ------------------------------------------------------------------------
 * Returns the current logging threshold.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
getLoggingThreshold( void )
{
    return _minimumLevel;
}


/* ------------------------------------------------------------------------
 * Shutdown logging subsystem.
 * ........................................................................
 * Close any files opened by initLogging, and do any other needed cleanup.
 * ----------------------------------------------------------------------*/

int
shutdownLogging() 
{
    /* Should never call this more than once, or without initLogging,
       but just in case: */
    if ( !isLoggingInitialized() ) 
        return LOGGING_RESULT_SUCCESS;

    /* Free up allocated memory: */
    if ( _logFileName != NULL )
    {
        free( _logFileName );
    }
    _logFileName = NULL;
    DeleteCriticalSection( &_loggingLock );

    /* Attempt to close any open file: */
    if ( _fileHandle != stderr ) 
    {
        if ( fclose( _fileHandle ) != 0) 
            return LOGGING_RESULT_ERROR;
    }
    /* If we were logging to stderr, there's nothing to close */

    _fileHandle = 0;

    return LOGGING_RESULT_SUCCESS;
}

/* ------------------------------------------------------------------------
 * Returns true if logging output is going to a file.
 * ........................................................................
 * Not mutually exclusive with logging to std err.  Returns false if
 * logging not initialized.
 * ----------------------------------------------------------------------*/

int
isLoggingToFile( void )
{
    if (!isLoggingInitialized())
    {
        return false;
    }
    return ( _fileHandle != stderr );
}

/* ------------------------------------------------------------------------
 * Returns true if logging output is going to standard error.
 * ........................................................................
 * Not mutually exclusive with logging to file.  Returns false if logging
 * not initialized.
 * ----------------------------------------------------------------------*/

int
isLoggingToStdErr( void )
{
    if (!isLoggingInitialized())
    {
        return false;
    }
    return ( _fileHandle == stderr || _logToBoth );
}

/* ------------------------------------------------------------------------
 * Returns a reference to the string containing the logfile name, if any
 * ........................................................................
 * The return value is a pointer to this module's internal copy of the
 * string.  This data should not be modified; if you want to modify it,
 * make your own copy!
 * ----------------------------------------------------------------------*/

const char*
getLoggingFileName( void )
{
    if ( !isLoggingToFile() )
    {
        return NULL;
    }
    return _logFileName;
}

/* ------------------------------------------------------------------------
 * Return whether an error has been logged.
 * ........................................................................
 * ----------------------------------------------------------------------*/

int
hasErrorBeenLogged( void )
{
    if ( !isLoggingInitialized() ) 
        initLoggingStdErr( LOGGING_DEBUG );

    return _hasErrorOccurred;
}

/* ------------------------------------------------------------------------
 * Like printf, but for logging messages.
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
logMessageWithVars( int level, 
                    const char *file, 
                    int line,
                    const char *msgString, 
                    ... )
{
    va_list formatArgs;

    /* Allocate new string long enough to hold original string plus
     * longest possible integer: */
    char *stringWithVars = NULL;
    long stringLen = strlen( msgString ) + MAX_VARS_STRING_LEN;
    stringWithVars = (char*)malloc( stringLen+1 );

    if ( stringWithVars == NULL )
    {
        /* If we don't have memory for that we're pretty much screwed */
        _logMessageImpl( LOGGING_ERROR,
                         "Help help I'm out of memory to log errors!",
                         file,
                         line);
    }

    va_start( formatArgs, msgString );
    /* Combine msgString with the integer variable into the new string.*/
    _vsnprintf( stringWithVars,
                stringLen,
                msgString,
                formatArgs ); 
    va_end( formatArgs );

    /* Null-terminate just in case _vsnprintf() truncates the string. */
    stringWithVars[stringLen] = 0;

    /* Pass the composed string on to the normal _logMessageImpl. */
    _logMessageImpl( level, stringWithVars, file, line );

    /* Clean up and exit */
    free( stringWithVars );
}


/* ***************************************************************************
 * Private Functions
 * **************************************************************************/

/*------------------------------------------------------------------------
 * Generates timestamp and puts it in the location given
 *........................................................................
 * 
 * The format of the timestamp is Www Mmm dd hh:mm:ss yyyy
 * with hours going 0 to 23.  The length of the timestamp is always
 * 24 characters plus one for the terminating null byte; use the
 * constant LONGEST_DATE when allocating a string to hold the
 * timestamp.
 * 
 *----------------------------------------------------------------------*/

void
_createTimeStamp( char *timeStampString )
{
    time_t rawtime;
    int length;
    char *tempString;

    time ( &rawtime );
    tempString = ctime( &rawtime );

    /* ctime puts a newline on the end of the string, which we
     * don't want.  Chop the last character off: */
    length = strlen( tempString ) - 1;

    if ( length >= LONGEST_DATE )
    {
        /* The date's too long to fit in the string!  This is bad, but
         * we'll be friendly and truncate. */

        length = LONGEST_DATE - 1;
    }

    strncpy( timeStampString, tempString, length );
    timeStampString[length] = '\0';
}

/* ------------------------------------------------------------------------
 * Generate the actual log messages.
 * ........................................................................
 * Outputs nothing if the given level is below the threshold set on
 * initialization.  Otherwise, adds a line to the message log,
 * prefixed with the severity level, telling the time and date, the
 * file and line number of source code that generated the message, and
 * including the given msgString.
 * ----------------------------------------------------------------------*/

void 
_logMessageImpl( int level, 
                 const char *msgString, 
                 const char *file, 
                 int line ) 
{
    /* will be a pointer to one of the static const strings */
    const char *levelString; 
    char timeStampString[LONGEST_DATE];

    if ( !isLoggingInitialized() ) 
        initLoggingStdErr( LOGGING_DEBUG );        

    /* Ignore messages below our threshold of caring. */
    if ( level < _minimumLevel ) 
    {
        return;
    }

    /* If this function is called by two threads at once, the output
     * could be interwoven; this is not a serious error but it is
     * annoying, so we put a critical section around the part of the
     * function that produces output: */
    EnterCriticalSection( &_loggingLock );

    /* Get a string appropriate to the logging level: */
    switch ( level ) 
    {
    case LOGGING_ERROR:
        _hasErrorOccurred = 1;
        levelString = errorText;
        break;
    case LOGGING_WARN:
        levelString = warningText;
        break;
    case LOGGING_INFO:
        levelString = infoText;
        break;
    case LOGGING_DEBUG:
        levelString = debugText;
        break;
    default:
        fprintf( _fileHandle,
                 "Invalid logging level constant; setting it to WARNING.\n" );
        level = LOGGING_WARN;
        levelString = warningText;
    }

    /* Generate a timestamp string: */
    _createTimeStamp( timeStampString );

    /* Here's where we actually write the message out: */
    _formattedOutput( _fileHandle,
                      levelString,
                      timeStampString,
                      file,
                      line,
                      msgString );
    /* Deal with the case where we log to both standard error and
     * the open file: */
    if ( _logToBoth )
    {
        _formattedOutput( stderr,
                          levelString,
                          timeStampString,
                          file,
                          line,
                          msgString );
    }  

    /* End of thread-sensitive region */
    LeaveCriticalSection( &_loggingLock );
}

/* ------------------------------------------------------------------------
 * Format msg with time, line, file, and immediately write to fileHandle
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
_formattedOutput( FILE *fileHandle,
                  const char *levelString,
                  char *timeStampString,
                  const char *file,
                  int line,
                  const char *msgString )
{
   fprintf( fileHandle, "%s [%s %s L%d]: %s\n", 
            levelString,
            timeStampString,
            file, 
            line, 
            msgString );

    /* Immediately flushing output buffer ensures that the message
     * appears even if we crash, and that it appears in correct
     * sequence relative to other events, for easy debugging. */
    fflush( fileHandle );

}


/* ------------------------------------------------------------------------
 * Substitute integer variable into string and call _logMessageImpl
 * ........................................................................
 * ----------------------------------------------------------------------*/

void
_logMessageWithOneInt( int level, 
                       const char *msgString, 
                       const char *file, 
                       int line,
                       int variable ) 
{
    /* Allocate new string long enough to hold original string plus
     * longest possible integer: */
    char *stringWithInt = NULL;
    long stringLen = strlen( msgString ) + LONGEST_INT;
    stringWithInt = (char*)malloc( stringLen+1 );

    if ( stringWithInt == NULL )
    {
        /* If we don't have memory for that we're pretty much screwed */
        _logMessageImpl( LOGGING_ERROR,
                         "Help help I'm out of memory to log errors!",
                         file,
                         line);
    }

    /* Combine msgString with the integer variable into the new string.*/
    _snprintf( stringWithInt,
               stringLen,
               "%s %d",
               msgString,
               variable ); 

    /* Null-terminate just in case _snprintf() truncates the string. */
    stringWithInt[stringLen] = 0;

    /* Pass the composed string on to the normal _logMessageImpl. */
    _logMessageImpl( level, stringWithInt, file, line );

    /* Clean up and exit */
    free( stringWithInt );
}
