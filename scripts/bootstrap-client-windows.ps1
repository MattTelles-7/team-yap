$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
  throw 'This bootstrap is for Windows only.'
}

$repoZipUrl = if ($env:TEAM_YAP_REPO_ZIP_URL) { $env:TEAM_YAP_REPO_ZIP_URL } else { 'https://github.com/MattTelles-7/team-yap/archive/refs/heads/main.zip' }
$workDir = if ($env:TEAM_YAP_WORKDIR) { $env:TEAM_YAP_WORKDIR } else { Join-Path $HOME 'team-yap-client' }
$serverUrl = if ($env:TEAM_YAP_SERVER_URL) { $env:TEAM_YAP_SERVER_URL } else { 'http://127.0.0.1:8080' }
$cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
$cargoExe = Join-Path $cargoBin 'cargo.exe'
$rustupExe = Join-Path $cargoBin 'rustup.exe'

if ($workDir -ne (Join-Path $HOME 'team-yap-client') -and $env:TEAM_YAP_ALLOW_CUSTOM_WORKDIR -ne '1') {
  throw 'Refusing to use a custom TEAM_YAP_WORKDIR unless TEAM_YAP_ALLOW_CUSTOM_WORKDIR=1 is set.'
}

if ([string]::IsNullOrWhiteSpace($workDir) -or $workDir -eq $HOME -or $workDir -eq [System.IO.Path]::GetPathRoot($HOME)) {
  throw "TEAM_YAP_WORKDIR resolved to an unsafe location: $workDir"
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  throw 'winget is required on Windows for this bootstrap.'
}

function Ensure-WingetPackage {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Id,

    [string]$Override = ''
  )

  $arguments = @(
    'install'
    '--id', $Id
    '--silent'
    '--accept-package-agreements'
    '--accept-source-agreements'
  )

  if ($Override) {
    $arguments += @('--override', $Override)
  }

  & winget @arguments
  if ($LASTEXITCODE -ne 0) {
    throw "winget failed while installing $Id."
  }
}

if (-not (Test-Path (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\EdgeWebView\Application'))) {
  Ensure-WingetPackage -Id 'Microsoft.EdgeWebView2Runtime'
}

if (-not (Test-Path $rustupExe) -or -not (Test-Path $cargoExe)) {
  Ensure-WingetPackage -Id 'Rustlang.Rustup'
}

$vs2022Root = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\2022'
$hasVisualStudioToolchain = Test-Path $vs2022Root
if (-not $hasVisualStudioToolchain) {
  Ensure-WingetPackage -Id 'Microsoft.VisualStudio.2022.BuildTools' -Override '--quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'
}

if (-not (Test-Path $rustupExe)) {
  throw "rustup.exe was not found at $rustupExe after installation."
}

if (-not (Test-Path $cargoExe)) {
  throw "cargo.exe was not found at $cargoExe after installation."
}

& $rustupExe default stable-msvc
if ($LASTEXITCODE -ne 0) {
  throw 'rustup failed while selecting the stable-msvc toolchain.'
}

& $cargoExe tauri -V | Out-Null
if ($LASTEXITCODE -ne 0) {
  & $cargoExe install tauri-cli --version '^2.0' --locked
  if ($LASTEXITCODE -ne 0) {
    throw 'cargo failed while installing tauri-cli.'
  }
}

$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("team-yap-" + [System.Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmpDir | Out-Null

try {
  $zipPath = Join-Path $tmpDir 'team-yap.zip'
  $extractPath = Join-Path $tmpDir 'unpacked'

  Invoke-WebRequest -Uri $repoZipUrl -OutFile $zipPath
  Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force

  $sourceDir = Get-ChildItem -Path $extractPath -Directory | Select-Object -First 1
  if (-not $sourceDir) {
    throw 'The Team Yap archive did not contain a top-level folder.'
  }

  New-Item -ItemType Directory -Path $workDir -Force | Out-Null
  Get-ChildItem -Path $workDir -Force | Remove-Item -Recurse -Force
  Copy-Item -Path (Join-Path $sourceDir.FullName '*') -Destination $workDir -Recurse -Force

  $configDir = Join-Path $env:APPDATA 'com.teamyap.desktop'
  New-Item -ItemType Directory -Path $configDir -Force | Out-Null

  @{
    server_url = $serverUrl
    auth_token = $null
    theme = 'dark'
  } | ConvertTo-Json | Set-Content -Path (Join-Path $configDir 'settings.json') -Encoding UTF8

  Set-Location (Join-Path $workDir 'desktop\src-tauri')
  & $cargoExe tauri dev
  if ($LASTEXITCODE -ne 0) {
    throw 'cargo tauri dev exited with a non-zero status.'
  }
}
finally {
  Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}
