!define APPNAME "Enso open-source"
!define VERSION "0.4.5"

!include LogicLib.nsh

!define APPNAMEANDVERSION "Enso open-source ${VERSION}"

; Main Install settings
Name "${APPNAMEANDVERSION}"
InstallDir "$APPDATA\enso"
InstallDirRegKey HKLM "Software\${APPNAME}" ""
OutFile "enso-open-source-${VERSION}.exe"

; Use compression
SetCompressor LZMA

; Modern interface settings
!include "MUI.nsh"

!define MUI_ICON "enso\media\images\Enso.ico"
!define MUI_UNICON "enso\media\images\Enso.ico"

!define MUI_HEADERIMAGE
;!define MUI_HEADERIMAGE_LEFT

!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\win.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "${NSISDIR}\Contrib\Graphics\Header\win.bmp"

!define MUI_WELCOMEFINISHPAGE_BITMAP "media\installer.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "media\installer.bmp"

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
#!define MUI_FINISHPAGE_RUN "$INSTDIR\run-enso.exe"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"
#!insertmacro MUI_RESERVEFILE_LANGDLL

Section "Enso open-source" Section_enso

	; Set Section properties
	SetOverwrite on

	; Set Section Files and Shortcuts
	SetOutPath "$INSTDIR\"
    File /r /x _retreat.pyd /x __pycache__ enso\enso
    File /r enso\media
    File /r /x __pycache__ enso\python
    File /r enso\scripts
    File enso\debug.bat
    File enso\run-enso.exe

    SetOutPath "$INSTDIR\lib"
    File enso\lib\SendKeys.py

    SetOutPath "$INSTDIR\commands"
    File enso\commands\calc.py
    File enso\commands\enso.py
    File enso\commands\go.py
    File enso\commands\open.py
    File enso\commands\text_tools.py
    File enso\commands\win_tools.py
SectionEnd

SectionGroup "Additional commands" Section_ensoRoot

Section "System" Section_system
    SetOutPath "$INSTDIR\commands"
    File enso\commands\system.py
SectionEnd

Section "Session" Section_session
    SetOutPath "$INSTDIR\commands"
    File enso\commands\session.py
SectionEnd

Section "Winamp" Section_winamp
    SetOutPath "$INSTDIR\commands"
    File enso\commands\winamp.py
SectionEnd

Section "Web search" Section_websearch
    SetOutPath "$INSTDIR\commands"
    File enso\commands\web_search.py
SectionEnd

Section /o "Media Player Classic" Section_mpc
    SetOutPath "$INSTDIR"
    File /r  /x __pycache__ enso\lib
    SetOutPath "$INSTDIR\commands"
    File enso\commands\mpc.py
SectionEnd

Section /o "Random" Section_idgen
    SetOutPath "$INSTDIR\commands"
    File enso\commands\idgen.py
SectionEnd

Section /o "Lingvo" Section_lingvo
    SetOutPath "$INSTDIR\commands"
    File enso\commands\lingvo.py
SectionEnd

Section /o "DD-WRT" Section_ddwrt
    SetOutPath "$INSTDIR\commands"
    File enso\commands\dd_wrt.py
SectionEnd

Section /o "Dial" Section_dial
    SetOutPath "$INSTDIR\commands"
    File enso\commands\dial.py
SectionEnd

SectionGroupEnd

Section /o "Enso Retreat" Section_retreat
    SetOutPath "$INSTDIR\commands"
    File enso\commands\retreat.py

    SetOutPath "$INSTDIR\enso\contrib"
    File enso\enso\contrib\_retreat.pyd
SectionEnd

Section /o "Portable installation" Section_portable
    SetOutPath "$INSTDIR\"
    File enso\enso-portable.exe

    Delete run-enso.exe
SectionEnd


Section -FinishSection
    ${IfNot} ${SectionIsSelected} ${Section_portable}
        CreateDirectory "$SMPROGRAMS\${APPNAME}"
        CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\run-enso.exe"
        CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"


        WriteRegStr HKLM "Software\${APPNAME}" "" "$INSTDIR"
        WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
        WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run\" "${APPNAME}" "$INSTDIR\run-enso.exe"
        WriteUninstaller "$INSTDIR\uninstall.exe"
    ${EndIf}
SectionEnd

; Modern install component descriptions
#!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
#	!insertmacro MUI_DESCRIPTION_TEXT ${Section1} ""
#!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstall section
Section Uninstall

	;Remove from registry...
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
	DeleteRegKey HKLM "SOFTWARE\${APPNAME}"
	DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run\" "${APPNAME}"

	; Delete self
	Delete "$INSTDIR\uninstall.exe"

	; Delete Shortcuts
	Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
	Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"

	; Remove remaining directories
	RMDir /r "$INSTDIR\"

SectionEnd

; On initialization
Function .onInit
    !insertmacro SetSectionFlag ${Section_enso} ${SF_RO}
FunctionEnd

BrandingText "${APPNAME}"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${Section_enso} "Main application components"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_ensoRoot} "Additional Enso commands"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_system} "'terminate' command that allows to end system processes"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_session} "Windows session management: logout, restart, hibernate..."
!insertmacro MUI_DESCRIPTION_TEXT ${Section_winamp} "Control WinAmp or foobar2000 from Enso"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_websearch} "Web search commands"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_mpc} "Send commands to Media Player Classic (requires MPC Web UI to be enabled)"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_idgen} "Generate random numbers or UUIDs"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_lingvo} "Translate words with ABBYY Lingvo software"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_ddwrt} "Send commands to a DD-WRT router"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_dial} "Initiate or end dial-up remote connections"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_retreat} "A break reminder utility with transparent UI"
!insertmacro MUI_DESCRIPTION_TEXT ${Section_portable} "Make the installation portable"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; eof