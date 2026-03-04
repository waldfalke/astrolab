# Task Log: ASTRO-029 - Synastry CSV invariant formatting

**Date:** 2026-03-04
**Status:** DONE
**Priority:** P1

## Problem
`run_synastry_matrix.ps1` wrote locale-dependent decimals (comma in RU locale).

## Implementation
- Replaced `Export-Csv` with `Write-InvariantCsv` from helper library.
- Added empty-result schema path to preserve stable CSV columns.

## Verification
Smoke run:
- Case: `trump_csv_smoke`
- Output: `artifacts/results/synastry_trump_csv_smoke_20260304_094013/03_synastry_aspect_matrix.csv`
- Decimal format now invariant dot-decimal (`82.928095`, not `82,928095`).
