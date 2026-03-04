# 05 Smoke Tests

Run these commands exactly. If expected markers are present, environment is considered healthy.

## A. Skill sync

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents
```

Expected marker:

- `Synced skills from .agents to targets.`

## B. Schema validator smoke

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
```

Expected markers:

- `"valid": true`
- `"chart_yaml_valid": true`
- `"provenance_valid": true`

## C. Obsidian export smoke

```powershell
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 -ChartId trump_19460614_105400_jamaica_ny_renderer
```

Expected marker:

- `Obsidian export completed: ...\artifacts\skill-smoke\obsidian\trump_19460614_105400_jamaica_ny_renderer`

## D. Transit recipe smoke

```powershell
pwsh artifacts/mcp-recipes/run_transits_to_natal.ps1 -CaseId smoke_transit -Latitude 40.7 -Longitude -73.8164 -BirthDateTimeUtc 1946-06-14T14:54:00Z -TransitDateTimeUtc 2026-03-04T06:29:42Z -Orb 1
```

Expected marker:

- `Transit-to-natal completed:`

## E. Chart validation smoke

```powershell
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId trump_19460614_105400_jamaica_ny
pwsh artifacts/mcp-recipes/validate_chart_project.ps1 -ChartId trump_19460614_105400_jamaica_ny
```

Expected markers:

- `Chart provenance integrity: PASS`
- `Chart project validation: PASS`

