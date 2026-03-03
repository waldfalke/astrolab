---
name: chart-data-preparator
description: Builds chart-project structures from birth data. Calls MCP providers via provider-orchestrator, organizes raw outputs to methods/, generates INDEX.yaml with canonical_source mappings, curates outputs/. Use when user provides birth datetime + place and requests chart calculation or "build chart project".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: provider-orchestrator skill
---

# Chart Data Preparator

Build complete chart-project structures from birth data.

## Quick Start

**Input:**
```yaml
birth_datetime: 1982-06-13 13:39:10
timezone: +04:00
location: Tuapse (44.100833, 39.083333)
methods: [natal_failover, house_placidus]
```

**Output:**
```
charts/<chart_id>/
├── chart.yaml
├── INDEX.yaml
├── methods/<method>/<run>/
└── outputs/
```

## Core Workflow

### 1. Parse Birth Data

Extract: datetime, timezone, UTC, lat/lon, chart_id (auto-gen).

### 2. Call Provider-Orchestrator

For each method:
- `natal_failover` → positions, aspects
- `house_placidus` → houses, chart points
- `secondary_progressions` → progressed positions
- `solar_arc` → directed positions

### 3. Create Structure

```bash
charts/<chart_id>/
  chart.yaml        # Create
  INDEX.yaml        # Create
  methods/          # Copy runs from artifacts/results/
  outputs/          # Copy curated files
```

### 4. Generate chart.yaml

```yaml
chart_id: tuapse_19820613_133910
display_name: Tuapse Natal 1982-06-13 13:39:10
birth:
  local_datetime: 1982-06-13 13:39:10
  timezone: +04:00
  utc_datetime: 1982-06-13T09:39:10Z
location:
  latitude: 44.100833
  longitude: 39.083333
structure:
  methods_dir: methods
  outputs_dir: outputs
  packs_dir: packs
```

### 5. Generate INDEX.yaml

```yaml
chart_id: tuapse_19820613_133910
generated_at: 2026-03-04T14:30:00Z
provenance_model: canonical_source_v1
raw_methods: [...]
outputs:
  - label: Natal longitudes
    file: outputs/natal_longitudes.csv
    canonical_source: methods/natal_failover/.../06_backup_longitudes.csv
```

### 6. Validate

Call `schema-validator` skill.

## Reference Documents

- `charts/README.md` — Chart project structure
- `artifacts/mcp-recipes/build_chart_project.ps1` — Reference implementation

## File Mapping

| Output | Source |
|---|---|
| `natal_longitudes.csv` | `*/06_backup_longitudes.csv` |
| `natal_aspects.json` | `*/04_backup_aspects.json` |
| `houses_placidus.csv` | `*/02_houses_placidus.csv` |
| `planets_primary.csv` | `*/04_planets_primary.csv` |

## Examples

**New natal:** `charts/tuapse_19820613_133910/` created

**Add forecast:** INDEX.yaml updated with new methods

## Troubleshooting

| Error | Solution |
|---|---|
| Provider unavailable | Check provider-orchestrator status |
| INDEX.yaml validation fails | Verify canonical_source paths exist |
| Duplicate chart_id | Append new runs, don't overwrite |
