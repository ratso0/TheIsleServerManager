; ============================================================
;  The Isle Server Manager - Inno Setup Installer Script
;  Skapar en professionell Setup.exe för Windows
; ============================================================

#define AppName      "The Isle Server Manager"
#define AppVersion   "1.0.0"
#define AppPublisher "The Isle Server Manager"
#define AppExeName   "TheIsleServerManager.exe"
#define AppURL       ""

[Setup]
AppId={{A3F7E2B1-4C8D-4E9F-B2A1-7D3C5E8F9A0B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=no
LicenseFile=
OutputDir=Output
OutputBaseFilename=TheIsleServerManager_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Installer
VersionInfoCompany={#AppPublisher}

; Snyggt utseende
WizardImageFile=assets\wizard_banner.bmp
WizardSmallImageFile=assets\wizard_icon.bmp

[Languages]
Name: "swedish";  MessagesFile: "compiler:Languages\Swedish.isl"
Name: "english";  MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Skapa genväg på skrivbordet"; \
    GroupDescription: "Genvägar:"; Flags: checkedonce
Name: "startmenuicon";  Description: "Skapa genväg i startmenyn"; \
    GroupDescription: "Genvägar:"; Flags: checkedonce

[Files]
; Huvud-exe (byggd av PyInstaller)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Startmeny
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExeName}"
Name: "{group}\Avinstallera";      Filename: "{uninstallexe}"

; Skrivbord
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

[Run]
; Starta programmet direkt efter installation
Filename: "{app}\{#AppExeName}"; \
    Description: "Starta {#AppName} nu"; \
    Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Messages]
; Svenska anpassade meddelanden
WelcomeLabel1=Välkommen till installationen av [name]
WelcomeLabel2=Detta kommer att installera [name/ver] på din dator.%n%nRekommenderas att stänga alla öppna program innan du fortsätter.%n%nKlicka på Nästa för att fortsätta.
FinishedLabel=Installationen av [name] är klar.%n%nProgrammet installerades som ett vanligt Windows-program och har en genväg på skrivbordet.
