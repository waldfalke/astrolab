# Artifact Registry

This file tracks runnable artifacts that produce astrology outputs directly.

## A1. Natal Snapshot Runner

- Path: `artifacts/mcp-recipes/run_natal_snapshot.ps1`
- Output: ephemeris, aspects, moon phase, daily events, longitudes CSV
- Example output folder: `artifacts/results/natal_pathcheck_20260301_160751`

## A2. Forecast Delta Runner

- Path: `artifacts/mcp-recipes/run_forecast_delta.ps1`
- Output: date-to-date movement, aspects on both dates, movement ranking CSV
- Example output folder: `artifacts/results/forecast_pathcheck_20260301_160818`

## A3. Synastry Matrix Runner

- Path: `artifacts/mcp-recipes/run_synastry_matrix.ps1`
- Output: cross-chart major aspect matrix (CSV+JSON)
- Example output folder: `artifacts/results/synastry_pathcheck_20260301_160819`

## A4. Pack Manifest Builder

- Path: `artifacts/mcp-recipes/build_pack_manifest.ps1`
- Output: `PACK_MANIFEST.yaml` with READY/INCOMPLETE status
- Example output files:
  - `artifacts/results/natal_pathcheck_20260301_160751/PACK_MANIFEST.yaml`
  - `artifacts/results/forecast_pathcheck_20260301_160818/PACK_MANIFEST.yaml`
  - `artifacts/results/synastry_pathcheck_20260301_160819/PACK_MANIFEST.yaml`

## A5. House-Layer Placidus Runner

- Path: `artifacts/mcp-recipes/run_house_layer_placidus.ps1`
- Output: house cusps, chart points, primary longitudes
- Example output folder: `artifacts/results/house_placidus_pathcheck_full_20260301_162839`

## A6. Natal Failover Runner

- Path: `artifacts/mcp-recipes/run_natal_with_failover.ps1`
- Output: full/degraded natal output with provider status
- Example output folder: `artifacts/results/natal_failover_pathcheck_full_20260301_162828`

## A7. Cross-Provider QC Runner

- Path: `artifacts/mcp-recipes/run_cross_provider_qc.ps1`
- Output: longitude deltas between primary and backup providers
- Example output folder: `artifacts/results/qc_cross_provider_pathcheck_full_20260301_163048`

## A8. One-Shot Full Workbench Runner

- Path: `artifacts/mcp-recipes/run_full_workbench.ps1`
- Output: natal failover + house layer + forecast + synastry + QC + manifests
- Example case id: `pathcheck_full`

## A9. MCP Provider Probe

- Path: `artifacts/mcp-recipes/run_mcp_provider_probe.ps1`
- Output: provider health + tool capability matrix (`provider_probe.csv`)
- Example output folder: `artifacts/results/provider_probe_20260301_164009`
