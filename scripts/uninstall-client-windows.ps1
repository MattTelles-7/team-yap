$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
  throw 'This uninstall script is for Windows only.'
}

$workDir = if ($env:TEAM_YAP_WORKDIR) { $env:TEAM_YAP_WORKDIR } else { Join-Path $HOME 'team-yap-client' }
$settingsDir = Join-Path $env:APPDATA 'com.teamyap.desktop'
$cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
$rustupExe = Join-Path $cargoBin 'rustup.exe'

if ($workDir -ne (Join-Path $HOME 'team-yap-client') -and $env:TEAM_YAP_ALLOW_CUSTOM_WORKDIR -ne '1') {
  throw 'Refusing to use a custom TEAM_YAP_WORKDIR unless TEAM_YAP_ALLOW_CUSTOM_WORKDIR=1 is set.'
}

if ([string]::IsNullOrWhiteSpace($workDir) -or $workDir -eq $HOME -or $workDir -eq [System.IO.Path]::GetPathRoot($HOME)) {
  throw "TEAM_YAP_WORKDIR resolved to an unsafe location: $workDir"
}

Get-Process cargo-tauri -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

if (Test-Path $rustupExe) {
  & $rustupExe self uninstall -y
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
  foreach ($packageId in @('Rustlang.Rustup', 'Microsoft.VisualStudio.2022.BuildTools', 'Microsoft.EdgeWebView2Runtime')) {
    & winget uninstall --id $packageId --silent --accept-source-agreements | Out-Null
  }
}

Remove-Item -Path $workDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $settingsDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path $env:USERPROFILE '.cargo') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path $env:USERPROFILE '.rustup') -Recurse -Force -ErrorAction SilentlyContinue

Write-Host 'Removed Team Yap Windows bootstrap assets, settings, Rust toolchains, and the local checkout.'

