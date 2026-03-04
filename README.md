# CATMEastrolab

Astrology engineering workspace with chart-as-project structure, reproducible artifacts, and agent-oriented skills.

## Current Scope

- Stable chart-project layout (`charts/<chart_id>/...`)
- Provider failover runbooks and recipes
- Schema/provenance validation
- Initial Codex skills set in `.codex/skills`

## Repository Layout

- `charts/` - source chart projects and produced outputs
- `artifacts/mcp-recipes/` - operational PowerShell recipes
- `artifacts/schemas/` - JSON schemas for chart project validation
- `.codex/skills/` - agent skills used in this project
- `Tasks/`, `TaskLogs/`, `BACKLOG.md`, `CURRENT_WORK.md` - planning and execution history
- `docs/` - methodology and operational docs

## Prerequisites

- Windows + PowerShell 7
- Python 3.11+
- Node.js (for MCP-related tooling)
- Python package: `pyyaml`

Install Python dependency:

```powershell
python -m pip install pyyaml
```

## Quick Start

1. Validate existing chart project:

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id tuapse_19820613_133910 --json
```

2. Generate Obsidian note from chart outputs:

```powershell
python .codex/skills/obsidian-export/scripts/generate_note.py --chart-id tuapse_19820613_133910 --output artifacts/skill-smoke/obsidian
```

3. Explore MCP recipes:

- `artifacts/mcp-recipes/run_full_workbench.ps1`
- `artifacts/mcp-recipes/run_natal_with_failover.ps1`
- `artifacts/mcp-recipes/validate_chart_project.ps1`

## Notes for Public Repository

- Private skill `.codex/skills/astro-engineering-scanner/` is intentionally excluded.
- Tool sandboxes (`.tools/`), local experiment outputs, and temporary artifacts are ignored.
- Repository contains real sample chart data in `charts/`; review before broad public distribution.

## Next Priority (from current backlog)

1. ASTRO-016 - serialization and observability standards
2. ASTRO-008/011/012 - modular architecture and orchestrator backbone
3. ASTRO-009/010 - renderer and Obsidian product modules on hardened backbone
