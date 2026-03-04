# Task Log: ASTRO-021 - Skill: artifact-builder

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

Create the `artifact-builder` skill that assembles delivery packs from chart-project outputs. This skill validates outputs against schemas, builds PACK_MANIFEST.yaml, generates client-ready folders, and manages archive operations.

## Skill Location

```
.qwen/skills/artifact-builder/
├── SKILL.md
├── scripts/
│   ├── build_pack.py
│   └── archive_runs.py
└── references/
    ├── pack-templates.md
    └── archive-runbook.md
```

## SKILL.md Frontmatter

```yaml
---
name: artifact-builder
description: Assembles delivery packs from chart-project outputs. Validates against schemas, builds PACK_MANIFEST.yaml, creates client-ready folders, manages archive with index rewrite. Use when user requests "prepare delivery pack", "archive old runs", or "package results for client".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: schema-validator skill
---
```

## Implementation Steps

### Step 1: Validate Chart-Project

Before building pack, call `schema-validator`:

```python
validation_result = call_skill('schema-validator', {
    "chart_id": chart_id,
    "validate": ["chart.yaml", "INDEX.yaml"]
})

if not validation_result['valid']:
    return {
        "status": "BLOCKED",
        "reason": "Schema validation failed",
        "errors": validation_result['errors']
    }
```

### Step 2: Build PACK_MANIFEST.yaml

Generate manifest with delivery status:

```yaml
pack_id: trump_19460614_105400_jamaica_ny_natal_20260304
chart_id: trump_19460614_105400_jamaica_ny
created_at: 2026-03-04T14:30:00Z
pack_type: natal | forecast | synastry | full_workbench

methods_included:
  - method: natal_failover
    run_name: natal_failover_trump_19460614_105400_jamaica_ny_20260304_141520
    status: READY | INCOMPLETE | MISSING
    files:
      - file: outputs/natal_longitudes.csv
        included: true
      - file: outputs/natal_aspects.json
        included: true
  - method: house_placidus
    run_name: house_placidus_trump_19460614_105400_jamaica_ny_20260304_142030
    status: READY
    files:
      - file: outputs/houses_placidus.csv
        included: true

qc_status:
  provider_qc: PASS | FAIL | SKIPPED
  schema_qc: PASS | FAIL
  cross_provider_delta_deg: 0.009

delivery_status: READY | INCOMPLETE
ready_files: 8
incomplete_files: 0
missing_files: 0
```

### Step 3: Create Delivery Pack Structure

```
packs/<pack_id>/
├── PACK_MANIFEST.yaml
├── 00_summary.txt           # Human-readable overview
├── 01_natal/
│   ├── positions.csv
│   ├── aspects.json
│   └── houses.csv
├── 02_forecast/
│   ├── progressions.csv
│   └── solar_arc.csv
├── 03_qc/
│   ├── provider_status.json
│   └── cross_provider_qc.csv
└── 04_interpretation/       # Optional
    └── analysis_notes.md
```

### Step 4: Copy and Rename Files

Map from chart-project outputs to pack structure:

| Source (outputs/) | Destination (packs/) |
|---|---|
| `natal_longitudes.csv` | `01_natal/positions.csv` |
| `natal_aspects.json` | `01_natal/aspects.json` |
| `houses_placidus.csv` | `01_natal/houses.csv` |
| `secondary_progressions_summary.txt` | `02_forecast/progressions.csv` |
| `solar_arc_directed_positions.csv` | `02_forecast/solar_arc.csv` |

### Step 5: Generate Summary

Create `00_summary.txt`:

```
CHART: Trump Natal 1946-06-14 10:54:00
PACK: trump_19460614_105400_jamaica_ny_natal_20260304
CREATED: 2026-03-04 14:30:00

METHODS INCLUDED:
  ✓ natal_failover (FULL - primary available, QC passed)
  ✓ house_placidus (FULL - Placidus houses calculated)

DELIVERY STATUS: READY

FILES:
  - 01_natal/positions.csv (10 planets)
  - 01_natal/aspects.json (14 aspects)
  - 01_natal/houses.csv (12 houses)
  ...

QC REPORT:
  - Provider: swissremote (primary)
  - Cross-check: ephemeris (delta: 0.009° - PASS)
```

### Step 6: Archive Old Runs

When archiving, update INDEX.yaml external links:

```python
def archive_runs(chart_id, older_than_days=30):
    """
    Move old run folders to archive batch.
    Rewrite INDEX.yaml external_source paths.
    Emit verification report.
    """
    # 1. Identify runs older than threshold
    old_runs = find_runs_older_than(chart_id, older_than_days)
    
    # 2. Create archive batch folder
    batch_name = f"{chart_id}_{timestamp}_archive"
    archive_path = f"artifacts/results/_archive/{batch_name}/"
    
    # 3. Move runs to archive
    for run in old_runs:
        move(run['project_run_dir'], archive_path)
    
    # 4. Rewrite INDEX.yaml external_source paths
    update_index_external_sources(chart_id, archive_path)
    
    # 5. Generate verification report
    report = {
        "archived_runs": len(old_runs),
        "index_updated": True,
        "verification": verify_archive_integrity(chart_id)
    }
    
    return report
```

### Step 7: Generate Archive Verification Report

```json
{
  "archive_batch": "trump_19460614_20260304_143000_archive",
  "archived_at": "2026-03-04T14:30:00Z",
  "runs_archived": 4,
  "archive_location": "artifacts/results/_archive/trump_19460614_20260304_143000_archive/",
  "index_rewrite": {
    "chart_id": "trump_19460614_105400_jamaica_ny",
    "external_sources_updated": 16,
    "all_paths_valid": true
  },
  "verification": {
    "all_files_moved": true,
    "all_links_updated": true,
    "canonical_sources_intact": true
  }
}
```

## Important Nuances

### 1. Pack Type Variants

Different pack types include different methods:

| Pack Type | Methods Included |
|---|---|
| `natal` | natal_failover, house_placidus |
| `forecast` | secondary_progressions, solar_arc |
| `synastry` | synastry_matrix (both charts) |
| `full_workbench` | all methods |

### 2. Status Definitions

| Status | Meaning |
|---|---|
| `READY` | All required files present, validation passed |
| `INCOMPLETE` | Some files present but not all required |
| `MISSING` | Method run not found in chart-project |
| `BLOCKED` | Schema validation failed, cannot build pack |

### 3. Archive Integrity

After archive, verify:
- All `canonical_source` paths still exist (in `methods/`)
- All `external_source` paths updated to archive location
- No broken links in INDEX.yaml

### 4. Client Delivery Conventions

- Use stable file names in packs (not run-specific names)
- Include QC report for transparency
- Add human-readable summary at root
- Keep original data files immutable (copy, don't move)

### 5. Idempotency

- Building pack twice with same inputs → same output
- Check if pack already exists before creating
- If exists, either overwrite (force=True) or skip

## Examples

### Example 1: Build Natal Delivery Pack

**User says:** "Prepare delivery pack for trump_19460614_105400_jamaica_ny natal"

**Actions:**
1. Validate chart.yaml and INDEX.yaml
2. Check natal_failover and house_placidus methods present
3. Build PACK_MANIFEST.yaml with READY status
4. Create packs/<pack_id>/ structure
5. Copy and rename files
6. Generate 00_summary.txt

**Result:**
```
packs/trump_19460614_105400_jamaica_ny_natal_20260304/
├── PACK_MANIFEST.yaml (READY)
├── 00_summary.txt
├── 01_natal/positions.csv
├── 01_natal/aspects.json
└── 01_natal/houses.csv
```

### Example 2: Archive Old Runs

**User says:** "Archive runs older than 30 days for trump_19460614_105400_jamaica_ny"

**Actions:**
1. Find runs in methods/ older than 30 days
2. Create archive batch folder
3. Move old runs to archive
4. Rewrite INDEX.yaml external_source paths
5. Verify all canonical_source paths still valid
6. Generate verification report

**Result:**
```
Archive complete:
  - 4 runs archived to artifacts/results/_archive/...
  - INDEX.yaml external paths updated (16 entries)
  - All canonical sources intact
  - Verification: PASS
```

### Example 3: Incomplete Pack

**User says:** "Build forecast pack (no progressions calculated yet)"

**Actions:**
1. Validate chart-project
2. Check for secondary_progressions → MISSING
3. Check for solar_arc → READY
4. Build PACK_MANIFEST.yaml with INCOMPLETE status
5. Include only available methods

**Result:**
```
PACK_MANIFEST.yaml:
  delivery_status: INCOMPLETE
  missing_methods:
    - secondary_progressions
  ready_methods:
    - solar_arc
```

## Troubleshooting

### Error: Schema validation failed

- **Cause:** chart.yaml or INDEX.yaml doesn't match schema
- **Solution:** Run schema-validator, fix errors before building pack

### Error: Missing required files

- **Cause:** Method run incomplete, outputs not copied
- **Solution:** Re-run method or mark pack as INCOMPLETE

### Error: Archive breaks external links

- **Cause:** External source paths not rewritten correctly
- **Solution:** Run archive verification, manually fix broken links

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-001 | MCP result artifact pack — this skill implements pack builder |
| ASTRO-005 | Client output packs — skill creates delivery-ready folders |
| ASTRO-015 | Safe archive — skill implements archive with index rewrite |

## Available Code / Tools

### PowerShell Scripts
- `artifacts/mcp-recipes/build_pack_manifest.ps1` — Pack manifest builder
- `artifacts/mcp-recipes/archive_runs.ps1` — Archive with index rewrite
- `artifacts/mcp-recipes/build_chart_project.ps1` — Chart project structure

### Templates
- `artifacts/mcp-recipes/` — PACK_MANIFEST.yaml format reference

### Configuration
- `artifacts/schemas/artifact-serialization/` — Serialization schemas

### Archive Logic (from archive_runs.ps1)
- `New-ArchiveBatch` — Create archive folder
- `Move-RunToArchive` — Move run folders
- `Rewrite-IndexExternalSources` — Update INDEX.yaml paths
- `Verify-ArchiveIntegrity` — Generate verification report

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/artifact-builder/`
- [ ] Skill validates chart-project before building pack
- [ ] PACK_MANIFEST.yaml generated with correct status (READY/INCOMPLETE)
- [ ] Delivery pack structure follows convention
- [ ] Files copied and renamed correctly
- [ ] Archive operation rewrites INDEX.yaml external paths
- [ ] Archive verification report generated
- [ ] Idempotent: building twice produces same result

