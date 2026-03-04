# AGENTS.md

Repository entrypoint for all AI agents.

## 0) First Read

1. `.agents/AGENTS.md` (canonical machine playbook)
2. `AGENTS_INDEX.md` (repository graph of local AGENTS files)
3. Local `AGENTS.md` in the directory you are editing

Rule: nearest `AGENTS.md` adds local constraints; root and `.agents/AGENTS.md` remain baseline.

## 1) Canonical Source of Truth

- Canonical agent layer is `.agents/`.
- Canonical skills source is `.agents/skills/`.
- Runtime mirrors may exist in `.codex/skills/` and `.qwen/skills/`.

Sync commands:

```powershell
# canonical -> codex
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents

# canonical -> codex + qwen
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeQwen

# codex -> canonical refresh
pwsh .agents/scripts/sync-skills.ps1 -Direction to-agents
```

## 2) Operational Defaults

1. Use executable recipes in `artifacts/mcp-recipes/` for computations.
2. Keep chart outputs reproducible and attached to run folders/chart projects.
3. Run provenance/schema validation before finalizing chart projects.
4. For Obsidian: use recipe wrappers (`run_obsidian_export.ps1`, `init_obsidian_vault.ps1`), not ad-hoc manual file moves.

## 3) Quick Start Commands

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 -ChartId trump_19460614_105400_jamaica_ny_renderer
```
