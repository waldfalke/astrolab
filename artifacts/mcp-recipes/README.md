# MCP Recipe Pack (Result-Oriented)

This folder contains executable artifacts that generate working astrology outputs via MCP, without building a custom backend.

## Prerequisites

1. Node.js + npm in PATH
2. Internet access
3. `mcporter` available via `npx` (no global install required)

## Implemented Providers

1. Primary (houses/Placidus): `https://www.theme-astral.me/mcp`
2. Backup (continuity): `https://ephemeris.fyi/mcp`

## Recipes

1. `run_natal_snapshot.ps1`
   - Produces: core longitudes, aspects, moon phase, sun/moon daily events.
2. `run_forecast_delta.ps1`
   - Produces: movement delta between two dates, aspects on both dates.
3. `run_synastry_matrix.ps1`
   - Produces: inter-chart aspect matrix (major aspects within orb).
4. `run_house_layer_placidus.ps1`
   - Produces: house cusps, chart points, primary-provider planet table, plus `North/South Node` and `Galactic Center` in `05_additional_points.csv`, and aspects from these points to planets in `06_custom_point_aspects.csv`.
5. `run_natal_with_failover.ps1`
   - Produces: natal output with automatic primary->backup failover.
6. `run_cross_provider_qc.ps1`
   - Produces: primary vs backup longitude delta QC report.
7. `run_full_workbench.ps1`
   - Produces: natal failover + house layer + forecast + synastry + QC + manifests in one run.
8. `run_mcp_provider_probe.ps1`
   - Produces: capability/health snapshot of multiple MCP astrology providers.
9. `run_secondary_progressions.ps1`
   - Produces: secondary progressed chart (`1 day after birth = 1 year`) and progressed-vs-natal deltas/aspects.
10. `run_solar_arc.ps1`
   - Produces: solar-arc directed positions and directed-vs-natal aspects.
11. `build_chart_project.ps1`
   - Produces: chart-as-project structure with per-method raw folders, top-level outputs, and `INDEX.yaml` provenance map.
12. `check_chart_provenance.ps1`
   - Validates canonical provenance links in chart projects (`canonical_run_dir` / `canonical_source`) and reports missing references.
13. `validate_chart_project.ps1`
   - Validates `chart.yaml` and `INDEX.yaml` against schema contracts and file-link consistency checks.
14. `archive_runs.ps1`
   - Safely archives run folders from `artifacts/results`, rewrites affected chart index external links, and emits verification report.

## Quick Run Examples

```powershell
# Natal snapshot
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_natal_snapshot.ps1 `
  -CaseId "demo_natal" -Latitude 44.1 -Longitude 39.07 -DateTimeUtc "1982-06-12T08:39:00Z"

# Forecast delta (date1 -> date2)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_forecast_delta.ps1 `
  -CaseId "demo_forecast" -Latitude 44.1 -Longitude 39.07 `
  -Date1Utc "1982-06-12T08:39:00Z" -Date2Utc "2026-03-01T00:00:00Z"

# Synastry matrix
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_synastry_matrix.ps1 `
  -CaseId "demo_synastry" `
  -LatA 44.1 -LonA 39.07 -DateAUtc "1982-06-12T08:39:00Z" `
  -LatB 55.75 -LonB 37.62 -DateBUtc "1990-01-01T12:00:00Z"

# House-layer (Placidus)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_house_layer_placidus.ps1 `
  -CaseId "demo_house" -Latitude 44.1 -Longitude 39.07 -DateTimeUtc "1982-06-12T08:39:00Z"

# Natal with failover
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_natal_with_failover.ps1 `
  -CaseId "demo_failover" -Latitude 44.1 -Longitude 39.07 -DateTimeUtc "1982-06-12T08:39:00Z"

# Cross-provider QC
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_cross_provider_qc.ps1 `
  -CaseId "demo_qc" -Latitude 44.1 -Longitude 39.07 -DateTimeUtc "1982-06-12T08:39:00Z" -MaxDeltaDeg 1.0

# One-shot full workbench
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_full_workbench.ps1 `
  -CaseId "demo_full" `
  -Latitude 44.1 -Longitude 39.07 -BirthDateTimeUtc "1982-06-12T08:39:00Z" `
  -CompareDateUtc "2026-03-01T00:00:00Z" `
  -SynLatB 55.75 -SynLonB 37.62 -SynDateBUtc "1990-01-01T12:00:00Z" `
  -ClientId "client_demo" -Analyst "Auto"

# Provider capability probe
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_mcp_provider_probe.ps1

# Secondary progressions (1 day = 1 year)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_secondary_progressions.ps1 `
  -CaseId "demo_secondary" -Latitude 44.1 -Longitude 39.07 `
  -BirthDateTimeUtc "1982-06-13T09:39:10Z" -TargetDateUtc "2026-03-02T00:00:00Z" -Orb 1

# Solar arc directions
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_solar_arc.ps1 `
  -CaseId "demo_solar_arc" -Latitude 44.1 -Longitude 39.07 `
  -BirthDateTimeUtc "1982-06-13T09:39:10Z" -TargetDateUtc "2026-03-02T00:00:00Z" -Orb 1

# Build chart project from method runs
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\build_chart_project.ps1 `
  -ChartId "tuapse_19820613_133910" `
  -BirthDateTimeLocal "1982-06-13 13:39:10" -BirthTimezone "+04:00" `
  -BirthDateTimeUtc "1982-06-13T09:39:10Z" -Latitude 44.100833 -Longitude 39.083333 `
  -NatalFailoverRunDir "D:\Dev\CATMEastrolab\artifacts\results\natal_failover_tuapse_19820613_133910_20260302_101307" `
  -HouseRunDir "D:\Dev\CATMEastrolab\artifacts\results\house_placidus_tuapse_19820613_133910_gc_nodes_aspects_orb6_20260302_103757" `
  -SecondaryProgressionsRunDir "D:\Dev\CATMEastrolab\artifacts\results\secondary_progressions_tuapse_19820613_progressions_now_20260302_110650" `
  -SolarArcRunDir "D:\Dev\CATMEastrolab\artifacts\results\solar_arc_tuapse_19820613_solar_arc_20260302_105559"

# Validate chart provenance integrity
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\check_chart_provenance.ps1 `
  -ChartId "tuapse_19820613_133910"

# Validate chart project contracts
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\validate_chart_project.ps1 `
  -ChartId "tuapse_19820613_133910"

# Archive runs safely with index rewrite (dry-run by default)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\archive_runs.ps1 `
  -Filter "provider_probe_*"

# Execute archive and rewrite only one chart index
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\archive_runs.ps1 `
  -Filter "provider_probe_20260302_130604" -ChartId "tuapse_19820613_133910" -Execute
```

## Output Location

All runs are saved under:

`artifacts/results/<recipe>_<caseId>_<timestamp>/`

Each run contains:

1. `00_summary.txt`
2. raw JSON response files from MCP
3. normalized CSV files for analyst workflows

## Scope and Gaps

What works now:

1. Planetary/luminary positions
2. Major aspect scans
3. Time-based deltas
4. Moon phase and daily events
5. House cusps (Placidus) and chart points
6. Additional points for house-layer: `North Node`, `South Node`, `Galactic Center` (tropical approximate precession model)
7. Aspects from additional points to planets (major aspects, configurable orb)
8. Provider failover with degraded/full status
9. Cross-provider QC (longitude deltas)
10. Secondary progressions (`1 day = 1 year`) with progressed deltas/aspects
11. Solar arc directions from progressed Sun arc

What is not covered by this provider pack:

1. Declination/parallel and contraparallel calculations
2. Chart wheel rendering / visual design layer

See also:

1. `provider_profile.yaml` - active provider setup
2. `failover_runbook.md` - incident and fallback process
