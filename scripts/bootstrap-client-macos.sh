#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This bootstrap is for macOS only." >&2
  exit 1
fi

REPO_ZIP_URL="${TEAM_YAP_REPO_ZIP_URL:-https://github.com/MattTelles-7/team-yap/archive/refs/heads/main.zip}"
WORKDIR="${TEAM_YAP_WORKDIR:-$HOME/team-yap-client}"
SERVER_URL="${TEAM_YAP_SERVER_URL:-http://127.0.0.1:8080}"

if [[ "$WORKDIR" != "$HOME/team-yap-client" && "${TEAM_YAP_ALLOW_CUSTOM_WORKDIR:-0}" != "1" ]]; then
  echo "Refusing to use a custom TEAM_YAP_WORKDIR unless TEAM_YAP_ALLOW_CUSTOM_WORKDIR=1 is set." >&2
  exit 1
fi

if [[ "$WORKDIR" == "/" || "$WORKDIR" == "$HOME" || -z "$WORKDIR" ]]; then
  echo "TEAM_YAP_WORKDIR resolved to an unsafe location: $WORKDIR" >&2
  exit 1
fi

if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install || true
  echo "macOS Command Line Tools are required. The installer has been triggered. Rerun the same command after it finishes." >&2
  exit 1
fi

if [[ ! -x "$HOME/.cargo/bin/cargo" ]]; then
  curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs | sh -s -- -y
fi

export PATH="$HOME/.cargo/bin:$PATH"

if ! cargo tauri -V >/dev/null 2>&1; then
  cargo install tauri-cli --version '^2.0' --locked
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

curl -fsSL "$REPO_ZIP_URL" -o "$TMPDIR/team-yap.zip"
mkdir -p "$TMPDIR/unpacked"
ditto -x -k "$TMPDIR/team-yap.zip" "$TMPDIR/unpacked"
SOURCE_DIR="$(find "$TMPDIR/unpacked" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

mkdir -p "$WORKDIR"
find "$WORKDIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -R "$SOURCE_DIR"/. "$WORKDIR"/

CONFIG_DIR="$HOME/Library/Application Support/com.teamyap.desktop"
mkdir -p "$CONFIG_DIR"
cat >"$CONFIG_DIR/settings.json" <<EOF
{
  "server_url": "$SERVER_URL",
  "auth_token": null
}
EOF

cd "$WORKDIR/desktop/src-tauri"
exec cargo tauri dev
