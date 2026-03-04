# [DONE][TASK][P0] ASTRO-013 - Provenance Integrity

## Goal

Harden chart-project provenance so output-to-source mapping remains valid after move/archive/rebuild operations.

## Delivered

1. Updated `build_chart_project.ps1` with canonical provenance model:
   - `provenance_model: canonical_source_v1`
   - `raw_methods[].canonical_run_dir`
   - `outputs[].canonical_source`
2. Preserved external lineage fields for audit:
   - `external_source_run_dir`, `external_source_run_exists`
   - `external_source`, `external_source_exists`
3. Added provenance validator:
   - `artifacts/mcp-recipes/check_chart_provenance.ps1`
4. Migrated active chart project index by rebuild from archived sources:
   - `charts/trump_19460614_105400_jamaica_ny/INDEX.yaml`
5. Validation report:
   - `charts/trump_19460614_105400_jamaica_ny/provenance_check.csv`

## Done Definition Check

1. Canonical provenance model implemented - achieved.
2. Existing chart project migrated - achieved.
3. Integrity checker reports no broken canonical references - achieved.

