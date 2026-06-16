; Phase theta.4 - Inno Setup script for the YHWH Windows installer.
;
; Wraps dist\YHWH.exe (produced by dev\build_desktop.cmd ->
; pyinstaller dev\launcher.spec) into a click-through .exe installer
; that drops shortcuts in Start Menu + optionally on the Desktop.
;
; Requires Inno Setup 6.x (free; download at https://jrsoftware.org/isdl.php).
; Compile via:  ISCC.exe dev\installer.iss
;               or via dev\build_msi.cmd
;
; Output:  dist\YHWH-<version>-windows-x64.exe (matches releases.html + gh release asset)
;
; Signing is opt-in - the SignTool flag below is set up to use a
; configured signtool command in Inno Setup's tools menu. If no
; cert is configured, the installer is unsigned (works fine for
; personal use; SmartScreen will warn end-users on download).

#define MyAppName "YHWH"
#define MyAppPublisher "YHWH Bible Publishing"
#define MyAppURL ""
#define MyAppExeName "YHWH.exe"

; Version: prefer /DMyAppVersion= from build_msi.cmd (first line of VERSION,
; matching build_dmg.sh). Fall back to reading VERSION when ISCC is invoked
; directly — still first line only (FileRead reads one line per call).
#ifndef MyAppVersion
  #define VersionFile "..\VERSION"
  #ifexist VersionFile
    #define MyAppVersion Trim(FileRead(FileOpen(VersionFile)))
  #else
    #define MyAppVersion "dev"
  #endif
#endif

[Setup]
AppId={{C7B9E4A1-2D8E-413B-B3D9-977F4505FC22}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=YHWH-{#MyAppVersion}-windows-x64
SolidCompression=yes
WizardStyle=modern
Compression=lzma2
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; SignTool=signtool   ; uncomment + configure in IDE to sign the installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
