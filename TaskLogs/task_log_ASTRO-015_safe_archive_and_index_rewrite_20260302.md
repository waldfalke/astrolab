# Task Log: ASTRO-015 - Safe Archiving and Index Rewrite

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Completed

## Objective

Archive run folders without breaking chart-level discoverability and index links.

## Problem Statement

1. Manual archiving moves run directories outside expected paths.
2. Chart indexes may continue to reference stale external locations.
3. No single archival command performs move + index rewrite + verification.

## Scope

1. Implement archive utility:
   - `archive_runs.ps1`
2. Operations in one transaction-like flow:
   - detect targets
   - move to archive root
   - update chart indexes (external reference fields)
   - verify post-archive consistency
3. Emit archive report with moved items and affected chart IDs.

## Out of Scope

1. Deduplicated content-addressable storage.
2. Multi-host archive replication.

## Done Definition

1. Archiving command supports dry-run and execute modes.
2. All affected chart indexes are updated automatically.
3. Archive report generated and stored with timestamp.

## Implementation

1. Added recipe:
   - `artifacts/mcp-recipes/archive_runs.ps1`
2. Implemented flow:
   - target detection by `-Filter`
   - dry-run and execute modes
   - archive batching under `artifacts/results/_archive/archive_batch_<timestamp>`
   - `INDEX.yaml` external link rewrite for:
     - `source_run_dir`
     - `external_source_run_dir`
     - `external_source`
   - post-rewrite external-link verification
   - JSON report emission
3. Hardened edge cases:
   - fixed PowerShell inline conditional syntax in report objects
   - ensured report parent directory creation for empty and non-empty runs

## Verification

1. Dry-run on real chart:
   - `archive_runs.ps1 -Filter "provider_probe_20260302_130604" -ChartId "tuapse_19820613_133910"`
   - Result: `CANDIDATE_RUNS=1`, `AFFECTED_CHARTS=0`, `VERIFICATION_FAIL_CHARTS=0`
2. Execute on real chart:
   - `archive_runs.ps1 -Filter "provider_probe_20260302_130604" -ChartId "tuapse_19820613_133910" -Execute`
   - Result: run moved to archive batch, zero missing external refs.
3. Rewrite integration check (isolated test chart root):
   - `archive_runs.ps1 -Filter "provider_probe_20260301_164009" -ChartsRoot "...\\artifacts\\tmp\\astro015_chart_test" -ChartId "rewrite_case" -Execute`
   - Result: `AFFECTED_CHARTS=1`, `changed_lines=3`, `external_refs_missing=0`
4. Regression checks:
   - `check_chart_provenance.ps1 -ChartId "tuapse_19820613_133910"` -> PASS
   - `validate_chart_project.ps1 -ChartId "tuapse_19820613_133910"` -> PASS

## Artifacts

1. `artifacts/results/_archive/archive_batch_20260302_144104/archive_report.json`
2. `artifacts/results/_archive/archive_batch_20260302_144218/archive_report.json`
