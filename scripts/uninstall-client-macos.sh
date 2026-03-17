#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This uninstall script is for macOS only." >&2
  exit 1
fi

WORKDIR="${TEAM_YAP_WORKDIR:-$HOME/team-yap-client}"
CONFIG_DIR="$HOME/Library/Application Support/com.teamyap.desktop"

if [[ "$WORKDIR" != "$HOME/team-yap-client" && "${TEAM_YAP_ALLOW_CUSTOM_WORKDIR:-0}" != "1" ]]; then
  echo "Refusing to use a custom TEAM_YAP_WORKDIR unless TEAM_YAP_ALLOW_CUSTOM_WORKDIR=1 is set." >&2
  exit 1
fi

if [[ "$WORKDIR" == "/" || "$WORKDIR" == "$HOME" || -z "$WORKDIR" ]]; then
  echo "TEAM_YAP_WORKDIR resolved to an unsafe location: $WORKDIR" >&2
  exit 1
fi

pkill -f "cargo tauri dev" >/dev/null 2>&1 || true

if [[ -x "$HOME/.cargo/bin/rustup" ]]; then
  "$HOME/.cargo/bin/rustup" self uninstall -y >/dev/null 2>&1 || true
fi

rm -rf "$HOME/.cargo" "$HOME/.rustup" "$WORKDIR" "$CONFIG_DIR"

echo "Removed Team Yap macOS bootstrap assets, settings, Rust toolchains, and the local checkout."

