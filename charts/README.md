# Charts As Projects

Each chart is a standalone project folder:

`charts/<chart_id>/`

Expected layout:

1. `chart.yaml` - chart identity and birth metadata.
2. `INDEX.yaml` - generated provenance index (raw method runs + output links).
3. `methods/` - immutable raw files grouped by methodology.
4. `outputs/` - curated analysis-ready files copied from method runs.
5. `packs/` - optional client delivery manifests and package files.

Method raw convention:

`methods/<method_name>/<run_folder_from_results>/...`

Output convention:

`outputs/<stable_file_name>`

The `build_chart_project.ps1` recipe assembles this structure from existing run folders in `artifacts/results`.

Validation:

1. Schemas:
   - `artifacts/schemas/chart-project/chart.schema.v1.json`
   - `artifacts/schemas/chart-project/index.schema.v1.json`
2. Validator:
   - `artifacts/mcp-recipes/validate_chart_project.ps1`

Archive maintenance:

1. Use `artifacts/mcp-recipes/archive_runs.ps1` to move old run folders to archive batches.
2. The script rewrites affected `INDEX.yaml` external links and emits a JSON verification report.
