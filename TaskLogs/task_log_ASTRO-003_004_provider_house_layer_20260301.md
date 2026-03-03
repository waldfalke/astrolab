# Task Log: ASTRO-003 + ASTRO-004

**Date:** 2026-03-01  
**Workspace:** `D:\Dev\CATMEastrolab`

## Objective

1. Finalize multi-provider MCP profile with practical failover.
2. Deliver Placidus house-layer capability with QC and artifact packaging.

## Work Done

1. Added provider and failover artifacts:
   - `artifacts/mcp-recipes/provider_profile.yaml`
   - `artifacts/mcp-recipes/failover_runbook.md`
2. Added runnable scripts:
   - `run_natal_with_failover.ps1`
   - `run_house_layer_placidus.ps1`
   - `run_cross_provider_qc.ps1`
   - `run_full_workbench.ps1`
3. Extended shared helpers:
   - Generic MCP invocation (`Invoke-McpToolJson`)
   - Swiss primary retry handling (`Invoke-SwissPrimaryToolJson`)
   - Result error detection for MCP responses.
4. Extended pack manifest builder:
   - New pack types: `house`, `natal_failover`, `qc`.
5. Extended result-pack templates:
   - `house_pack_manifest.template.yaml`
   - `natal_failover_pack_manifest.template.yaml`
   - `qc_pack_manifest.template.yaml`
6. Added provider discovery artifact:
   - `run_mcp_provider_probe.ps1`
   - Output: `provider_probe.csv` + raw snapshots.

## External Validation

1. Primary provider validated via MCP:
   - `https://www.theme-astral.me/mcp`
   - Tool: `calculate_planetary_positions` (returns houses + chart points).
2. Backup provider validated via MCP:
   - `https://ephemeris.fyi/mcp`
   - Tools: ephemeris/aspects/moon phase.

## Runtime Validation (actual outputs)

1. `natal_failover_pathcheck2_20260301_162554` -> `RUN_STATUS=FULL`, manifest `READY`.
2. `house_placidus_pathcheck2_20260301_162555` -> `HOUSE_COUNT=12`, manifest `READY`.
3. `qc_cross_provider_pathcheck3_20260301_162729` -> `QC_STATUS=PASS`, `CHECKED_BODIES=10`.
4. One-shot run:
   - `run_full_workbench.ps1` case `pathcheck_full`
   - Generated 5 packs + 5 manifests with `READY` status.
5. Provider probe run:
   - `provider_probe_20260301_164009`
   - 3 providers reachable and tool-discoverable.

## Issues and Fixes

1. Primary provider intermittently returned `504/400`:
   - Added retry in `Invoke-SwissPrimaryToolJson`.
2. QC script initially passed with `CHECKED_BODIES=0`:
   - Root cause: MCP error payload parsed as normal JSON.
   - Fix: helper now throws on `error` or `isError=true`.

## Self-Check (quality prompts)

1. What was not done?
   - No dedicated progression/declination provider integrated yet.
2. What was weak?
   - Primary uptime is not deterministic (external dependency).
3. How not to do it?
   - Do not treat MCP error payloads as valid domain data.
4. How to do it properly?
   - Keep failover + QC mandatory for production output.
5. Better without extra complexity?
   - Use one-shot runner with manifest generation to reduce manual steps.
