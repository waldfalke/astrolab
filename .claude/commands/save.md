---
description: Save session state by logging completed and current work. Use before ending session.
allowed-tools: Read, Edit, Bash, Grep, Glob
---

## Task

Log completed and in-progress work to CURRENT_WORK.md and active tasklog before ending session.

## Workflow

### Step 1: Identify Context

Read `CURRENT_WORK.md` to find active subproject and tasks.
If file doesn't exist, create it.

### Step 2: Analyze Session

Review conversation to identify:

- **Completed:** What was finished this session?
- **In Progress:** What's partially done?
- **Next:** What's the immediate next step?
- **Blockers:** Any impediments discovered?

### Step 3: Update CURRENT_WORK.md

Update the Active WIP table with current state.

### Step 4: Append to Tasklog

Find the relevant tasklog in the subproject's `tasks/` directory.
Append Progress Log entry:

```markdown
### YYYY-MM-DD HH:MM [Chat-N: Model]

**Completed:**
- Item 1
- Item 2

**In Progress:**
- Current task state

**Next:**
- Immediate next step
```

**Chat identifier examples:** `[Chat-1: Opus]`, `[Chat-2: Sonnet]`, `[Codex: GPT]`, `[Qwen: Qwen]`

### Step 5: Update Task Status

If a task completed:
1. Change task file header `[TODO]` → `[DONE]`
2. Update BACKLOG.md entry

### Step 6: NKS sweep (end-of-session graph ritual — 時-cycle 忠 light update)

Realm `astrolab` is the living graph of this work. Before ending, do NOT skip — the graph silts up
silently otherwise (17 tensions once accumulated this way):

1. `nks_orient(realm="astrolab", lens="tensions")` — what did THIS session leave unclosed?
   - Weave your own gaps (`weaving` skill): a new node without `vimarsha_of`/`context`, an arrow
     without `sense`, an unclosed lifecycle.
   - Sanctioned boundaries (realm inlet, ambient principle) — leave **consciously**, don't "fix"
     them. Tensions are truthful; a wrong arrow to zero a counter is worse than the tension.
2. Crystallize ≥1 understanding from the session: a `bildung` phenomenon (`arose_from` its origin,
   `context` into the holon) — a session must leave an **understanding**, not only new questions
   (methodology #435). If nothing crystallized, the session didn't land.
3. Update active bianhua progress: what advanced, which driving vimarshas resolved.

### Step 7: Check Git

```bash
git status -sb
```

If uncommitted changes, offer: commit / leave / stash.

### Step 8: Output Confirmation

```markdown
## Saved

**Subproject:** l402-proof-of-vision
**Tasklog:** L402-APR-001

**Completed:**
- Integrated Aperture into docker-compose

**Next:**
- Test Aperture startup with LND

**Git:** N files uncommitted
```

## Notes

- Always append to Progress Log, never overwrite
- Include timestamp and chat/model identifier
- If no significant work, still log brief entry
- Update `.agents/docs/` if architectural decisions were made
- The NKS sweep (Step 6) is not optional bookkeeping — it is how the graph stays in tension with
  reality. Match the graph to what changed; leave an understanding behind.
