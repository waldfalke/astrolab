# Chart Project Schema Reference

## chart.yaml Schema

**File:** `artifacts/schemas/chart-project/chart.schema.v1.json`

### Required Top-Level Keys

```yaml
chart_id: string        # kebab-case or snake_case identifier
display_name: string    # Human-readable name
birth: object           # Birth data
location: object        # Geographic coordinates
structure: object       # Folder structure config
```

### Required Nested Keys

```yaml
birth:
  local_datetime: string    # "YYYY-MM-DD HH:MM:SS"
  timezone: string          # "+04:00" or "Asia/Yekaterinburg"
  utc_datetime: string      # ISO8601 "1946-06-14T14:54:00Z"

location:
  latitude: number          # -90 to +90
  longitude: number         # -180 to +180

structure:
  methods_dir: string       # Usually "methods"
  outputs_dir: string       # Usually "outputs"
  packs_dir: string         # Usually "packs"
```

### Common Validation Errors

| Error | Cause | Fix |
|---|---|---|
| `birth.timezone` pattern mismatch | "+4" instead of "+04:00" | Use HH:MM format |
| `location.latitude` out of range | Value > 90 or < -90 | Check coordinate order |
| Missing `utc_datetime` | Only local time provided | Convert to UTC |

---

## INDEX.yaml Schema

**File:** `artifacts/schemas/chart-project/index.schema.v1.json`

### Required Top-Level Keys

```yaml
chart_id: string          # Must match chart.yaml
generated_at: string      # ISO8601 timestamp
raw_methods: array        # Method run metadata
outputs: array            # Output file mappings
```

### raw_methods Entry Structure

```yaml
- method: string                    # Method name (natal_failover, etc.)
  run_name: string                  # Run folder name
  project_run_dir: string           # Path within chart project
  canonical_run_dir: string         # Canonical path (same as project_run_dir)
  source_run_dir: string            # Original location in artifacts/results/
  external_source_run_dir: string   # Same as source_run_dir
  external_source_run_exists: bool  # True if source still exists
  summary: object                   # Key metrics from 00_summary.txt
```

### outputs Entry Structure

```yaml
- label: string             # Human-readable description
  file: string              # Path relative to chart root (outputs/...)
  source: string            # Original location in methods/
  canonical_source: string  # Canonical path (must exist)
  external_source: string   # Full path to original (optional)
  external_source_exists: bool  # True if external source exists
```

### Provenance Integrity Checks

1. All `canonical_source` paths must exist
2. `external_source` may not exist (if archived)
3. `external_source_exists` flag must be consistent

---

## Validation Functions (from validate_chart_project.ps1)

### Parse-ChartYaml

```powershell
function Parse-ChartYaml {
  # Manual YAML parsing (no external dependencies)
  # Returns: @{ top = @{}; nested = @{} }
}
```

### Validate-ChartSchema

```powershell
function Validate-ChartSchema {
  # Check required keys present
  # Validate timezone pattern
  # Validate lat/lon ranges
}
```

### Check-ProvenanceIntegrity

```powershell
function Check-ProvenanceIntegrity {
  # Verify all canonical_source paths exist
  # Check external_source consistency
  # Return: @{ valid = bool; missing_files = @(); broken_links = @() }
}
```

---

## Example Valid chart.yaml

```yaml
chart_id: trump_19460614_105400_jamaica_ny
display_name: Trump Natal 1946-06-14 10:54:00
birth:
  local_datetime: 1946-06-14 10:54:00
  timezone: +04:00
  utc_datetime: 1946-06-14T14:54:00Z
location:
  latitude: 40.700000
  longitude: -73.816400
structure:
  methods_dir: methods
  outputs_dir: outputs
  packs_dir: packs
```

---

## Example Valid INDEX.yaml Entry

```yaml
chart_id: trump_19460614_105400_jamaica_ny
generated_at: 2026-03-02T14:22:47+03:00
chart_file: chart.yaml
provenance_model: canonical_source_v1

raw_methods:
  - method: natal_failover
    run_name: natal_failover_trump_19460614_105400_jamaica_ny_20260302_101307
    project_run_dir: methods/natal_failover/natal_failover_trump_19460614_105400_jamaica_ny_20260302_101307
    canonical_run_dir: methods/natal_failover/natal_failover_trump_19460614_105400_jamaica_ny_20260302_101307
    source_run_dir: D:\Dev\CATMEastrolab\artifacts\results\...
    external_source_run_dir: D:\Dev\CATMEastrolab\artifacts\results\...
    external_source_run_exists: true
    summary:
      CASE_ID: trump_19460614_105400_jamaica_ny
      RUN_STATUS: FULL
      PROVIDER_USED: swissremote

outputs:
  - label: Natal longitudes
    file: outputs/natal_longitudes.csv
    source: methods/natal_failover/.../06_backup_longitudes.csv
    canonical_source: methods/natal_failover/.../06_backup_longitudes.csv
    external_source: D:\Dev\CATMEastrolab\artifacts\results\...
    external_source_exists: true
```

