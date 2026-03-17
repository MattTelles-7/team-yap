# Proxmox Deployment Guide

This guide documents the recommended production path for Team Yap on a Proxmox-hosted machine.

## One-Line Debian Bootstrap

On a fresh Debian VM, paste this one line as `root` or through `sudo`:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-server-debian.sh)"
```

That command:

- installs Docker Engine and Docker Compose
- clones the repo into `/opt/team-yap`
- creates `/opt/team-yap/data` and `/opt/team-yap/backups`
- writes `/opt/team-yap/.env`
- initializes the SQLite database
- creates the first admin if one does not already exist
- starts the Team Yap server
- prints the health URL and the initial admin password if it had to generate one

Important:

- the raw GitHub one-liner only reflects the contents already pushed to `main`
- if you changed the bootstrap or uninstall scripts locally but have not pushed them yet, run the local script from your checkout instead of the raw GitHub URL

Optional custom admin password example:

```bash
sudo TEAM_YAP_ADMIN_PASSWORD='ChangeThisNow123' bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-server-debian.sh)"
```

Optional custom published port example:

```bash
sudo TEAM_YAP_PORT='8090' bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/bootstrap-server-debian.sh)"
```

## One-Line Debian Uninstall

This command is intentionally destructive.

It removes:

- `/opt/team-yap`
- Team Yap data and backups under that directory
- Docker containers, images, and runtime data under `/var/lib/docker` and `/var/lib/containerd`
- the Docker packages installed by the Team Yap bootstrap
- `git` and `sqlite3` if they were installed only for this deployment

Use it only on a Debian VM that was dedicated to Team Yap.

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/MattTelles-7/team-yap/main/scripts/uninstall-server-debian.sh)"
```

## Recommended Deployment Target

Use a small Debian VM on Proxmox, not an LXC container.

Why the VM path is recommended:

- Docker Engine is simpler and more predictable inside a full VM
- you avoid nested-container edge cases around AppArmor, cgroups, overlay filesystems, and Docker socket behavior
- backup and restore are easier to reason about for a small private service

An LXC can work, but this repo is documented and validated for a VM with Docker Engine and Docker Compose.

## Suggested VM Sizing

For a small private deployment:

- minimum: 1 vCPU, 2 GB RAM, 20 GB disk
- recommended: 2 vCPU, 4 GB RAM, 20 GB disk

The app is lightweight. Disk usage is mostly:

- the Git checkout
- Docker image layers
- the SQLite database and backups

## Operating System Recommendation

Use:

- Debian 12 Bookworm

This guide assumes Debian 12 throughout.

## Network And Port Model

The Team Yap server:

- listens on internal HTTP port `8080`
- does not require websockets in the current build
- does not use cookies for auth
- uses bearer tokens from the desktop client

Cloudflare Tunnel should forward to:

- `http://127.0.0.1:8080` if the tunnel daemon runs on the same VM
- or `http://<vm-lan-ip>:8080` if the tunnel runs elsewhere on your network

Current server-side caveats:

- no voice transport exists in this build
- no websocket support is required for the desktop app
- CORS is only needed if you later add a browser-based client
- if you do add a browser client, set `TEAM_YAP_ALLOWED_ORIGINS` to that browser origin

## 1. Create The VM In Proxmox

Create a new VM with:

- Debian 12 ISO
- VirtIO disk and NIC if that is already your Proxmox standard
- the sizing listed above
- a static DHCP reservation or static IP you can rely on

Finish the Debian install and confirm you can SSH into the VM.

## 2. Install Base Packages

SSH into the VM and install the base tools:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git sqlite3
```

`sqlite3` is included here because the operational procedures below use it for backups and read-only inspection.

## 3. Install Docker Engine And Docker Compose

This follows Docker’s official Debian repository flow.

Remove conflicting packages if this VM already had older Docker packages:

```bash
sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc || true
```

Add Docker’s repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
```

Install Docker Engine and the Compose plugin:

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Enable Docker at boot and verify it:

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker --no-pager
sudo docker run --rm hello-world
```

## 4. Put The Repo On The VM

Create the deployment directory:

```bash
sudo mkdir -p /opt/team-yap
sudo chown "$USER":"$USER" /opt/team-yap
```

Clone the repo:

```bash
git clone https://github.com/MattTelles-7/team-yap.git /opt/team-yap
cd /opt/team-yap
```

If the VM cannot pull from GitHub directly, copy the repo from your workstation instead:

```bash
scp -r /path/to/local/team-yap/. user@vm-ip:/opt/team-yap/
```

## 5. Create The Runtime Directories

Create the data and backup directories:

```bash
cd /opt/team-yap
mkdir -p data backups
```

## 6. Configure Environment Variables

Copy the sample environment file:

```bash
cp .env.example .env
```

Edit `.env` and set these values:

```dotenv
TEAM_YAP_HOST=0.0.0.0
TEAM_YAP_PORT=8080
TEAM_YAP_DATA_DIR=/data
TEAM_YAP_DATABASE_PATH=/data/team-yap.db
TEAM_YAP_LOG_LEVEL=INFO
TEAM_YAP_SESSION_TTL_HOURS=720
TEAM_YAP_ALLOWED_ORIGINS=
```

Notes:

- keep `TEAM_YAP_DATA_DIR=/data` and `TEAM_YAP_DATABASE_PATH=/data/team-yap.db` when using the provided `docker-compose.yml`
- leave `TEAM_YAP_ALLOWED_ORIGINS` empty if only the Tauri desktop app is talking to the server
- if you add a browser client later, set `TEAM_YAP_ALLOWED_ORIGINS` to a comma-separated list of allowed browser origins

## 7. Build The Server Image

From `/opt/team-yap`:

```bash
sudo docker compose build
```

## 8. Initialize The Database

Run the idempotent database init command:

```bash
sudo docker compose run --rm server python -m team_yap.manage init-db
```

This creates the SQLite schema in:

```text
/opt/team-yap/data/team-yap.db
```

## 9. Create The First Admin

Create the first admin account before handing the desktop app to users:

```bash
sudo docker compose run --rm server python -m team_yap.manage bootstrap-admin --username admin --display-name "Team Yap Admin" --prompt-password
```

If you run that again after an admin already exists, the command will stop with:

```text
An admin account already exists.
```

## 10. Start The Server Stack

Bring up the stack:

```bash
sudo docker compose up -d
```

Verify that the container is running:

```bash
sudo docker compose ps
```

## 11. Persistence Across Reboots

Persistence comes from two parts already present in this setup:

- Docker is enabled with `systemctl enable docker`
- the `server` service uses `restart: unless-stopped`

That means the Team Yap container restarts automatically after a VM reboot.

You do not need a separate systemd unit for the app.

## 12. Health Checks After Deployment

Run these checks on the VM:

```bash
curl http://127.0.0.1:8080/healthz
```

Expected response:

```json
{"status":"ok"}
```

Check container logs:

```bash
sudo docker compose logs --tail=100 server
```

Check the database summary through the app CLI:

```bash
sudo docker compose run --rm server python -m team_yap.manage db-summary
```

Then test from the desktop client using your public server URL.

## 13. What Cloudflare Tunnel Should Forward To

You said you already know the Cloudflare Tunnel setup, so the only server-side assumption is:

- forward HTTP to `http://127.0.0.1:8080`

No extra proxy features are required for the current build:

- no websocket upgrades
- no sticky cookies
- no special voice relay handling

If you later put a browser-based client on another origin:

- allow that origin in `TEAM_YAP_ALLOWED_ORIGINS`

## 14. Update To A Newer Version

Always back up the database first.

Then update:

```bash
cd /opt/team-yap
sudo sqlite3 /opt/team-yap/data/team-yap.db ".backup '/opt/team-yap/backups/pre-upgrade-$(date +%F-%H%M%S).db'"
git pull --ff-only
```

Review `.env.example` for new variables. If it changed, merge those changes into `.env`.

Rebuild and restart:

```bash
sudo docker compose build
sudo docker compose run --rm server python -m team_yap.manage init-db
sudo docker compose up -d
```

Run the health checks again after the restart.

## 15. Backup The Database

The live database file is:

```text
/opt/team-yap/data/team-yap.db
```

Take a backup with SQLite’s online backup command:

```bash
sudo sqlite3 /opt/team-yap/data/team-yap.db ".backup '/opt/team-yap/backups/team-yap-$(date +%F-%H%M%S).db'"
```

That is the recommended backup command for this stack.

At minimum, include these paths in your Proxmox backup strategy:

- `/opt/team-yap/data/`
- `/opt/team-yap/backups/`
- `/opt/team-yap/.env`

## 16. Restore The Database

Stop the app first:

```bash
cd /opt/team-yap
sudo docker compose down
```

Restore the desired backup:

```bash
sudo cp /opt/team-yap/backups/team-yap-YYYY-MM-DD-HHMMSS.db /opt/team-yap/data/team-yap.db
sudo rm -f /opt/team-yap/data/team-yap.db-wal /opt/team-yap/data/team-yap.db-shm
```

Then start the app again:

```bash
sudo docker compose up -d
```

Verify with:

```bash
curl http://127.0.0.1:8080/healthz
sudo docker compose run --rm server python -m team_yap.manage db-summary
```

## Troubleshooting

### `curl http://127.0.0.1:8080/healthz` fails

Check:

```bash
sudo docker compose ps
sudo docker compose logs --tail=200 server
```

Common causes:

- the container never built successfully
- port `8080` is already in use on the VM
- `.env` points the database to the wrong path

### The container restarts repeatedly

Check:

```bash
sudo docker compose logs --tail=200 server
```

Common causes:

- invalid environment values
- broken Python dependency install during image build
- corrupted or inaccessible SQLite file

### Desktop users can reach the public hostname but still cannot log in

Check:

- the admin or user account actually exists
- the user’s password is correct
- the desktop app is pointed at the exact public URL

Server-side verification:

```bash
sudo docker compose run --rm server python -m team_yap.manage db-summary
```

### Cloudflare Tunnel returns 502

Server-side checks:

- confirm Team Yap is healthy on `http://127.0.0.1:8080/healthz`
- confirm the tunnel is forwarding to the correct internal HTTP port

### You need to move the database to a new disk

1. Stop the stack with `sudo docker compose down`.
2. Copy `team-yap.db` to the new storage location.
3. Update `.env` so `TEAM_YAP_DATABASE_PATH` points to the new mounted path inside the container.
4. Update `docker-compose.yml` volume mounts if you also move the container-side data path.
5. Start the stack again and rerun the health checks.
