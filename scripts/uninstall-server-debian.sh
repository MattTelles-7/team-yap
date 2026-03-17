#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this uninstall script as root or through sudo." >&2
  exit 1
fi

INSTALL_DIR="${TEAM_YAP_INSTALL_DIR:-/opt/team-yap}"

if [[ "$INSTALL_DIR" != "/opt/team-yap" && "${TEAM_YAP_ALLOW_CUSTOM_INSTALL_DIR:-0}" != "1" ]]; then
  echo "Refusing to use a custom TEAM_YAP_INSTALL_DIR unless TEAM_YAP_ALLOW_CUSTOM_INSTALL_DIR=1 is set." >&2
  exit 1
fi

if [[ "$INSTALL_DIR" == "/" || -z "$INSTALL_DIR" ]]; then
  echo "TEAM_YAP_INSTALL_DIR resolved to an unsafe location: $INSTALL_DIR" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1 && [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/docker-compose.yml" ]]; then
  (
    cd "$INSTALL_DIR"
    docker compose down --remove-orphans --rmi local || true
  )
fi

systemctl stop docker >/dev/null 2>&1 || true
systemctl disable docker >/dev/null 2>&1 || true

rm -rf "$INSTALL_DIR" /var/lib/docker /var/lib/containerd /etc/docker /etc/containerd
apt-get remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git sqlite3 || true
apt-get autoremove -y || true
rm -f /etc/apt/keyrings/docker.asc /etc/apt/sources.list.d/docker.list
apt-get update || true

echo "Removed Team Yap server files, Docker packages and data, git, sqlite3, and the Docker apt source."

