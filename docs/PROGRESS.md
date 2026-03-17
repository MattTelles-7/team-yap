# Progress

Last updated: 2026-03-17

## Current Objective

- Keep the one-line server and desktop setup paths working.
- Keep the one-line uninstall paths working.
- Preserve exact, step-by-step docs that match the implementation.
- Maintain restart-ready checkpoint docs and rules for future work.

## Current Validated State

- Python server modules compile with `python3 -m py_compile backend/team_yap/*.py`.
- Desktop Rust compile validation passes with `cargo check` from `desktop/src-tauri`.
- Shell syntax checks pass for:
  - `scripts/bootstrap-server-debian.sh`
  - `scripts/bootstrap-client-macos.sh`
  - `scripts/uninstall-client-macos.sh`
  - `scripts/uninstall-server-debian.sh`
- The Tauri ACL definition has been corrected in `desktop/src-tauri/permissions/default.toml` so it uses `[[permission]]` and `commands.allow`.
- Desktop install docs now include the exact raw GitHub 404 failure mode and the exact Tauri ACL failure mode reported in this thread.

## Active Checkpoint

- In progress: add a dark desktop theme as the default, persist a local theme preference, expose a theme toggle in the desktop settings UI, and refresh the desktop icon set to a transparent liquid-glass style.
- Rules file now covers restart files, checkpoint history, small bets, exact error capture, and security/logging boundaries.
- Rules file now explicitly requires every new repo task to read `AGENTS.md`, `docs/PROGRESS.md`, and `docs/CHECKPOINT_HISTORY.md` before planning or editing.
- Progress checkpoint docs are in place so future runs can restart without rereading the full conversation.
- A reusable subagent prompt exists to audit workflow practice against the supervision guidance from the transcript.
- These checkpoint files now need to stay current for every future user-directed change.
- The current repo consistency audit confirmed the referenced workflow files are present. The current uncommitted changes are the checkpoint-maintenance edits from this audit.

## Next Small Bets

- Add the new persisted theme field to desktop settings, bootstrap scripts, and Tauri commands.
- Update the desktop HTML, CSS, and JavaScript to default to dark mode and expose a saved theme toggle.
- Regenerate the desktop icon assets with a transparent liquid-glass design and verify the bundle inputs still exist.
- Keep README and docs aligned with any new workflow files added in this checkpoint.
- Continue updating the checkpoint files and rules file for each user-directed change from this point forward.
- Keep startup instructions in `AGENTS.md` minimal and load-bearing so they stay useful instead of bloated.
- If packaged installers are the next milestone, run `cargo tauri build` on macOS and Windows and record the exact output artifact paths.

## Known Risks And Gaps

- Raw GitHub one-liners only work after the corresponding scripts are pushed to the branch referenced by the URL.
- Windows bootstrap and uninstall scripts were reviewed, but PowerShell execution was not validated in this macOS workspace.
- A full packaged desktop build has not yet been executed from this workspace. `cargo check` passed, but installer generation still needs native platform validation.
- Icon asset generation needs to preserve all bundle formats used by Tauri: PNG sizes, `icon.ico`, and `icon.icns`.
