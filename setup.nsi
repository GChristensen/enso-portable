Unicode True

!define DIRNAME "Enso Launcher"
!define APPNAME "Enso Launcher (OSS)"
!define VERSION "1.0"

!include LogicLib.nsh

!define APPNAMEANDVERSION "${APPNAME} ${VERSION}"

; Main Install settings
Name "${APPNAMEANDVERSION}"
InstallDir "$APPDATA\${DIRNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" ""
OutFile "enso-open-source-${VERSION}-x86_64.exe"

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

!define StrLoc "!insertmacro StrLoc"
 
!macro StrLoc ResultVar String SubString StartPoint
  Push "${String}"
  Push "${SubString}"
  Push "${StartPoint}"
  Call StrLoc
  Pop "${ResultVar}"
!macroend
 
Function StrLoc
/*After this point:
  ------------------------------------------
   $R0 = StartPoint (input)
   $R1 = SubString (input)
   $R2 = String (input)
   $R3 = SubStringLen (temp)
   $R4 = StrLen (temp)
   $R5 = StartCharPos (temp)
   $R6 = TempStr (temp)*/
 
  ;Get input from user
  Exch $R0
  Exch
  Exch $R1
  Exch 2
  Exch $R2
  Push $R3
  Push $R4
  Push $R5
  Push $R6
 
  ;Get "String" and "SubString" length
  StrLen $R3 $R1
  StrLen $R4 $R2
  ;Start "StartCharPos" counter
  StrCpy $R5 0
 
  ;Loop until "SubString" is found or "String" reaches its end
  ${Do}
    ;Remove everything before and after the searched part ("TempStr")
    StrCpy $R6 $R2 $R3 $R5
 
    ;Compare "TempStr" with "SubString"
    ${If} $R6 == $R1
      ${If} $R0 == `<`
        IntOp $R6 $R3 + $R5
        IntOp $R0 $R4 - $R6
      ${Else}
        StrCpy $R0 $R5
      ${EndIf}
      ${ExitDo}
    ${EndIf}
    ;If not "SubString", this could be "String"'s end
    ${If} $R5 >= $R4
      StrCpy $R0 ``
      ${ExitDo}
    ${EndIf}
    ;If not, continue the loop
    IntOp $R5 $R5 + 1
  ${Loop}
 
  ;Return output to user
  Pop $R6
  Pop $R5
  Pop $R4
  Pop $R3
  Pop $R2
  Exch
  Pop $R1
  Exch $R0
FunctionEnd

!define CreateJunction "!insertmacro CreateJunction"

Function CreateJunction
  Exch $4
  Exch
  Exch $5
  Push $1
  Push $2
  Push $3
  Push $6
  CreateDirectory "$5"
  System::Call "kernel32::CreateFileW(w `$5`, i 0x40000000, i 0, i 0, i 3, i 0x02200000, i 0) i .r6"

  ${If} $0 = "-1"
    StrCpy $0 "0"
    RMDir "$5"
    goto create_junction_end
  ${EndIf}

  CreateDirectory "$4"  ; Windows XP requires that the destination exists
  StrCpy $4 "\??\$4"
  StrLen $0 $4
  IntOp $0 $0 * 2
  IntOp $1 $0 + 2
  IntOp $2 $1 + 10
  IntOp $3 $1 + 18
  System::Call "*(i 0xA0000003, &i4 $2, &i2 0, &i2 $0, &i2 $1, &i2 0, &w$1 `$4`, &i2 0)i.r2"
  System::Call "kernel32::DeviceIoControl(i r6, i 0x900A4, i r2, i r3, i 0, i 0, *i r4r4, i 0) i.r0"
  System::Call "kernel32::CloseHandle(i r6) i.r1"

  ${If} $0 == "0"
    RMDir "$5"
  ${EndIf}

  create_junction_end:
  Pop $6
  Pop $3
  Pop $2
  Pop $1
  Pop $5
  Pop $4
FunctionEnd

!macro CreateJunction Junction Target outVar
  Push $0
  Push "${Junction}"
  Push "${Target}"
  Call CreateJunction
  StrCpy ${outVar} $0
  Pop $0
!macroend

!macro UninstallExisting exitcode uninstcommand
    Push `${uninstcommand}`
    Call UninstallExisting
    Pop ${exitcode}
!macroend
Function UninstallExisting
    Exch $1 ; uninstcommand
    Push $2 ; Uninstaller
    Push $3 ; Len
    StrCpy $3 ""
    StrCpy $2 $1 1
    StrCmp $2 '"' qloop sloop
    sloop:
        StrCpy $2 $1 1 $3
        IntOp $3 $3 + 1
        StrCmp $2 "" +2
        StrCmp $2 ' ' 0 sloop
        IntOp $3 $3 - 1
        Goto run
    qloop:
        StrCmp $3 "" 0 +2
        StrCpy $1 $1 "" 1 ; Remove initial quote
        IntOp $3 $3 + 1
        StrCpy $2 $1 1 $3
        StrCmp $2 "" +2
        StrCmp $2 '"' 0 qloop
    run:
        StrCpy $2 $1 $3 ; Path to uninstaller
        StrCpy $1 161 ; ERROR_BAD_PATHNAME
        GetFullPathName $3 "$2\.." ; $InstDir
        #IfFileExists "$2" 0 +4
        #ExecWait '"$2" /S _?=$3' $1 ; This assumes the existing uninstaller is a NSIS uninstaller, other uninstallers don't support /S nor _?=
        RMDir /r "$3"
        #IntCmp $1 0 "" +2 +2 ; Don't delete the installer if it was aborted
        #Delete "$2" ; Delete the uninstaller
        #RMDir "$3" ; Try to delete $InstDir
        #RMDir "$3\.." ; (Optional) Try to delete the parent of $InstDir
    #Pop $3
    #Pop $2
    #Exch $1 ; exitcode
    StrCpy $1 0
    Exch $1
FunctionEnd

Var uninstallString
Section "Enso Launcher (OSS)" Section_enso
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString"

    ${If} $0 != ""
        StrCpy $uninstallString $0
    ${EndIf}

    ${If} $uninstallString != ""
    ${AndIf} ${Cmd} `MessageBox MB_YESNO|MB_ICONQUESTION "Uninstall previous version?" /SD IDYES IDYES`
        !insertmacro UninstallExisting $uninstallString '"$uninstallString"'
        ${If} $1 <> 0
            MessageBox MB_YESNO|MB_ICONSTOP "Failed to uninstall, continue anyway?" /SD IDYES IDYES +2
                Abort
        ${EndIf}
    ${EndIf}
    
	; Set Section properties
	SetOverwrite on

	; Set Section Files and Shortcuts
	SetOutPath "$INSTDIR\"
#    File /r /x _retreat.pyd /x retreat.html /x __pycache__ enso\enso
    File /r /x _retreat.pyd enso\enso
    File /r enso\media
#    File /r /x __pycache__ enso\python
    File /r enso\python
    File /r enso\scripts
    File enso\debug.bat
    File enso\run-enso.exe

    StrCpy $0 0
    ${StrLoc} $1 "$INSTDIR" "C:\Program Files\" ">"
    StrCmp $0 $1 create_junction without_junction

create_junction:
    ${CreateJunction} "$INSTDIR\python\Lib\site-packages\enso" "$INSTDIR\enso" $9

without_junction:
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
#    File /r  /x __pycache__ enso\lib
    File /r enso\lib
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
    File enso\enso\contrib\retreat.html
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
        WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\uninstall.exe"
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
