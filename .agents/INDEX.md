# Agent Layer Index

Canonical agent layer root for this repository.

## Structure

- `.agents/skills/` - canonical shared skills (tracked)
- `.agents/scripts/sync-skills.ps1` - sync utility for `.codex/skills` and optional `.qwen/skills`
- `.agents/docs/` - agent-facing documentation (to be filled next)

## Current Canonical Skills

- artifact-builder
- chart-analyst
- chart-data-preparator
- knowledge-ingestion
- obsidian-export
- provider-orchestrator
- renderer
- run-planner
- schema-validator

## Sync Commands

```powershell
# sync canonical skills -> .codex/skills
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents

# sync canonical skills -> .codex/skills and .qwen/skills
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeQwen

# refresh canonical skills from .codex/skills
pwsh .agents/scripts/sync-skills.ps1 -Direction to-agents
```

## Private Skills

Private skill `astro-engineering-scanner` is intentionally excluded from canonical tracked set.
If needed locally, use `-IncludePrivate` explicitly and keep path-level ignore policy.
