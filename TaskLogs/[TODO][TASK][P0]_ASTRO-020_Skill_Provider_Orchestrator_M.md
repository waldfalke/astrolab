# Task Log: ASTRO-020 - Skill: provider-orchestrator

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P0
**Cynefin Domain:** Complicated

## Objective

Create the `provider-orchestrator` skill that manages MCP provider calls with failover logic, cross-provider QC, and provenance tracking. This skill abstracts provider complexity and ensures reliable ephemeris calculations.

## Skill Location

```
.qwen/skills/provider-orchestrator/
├── SKILL.md
├── scripts/
│   └── mcp_client.py (optional - MCP call helper)
└── references/
    ├── provider-profiles.md
    └── failover-runbook.md
```

## SKILL.md Frontmatter

```yaml
---
name: provider-orchestrator
description: Manages MCP provider calls with failover, QC, and provenance. Calls primary provider, switches to backup on failure, runs cross-provider QC, tracks provider status. Use when user requests chart calculations, ephemeris data, or any MCP-dependent operation.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  provider-config: artifacts/mcp-recipes/provider_profile.yaml
---
```

## Implementation Steps

### Step 1: Load Provider Configuration

Read `provider_profile.yaml`:

```yaml
providers:
  primary:
    name: swissremote
    url: https://www.theme-astral.me/mcp
    tools:
      - get_planet_positions
      - get_house_cusps
      - get_aspects
      - get_synastry
    auth:
      type: api_key
      key_env: SWISS_REMOTE_API_KEY

  backup:
    name: ephemeris
    url: https://ephemeris.fyi/mcp
    tools:
      - positions
      - aspects
      - moon_phase
    auth:
      type: none

  fallback:
    name: vedastro
    url: https://mcp.vedastro.org/api/mcp
    tools:
      - GetPlanetaryPositions
    auth:
      type: api_key
      key_env: VEDASTRO_API_KEY

failover:
  max_retries: 2
  timeout_seconds: 30
  qc_threshold_deg: 1.0  # max acceptable delta between providers
```

### Step 2: Define Call Interface

**Input:**
```python
{
    "method": "natal" | "houses" | "progressions" | "solar_arc" | "synastry",
    "params": { ... },  # method-specific parameters
    "require_qc": True | False,
    "chart_id": "optional_id"
}
```

**Output:**
```python
{
    "status": "SUCCESS" | "DEGRADED" | "FAILED",
    "provider_used": "swissremote",
    "provider_fallback": False,
    "qc_status": "PASS" | "FAIL" | "SKIPPED",
    "qc_delta_deg": 0.02,
    "output_dir": "artifacts/results/<run_name>/",
    "files": ["00_summary.txt", "06_backup_longitudes.csv", ...],
    "provenance": {
        "run_name": "natal_trump_19460614_105400_jamaica_ny_20260304_141520",
        "started_at": "2026-03-04T14:15:20Z",
        "completed_at": "2026-03-04T14:15:35Z",
        "provider_calls": [
            {"provider": "swissremote", "tool": "get_planet_positions", "status": "OK"},
            {"provider": "ephemeris", "tool": "positions", "status": "OK", "purpose": "QC"}
        ]
    }
}
```

### Step 3: Implement Failover Logic

```
1. Attempt primary provider
   ├─ Success → proceed to QC (if enabled)
   └─ Failure → retry (max 2 times)
       └─ Still failing → switch to backup

2. Attempt backup provider
   ├─ Success → mark as DEGRADED, proceed
   └─ Failure → retry
       └─ Still failing → switch to fallback

3. Attempt fallback provider
   ├─ Success → mark as DEGRADED, skip QC
   └─ Failure → return FAILED
```

### Step 4: Implement Cross-Provider QC

When `require_qc=True`:

```
1. Call primary provider → get positions P1
2. Call backup provider → get positions P2
3. Compute delta for each planet: |P1_lon - P2_lon| (shortest arc)
4. If max_delta < qc_threshold → QC PASS
5. If max_delta >= qc_threshold → QC FAIL, flag in output
```

**QC Output:**
```csv
planet,primary_lon,backup_lon,delta_deg,status
Sun,72.453,72.451,0.002,OK
Moon,156.892,156.901,0.009,OK
Mercury,85.234,85.240,0.006,OK
...
max_delta: 0.009
threshold: 1.0
qc_status: PASS
```

### Step 5: Track Provenance

Record every provider call:

```yaml
provenance:
  run_name: <method>_<chart_id>_<timestamp>
  method: natal_failover
  chart_id: trump_19460614_105400_jamaica_ny
  started_at: 2026-03-04T14:15:20Z
  completed_at: 2026-03-04T14:15:35Z
  provider_calls:
    - sequence: 1
      provider: swissremote
      tool: get_planet_positions
      params: { datetime: "1946-06-14T14:54:00Z", lat: 40.700000, lon: -73.816400 }
      status: OK
      duration_ms: 1250
      response_hash: sha256:abc123...
    - sequence: 2
      provider: ephemeris
      tool: positions
      params: { ... }
      status: OK
      duration_ms: 890
      purpose: QC
      response_hash: sha256:def456...
  qc_result:
    performed: true
    max_delta_deg: 0.009
    threshold_deg: 1.0
    status: PASS
```

### Step 6: Generate Output Files

Create standard output structure in `artifacts/results/<run_name>/`:

```
<run_name>/
├── 00_summary.txt        # Human-readable summary
├── 01_provider_status.json
├── 02_qc_report.csv      # If QC performed
├── 03_planet_positions.csv
├── 04_aspects.json
├── 05_moon_phase.json
├── 06_longitudes.csv
└── PACK_MANIFEST.yaml    # Ready status
```

## Important Nuances

### 1. Provider Tool Mapping

Different providers use different tool names. Create abstraction layer:

| Abstract Tool | Swiss Remote | Ephemeris | Vedastro |
|---|---|---|---|
| `get_positions` | `get_planet_positions` | `positions` | `GetPlanetaryPositions` |
| `get_houses` | `get_house_cusps` | `house_cusps` | `GetHouseCusps` |
| `get_aspects` | `get_aspects` | `aspects` | `GetAspects` |

### 2. Response Normalization

Each provider returns different formats. Normalize to common schema:

```python
# Swiss Remote response
{
    "planets": [
        {"name": "Sun", "longitude": 72.453, "sign": "Gemini", ...}
    ]
}

# Ephemeris response
{
    "data": {
        "bodies": [
            {"id": "sun", "lon": 72.451, "sign": "gemini", ...}
        ]
    }
}

# Normalized output
{
    "planets": [
        {"name": "Sun", "longitude": 72.453, "sign": "Gemini", "source": "swissremote"}
    ]
}
```

### 3. Failover Status Reporting

Always report which provider was actually used:

```
PROVIDER STATUS:
  Primary (swissremote): AVAILABLE → USED
  Backup (ephemeris): AVAILABLE → QC ONLY
  Fallback (vedastro): NOT USED

RUN STATUS: FULL (primary available, QC passed)
```

### 4. Timeout Handling

- Set per-call timeout (30 seconds default)
- Timeout counts as failure → trigger failover
- Log timeout duration and provider

### 5. Auth Error Handling

- Auth errors should NOT trigger failover (config issue, not provider issue)
- Report auth error clearly: "AUTH_FAILED: check API key"
- User must fix credentials before retry

### 6. Rate Limiting

- Track calls per provider per minute
- If rate limited, wait and retry (exponential backoff)
- If still limited after retries, failover to backup

### 7. Idempotency

- Same input → same run_name (based on chart_id + timestamp + method)
- Check if run already exists before calling providers
- If exists, return cached result (unless force_refresh=True)

## Examples

### Example 1: Normal Natal Calculation

**User says:** "Calculate natal positions for June 13, 1982, 13:39, Jamaica Queens NY"

**Actions:**
1. Parse birth data
2. Call primary (swissremote) → success
3. Call backup (ephemeris) for QC → success
4. Compare positions → delta 0.009° < 1.0° threshold → QC PASS
5. Generate output files

**Result:**
```
STATUS: SUCCESS
PROVIDER: swissremote
QC: PASS (max delta 0.009°)
OUTPUT: artifacts/results/natal_trump_19460614_105400_jamaica_ny_20260304_141520/
```

### Example 2: Primary Unavailable

**User says:** "Calculate houses (Placidus) for same chart"

**Actions:**
1. Call primary → timeout after 30s
2. Retry → connection refused
3. Failover to backup (ephemeris) → success
4. No QC possible (only one provider available)
5. Generate output with DEGRADED status

**Result:**
```
STATUS: DEGRADED
PROVIDER: ephemeris (backup)
QC: SKIPPED (no secondary provider)
OUTPUT: artifacts/results/houses_tuapse_.../
```

### Example 3: QC Mismatch

**User says:** "Run cross-provider QC check"

**Actions:**
1. Call both providers
2. Compare positions
3. Find Mercury delta = 1.5° > 1.0° threshold
4. Flag QC FAIL for Mercury

**Result:**
```
STATUS: SUCCESS (with QC warnings)
PROVIDER: swissremote
QC: FAIL
  - Mercury: delta 1.5° (threshold 1.0°)
  - All other planets: OK
ACTION: Review Mercury calculation manually
```

## Troubleshooting

### Error: All providers unavailable

- **Cause:** Network issue, all MCP servers down
- **Solution:** Check network, verify provider URLs, retry later

### Error: QC fails consistently

- **Cause:** Providers use different ephemerides (Swiss vs. NASA)
- **Solution:** Increase QC threshold or investigate ephemeris difference

### Error: Rate limited

- **Cause:** Too many calls in short time
- **Solution:** Add delay between calls, implement request queue

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-003 | Multi-provider MCP profile — this skill implements the profile |
| ASTRO-004 | House-layer capability — skill handles house calculations |
| ASTRO-011 | Core backbone extraction — skill extracts provider logic |
| ASTRO-017 | Skills architecture — this is a core infrastructure skill |

## Available Code / Tools

### PowerShell Scripts
- `artifacts/mcp-recipes/run_natal_with_failover.ps1` — Failover logic reference
- `artifacts/mcp-recipes/run_cross_provider_qc.ps1` — QC comparison
- `artifacts/mcp-recipes/run_mcp_provider_probe.ps1` — Provider health check

### Configuration
- `artifacts/mcp-recipes/provider_profile.yaml` — Provider configuration
- `artifacts/mcp-recipes/failover_runbook.md` — Failover decision rules

### MCP Providers
- Swiss Ephemeris (primary): `https://www.theme-astral.me/mcp`
  - Tools: `get_planet_positions`, `get_house_cusps`, `get_aspects`, `get_synastry`
- Ephemeris (backup): `https://ephemeris.fyi/mcp`
  - Tools: `positions`, `aspects`, `moon_phase`

### Libraries
- `artifacts/mcp-recipes/lib/mcp_helpers.ps1`
  - `Invoke-SwissPrimaryToolJson` — Call primary provider
  - `Invoke-EphemToolJson` — Call backup provider
  - `Get-SwissBodyLongitudes` — Parse Swiss response
  - `Get-BodyLongitudes` — Parse Ephemeris response

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/provider-orchestrator/`
- [ ] Skill can call primary provider and handle failures
- [ ] Failover to backup works when primary unavailable
- [ ] Cross-provider QC implemented with configurable threshold
- [ ] Provenance tracking records all provider calls
- [ ] Output files generated in standard format
- [ ] Provider status reported clearly (FULL/DEGRADED/FAILED)
- [ ] Auth errors handled separately from provider failures

