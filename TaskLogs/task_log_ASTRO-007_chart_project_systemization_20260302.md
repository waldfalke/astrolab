# Task Log: ASTRO-007 - Chart Project Systemization

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Completed

## Objective

Turn "one chart = one project" into an operational artifact model with:

1. Raw method files grouped by methodology.
2. Curated result files colocated at chart root level.
3. Explicit index for provenance and reproducibility.

## Concerns Captured

1. Chart artifacts are currently scattered under `artifacts/results` without chart-level ownership.
2. "Raw by methodology" vs "result for analyst" boundaries are blurred.
3. No stable chart-level file index to answer:
   - Which final file came from which raw run?
   - Which method parameters were used?
4. Re-runs can overwrite analyst context because there is no chart project root.
5. Lack of a predictable handoff package per chart project.

## Decisions

1. Define chart as primary unit:
   - `charts/<chart_id>/`
2. Keep raw immutable and method-scoped:
   - `methods/<method>/<run_folder>/...`
3. Keep analyst-facing outputs stable and colocated:
   - `outputs/<stable_name>`
4. Generate provenance index:
   - `INDEX.yaml` maps outputs to raw sources.
5. Keep method run folders as copies from `artifacts/results` to decouple analysis from transient run storage.

## Implemented

1. Added chart project builder recipe:
   - `artifacts/mcp-recipes/build_chart_project.ps1`
2. Added chart structure documentation:
   - `charts/README.md`
3. Extended recipe docs with chart-project build flow:
   - `artifacts/mcp-recipes/README.md`
4. Confirmed secondary progressions and solar arc method outputs are available for chart-project ingestion.
5. Built chart project for:
   - `charts/trump_19460614_105400_jamaica_ny`
6. Generated chart metadata and provenance index:
   - `charts/trump_19460614_105400_jamaica_ny/chart.yaml`
   - `charts/trump_19460614_105400_jamaica_ny/INDEX.yaml`
7. Materialized method raw folders and curated outputs:
   - `methods/natal_failover/*`
   - `methods/house_placidus/*`
   - `methods/secondary_progressions/*`
   - `methods/solar_arc/*`
   - `outputs/*.csv|*.json|*.txt`

## Runtime Validation

1. `build_chart_project.ps1` executed successfully for Jamaica Queens NY chart.
2. Chart project directory contains:
   - `chart.yaml`
   - `INDEX.yaml`
   - `methods/` with raw run copies for 4 methodologies
   - `outputs/` with stable analyst-facing files
3. `INDEX.yaml` correctly maps each output file to source method run and stores run summaries.

## Quality Self-Check

1. What is not done yet?
   - Chart project materialization for this specific chart has not been executed in this log section yet.
2. What is weak?
   - Current YAML writing is plain-text generation; no schema validator is applied yet.
3. How not to do it?
   - Do not store only "latest" outputs without preserving source run folders.
4. How to do it properly?
   - Preserve immutable raw runs, stable outputs, and explicit output-to-source links.
5. How to improve further?
   - Add machine-readable schema validation for `chart.yaml` and `INDEX.yaml`.

