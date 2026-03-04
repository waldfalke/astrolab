# Task Log: ASTRO-028 - Dedicated transit-to-natal recipe

**Date:** 2026-03-04
**Status:** DONE
**Priority:** P1

## Problem
Current transit run was done through `run_synastry_matrix.ps1`, which is semantically indirect.

## Implementation
- Added new recipe: `artifacts/mcp-recipes/run_transits_to_natal.ps1`
- Explicit parameters:
  - `-BirthDateTimeUtc`
  - `-TransitDateTimeUtc`
  - shared natal location (`-Latitude`, `-Longitude`)
- Output artifacts:
  - `01_natal_ephemeris.json`
  - `02_transit_ephemeris.json`
  - `03_transit_to_natal_aspects.csv`
  - `04_transit_to_natal_aspects.json`
  - `00_summary.txt`

## Verification
Smoke run:
- Case: `trump_now_smoke`
- Output: `artifacts/results/transit_to_natal_trump_now_smoke_20260304_094011`
- Summary confirms `METHOD=TRANSITS_TO_NATAL`, `MATCH_COUNT=2`.
