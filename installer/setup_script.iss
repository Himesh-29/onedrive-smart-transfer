; Inno Setup Script for OneDrive Smart Transfer
; This creates a professional Windows installer from the PyInstaller output.
;
; Prerequisites:
;   1. Build the app first: python build_exe.py
;   2. Install Inno Setup: https://jrsoftware.org/isdl.php
;   3. Open this .iss file in Inno Setup Compiler and click Build.
;
; The installer will:
;   - Ask user for install location
;   - Create Start Menu shortcuts
;   - Create Desktop shortcut (optional)
;   - Register an uninstaller in Add/Remove Programs
;   - Run as standard user (NO admin privileges required)

[Setup]
AppName=OneDrive Smart Transfer
AppVersion=1.0.0
AppPublisher=Open Source Community
AppPublisherURL=https://github.com/Himesh-29/onedrive-smart-transfer
DefaultDirName={autopf}\OneDrive Smart Transfer
DefaultGroupName=OneDrive Smart Transfer
OutputBaseFilename=OneDriveSmartTransfer_Setup_1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
OutputDir=installer\output
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\OneDriveSmartTransfer.exe
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; Bundle the entire PyInstaller output directory
Source: "dist\OneDriveSmartTransfer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OneDrive Smart Transfer"; Filename: "{app}\OneDriveSmartTransfer.exe"
Name: "{group}\Uninstall OneDrive Smart Transfer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OneDrive Smart Transfer"; Filename: "{app}\OneDriveSmartTransfer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OneDriveSmartTransfer.exe"; Description: "Launch OneDrive Smart Transfer"; Flags: nowait postinstall skipifsilent
