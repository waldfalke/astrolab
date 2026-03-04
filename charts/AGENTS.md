# AGENTS.md

Local rules for `charts/`.

## Scope

- Applies to `charts/<chart_id>/...`.

## Rules

1. Treat each `charts/<chart_id>` as a chart project with provenance.
2. Preserve `chart.yaml`, `INDEX.yaml`, and `outputs/` consistency.
3. If replacing canonical outputs, ensure source method run references remain valid.
4. Run checks before finalize:
   - `pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId <chart_id>`
   - `pwsh artifacts/mcp-recipes/validate_chart_project.ps1 -ChartId <chart_id>`
5. Do not leak private chart inputs into public docs or examples; use public-safe cases (e.g., Trump demo chart).
