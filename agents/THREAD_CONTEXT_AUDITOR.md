# Thread Context Auditor

Use this prompt when you want a subagent to review the current thread and repo workflow against the supervision practices adopted for Team Yap.

## Purpose

Audit whether the current task and repo process are following the standing orders in `AGENTS.md` and the supervision habits captured from the transcript that drove this file.

## Inputs To Review

- the current user request
- the recent thread context
- `AGENTS.md`
- `docs/PROGRESS.md`
- `docs/CHECKPOINT_HISTORY.md`
- any docs or scripts touched by the current task

## Required Audit Checks

### Standing Orders

- Are the repo rules specific enough for the mistakes that have already happened in this thread?
- Did a repeated failure happen that should become a permanent rule?

### Save Points And Version Control

- Is the current checkpoint recorded in `docs/PROGRESS.md`?
- Is there a milestone entry in `docs/CHECKPOINT_HISTORY.md` if the work changed repo behavior, setup, uninstall, deployment, packaging, ports, env vars, commands, or file paths?
- Is the current change small enough to validate safely?

### Restart And Context Management

- If the next run starts fresh, can it recover from `docs/PROGRESS.md` and `docs/CHECKPOINT_HISTORY.md` without rereading the whole thread?
- Are the next small bets, open risks, and validation commands written down?
- Does `docs/PROGRESS.md` describe the current state accurately, or is it still using stale future-tense wording for work that already finished?

### Failure Handling

- Did a real error message appear in the thread?
- If yes, was the exact error string captured in the relevant docs with a concrete fix?
- Do the docs explain verification and recovery, not just setup?

### Security And Logging

- Did any change add or expose secrets, passwords, auth tokens, or sensitive user data?
- Did any code or docs introduce logging that should be removed or narrowed?
- Did the work move into a higher-risk domain that should trigger explicit escalation?

## Output Format

Return a concise audit grouped as:

- rules file additions
- progress doc updates
- doc maintenance workflow
- risks or gaps
