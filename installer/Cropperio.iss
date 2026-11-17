#define AppName "Cropperio"
#define AppPublisher "Cropperio"
#define AppExeName "Cropperio.exe"

#ifndef AppVersion
  #error AppVersion must be supplied by build.ps1 using /DAppVersion=x.y.z
#endif

[Setup]
AppId={{76F69A08-DC5C-43EE-A5CD-3130BBF7EF5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Cropperio_Setup
SetupIconFile=..\assets\cropperio.ico
UninstallDisplayIcon={app}\{#AppExeName}
LicenseFile=..\LICENSE
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl,JapaneseOverrides.isl"
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl,ChineseOverrides.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
english.DesktopShortcut=Create a desktop shortcut
english.AdditionalShortcuts=Additional shortcuts:
english.LaunchApp=Launch {#AppName}
french.DesktopShortcut=Créer un raccourci sur le Bureau
french.AdditionalShortcuts=Raccourcis supplémentaires :
french.LaunchApp=Lancer {#AppName}
japanese.DesktopShortcut=デスクトップにショートカットを作成する
japanese.AdditionalShortcuts=追加のショートカット：
japanese.LaunchApp={#AppName} を起動する
chinesesimplified.DesktopShortcut=创建桌面快捷方式
chinesesimplified.AdditionalShortcuts=附加快捷方式：
chinesesimplified.LaunchApp=启动 {#AppName}
russian.DesktopShortcut=Создать ярлык на рабочем столе
russian.AdditionalShortcuts=Дополнительные ярлыки:
russian.LaunchApp=Запустить {#AppName}
german.DesktopShortcut=Desktop-Verknüpfung erstellen
german.AdditionalShortcuts=Zusätzliche Verknüpfungen:
german.LaunchApp={#AppName} starten

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; GroupDescription: "{cm:AdditionalShortcuts}"; Flags: unchecked

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\papagori\Cropperio"; ValueType: string; ValueName: "language"; ValueData: "{code:InitialLanguage}"; Flags: createvalueifdoesntexist uninsdeletevalue

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[Code]
function PreferredJapaneseFont: String;
begin
  if FontExists('Yu Gothic UI') then
    Result := 'Yu Gothic UI'
  else if FontExists('Meiryo UI') then
    Result := 'Meiryo UI'
  else if FontExists('MS UI Gothic') then
    Result := 'MS UI Gothic'
  else
    Result := 'Segoe UI';
end;

function PreferredChineseFont: String;
begin
  if FontExists('Microsoft YaHei UI') then
    Result := 'Microsoft YaHei UI'
  else if FontExists('Microsoft YaHei') then
    Result := 'Microsoft YaHei'
  else if FontExists('SimSun') then
    Result := 'SimSun'
  else
    Result := 'Segoe UI';
end;

procedure InitializeWizard;
var
  WizardFont: String;
begin
  if (ActiveLanguage = 'japanese') or (ActiveLanguage = 'chinesesimplified') then
  begin
    if ActiveLanguage = 'japanese' then
      WizardFont := PreferredJapaneseFont
    else
      WizardFont := PreferredChineseFont;
    WizardForm.Font.Name := WizardFont;
    WizardForm.WelcomeLabel1.Font.Name := WizardFont;
    WizardForm.WelcomeLabel2.Font.Name := WizardFont;
    WizardForm.PageNameLabel.Font.Name := WizardFont;
    WizardForm.PageDescriptionLabel.Font.Name := WizardFont;
  end;
end;

function InitialLanguage(Param: String): String;
begin
  if ActiveLanguage = 'japanese' then
    Result := 'ja'
  else if ActiveLanguage = 'french' then
    Result := 'fr'
  else if ActiveLanguage = 'chinesesimplified' then
    Result := 'zh-CN'
  else if ActiveLanguage = 'russian' then
    Result := 'ru-RU'
  else if ActiveLanguage = 'german' then
    Result := 'de-DE'
  else
    Result := 'en';
end;
