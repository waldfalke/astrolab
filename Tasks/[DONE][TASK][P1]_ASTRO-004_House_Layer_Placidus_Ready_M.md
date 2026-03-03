# [DONE][TASK][P1] ASTRO-004 - House-Layer Capability (Placidus-ready)

## Goal

Add house-layer processing with Placidus output and quality control against backup provider.

## Scope

1. House-cusp and chart-point extraction from primary provider.
2. Cross-provider longitude QC protocol (primary vs backup).
3. Artifact-level packaging with READY/INCOMPLETE manifests.

## Delivered

1. `artifacts/mcp-recipes/run_house_layer_placidus.ps1`
2. `artifacts/mcp-recipes/run_cross_provider_qc.ps1`
3. `artifacts/mcp-recipes/build_pack_manifest.ps1` updated with `house` and `qc` pack types.

## Validation Runs

1. House layer:
   - `artifacts/results/house_placidus_pathcheck2_20260301_162555`
   - `artifacts/results/house_placidus_pathcheck_full_20260301_162839`
2. QC:
   - `artifacts/results/qc_cross_provider_pathcheck3_20260301_162729` (`QC_STATUS=PASS`, 10 bodies)
   - `artifacts/results/qc_cross_provider_pathcheck_full_20260301_163048` (`QC_STATUS=PASS`)

## Done Definition

1. House pack status `READY` - achieved.
2. QC pack status `READY` with numeric deltas - achieved.
3. Integrated into one-shot runner - achieved (`run_full_workbench.ps1`).
