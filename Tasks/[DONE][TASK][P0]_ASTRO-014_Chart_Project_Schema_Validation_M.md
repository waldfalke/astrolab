# [DONE][TASK][P0] ASTRO-014 - Chart Project Schema Validation

## Goal

Introduce explicit schema contracts and validator for chart project files.

## Delivered

1. Schema definitions:
   - `artifacts/schemas/chart-project/chart.schema.v1.json`
   - `artifacts/schemas/chart-project/index.schema.v1.json`
2. Validator:
   - `artifacts/mcp-recipes/validate_chart_project.ps1`
3. Documentation updates:
   - `artifacts/mcp-recipes/README.md`
   - `charts/README.md`
4. Machine-readable validation report:
   - `artifacts/results/chart_validation_20260302.json`

## Done Definition Check

1. Schema files committed and documented - achieved.
2. Validator returns `PASS/FAIL` with diagnostics - achieved.
3. Validation applied to active chart project - achieved.
