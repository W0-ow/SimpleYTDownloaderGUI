#ifndef AppVersion
  #error AppVersion is required
#endif
[Setup]
AppId={{8A31A064-D589-44EA-B5DD-146117227D02}
AppName=Super YT Downloader
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\SuperYTDownloader
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputDir=..\dist
OutputBaseFilename=SuperYTDownloader-Setup
SetupIconFile=..\build\app.ico
UninstallDisplayIcon={app}\SuperYTDownloader.exe
Compression=lzma2
SolidCompression=yes
CloseApplications=no
RestartApplications=no
WizardStyle=modern
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Files]
Source: "..\dist\SuperYTDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{userprograms}\Super YT Downloader"; Filename: "{app}\SuperYTDownloader.exe"
Name: "{userdesktop}\Super YT Downloader"; Filename: "{app}\SuperYTDownloader.exe"
[Run]
Filename: "{app}\SuperYTDownloader.exe"; Description: "Abrir Super YT Downloader"; Flags: nowait postinstall skipifsilent
