@echo off
setlocal

rem --- Build a Linux / macOS distribution archive using 7za -----------
rem
rem The resulting .tar.gz contains a single root folder "enso" with:
rem   - the contents of enso\ (commands, enso, lib, media, scripts, debug.sh)
rem     minus the "python" directory and Windows-only binaries
rem   - README.linux.md, README.macos.md, LICENSE
rem   - install_linux.sh, install_macos.sh

set "VERSION=1.4"
set "ARCHIVE=enso-open-source-%VERSION%-unix.tar.gz"
set "STAGING=_dist_unix"
set "ROOT=%STAGING%\enso"

echo --- Cleaning previous staging area ---
if exist "%STAGING%" rd /s /q "%STAGING%"

echo --- Creating staging directory ---
mkdir "%ROOT%"

rem --- Copy enso\ contents, excluding the python folder and Windows binaries ---
echo --- Copying enso contents (excluding python folder and Windows binaries) ---
robocopy enso\commands "%ROOT%\commands" /e /xd __pycache__ >nul
robocopy enso\enso     "%ROOT%\enso"     /e /xd __pycache__ win32 >nul
robocopy enso\lib      "%ROOT%\lib"      /e /xd __pycache__ >nul
robocopy enso\media    "%ROOT%\media"    /e >nul
robocopy enso\scripts  "%ROOT%\scripts"  /e /xd __pycache__ >nul
copy enso\debug.sh "%ROOT%\" >nul

rem --- Copy READMEs, license, and install scripts into the root ---
echo --- Copying documentation and install scripts ---
copy README.linux.md "%ROOT%\" >nul
copy README.macos.md "%ROOT%\" >nul
copy LICENSE         "%ROOT%\" >nul
copy install_linux.sh "%ROOT%\" >nul
copy install_macos.sh "%ROOT%\" >nul

rem --- Create the archive with 7za ----
echo --- Creating %ARCHIVE% ---
if exist "%ARCHIVE%" del "%ARCHIVE%"

rem 7za cannot create .tar.gz in one step; first create a .tar, then compress.
7za a -ttar "%STAGING%\enso.tar" ".\%STAGING%\enso" >nul
if errorlevel 1 (
    echo ERROR: 7za tar creation failed.
    goto :cleanup
)

7za a -tgzip "%ARCHIVE%" "%STAGING%\enso.tar" >nul
if errorlevel 1 (
    echo ERROR: 7za gzip compression failed.
    goto :cleanup
)

echo --- Done: %ARCHIVE% ---

:cleanup
echo --- Cleaning up staging area ---
if exist "%STAGING%" rd /s /q "%STAGING%"

endlocal
