#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this bootstrap as root or through sudo." >&2
  exit 1
fi

REPO_URL="${TEAM_YAP_REPO_URL:-https://github.com/MattTelles-7/team-yap.git}"
GIT_REF="${TEAM_YAP_GIT_REF:-main}"
INSTALL_DIR="${TEAM_YAP_INSTALL_DIR:-/opt/team-yap}"
HOST_PORT="${TEAM_YAP_PORT:-8080}"
LOG_LEVEL="${TEAM_YAP_LOG_LEVEL:-INFO}"
SESSION_TTL_HOURS="${TEAM_YAP_SESSION_TTL_HOURS:-720}"
ALLOWED_ORIGINS="${TEAM_YAP_ALLOWED_ORIGINS:-}"
ADMIN_USERNAME="${TEAM_YAP_ADMIN_USERNAME:-admin}"
ADMIN_DISPLAY_NAME="${TEAM_YAP_ADMIN_DISPLAY_NAME:-Team Yap Admin}"
REWRITE_ENV="${TEAM_YAP_REWRITE_ENV:-0}"
ADMIN_PASSWORD="${TEAM_YAP_ADMIN_PASSWORD:-}"
GENERATED_PASSWORD=0

if [[ -z "$ADMIN_PASSWORD" ]]; then
  ADMIN_PASSWORD="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
  GENERATED_PASSWORD=1
fi

export DEBIAN_FRONTEND=noninteractive

. /etc/os-release

if [[ "${ID:-}" != "debian" ]]; then
  echo "This bootstrap is documented for Debian. Detected ${PRETTY_NAME:-unknown}." >&2
fi

apt-get update
apt-get install -y ca-certificates curl git sqlite3
apt-get remove -y docker.io docker-doc docker-compose podman-docker containerd runc || true

install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker
systemctl restart docker

mkdir -p "$(dirname "$INSTALL_DIR")"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" fetch --depth 1 origin "$GIT_REF"
  git -C "$INSTALL_DIR" checkout -q "$GIT_REF"
  git -C "$INSTALL_DIR" pull --ff-only origin "$GIT_REF"
elif [[ -d "$INSTALL_DIR" && -n "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "$INSTALL_DIR already exists and is not an empty Team Yap checkout." >&2
  exit 1
else
  git clone --branch "$GIT_REF" --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
mkdir -p data backups

if [[ ! -f .env || "$REWRITE_ENV" == "1" ]]; then
  cat >.env <<EOF
TEAM_YAP_HOST=0.0.0.0
TEAM_YAP_PORT=$HOST_PORT
TEAM_YAP_DATA_DIR=/data
TEAM_YAP_DATABASE_PATH=/data/team-yap.db
TEAM_YAP_LOG_LEVEL=$LOG_LEVEL
TEAM_YAP_SESSION_TTL_HOURS=$SESSION_TTL_HOURS
TEAM_YAP_ALLOWED_ORIGINS=$ALLOWED_ORIGINS
EOF
fi

EFFECTIVE_PORT="$(awk -F= '$1=="TEAM_YAP_PORT" {print $2}' .env | tail -n 1)"
EFFECTIVE_PORT="${EFFECTIVE_PORT:-8080}"

docker compose build
docker compose run --rm server python -m team_yap.manage init-db

ADMIN_COUNT="$(sqlite3 data/team-yap.db "SELECT COUNT(*) FROM users WHERE is_admin = 1;" 2>/dev/null || echo 0)"

if [[ "$ADMIN_COUNT" == "0" ]]; then
  docker compose run --rm server python -m team_yap.manage bootstrap-admin \
    --username "$ADMIN_USERNAME" \
    --display-name "$ADMIN_DISPLAY_NAME" \
    --password "$ADMIN_PASSWORD"
fi

docker compose up -d

HEALTH_OK=0
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${EFFECTIVE_PORT}/healthz" >/dev/null; then
    HEALTH_OK=1
    break
  fi
  sleep 2
done

if [[ "$HEALTH_OK" != "1" ]]; then
  docker compose logs --tail=100 server >&2
  echo "Team Yap did not pass the health check on port ${EFFECTIVE_PORT}." >&2
  exit 1
fi

echo
echo "Team Yap server is running."
echo "Install directory: $INSTALL_DIR"
echo "Server health URL: http://127.0.0.1:${EFFECTIVE_PORT}/healthz"
echo "Cloudflare forward target: http://127.0.0.1:${EFFECTIVE_PORT}"

if [[ "$ADMIN_COUNT" == "0" ]]; then
  echo "Admin username: $ADMIN_USERNAME"
  echo "Admin display name: $ADMIN_DISPLAY_NAME"
  echo "Admin password: $ADMIN_PASSWORD"
  if [[ "$GENERATED_PASSWORD" == "1" ]]; then
    echo "The admin password was generated automatically because TEAM_YAP_ADMIN_PASSWORD was not set."
  fi
else
  echo "An admin account already existed, so bootstrap-admin was skipped."
fi

