# AGENTS.md

Canonical machine instructions are maintained in:

- `.agents/AGENTS.md`

Start there and follow its mandatory read order (`.agents/docs/00..11`).

## Compatibility note

Legacy agent-specific folders may exist (`.codex/`, `.qwen/`), but canonical authoring source is `.agents/`.

Use sync utility when needed:

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents
```
