# MCP Recipe Pack (Result-Oriented)

This folder contains executable artifacts that generate working astrology outputs via MCP, without building a custom backend.

## Prerequisites

1. Node.js + npm in PATH
2. Internet access
3. `mcporter` available via `npx` (no global install required)

## Implemented Providers

1. Primary (engine): self-hosted swiss — `swiss-mcp` Docker on `http://localhost:8000/mcp`
   (theme-astral.me died; see memory `swiss-self-host-primary` / `.mcp.json`)
2. Backup (continuity): `https://ephemeris.fyi/mcp`
3. Probe-only (NOT in production failover): `https://mcp.vedastro.org/api/mcp`

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
11. `run_transits_to_natal.ps1`
   - Produces: current transit-to-natal aspect matrix with explicit transit semantics.
12. `run_renderer.ps1`
   - Produces: `chart_wheel.svg`, `aspect_grid.svg`, and render manifest from chart outputs.
13. `build_chart_project.ps1`
   - Produces: chart-as-project structure with per-method raw folders, top-level outputs, and `INDEX.yaml` provenance map.
14. `check_chart_provenance.ps1`
   - Validates canonical provenance links in chart projects (`canonical_run_dir` / `canonical_source`) and reports missing references.
15. `validate_chart_project.ps1`
   - Validates `chart.yaml` and `INDEX.yaml` against schema contracts and file-link consistency checks.
16. `archive_runs.ps1`
   - Safely archives run folders from `artifacts/results`, rewrites affected chart index external links, and emits verification report.
17. `run_obsidian_export.ps1`
   - Produces: Obsidian bundle (`.md`, `.canvas`, `attachments/*.svg`) for a chart; supports direct export into a target vault.
18. `init_obsidian_vault.ps1`
   - Produces: minimal standalone Obsidian vault and optional chart export in one command.
19. `run_canvas_do_extract.ps1`
   - Produces: extracted `[DO]` task nodes from `.canvas` plus linked edges/context.
20. `run_canvas_ai_update.ps1`
   - Produces: safe AI status upsert (`[AI] in_progress|done|blocked`) for a target canvas node.
21. `run_obsidian_mcp_probe.ps1`
   - Produces: stdio MCP probe report for Obsidian MCP server (tool list + health).
22. `run_obsidian_mcp_e2e.ps1`
   - Produces: end-to-end Obsidian MCP check (`list -> create -> read -> edit -> read`) with PASS/FAIL summary.
23. `run_solar_revolution.ps1`
   - Produces: solar return for `ReturnYear`, cast at the TRUE Sun-return instant (bisection, not naive birthday cast), with relocation (`ReturnLatitude/ReturnLongitude`), SR→natal aspects, SR dignities, and annual profection.
24. `run_phase_vectors.ps1`
   - Produces: Zakharian phase vector `P⟨Z.z:H.h:D⟩` for all 10 bodies, built FROM the operator (book Table 2.2 embedded as a self-test, throws on mismatch). Tiers: Z,H grounded · z,h,D anumita. Working layer only (copyright).
25. `build_coverage_ledger.ps1`
   - Produces: keyed-contract coverage ledger (factors / dispositions / versions / report) over the chart project + SR + transit timeline. Transits split into `транзиты-несущие` (slow) and `транзиты-триггеры` (fast, auto-quiet). Runs gate-2/gate-3 structural checks.
26. `run_rising_hands.ps1`
   - Produces: the FLOATING intraday "hands" of the rising-sign clock (NKS astrolab #93) for a day + location — ASC/MC/Moon recomputed at every grid step (6-min). Emits `03_watches.csv` (rising-sign "караулы" + dual rulers = minute hand), and with `-NatalPointsCsv`: `04_rising_cross.csv` (transiting ASC/MC crossing natal points = fine hand) + `05_moon_timing.csv` (Moon's aspects to natal points = hour hand) + `06_coincidences.csv` (axis nodes where layers converge). Standalone hands instrument; transit-day-to-natal CONSUMES it. Does NOT compute transit→natal aspects (that's `run_transits_to_natal` snapshot). Data only — prose is the model's.
27. `run_transit_day.ps1`
   - The predictable transit-day PROTOCOL (NKS astrolab #90): `data → TWIN (gate) → prose → PDF`, same shape as `run_solar_gift`. ORCHESTRATES existing recipes (`run_transits_to_natal` snapshot for aspects/angles + `run_rising_hands` for hands/coincidences), never duplicates them. Computes natal points (chart ruler derived from the ASC sign, not hardcoded), builds a `_model_input/` work-package with `BRIEF.md` + cold data + `template_prose.html` (canonical format, self-contained). Build pass hands off; `-Assemble` second pass GATES on a real `twin.md` (read-as-system before prose — the gate is the harness, not the model's goodwill) then renders the PDF. PII → `.private` only.

## Full chart rebuild (orchestration)

Rebuild a chart-as-project from scratch, in order. Engine = self-hosted swiss (`swiss-mcp` Docker on
`:8000`); a Node-25 libuv teardown crash (exit 9) is non-fatal — trust the written files, not the exit code.

1. `run_natal_with_failover.ps1` — natal longitudes / aspects (failover swiss→ephem).
2. `run_house_layer_placidus.ps1` — Placidus cusps, chart points, sect, dignities, declinations.
3. `run_secondary_progressions.ps1` · `run_solar_arc.ps1` — `-TargetDateUtc` = the forecast year's anchor.
4. `run_solar_revolution.ps1` — `-ReturnYear` + relocation coords; true-instant + profection.
5. `run_transits_to_natal.ps1` (range-scan) — **ALL bodies** for the forecast year (`-RangeStart/-RangeEnd -StepDays 4 -Orb 1`). Emits the full timeline + `03_carrier_windows.csv`. Do NOT pre-filter to slow movers: the ledger needs every pass for the two-layer walk and chain analysis (see semantic-base «Полнота обхода»).
6. `build_chart_project.ps1` — assemble methods/ + outputs/ + INDEX from the run-dirs.
7. `run_renderer.ps1` — wheel; then re-run `build_chart_project.ps1` with `-RendererRunDir` to fold the wheel into outputs.
8. `run_phase_vectors.ps1` — phase layer (join copy → outputs/, run-dir in results/).
9. `build_coverage_ledger.ps1` — coverage ledger with `-SolarReturnRunDir` + `-TransitTimelineCsv` (full timeline). Transits auto-split slow/fast; fast auto-quiet.
10. `validate_chart_project.ps1` · `check_chart_provenance.ps1` — both must PASS before reading.

Then interpretation (not orchestrated here): walk → dispositions + version log → reading → report.
Personal charts live ONLY in `.private/charts/<id>/` (gitignored); never commit a filled chart.

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
  -BirthDateTimeUtc "1946-06-14T14:54:00Z" -TargetDateUtc "2026-03-02T00:00:00Z" -Orb 1

# Solar arc directions
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_solar_arc.ps1 `
  -CaseId "demo_solar_arc" -Latitude 44.1 -Longitude 39.07 `
  -BirthDateTimeUtc "1946-06-14T14:54:00Z" -TargetDateUtc "2026-03-02T00:00:00Z" -Orb 1

# Transits to natal (explicit transit recipe)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_transits_to_natal.ps1 `
  -CaseId "demo_transits_now" -Latitude 44.1 -Longitude 39.07 `
  -BirthDateTimeUtc "1946-06-14T14:54:00Z" -TransitDateTimeUtc "2026-03-02T00:00:00Z" -Orb 1

# Renderer (SVG wheel + aspect grid)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_renderer.ps1 `
  -ChartId "trump_19460614_105400_jamaica_ny"

# Build chart project from method runs
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\build_chart_project.ps1 `
  -ChartId "trump_19460614_105400_jamaica_ny" `
  -BirthDateTimeLocal "1946-06-14 10:54:00" -BirthTimezone "+04:00" `
  -BirthDateTimeUtc "1946-06-14T14:54:00Z" -Latitude 40.700000 -Longitude -73.816400 `
  -NatalFailoverRunDir "D:\Dev\CATMEastrolab\artifacts\results\natal_failover_trump_19460614_105400_jamaica_ny_20260302_101307" `
  -HouseRunDir "D:\Dev\CATMEastrolab\artifacts\results\house_placidus_trump_19460614_105400_jamaica_ny_gc_nodes_aspects_orb6_20260302_103757" `
  -SecondaryProgressionsRunDir "D:\Dev\CATMEastrolab\artifacts\results\secondary_progressions_trump_19460614_progressions_now_20260302_110650" `
  -SolarArcRunDir "D:\Dev\CATMEastrolab\artifacts\results\solar_arc_trump_19460614_solar_arc_20260302_105559" `
  -RendererRunDir "D:\Dev\CATMEastrolab\artifacts\results\renderer_trump_19460614_105400_jamaica_ny_20260304_000000"

# Validate chart provenance integrity
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\check_chart_provenance.ps1 `
  -ChartId "trump_19460614_105400_jamaica_ny"

# Validate chart project contracts
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\validate_chart_project.ps1 `
  -ChartId "trump_19460614_105400_jamaica_ny"

# Archive runs safely with index rewrite (dry-run by default)
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\archive_runs.ps1 `
  -Filter "provider_probe_*"

# Execute archive and rewrite only one chart index
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\archive_runs.ps1 `
  -Filter "provider_probe_20260302_130604" -ChartId "trump_19460614_105400_jamaica_ny" -Execute

# Export chart bundle to an existing Obsidian vault
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_obsidian_export.ps1 `
  -ChartId "trump_19460614_105400_jamaica_ny_renderer" `
  -VaultRoot "D:\AstrolabVault" -VaultSubdir "Astrolab/exports"

# Initialize standalone vault and export a chart bundle in one step
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\init_obsidian_vault.ps1 `
  -VaultRoot "D:\AstrolabVault" -ChartId "trump_19460614_105400_jamaica_ny_renderer"

# Extract [DO] nodes from canvas
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_canvas_do_extract.ps1 `
  -CanvasPath "D:\AstrolabVault\Astrolab\exports\trump_19460614_105400_jamaica_ny_renderer\trump_19460614_105400_jamaica_ny_renderer_canvas.canvas" `
  -OutJson "artifacts\skill-smoke\canvas\do_extract.json"

# Upsert AI status node linked to target node
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_canvas_ai_update.ps1 `
  -CanvasPath "D:\AstrolabVault\Astrolab\exports\trump_19460614_105400_jamaica_ny_renderer\trump_19460614_105400_jamaica_ny_renderer_canvas.canvas" `
  -TargetNodeId "<node_id>" -Status in_progress -Message "Started" -Label "ai-status"

# Probe Obsidian MCP over stdio via MCPorter
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_obsidian_mcp_probe.ps1 `
  -VaultRoot "D:\Dev\CATMEastrolab\obsidian-vault" -ServerName "obsidian"

# E2E read/write check over Obsidian MCP
powershell -ExecutionPolicy Bypass -File .\artifacts\mcp-recipes\run_obsidian_mcp_e2e.ps1 `
  -VaultRoot "D:\Dev\CATMEastrolab\obsidian-vault" -ServerName "obsidian"
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

