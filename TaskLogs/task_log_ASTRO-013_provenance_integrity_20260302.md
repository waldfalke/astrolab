# Task Log: ASTRO-013 - Provenance Integrity for Chart Projects

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Completed

## Objective

Guarantee that chart project provenance remains valid after run moves, archiving, and project rebuilds.

## Problem Statement

1. `INDEX.yaml` currently stores external absolute `source_run_dir`.
2. After archiving/moving run folders, external paths become invalid.
3. Provenance links degrade over time and cannot be trusted as stable references.

## Scope

1. Define canonical provenance fields:
   - `canonical_source` (always project-relative path)
   - `external_source` (optional, may become stale)
2. Ensure outputs always map to canonical internal sources.
3. Add integrity checks for missing source files referenced in index.

## Out of Scope

1. Full migration to DB metadata store.
2. Cross-machine artifact registry.

## Done Definition

1. `INDEX.yaml` schema updated with canonical provenance model.
2. Existing chart projects migrated to new fields.
3. Integrity check reports no broken canonical references.

## Implemented

1. Updated chart project builder:
   - `artifacts/mcp-recipes/build_chart_project.ps1`
2. Added canonical provenance fields:
   - `provenance_model: canonical_source_v1`
   - `raw_methods[].canonical_run_dir`
   - `outputs[].canonical_source`
3. Preserved external lineage fields:
   - `external_source_run_dir`, `external_source_run_exists`
   - `external_source`, `external_source_exists`
4. Added provenance checker:
   - `artifacts/mcp-recipes/check_chart_provenance.ps1`
5. Updated recipe docs:
   - `artifacts/mcp-recipes/README.md`

## Runtime Validation

1. Rebuilt chart project from archived runs:
   - `charts/trump_19460614_105400_jamaica_ny`
2. Verified provenance checker output:
   - `CHARTS_CHECKED=1`
   - `CANONICAL_MISSING=0`
   - `EXTERNAL_MISSING=0`
3. Saved checker report:
   - `charts/trump_19460614_105400_jamaica_ny/provenance_check.csv`

