# [DONE][TASK][P1] ASTRO-007 - Chart Project Systemization

## Goal

Make chart the primary project unit with clear separation between method raw files and analyst-facing outputs.

## Scope

1. Introduce `charts/<chart_id>/` structure.
2. Keep raw runs in `methods/<method>/<run>/`.
3. Keep curated files in `outputs/`.
4. Add provenance index `INDEX.yaml` and chart metadata `chart.yaml`.

## Delivered

1. `artifacts/mcp-recipes/build_chart_project.ps1`
2. `charts/README.md`
3. Built chart project:
   - `charts/tuapse_19820613_133910`
4. Task log:
   - `TaskLogs/task_log_ASTRO-007_chart_project_systemization_20260302.md`

## Done Definition

1. Chart project generated from real method runs.
2. Outputs mapped to raw sources in `INDEX.yaml`.
3. Structure reproducible via script - achieved.
