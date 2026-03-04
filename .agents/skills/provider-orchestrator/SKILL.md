---
name: provider-orchestrator
description: Manages MCP provider calls with failover, QC, and provenance. Calls primary provider, switches to backup on failure, runs cross-provider QC, tracks provider status. Use when user requests chart calculations, ephemeris data, or any MCP-dependent operation.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  provider-config: artifacts/mcp-recipes/provider_profile.yaml
---

# Provider Orchestrator

Manage MCP provider calls with automatic failover, cross-provider quality control, and provenance tracking.

## Quick Start

**Input:**
```yaml
method: natal | houses | progressions | solar_arc | synastry
params:
  datetime_utc: 1946-06-14T14:54:00Z
  latitude: 40.700000
  longitude: -73.816400
require_qc: true
```

**Output:**
```yaml
status: SUCCESS | DEGRADED | FAILED
provider_used: swissremote
qc_status: PASS | FAIL | SKIPPED
output_dir: artifacts/results/<run_name>/
```

## Core Workflow

### 1. Load Configuration

Read `artifacts/mcp-recipes/provider_profile.yaml`.

### 2. Call Primary (Swiss Ephemeris)

- Timeout: 30s
- Retries: 2 (exponential backoff 1s, 2s)
- On success → proceed to QC

### 3. Failover

```
Primary fails → Retry (max 2) → Switch to backup (ephemeris)
Backup fails → Retry → Switch to fallback (vedastro)
```

**Do NOT failover for:** auth errors, invalid params (fix first).

### 4. Cross-Provider QC

When `require_qc=true`:
1. Call backup for comparison
2. Compute delta per planet
3. PASS if max_delta < 1.0°

### 5. Output Files

In `artifacts/results/<run_name>/`:
- `00_summary.txt`
- `01_provider_status.json`
- `02_qc_report.csv` (if QC)
- `03_planet_positions.csv`
- `04_aspects.json`
- `06_longitudes.csv`

## Reference Documents

- `references/provider-profiles.md` — Provider details
- `references/failover-runbook.md` — Failover decision rules

## Scripts

- `artifacts/mcp-recipes/run_natal_with_failover.ps1`
- `artifacts/mcp-recipes/run_cross_provider_qc.ps1`
- `artifacts/mcp-recipes/lib/mcp_helpers.ps1`

## Examples

**Normal:** `SUCCESS, swissremote, QC PASS`

**Timeout:** `DEGRADED, ephemeris, QC SKIPPED`

**QC Mismatch:** `SUCCESS, swissremote, QC FAIL (Mercury 1.5°)`

## Troubleshooting

| Error | Solution |
|---|---|
| All providers down | Check network |
| QC fails consistently | Increase threshold |
| Auth error | Fix credentials (no failover) |

