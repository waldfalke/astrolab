# External Capabilities Map

Snapshot date: 2026-03-04
Source snapshot run: `artifacts/results/provider_probe_20260304_110257`

## 1) External Providers (MCP HTTP)

| Provider | URL | Family | Health (snapshot) | Tool count | Key tools we use | Current role |
|---|---|---|---|---:|---|---|
| swissremote | https://www.theme-astral.me/mcp | western | healthy | 4 | `calculate_planetary_positions`, `calculate_transits`, `calculate_solar_revolution`, `calculate_synastry` | Primary provider (houses/placidus-oriented workflows) |
| ephem | https://ephemeris.fyi/mcp | western | healthy | 11 | `get_ephemeris_data`, `calculate_aspects`, `get_moon_phase`, `get_daily_events`, `compare_positions` | Backup + continuity + broad raw tooling |
| vedastro | https://mcp.vedastro.org/api/mcp | vedic | healthy | 6 | `get_horoscope_predictions`, `get_astrology_raw_data`, `get_ashtakvarga_data` | Probe-only today (not in production recipes) |

Notes:

- Production profile is defined in `artifacts/mcp-recipes/provider_profile.yaml`.
- Active failover path in recipes is primary `swissremote` -> backup `ephem`.

## 2) MCP Transport/Client Layer

| External component | How used in repo | Key capabilities | Where configured |
|---|---|---|---|
| MCPorter | `npx -y mcporter call` and `list` | Uniform MCP call envelope for HTTP/stdio servers; JSON output mode | `artifacts/mcp-recipes/lib/mcp_helpers.ps1` |
| npm/npx | Runtime delivery for MCPorter | No global install required | `package.json` (`mcporter` dependency) |

Operational behavior already implemented:

- Timeout propagation via `MCPORTER_CALL_TIMEOUT`.
- Retry loop for Swiss primary calls (`MaxAttempts=3`).
- Retry telemetry fields in summaries:
  - `SWISS_RETRY_TOTAL`
  - `SWISS_RETRY_BY_TOOL`

## 3) Runtime Platforms/Libraries

| External component | Purpose | Used by |
|---|---|---|
| PowerShell 7 (`pwsh`) | Main orchestration/runtime for recipes | `artifacts/mcp-recipes/*.ps1` |
| Python 3.11+ | Skill scripts (validation/export) | `.codex/skills/*/scripts/*.py` |
| `pyyaml` | YAML read/write in Python skills | schema-validator, obsidian-export |
| Node.js | host for `npx mcporter` | all MCP recipe calls |

## 4) Current Capability Coverage

Covered now:

1. Planetary/luminary positions
2. Major aspects and deltas
3. Moon phase and daily events
4. House cusps (Placidus) + chart points
5. Secondary progressions
6. Solar arc directions
7. Transit-to-natal matrix
8. Provider failover and cross-provider QC
9. Chart project provenance/schema validation

Known gaps:

1. Declination + parallel/contraparallel
2. Native chart wheel image rendering from external providers (handled internally by renderer roadmap)

## 5) How To Refresh This Map

1. Run provider probe:

```powershell
pwsh artifacts/mcp-recipes/run_mcp_provider_probe.ps1
```

2. Take latest run from:

- `artifacts/results/provider_probe_<timestamp>/`

3. Update this document with:

- health status
- tool counts and key tool names
- role changes (primary/backup/probe-only)

## 6) Decision Guidance

- Need robust production continuity -> use `swissremote` primary + `ephem` backup.
- Need broad raw ephemeris utilities -> use `ephem`.
- Need vedic-specific experimentation -> evaluate `vedastro` in isolated recipe before production adoption.
