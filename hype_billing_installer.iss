; ===========================================================================
; Hype ERP v3.0.0 - Inno Setup Script
; Developer: David | Nexuzy Lab
; Website: https://github.com/david0154/hype-billing-system
; Build with Inno Setup 6.x: https://jrsoftware.org/isinfo.php
; ===========================================================================

[Setup]
AppName=Hype ERP
AppVersion=3.0.0
AppVerName=Hype ERP v3.0.0
AppPublisher=Nexuzy Lab
AppPublisherURL=https://github.com/david0154
AppSupportURL=https://github.com/david0154/hype-billing-system/issues
AppUpdatesURL=https://github.com/david0154/hype-billing-system/releases
AppCopyright=Copyright (C) 2025-2026 Nexuzy Lab. Lead Developer: David
DefaultDirName={autopf}\HypeERP
DefaultGroupName=Hype ERP
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=HypeERP_Setup_v3.0.0
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\HypeERP.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
MinVersion=6.1sp1
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=auto
LicenseFile=LICENSE
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=no

; App data directory (writable, no admin needed)
[Dirs]
Name: "{localappdata}\HypeERP"
Name: "{localappdata}\HypeERP\models"
Name: "{localappdata}\HypeERP\backups"
Name: "{localappdata}\HypeERP\exports"
Name: "{localappdata}\HypeERP\logs"

[Files]
; Main EXE
Source: "dist\HypeERP.exe"; DestDir: "{app}"; Flags: ignoreversion

; Firebase encrypted key (required for cloud sync)
Source: "serviceAccountKey.enc"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Assets
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "SETUP.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu
Name: "{group}\Hype ERP"; Filename: "{app}\HypeERP.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall Hype ERP"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\Hype ERP"; Filename: "{app}\HypeERP.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Launch app after install
Filename: "{app}\HypeERP.exe"; Description: "Launch Hype ERP now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up local data on uninstall (optional - ask user)
Type: dirifempty; Name: "{localappdata}\HypeERP\models"
Type: dirifempty; Name: "{localappdata}\HypeERP\backups"
Type: dirifempty; Name: "{localappdata}\HypeERP\exports"
Type: dirifempty; Name: "{localappdata}\HypeERP\logs"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nDeveloped by David | Nexuzy Lab%n%nHype ERP is a complete offline-first GST billing and ERP system with 19 enterprise modules, AI features, and Firebase cloud sync.%n%nIt is recommended that you close all other applications before continuing.
FinishedLabel=Hype ERP v3.0.0 has been installed successfully!%n%nDefault Login: admin / admin123%nChange your password after first login.%n%nDeveloped by David | Nexuzy Lab

[Code]
// Check if .NET / VC++ Redistributable is present (optional check)
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Create data directory
    DataDir := ExpandConstant('{localappdata}\HypeERP');
    if not DirExists(DataDir) then
      CreateDir(DataDir);
  end;
end;
