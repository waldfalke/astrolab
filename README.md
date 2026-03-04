# CATMEastrolab

CATMEastrolab is an open engineering platform for astrology computation.

Old astrology processors were often expensive and monolithic desktop tools.  
This project takes another approach: API-first, artifact-first, agent-friendly.

You can run standard techniques out of the box and quickly add new techniques as reproducible pipelines.

## What The Platform Solves

1. Reproducible calculations instead of black-box UI flows.
2. Fast experimentation with new techniques using script recipes.
3. Provider flexibility (primary/backup MCP providers with retry/failover).
4. Agent-native workflows (`.agents`) for modern AI assistants.

## Built-In Techniques

- Natal snapshot with failover
- House layer (Placidus + chart points + additional points)
- Secondary progressions
- Solar arc directions
- Transit-to-natal aspect matrix
- Cross-provider QC
- Chart project build + provenance/schema validation

## Core Architecture

- `artifacts/mcp-recipes/` - operational PowerShell recipes (main execution layer)
- `artifacts/schemas/` - chart project contracts
- `charts/<chart_id>/` - chart-as-project outputs with method folders and `INDEX.yaml`
- `.agents/` - canonical machine playbook and skill layer
- `.codex/skills/` - runtime skill path (synced from `.agents/skills`)
- `docs/` - public docs (`docs/public/` contains public-safe redacted copies for sensitive docs)

## Requirements

- Windows + PowerShell 7 (`pwsh`)
- Python 3.11+
- Node.js 18+ (for `npx mcporter`)
- Python dependency: `pyyaml`

```powershell
python -m pip install pyyaml
npm install
```

## Quick Start

1. Sync canonical agent skills:

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents
```

2. Validate sample chart project:

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
```

3. Run transit-to-natal example:

```powershell
pwsh artifacts/mcp-recipes/run_transits_to_natal.ps1 -CaseId demo_transit -Latitude 40.7 -Longitude -73.8164 -BirthDateTimeUtc 1946-06-14T14:54:00Z -TransitDateTimeUtc 2026-03-04T06:29:42Z -Orb 1
```

4. Validate chart integrity:

```powershell
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId trump_19460614_105400_jamaica_ny
pwsh artifacts/mcp-recipes/validate_chart_project.ps1 -ChartId trump_19460614_105400_jamaica_ny
```

5. Create a lightweight Obsidian vault and export chart bundle:

```powershell
pwsh artifacts/mcp-recipes/init_obsidian_vault.ps1 `
  -VaultRoot D:\AstrolabVault `
  -ChartId trump_19460614_105400_jamaica_ny_renderer
```

Open `D:\AstrolabVault` as Obsidian vault, then open:
`Astrolab/exports/<chart_id>/<chart_id>_canvas.canvas`

## How To Add A New Technique

Use this minimal extension pattern:

1. Create a new recipe script in `artifacts/mcp-recipes/`:
   - example: `run_<technique_name>.ps1`
2. Reuse helper primitives from `artifacts/mcp-recipes/lib/mcp_helpers.ps1`:
   - MCP calls
   - invariant CSV writing
   - summary generation
3. Write output contract:
   - `00_summary.txt`
   - raw JSON source responses
   - normalized CSV tables
4. Add recipe docs:
   - update `artifacts/mcp-recipes/README.md`
5. Wire technique into chart project assembly:
   - extend `build_chart_project.ps1` mappings if technique should be included in `charts/<chart_id>/outputs`
6. Validate:
   - provenance check
   - schema check
7. Add agent-facing usage in `.agents/docs/` (smoke command + known caveats)

## Agent-First Documentation

Main machine entrypoint:

- `.agents/AGENTS.md`

Read order and operational guides are in:

- `.agents/docs/00..11`

This includes smoke tests, fail-fast rules, known issues (including provider 500/400 transients), PowerShell style, MCPorter usage, and anti-patterns.

## Public/Private Data Policy

- Public-safe docs: `docs/public/`
- Private docs (ignored): `docs/private/`
- Private task management (ignored): `.private/pm/`
- Private chart data (ignored): `.private/charts/`

## License

Apache License 2.0.  
See [LICENSE](LICENSE).

