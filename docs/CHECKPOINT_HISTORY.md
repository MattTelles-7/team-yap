# Checkpoint History

## 2026-03-17 Checkpoint 1

Summary:

- Created the first working Team Yap baseline with a FastAPI server, SQLite database, Tauri desktop client, Docker Compose deployment path, and real documentation.

Validation:

- `python3 -m py_compile backend/team_yap/*.py`
- Tauri JSON config validation

Open risk at that point:

- Rust/Tauri builds and Docker runtime were documented but not executed in the initial workspace.

## 2026-03-17 Checkpoint 2

Summary:

- Added one-line bootstrap flows for Debian, macOS, and Windows.
- Added one-line uninstall flows for Debian, macOS, and Windows.
- Updated the docs to lead with copy-and-paste setup commands.

Validation:

- `bash -n scripts/bootstrap-server-debian.sh`
- `bash -n scripts/bootstrap-client-macos.sh`
- `bash -n scripts/uninstall-client-macos.sh`
- `bash -n scripts/uninstall-server-debian.sh`
- `python3 -m py_compile backend/team_yap/*.py`

Open risk at that point:

- PowerShell syntax and runtime validation were still pending outside this macOS workspace.

## 2026-03-17 Checkpoint 3

Summary:

- Fixed the desktop Tauri ACL issue behind `SetPermissionNotFound { permission: "allow-load-settings", set: "default" }`.
- Added persistent repo supervision artifacts: `AGENTS.md`, `docs/PROGRESS.md`, `docs/CHECKPOINT_HISTORY.md`, and `agents/THREAD_CONTEXT_AUDITOR.md`.
- Updated the desktop docs to preserve the exact 404 and Tauri ACL failures reported in this thread.
- Added explicit session-start rules so every new repo task must read `AGENTS.md`, `docs/PROGRESS.md`, and `docs/CHECKPOINT_HISTORY.md` before planning or editing.

Validation:

- `python3 -m py_compile backend/team_yap/*.py`
- `bash -n scripts/bootstrap-client-macos.sh`
- `bash -n scripts/uninstall-client-macos.sh`
- `bash -n scripts/uninstall-server-debian.sh`
- `cargo check` in `desktop/src-tauri`

Open risk at that point:

- Windows PowerShell bootstrap and uninstall execution still need validation outside this macOS workspace.

## 2026-03-17 Checkpoint 4

Summary:

- Completed a real `cargo check` in `desktop/src-tauri`, confirming the fixed Tauri permission file clears the reported ACL compile failure.
- Kept the persistent supervision artifacts in place for future work: `AGENTS.md`, `docs/PROGRESS.md`, `docs/CHECKPOINT_HISTORY.md`, and `agents/THREAD_CONTEXT_AUDITOR.md`.
- Tightened the standing orders to preserve explicit failure handling and the default small private deployment assumption unless the user changes it.

Validation:

- `cargo check` in `desktop/src-tauri`
- `python3 -m py_compile backend/team_yap/*.py`
- `bash -n scripts/bootstrap-client-macos.sh`
- `bash -n scripts/uninstall-client-macos.sh`
- `bash -n scripts/uninstall-server-debian.sh`

Open risk at that point:

- Raw GitHub one-liners still require these local changes to be pushed before the remote copy-and-paste commands can use them.
- Windows PowerShell runtime validation and full packaged installer builds are still pending on native target machines.

## 2026-03-17 Checkpoint 5

Summary:

- Re-reviewed `AGENTS.md`, `docs/PROGRESS.md`, `docs/CHECKPOINT_HISTORY.md`, `README.md`, `docs/INSTALL_DESKTOP.md`, `docs/DEPLOY_PROXMOX.md`, `docs/OPERATIONS.md`, and `agents/THREAD_CONTEXT_AUDITOR.md` after multi-agent work.
- Fixed stale wording in `docs/PROGRESS.md` so the restart file now describes the current workflow artifacts as already present rather than still being added.
- Added a standing-order reminder that completed checkpoints must update `docs/PROGRESS.md` to current-state wording.

Validation:

- `git status --short`
- manual consistency review of the repo rules, checkpoint files, audit prompt, and user-facing docs

Open risk at that point:

- Raw GitHub one-liners still depend on the pushed branch contents.
- Windows PowerShell runtime validation and full packaged installer builds are still pending on native target machines.
