# Task Log: ASTRO-018 - Skill: chart-data-preparator

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P0
**Cynefin Domain:** Complicated

## Objective

Create the `chart-data-preparator` skill that builds complete chart-project structures from birth data. This skill orchestrates MCP provider calls, organizes raw outputs, generates INDEX.yaml with provenance tracking, and curates analysis-ready files.

## Skill Location

```
.qwen/skills/chart-data-preparator/
├── SKILL.md
├── scripts/
│   └── build_chart.py (optional - Python helper)
└── references/
    └── chart-project-layout.md
```

## SKILL.md Frontmatter

```yaml
---
name: chart-data-preparator
description: Builds chart-project structures from birth data. Calls MCP providers, organizes raw outputs to methods/, generates INDEX.yaml with canonical_source mappings, curates outputs/. Use when user provides birth datetime + place and requests chart calculation or "build chart project".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: provider-orchestrator skill
---
```

## Implementation Steps

### Step 1: Define Input Requirements

The skill must accept:

**Required:**
- `birth_datetime` — local datetime (YYYY-MM-DD HH:MM:SS)
- `timezone` — UTC offset or IANA timezone
- `location` — city name OR (latitude, longitude)
- `chart_id` — optional, auto-generated if not provided

**Optional:**
- `methods` — list of methods to run (default: `[natal_failover, house_placidus]`)
- `target_date` — for progressions/solar arc (default: now)

### Step 2: Orchestrate Provider Calls

Call `provider-orchestrator` skill for each method:

```
1. natal_failover → primary + backup positions/aspects
2. house_placidus → house cusps + chart points
3. secondary_progressions → progressed positions (if requested)
4. solar_arc → directed positions (if requested)
```

Each call returns:
- Raw output files (CSV, JSON, TXT)
- Run metadata (provider used, status, timestamps)
- QC flags (cross-provider deltas if applicable)

### Step 3: Build Chart-Project Structure

Create folder structure:

```
charts/<chart_id>/
├── chart.yaml           # Birth metadata
├── INDEX.yaml           # Provenance index
├── methods/
│   ├── natal_failover/
│   │   └── <run_folder>/
│   │       └── (raw files copied from artifacts/results/)
│   ├── house_placidus/
│   │   └── <run_folder>/
│   │       └── (raw files)
│   └── ...
└── outputs/
    ├── natal_longitudes.csv
    ├── natal_aspects.json
    ├── houses_placidus.csv
    ├── chart_points.csv
    └── ...
```

### Step 4: Generate chart.yaml

```yaml
chart_id: <id>
display_name: <Location> Natal <YYYY-MM-DD>
birth:
  local_datetime: <datetime>
  timezone: <offset>
  utc_datetime: <ISO8601>
location:
  latitude: <lat>
  longitude: <lon>
structure:
  methods_dir: methods
  outputs_dir: outputs
  packs_dir: packs
```

### Step 5: Generate INDEX.yaml

Structure:

```yaml
chart_id: <id>
generated_at: <ISO8601>
chart_file: chart.yaml
provenance_model: canonical_source_v1
raw_methods:
  - method: natal_failover
    run_name: <run_folder_name>
    project_run_dir: methods/natal_failover/<run_folder>
    canonical_run_dir: methods/natal_failover/<run_folder>
    source_run_dir: <original path in artifacts/results/>
    external_source_run_dir: <same as source>
    external_source_run_exists: true
    summary:
      # Key metrics from run summary
outputs:
  - label: Natal longitudes
    file: outputs/natal_longitudes.csv
    source: methods/natal_failover/<run>/06_backup_longitudes.csv
    canonical_source: methods/natal_failover/<run>/06_backup_longitudes.csv
    external_source: <full path>
    external_source_exists: true
  # ... more outputs
```

### Step 6: Copy Files

**To methods/:**
- Copy entire run folders from `artifacts/results/<run_name>/` to `charts/<id>/methods/<method>/<run_name>/`

**To outputs/:**
- Copy curated files from methods to outputs with stable names
- Use mapping from existing `build_chart_project.ps1` logic

### Step 7: Validate

Call `schema-validator` skill to validate:
- `chart.yaml` against `chart.schema.v1.json`
- `INDEX.yaml` against `index.schema.v1.json`

## Important Nuances

### 1. Provenance Integrity

- `canonical_source` in INDEX.yaml must point to **project-internal** paths (relative to chart root)
- `external_source` points to original location in `artifacts/results/` or archive
- If files are archived, `external_source_exists` may be `false` but `canonical_source` must always exist

### 2. Method Naming Consistency

Use exact method names from existing recipes:
- `natal_failover` (not just `natal`)
- `house_placidus` (not just `houses`)
- `secondary_progressions`
- `solar_arc`

### 3. File Naming in outputs/

Follow existing conventions from `build_chart_project.ps1`:

| Output File | Source Pattern |
|---|---|
| `natal_longitudes.csv` | `*/06_backup_longitudes.csv` |
| `natal_aspects.json` | `*/04_backup_aspects.json` |
| `houses_placidus.csv` | `*/02_houses_placidus.csv` |
| `chart_points.csv` | `*/03_chart_points.csv` |
| `planets_primary.csv` | `*/04_planets_primary.csv` |

### 4. Error Handling

- If provider call fails, mark method status as `DEGRADED` or `UNAVAILABLE`
- Continue with remaining methods (don't abort entire chart build)
- Record failure in INDEX.yaml with error message

### 5. Idempotency

- Running the skill twice with same `chart_id` should:
  - Preserve existing `methods/` folders (append new runs with timestamps)
  - Update `INDEX.yaml` with new provenance entries
  - Not duplicate outputs (overwrite with same stable names)

### 6. Archive Awareness

- Check if source runs have been archived before copying
- Use `archive_runs.ps1` verification report format to track moves
- Update `external_source_run_dir` if archive location differs

## Examples

### Example 1: Basic Natal Chart

**User says:** "Build natal chart for June 13, 1982, 13:39, Jamaica Queens NY"

**Actions:**
1. Parse birth data → `1946-06-14 10:54:00`, UTC+4, Jamaica Queens NY (40.700000, -73.816400)
2. Generate chart_id: `trump_19460614_105400_jamaica_ny`
3. Call provider-orchestrator for `natal_failover` + `house_placidus`
4. Build chart-project structure
5. Validate schemas

**Result:** `charts/trump_19460614_105400_jamaica_ny/` with all files

### Example 2: Full Workbench

**User says:** "Натал + прогноз для trump_19460614_105400_jamaica_ny"

**Actions:**
1. Check if chart exists → yes, load chart.yaml
2. Call provider-orchestrator for `secondary_progressions` + `solar_arc`
3. Add new methods to existing chart-project
4. Update INDEX.yaml with new provenance entries

## Troubleshooting

### Error: Provider unavailable

- **Cause:** MCP server not responding, auth failure
- **Solution:** Check provider-orchestrator status, verify credentials in `provider_profile.yaml`

### Error: INDEX.yaml validation fails

- **Cause:** Missing `canonical_source` or broken path
- **Solution:** Verify all output files exist in `methods/` before generating INDEX

### Error: Duplicate chart_id

- **Cause:** Chart already exists with same ID
- **Solution:** Append timestamp to new runs, don't overwrite existing methods

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-007 | Chart project systemization — this skill implements the builder |
| ASTRO-011 | Core backbone extraction — skill extracts logic from recipes |
| ASTRO-014 | Schema validation — skill calls validator after build |

## Available Code / Tools

### PowerShell Scripts
- `artifacts/mcp-recipes/build_chart_project.ps1` — Main chart project builder
- `artifacts/mcp-recipes/run_natal_with_failover.ps1` — Natal calculation
- `artifacts/mcp-recipes/run_house_layer_placidus.ps1` — House calculation
- `artifacts/mcp-recipes/run_secondary_progressions.ps1` — Progressions
- `artifacts/mcp-recipes/run_solar_arc.ps1` — Solar arc directions

### MCP Providers
- Swiss Ephemeris: `https://www.theme-astral.me/mcp` (primary)
- Ephemeris: `https://ephemeris.fyi/mcp` (backup)

### Libraries
- `artifacts/mcp-recipes/lib/mcp_helpers.ps1` — MCP call helpers

### Schemas
- `artifacts/schemas/chart-project/chart.schema.v1.json`
- `artifacts/schemas/chart-project/index.schema.v1.json`

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/chart-data-preparator/`
- [ ] Skill can build chart-project from birth data alone
- [ ] INDEX.yaml generated with correct `canonical_source` mappings
- [ ] All output files copied to `outputs/` with stable names
- [ ] Schema validation passes after build
- [ ] Skill handles provider failures gracefully (degraded mode)
- [ ] Idempotent: running twice doesn't break chart structure

