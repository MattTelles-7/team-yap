# Operations Guide

This guide covers the day-2 tasks for the Team Yap server.

The operational commands below assume:

- the repo is deployed at `/opt/team-yap`
- you are running the Docker deployment from [`docs/DEPLOY_PROXMOX.md`](DEPLOY_PROXMOX.md)

All server-side management commands are implemented in:

```text
backend/team_yap/manage.py
```

## Admin Bootstrap Method

The bootstrap method is the `bootstrap-admin` CLI command.

It is intended for the very first administrator only:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage bootstrap-admin --username admin --display-name "Team Yap Admin" --prompt-password
```

Behavior:

- it creates a user with `is_admin = 1`
- it fails if any admin already exists

## How To Create The First Admin

From the deployed server:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage init-db
sudo docker compose run --rm server python -m team_yap.manage bootstrap-admin --username admin --display-name "Team Yap Admin" --prompt-password
```

After that, sign in from the desktop app with:

- server URL: your internal or public Team Yap URL
- username: `admin`
- the password you entered during bootstrap

## How To Create Additional Users

Create a normal user:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage create-user --username alice --display-name "Alice" --prompt-password
```

Create another admin:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage create-user --username opsadmin --display-name "Ops Admin" --admin --prompt-password
```

## How Logs Work

The current server logs go to container stdout and stderr.

There is no separate rotating application log file in this repo.

View live logs:

```bash
cd /opt/team-yap
sudo docker compose logs -f server
```

View the last 200 log lines:

```bash
cd /opt/team-yap
sudo docker compose logs --tail=200 server
```

Desktop logging behavior:

- during development, logs appear in the terminal running `cargo tauri dev`
- the packaged desktop app does not currently write a dedicated user-facing log file

## How To Reset A Password Manually

Run:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage reset-password --username alice --prompt-password
```

What this command does:

- overwrites the stored password hash
- deletes active sessions for that user

That forces the user to sign in again with the new password.

## How To Inspect Database State Safely

Recommended first step:

```bash
cd /opt/team-yap
sudo docker compose run --rm server python -m team_yap.manage db-summary
```

That prints:

- database path
- user count
- message count
- active session count
- per-user message counts

If you need direct SQL inspection, use SQLite in read-only mode:

```bash
sqlite3 -readonly /opt/team-yap/data/team-yap.db
```

Useful read-only queries:

```sql
SELECT username, display_name, is_admin, created_at
FROM users
ORDER BY created_at;
```

```sql
SELECT id, body, created_at
FROM messages
ORDER BY created_at DESC
LIMIT 20;
```

```sql
SELECT COUNT(*) AS sessions
FROM sessions;
```

Do not edit production rows directly unless you are restoring from a known-good backup or handling a one-off emergency and understand the consequences.

## How To Rotate Or Update Environment Config

The runtime config lives in:

```text
/opt/team-yap/.env
```

To change it safely:

1. Back up the current file.
2. Edit `.env`.
3. Rebuild and restart the stack.
4. Re-run the health checks.

Exact sequence:

```bash
cd /opt/team-yap
cp .env .env.$(date +%F-%H%M%S).bak
nano .env
sudo docker compose build
sudo docker compose up -d
curl http://127.0.0.1:8080/healthz
```

When changing these values, verify external dependencies too:

- `TEAM_YAP_PORT`: update the host firewall and tunnel target if needed
- `TEAM_YAP_ALLOWED_ORIGINS`: update it if you add a browser-based client
- `TEAM_YAP_DATABASE_PATH`: verify the underlying storage mount exists before restart

## Backup And Restore Notes

### Backup

Use SQLite’s `.backup` command:

```bash
sudo sqlite3 /opt/team-yap/data/team-yap.db ".backup '/opt/team-yap/backups/team-yap-$(date +%F-%H%M%S).db'"
```

### Restore

Stop the app, replace the main database file, remove stale WAL files, then start the app again:

```bash
cd /opt/team-yap
sudo docker compose down
sudo cp /opt/team-yap/backups/team-yap-YYYY-MM-DD-HHMMSS.db /opt/team-yap/data/team-yap.db
sudo rm -f /opt/team-yap/data/team-yap.db-wal /opt/team-yap/data/team-yap.db-shm
sudo docker compose up -d
```

### Minimum Files To Preserve

At minimum, back up:

- `/opt/team-yap/data/team-yap.db`
- `/opt/team-yap/.env`
- `/opt/team-yap/backups/`

## Upgrade Notes For Future Versions

Before every upgrade:

1. Back up the database.
2. Review release notes or diffs.
3. Compare the new `.env.example` with your current `.env`.

Upgrade sequence:

```bash
cd /opt/team-yap
sudo sqlite3 /opt/team-yap/data/team-yap.db ".backup '/opt/team-yap/backups/pre-upgrade-$(date +%F-%H%M%S).db'"
git pull --ff-only
sudo docker compose build
sudo docker compose run --rm server python -m team_yap.manage init-db
sudo docker compose up -d
curl http://127.0.0.1:8080/healthz
sudo docker compose run --rm server python -m team_yap.manage db-summary
```

Why `init-db` is part of the upgrade path:

- the schema creation is idempotent
- if a future version adds new `CREATE TABLE IF NOT EXISTS` or index statements, rerunning the init step is the safest built-in migration path this repo currently provides

## Operational Limits To Keep In Mind

- This app is backed by SQLite, so keep it on reliable local storage.
- There is no built-in multi-node or HA mode.
- There is no voice subsystem to operate.
- There is no websocket transport to monitor in the current build.
- The desktop client does not auto-refresh; users refresh the feed manually.
