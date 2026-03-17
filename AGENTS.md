# Repository Rules

## Session Start Requirements

- At the start of every new task in this repo, read this file first.
- Immediately after reading this file, read [docs/PROGRESS.md](docs/PROGRESS.md) and [docs/CHECKPOINT_HISTORY.md](docs/CHECKPOINT_HISTORY.md) before planning, editing, or validating.
- If the task touches setup, uninstall, deployment, packaging, ports, env vars, commands, or file paths, also read the relevant operational doc before making changes:
  - [README.md](README.md)
  - [docs/INSTALL_DESKTOP.md](docs/INSTALL_DESKTOP.md)
  - [docs/DEPLOY_PROXMOX.md](docs/DEPLOY_PROXMOX.md)
  - [docs/OPERATIONS.md](docs/OPERATIONS.md)
- Treat those files as standing context for the session, not optional references.
- If a task starts outside this repo root, switch into the repo context before proceeding so these rules apply.

- Re-review and update the docs for every user-requested change that affects behavior, setup, uninstall, deployment, packaging, ports, env vars, commands, or file paths.
- Keep [README.md](README.md), [docs/INSTALL_DESKTOP.md](docs/INSTALL_DESKTOP.md), [docs/DEPLOY_PROXMOX.md](docs/DEPLOY_PROXMOX.md), and [docs/OPERATIONS.md](docs/OPERATIONS.md) aligned with the actual implementation and scripts.
- Keep the one-line bootstrap and one-line uninstall commands working and documented whenever related code changes.
- Do not leave setup or uninstall docs as placeholders. They must match the real scripts, commands, and paths in the repo.
- Keep [docs/PROGRESS.md](docs/PROGRESS.md) current after each user-directed change. It is the restart file for the next run.
- When a checkpoint completes, rewrite [docs/PROGRESS.md](docs/PROGRESS.md) so it describes the current state rather than stale future or in-progress wording.
- Append meaningful milestones to [docs/CHECKPOINT_HISTORY.md](docs/CHECKPOINT_HISTORY.md) with the date, the checkpoint summary, the validations run, and any remaining risk.
- Use small bets. Break larger requests into checkpoints that can be validated before moving to the next change.
- Before risky multi-file work, record the intended checkpoint and validation plan in [docs/PROGRESS.md](docs/PROGRESS.md).
- When a real error is reported by a user, capture the exact error string and add the fix to the relevant docs instead of paraphrasing it away.
- Prefer explicit health checks, verification commands, rollback notes, and recovery steps over vague operational guidance.
- Treat raw GitHub one-liners as pushed-branch artifacts. If local scripts change, update the docs to note whether the fix requires a push before the one-liner can work.
- Never commit secrets or add live passwords, bearer tokens, or API keys to tracked files.
- Never add logging that exposes auth tokens, passwords, or sensitive user data.
- When a client or server action can fail, document and implement a clear user-visible failure path instead of a blank screen or silent failure.
- State the expected scale when it materially affects a design or deployment choice. Default assumption for Team Yap is a small private deployment unless the user says otherwise.
- If requirements move into higher-risk areas such as payments, medical data, children's data, legal compliance, or serious scale/performance work, stop and call out that a professional engineering review is required.
