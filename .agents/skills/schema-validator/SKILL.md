---
name: schema-validator
description: Validates chart.yaml and INDEX.yaml against JSON schemas. Checks file structure, required fields, data types, provenance integrity. Use when user requests "validate chart", "check schema", or before building delivery packs.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  schemas: artifacts/schemas/chart-project/
---

# Schema Validator

Validate chart-project files against JSON schemas and check provenance integrity.

## Quick Start

**Input:**
```yaml
chart_id: tuapse_19820613_133910
validate: [chart.yaml, INDEX.yaml]
check_provenance: true
```

**Output:**
```yaml
overall_status: PASS | FAIL
chart_yaml: {valid: true, errors: []}
index_yaml: {valid: true, errors: []}
provenance_integrity: {valid: true, missing_files: []}
```

## Core Workflow

### 1. Load Schemas

- `artifacts/schemas/chart-project/chart.schema.v1.json`
- `artifacts/schemas/chart-project/index.schema.v1.json`

### 2. Validate chart.yaml

Check required keys: `chart_id`, `birth`, `location`, `structure`

Validate:
- Timezone format: `+04:00` (not `+4`)
- Lat/lon ranges: -90..90, -180..180
- UTC datetime ISO8601

### 3. Validate INDEX.yaml

Check required keys: `chart_id`, `generated_at`, `raw_methods`, `outputs`

### 4. Check Provenance

Verify all `canonical_source` paths exist.

### 5. Generate Report

```yaml
validation_report:
  chart_id: tuapse_19820613_133910
  overall_status: PASS
  errors: [...]
  recommendations: [...]
```

## Reference Documents

- `references/schema-reference.md` — Full schema details
- `artifacts/mcp-recipes/validate_chart_project.ps1` — Reference implementation

## Scripts

- `scripts/validate_chart.py` — Python validator (use for quick validation)

## Common Errors

| Error | Fix |
|---|---|
| `birth.timezone` pattern | Use `+04:00` not `+4` |
| Missing `canonical_source` | File not copied to methods/ |
| `external_source_exists` mismatch | Update after archive |

## Examples

**Valid chart:** `PASS, no errors`

**Invalid timezone:** `FAIL, birth.timezone pattern mismatch`

**Missing file:** `FAIL, provenance_integrity.missing_files`
