# Task Log: ASTRO-031 - Swiss retry observability

**Date:** 2026-03-04
**Status:** DONE
**Priority:** P2

## Problem
Transient Swiss provider issues were not reflected in run summaries.

## Implementation
- Added retry telemetry in `artifacts/mcp-recipes/lib/mcp_helpers.ps1`:
  - `Reset-SwissRetryTelemetry`
  - `Get-SwissRetryTelemetry`
  - retry counters per tool and total
- Integrated telemetry into summaries for:
  - `run_secondary_progressions.ps1`
  - `run_solar_arc.ps1`
- New summary fields:
  - `SWISS_RETRY_TOTAL`
  - `SWISS_RETRY_BY_TOOL`

## Verification
Smoke run:
- `solar_arc_telemetry_smoke_20260304_094040`
- `00_summary.txt` includes new telemetry fields.
