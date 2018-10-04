!define APPNAME "Enso open-source"
!define VERSION "0.4.0"

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
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"
#!insertmacro MUI_RESERVEFILE_LANGDLL

Section "-Enso open-source" Section_enso

	; Set Section properties
	SetOverwrite on

	; Set Section Files and Shortcuts
	SetOutPath "$INSTDIR\"
	File /r enso\docs
    File /r /x retreat.pyd /x __pycache__ enso\enso
    File /r enso\media
    File /r /x __pycache__ enso\python
    File /r enso\scripts
    File enso\debug.bat
    File enso\run-enso.exe

    SetOutPath "$INSTDIR\commands"
    File enso\commands\calc.py
    File enso\commands\color_theme.py
    File enso\commands\enso.py
    File enso\commands\go.py
    File enso\commands\open.py
    File enso\commands\text_tools.py
    File enso\commands\win_tools.py

	CreateDirectory "$SMPROGRAMS\${APPNAME}"
	CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\run-enso.exe"
	CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

SectionEnd

SectionGroup "Enso open-source"

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

Section /o "Media Player Classic" Section_mpc
    SetOutPath "$INSTDIR\commands"
    File enso\commands\mpc.py
SectionEnd

Section /o "ID Generator" Section_idgen
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

    SetOutPath "$INSTDIR\enso"
    File enso\enso\retreat.pyd
SectionEnd


Section -FinishSection

	WriteRegStr HKLM "Software\${APPNAME}" "" "$INSTDIR"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
	#WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run\" "${APPNAME}" "$INSTDIR\retreat.exe"
	WriteUninstaller "$INSTDIR\uninstall.exe"

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
	#DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run\" "${APPNAME}"

	; Delete self
	Delete "$INSTDIR\uninstall.exe"

	; Delete Shortcuts
	#Delete "$SMPROGRAMS\Enso Retreat\Enso Retreat.lnk"
	Delete "$SMPROGRAMS\Enso Retreat\Uninstall.lnk"

	#Delete "$INSTDIR\retreat.exe"


	; Remove remaining directories
	RMDir "$INSTDIR\"

SectionEnd

; On initialization
Function .onInit

FunctionEnd

BrandingText "${APPNAME}"

; eof