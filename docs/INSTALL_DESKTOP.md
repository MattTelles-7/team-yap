# Desktop Install And Build Guide

This guide covers:

- local development on macOS and Windows
- production desktop builds on macOS and Windows
- end-user installation of the packaged app
- settings file locations
- common desktop-side errors

The desktop client lives in `desktop/src-tauri` and talks to the Team Yap server over HTTP. Node.js is not required for this repo because the frontend is static.

## One-Line Client Startup

These are the fastest source-based client startup commands.

They:

- download the repo into a local bootstrap folder
- install the required local toolchain
- write the desktop `settings.json` with the server URL you choose
- launch the app with `cargo tauri dev`

### macOS One-Liner

Paste this into Terminal:

```bash
TEAM_YAP_SERVER_URL="https://yap.example.com" bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-macos.sh)"
```

What it uses:

- work directory: `~/team-yap-client`
- settings file: `~/Library/Application Support/com.teamyap.desktop/settings.json`

Important macOS caveat:

- if Xcode Command Line Tools are not installed yet, the script triggers the Apple installer and exits
- after the Apple installer finishes, rerun the exact same one-liner once

If your server is local instead of remote, use:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-macos.sh)"
```

### Windows One-Liner

Paste this into PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "$env:TEAM_YAP_SERVER_URL='https://yap.example.com'; irm https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-windows.ps1 | iex"
```

What it uses:

- work directory: `%USERPROFILE%\team-yap-client`
- settings file: `%APPDATA%\com.teamyap.desktop\settings.json`

If your server is local instead of remote, use:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-windows.ps1 | iex"
```

Important Windows caveats:

- the first run installs Rust, WebView2, and Visual Studio Build Tools if they are missing
- Visual Studio Build Tools installation can take several minutes
- you may see UAC prompts during the bootstrap

## What The Desktop App Does

The packaged desktop app:

- stores the server URL locally
- stores the current bearer token locally
- lets a user sign in
- lets a user refresh the team feed
- lets a user post a message

The settings file is named `settings.json`.

## macOS

### Prerequisites

If you want the shortest path, use the one-line command above.

Install the macOS dependencies first:

1. Install Xcode Command Line Tools:

```bash
xcode-select --install
```

2. Install Rust with `rustup`:

```bash
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
```

3. Restart your terminal and verify Rust:

```bash
rustc -V
cargo -V
```

4. Install the Tauri CLI:

```bash
cargo install tauri-cli --version '^2.0' --locked
```

5. Verify Python 3 is available for the server:

```bash
python3 --version
```

### Run In Development On macOS

Fastest path:

```bash
TEAM_YAP_SERVER_URL="https://yap.example.com" bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-macos.sh)"
```

Manual path:

Open Terminal in the repo root and start the server:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
export PYTHONPATH="$PWD/backend"
export TEAM_YAP_DATA_DIR="$PWD/data"
export TEAM_YAP_DATABASE_PATH="$PWD/data/team-yap.db"
export TEAM_YAP_HOST="127.0.0.1"
export TEAM_YAP_PORT="8080"
python -m team_yap.manage init-db
python -m team_yap.manage bootstrap-admin --username admin --display-name "Admin" --prompt-password
python -m team_yap.runserver
```

Leave that terminal running. Open a second terminal in the repo root and start the desktop app:

```bash
cd desktop/src-tauri
cargo tauri dev
```

Expected result:

- the desktop window opens
- the server URL field is prefilled with `http://127.0.0.1:8080`
- you can sign in with the admin account you just created

### Build A Production macOS App

Run this on a Mac:

```bash
cd desktop/src-tauri
cargo tauri build
```

Expected build outputs:

- app bundle: `desktop/src-tauri/target/release/bundle/macos/Team Yap.app`
- disk image: `desktop/src-tauri/target/release/bundle/dmg/*.dmg`

The exact DMG filename includes the version and architecture. Example:

- `Team Yap_0.1.0_aarch64.dmg`
- `Team Yap_0.1.0_x64.dmg`

### How A Normal User Installs On macOS

Use the `.dmg` file from `desktop/src-tauri/target/release/bundle/dmg/`.

1. Double-click the `.dmg`.
2. In the installer window, drag `Team Yap.app` into `Applications`.
3. Eject the mounted DMG.
4. Open `Applications` and launch `Team Yap`.

Because signing and notarization are not configured in this repo, macOS may block first launch. If that happens:

1. Right-click `Team Yap.app`.
2. Click `Open`.
3. Confirm the warning dialog.

If macOS still blocks it:

1. Open `System Settings`.
2. Go to `Privacy & Security`.
3. Use `Open Anyway` for the Team Yap app.

### macOS Settings Location

The desktop app writes settings to:

```text
~/Library/Application Support/com.teamyap.desktop/settings.json
```

That file stores:

- `server_url`
- `auth_token`

## Windows

### Prerequisites

If you want the shortest path, use the one-line command above.

Install the Windows dependencies first:

1. Install Microsoft C++ Build Tools and enable `Desktop development with C++`.
2. Ensure Microsoft Edge WebView2 Runtime is installed.
   On current Windows 10 and Windows 11 builds it is usually already present.
3. If you want MSI output, ensure the `VBSCRIPT` Windows feature is enabled.
   If MSI builds fail with `failed to run light.exe`, enable it in:
   `Settings -> Apps -> Optional features -> More Windows features`
4. Install Rust with `rustup`.
   PowerShell option:

```powershell
winget install --id Rustlang.Rustup
rustup default stable-msvc
```

5. Restart PowerShell and verify Rust:

```powershell
rustc -V
cargo -V
```

6. Install the Tauri CLI:

```powershell
cargo install tauri-cli --version '^2.0' --locked
```

7. Verify Python 3 is available:

```powershell
py -3 --version
```

### Run In Development On Windows

Fastest path:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "$env:TEAM_YAP_SERVER_URL='https://yap.example.com'; irm https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-client-windows.ps1 | iex"
```

Manual path:

Open PowerShell in the repo root and start the server:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
$env:TEAM_YAP_DATA_DIR = (Join-Path (Get-Location) 'data')
$env:TEAM_YAP_DATABASE_PATH = (Join-Path $env:TEAM_YAP_DATA_DIR 'team-yap.db')
$env:TEAM_YAP_HOST = '127.0.0.1'
$env:TEAM_YAP_PORT = '8080'
python -m team_yap.manage init-db
python -m team_yap.manage bootstrap-admin --username admin --display-name 'Admin' --prompt-password
python -m team_yap.runserver
```

Leave that PowerShell window running. Open a second PowerShell window and start the desktop app:

```powershell
Set-Location desktop/src-tauri
cargo tauri dev
```

### Build A Production Windows App

Run this on a Windows machine:

```powershell
Set-Location desktop/src-tauri
cargo tauri build
```

Expected build outputs:

- NSIS installer: `desktop/src-tauri/target/release/bundle/nsis/*-setup.exe`
- MSI installer: `desktop/src-tauri/target/release/bundle/msi/*.msi`

Typical filenames look like:

- `Team Yap_0.1.0_x64-setup.exe`
- `Team Yap_0.1.0_x64_en-US.msi`

The NSIS `.exe` is the simpler end-user installer. The `.msi` is also produced because `tauri.conf.json` uses `bundle.targets = "all"`.

### How A Normal User Installs On Windows

Preferred path:

1. Give the user the NSIS setup `.exe` from `desktop/src-tauri/target/release/bundle/nsis/`.
2. Double-click the installer.
3. If SmartScreen appears, click `More info` and then `Run anyway`.
4. Complete the installer.
5. Launch `Team Yap` from the Start menu or desktop shortcut.

Alternative path:

1. Run the `.msi` from `desktop/src-tauri/target/release/bundle/msi/`.
2. Complete the Windows Installer wizard.

### Windows Settings Location

The desktop app writes settings to:

```text
%APPDATA%\com.teamyap.desktop\settings.json
```

For a typical user that resolves to something like:

```text
C:\Users\<username>\AppData\Roaming\com.teamyap.desktop\settings.json
```

That file stores:

- `server_url`
- `auth_token`

## Point The Client At A Server URL

The desktop app exposes the server URL in the top `Connection` panel.

To change it:

1. Open the desktop app.
2. Enter the full server URL, for example `https://yap.example.com`.
3. Click `Save server URL`.
4. Sign in again.

Important behavior:

- saving a new server URL clears the saved session token
- the app expects `http://` or `https://`
- the app trims a trailing `/`

## Common Errors And Fixes

### `The Tauri API is unavailable`

Cause:

- you opened `desktop/app/index.html` directly in a browser instead of running Tauri

Fix:

- use `cargo tauri dev` for development
- or install the packaged desktop app

### `Could not reach the server`

Cause:

- the Team Yap server is not running
- the server URL is wrong
- DNS or TLS is failing

Fix:

1. Verify the server with `curl http://127.0.0.1:8080/healthz` for local development.
2. Re-check the saved server URL in the app.
3. If using a public URL, verify the Cloudflare Tunnel or reverse proxy is healthy.

### `Login failed`

Cause:

- wrong username or password
- account was never created on the server

Fix:

- create the first admin with `python -m team_yap.manage bootstrap-admin ...`
- create additional users with `python -m team_yap.manage create-user ...`
- reset a password with `python -m team_yap.manage reset-password ...`

### macOS says the app is damaged or cannot be opened

Cause:

- the app is unsigned and not notarized

Fix:

- right-click the app and use `Open`
- or allow it from `System Settings -> Privacy & Security`

### Windows build fails with `failed to run light.exe`

Cause:

- the `VBSCRIPT` Windows feature is disabled

Fix:

- enable `VBSCRIPT` in Windows Features
- reboot if Windows prompts for it
- rerun `cargo tauri build`

### Windows app opens but renders a blank or broken window

Cause:

- WebView2 runtime is missing or corrupted

Fix:

- install or repair Microsoft Edge WebView2 Runtime

### `cargo tauri build` fails immediately on macOS

Cause:

- Xcode Command Line Tools were not installed or not initialized

Fix:

```bash
xcode-select --install
```

If you installed full Xcode, open it once so it can finish its first-run setup.
