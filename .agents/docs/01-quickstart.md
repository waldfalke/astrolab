# 01 Quickstart

Use this exact sequence when starting from a clean context.

## A. Verify environment

```powershell
python --version
node --version
pwsh --version
```

## B. Sync canonical skills

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents
```

## C. Run baseline checks

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
python .codex/skills/obsidian-export/scripts/generate_note.py --chart-id trump_19460614_105400_jamaica_ny --output artifacts/skill-smoke/obsidian
```

## D. Produce chart methods (example)

```powershell
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1 -CaseId demo -Latitude 44.1 -Longitude 39.07 -DateTimeUtc 1946-06-14T14:54:00Z
pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1 -CaseId demo -Latitude 44.1 -Longitude 39.07 -DateTimeUtc 1946-06-14T14:54:00Z
pwsh artifacts/mcp-recipes/run_secondary_progressions.ps1 -CaseId demo_prog -Latitude 44.1 -Longitude 39.07 -BirthDateTimeUtc 1946-06-14T14:54:00Z -TargetDateUtc 2026-03-04T00:00:00Z -Orb 1
pwsh artifacts/mcp-recipes/run_solar_arc.ps1 -CaseId demo_arc -Latitude 44.1 -Longitude 39.07 -BirthDateTimeUtc 1946-06-14T14:54:00Z -TargetDateUtc 2026-03-04T00:00:00Z -Orb 1
pwsh artifacts/mcp-recipes/run_transits_to_natal.ps1 -CaseId demo_transit -Latitude 44.1 -Longitude 39.07 -BirthDateTimeUtc 1946-06-14T14:54:00Z -TransitDateTimeUtc 2026-03-04T00:00:00Z -Orb 1
```

## E. Build chart project and validate

```powershell
pwsh artifacts/mcp-recipes/build_chart_project.ps1 -ChartId demo_chart -BirthDateTimeLocal "1946-06-14 10:54:00" -BirthTimezone "+04:00" -BirthDateTimeUtc 1946-06-14T14:54:00Z -Latitude 40.700000 -Longitude -73.816400 -NatalFailoverRunDir <ABS_PATH> -HouseRunDir <ABS_PATH> -SecondaryProgressionsRunDir <ABS_PATH> -SolarArcRunDir <ABS_PATH>
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId demo_chart
pwsh artifacts/mcp-recipes/validate_chart_project.ps1 -ChartId demo_chart
```

## F. Log work

- Add TaskLog entry in `TaskLogs/` with status, run dirs, and issues.

