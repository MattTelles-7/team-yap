# Team Yap

Team Yap is a small self-hosted team message board. It ships with:

- a Python/FastAPI server
- a SQLite database
- a Tauri desktop client for macOS and Windows
- a Docker Compose deployment path for a small private server

The current build is intentionally narrow: users sign in from the desktop app, read the latest 100 messages, and post new ones. User creation, admin bootstrap, and password resets are handled from the server CLI.

## Repo Structure

```text
.
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── team_yap/
│       ├── config.py
│       ├── db.py
│       ├── main.py
│       ├── manage.py
│       ├── runserver.py
│       ├── schema.sql
│       └── security.py
├── desktop/
│   ├── app/
│   │   ├── app.js
│   │   ├── index.html
│   │   └── styles.css
│   └── src-tauri/
│       ├── capabilities/
│       ├── icons/
│       ├── permissions/
│       ├── src/
│       ├── Cargo.toml
│       └── tauri.conf.json
├── docs/
│   ├── DEPLOY_PROXMOX.md
│   ├── INSTALL_DESKTOP.md
│   └── OPERATIONS.md
├── .env.example
└── docker-compose.yml
```

## Chosen Stack

- Server: Python 3.12+, FastAPI, Uvicorn
- Database: SQLite in WAL mode
- Desktop client: Rust + Tauri 2 + static HTML/CSS/JavaScript
- Packaging: native Tauri bundles
  - macOS: `.app` bundle and `.dmg`
  - Windows: `.msi` and NSIS setup `.exe`
- Deployment: Docker Engine + Docker Compose on an Ubuntu VM

## Local Development Quick Start

This repo does not require Node.js for the desktop app. The frontend is static and is bundled directly by Tauri.

1. Install the desktop prerequisites for your OS from [`docs/INSTALL_DESKTOP.md`](docs/INSTALL_DESKTOP.md).
2. Create a Python virtual environment and install server dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

3. Export the local server environment:

```bash
export PYTHONPATH="$PWD/backend"
export TEAM_YAP_DATA_DIR="$PWD/data"
export TEAM_YAP_DATABASE_PATH="$PWD/data/team-yap.db"
export TEAM_YAP_HOST="127.0.0.1"
export TEAM_YAP_PORT="8080"
```

4. Initialize the database and create the first admin:

```bash
python -m team_yap.manage init-db
python -m team_yap.manage bootstrap-admin --username admin --display-name "Admin" --prompt-password
```

5. Start the server:

```bash
python -m team_yap.runserver
```

6. In a second terminal, start the desktop app:

```bash
cd desktop/src-tauri
cargo tauri dev
```

The desktop app defaults to `http://127.0.0.1:8080`.

## Desktop Install Instructions

Full desktop development, packaging, and end-user install steps are in [`docs/INSTALL_DESKTOP.md`](docs/INSTALL_DESKTOP.md).

## Proxmox Deployment Instructions

The recommended server deployment path is documented in [`docs/DEPLOY_PROXMOX.md`](docs/DEPLOY_PROXMOX.md).

## Environment Variables Overview

The server reads these variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TEAM_YAP_HOST` | `127.0.0.1` | Bind address for direct Python runs. In Docker, use `0.0.0.0`. |
| `TEAM_YAP_PORT` | `8080` | Uvicorn listen port for local runs. Docker publishes host port `TEAM_YAP_PORT` to container port `8080`. |
| `TEAM_YAP_DATA_DIR` | `./data` | Directory used for database storage when `TEAM_YAP_DATABASE_PATH` is not set. |
| `TEAM_YAP_DATABASE_PATH` | `<TEAM_YAP_DATA_DIR>/team-yap.db` | Absolute or relative path to the SQLite database file. |
| `TEAM_YAP_LOG_LEVEL` | `INFO` | Uvicorn log level. |
| `TEAM_YAP_SESSION_TTL_HOURS` | `720` | Session lifetime in hours. |
| `TEAM_YAP_ALLOWED_ORIGINS` | empty | Optional comma-separated CORS allowlist for browser-based clients. The Tauri desktop app does not require this. |

Use `.env.example` as the starting point for Docker deployments.

## Known Limitations

- There is no voice transport in the current build. No audio calling, streaming, or voice relay is implemented.
- The desktop client is not realtime. It refreshes the feed on demand and does not open a websocket.
- There are no channels, attachments, or threaded conversations.
- User creation and password resets are CLI-driven on the server. There is no in-app admin panel yet.
- The packaged desktop app is not code signed or notarized in this repo. macOS Gatekeeper and Windows SmartScreen prompts are expected for locally built installers.
