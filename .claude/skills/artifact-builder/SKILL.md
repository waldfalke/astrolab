---
name: artifact-builder
description: Assembles delivery packs from chart-project outputs. Validates against schemas, builds PACK_MANIFEST.yaml, creates client-ready folders, manages archive with index rewrite. Use when user requests "prepare delivery pack", "archive old runs", or "package results for client".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: schema-validator skill
---

# Artifact Builder

Assemble delivery packs from chart-project outputs with validation and QC gates.

## Quick Start

**Input:**
```yaml
chart_id: trump_19460614_105400_jamaica_ny
pack_type: natal | forecast | synastry | full_workbench
include_qc: true
```

**Output:**
```yaml
pack_id: trump_19460614_105400_jamaica_ny_natal_20260304
status: READY | INCOMPLETE | BLOCKED
pack_dir: packs/<pack_id>/
```

## Core Workflow

### 1. Validate Chart-Project

Call `schema-validator`. Block if FAIL.

### 2. Check Methods

| Pack Type | Required Methods |
|---|---|
| natal | natal_failover, house_placidus |
| forecast | secondary_progressions, solar_arc |
| full_workbench | all methods |

### 3. Build PACK_MANIFEST.yaml

```yaml
pack_id: trump_19460614_105400_jamaica_ny_natal_20260304
methods_included:
  - method: natal_failover
    status: READY
qc_status:
  provider_qc: PASS
  schema_qc: PASS
delivery_status: READY
```

### 4. Create Pack Structure

```
packs/<pack_id>/
├── PACK_MANIFEST.yaml
├── 00_summary.txt
├── 01_natal/
└── 02_qc/
```

### 5. Copy Files

Map `outputs/` → pack folders with stable names.

## Archive Operations

### Archive Old Runs

1. Find runs older than 30 days
2. Move to `artifacts/results/_archive/<batch>/`
3. Rewrite INDEX.yaml `external_source` paths
4. Generate verification report

## Reference Documents

- `references/archive-runbook.md` — Archive procedure
- `artifacts/mcp-recipes/build_pack_manifest.ps1` — Reference

## Status Definitions

| Status | Meaning |
|---|---|
| READY | All files present, validation passed |
| INCOMPLETE | Some files missing |
| BLOCKED | Schema validation failed |

## Examples

**Natal pack:** `READY, 8 files`

**Incomplete forecast:** `INCOMPLETE, missing secondary_progressions`

**Archive:** `4 runs archived, INDEX.yaml updated`

