---
description: Load session state from CURRENT_WORK.md and active tasklogs. Use at session start to restore context.
allowed-tools: Read, Grep, Glob, Bash
---

## Task

Restore context from previous session by reading CURRENT_WORK.md and active tasklogs.

## Workflow

### Step 1: Read Router

Read `CURRENT_WORK.md` to get active WIP list.

If file doesn't exist, check `BACKLOG.md` files in subprojects for TODO tasks.

### Step 2: Read the NKS map (where the realm is going)

`CURRENT_WORK.md` is the task router; the NKS realm `astrolab` is the **map**. Read both:

- `nks_orient(realm="astrolab")` — overview (active contours, entry/exit, recent changes).
- `nks_orient(realm="astrolab", lens="bianhua")` — the forest of transformations 形: the
  owner-facing "where the realm is going", ready/blocked/done. Orient by this, not just the WIP table.
- `nks_orient(realm="astrolab", lens="tensions")` — what last session left unclosed (a heads-up,
  not a mandate to fix now).

### Step 3: Read Active Tasklogs

For each task in Active WIP:

1. Read the task spec file
2. Read last Progress Log entries (if any exist as `task_log_*.md`)
3. Note: last action, current state, next steps, blockers

### Step 4: Check Git State

```bash
git status -sb
git log --oneline -5
```

Extract: branch, uncommitted files, recent commits.

### Step 5: Read Subproject AGENTS.md

Read the local `AGENTS.md` for the active subproject to understand constraints and architecture.

### Step 6: Present Summary

```markdown
## Loaded

**Branch:** master | **Uncommitted:** N files

### Active WIP

| Task | Subproject | Status | Last Action | Next |
|------|-----------|--------|-------------|------|
| L402-APR-001 | l402-proof-of-vision | TODO | — | Integrate Aperture |

### Paused

- L402-MVP-007: Superseded by APR-003

### Recent Commits

- `abc1234` feat: add L402 Aperture architecture docs

### Suggested Action

Continue with [task] or pick from BACKLOG?
```

## Notes

- If CURRENT_WORK.md doesn't exist, scan for BACKLOG.md files with TODO tasks
- Always read the subproject's local AGENTS.md for context
- End with actionable suggestion
- Reference `.agents/docs/` for global context if needed
