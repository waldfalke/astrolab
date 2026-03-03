# [DONE][TASK][P1] ASTRO-003 - Multi-Provider MCP Profile

## Goal

Set primary/backup provider profile for production workbench with explicit failover.

## Scope

1. Primary provider profile (houses + chart points + transit-class tools).
2. Backup provider profile (ephemeris + aspects + continuity).
3. Failover model with explicit degraded/full status policy.

## Current State

1. Primary selected and validated: `https://www.theme-astral.me/mcp`.
2. Backup validated: `https://ephemeris.fyi/mcp`.
3. Operational files:
   - `artifacts/mcp-recipes/provider_profile.yaml`
   - `artifacts/mcp-recipes/failover_runbook.md`
   - `artifacts/mcp-recipes/run_natal_with_failover.ps1`

## Done Definition

1. `provider_profile.yaml` approved and committed in project tree.
2. `failover_runbook.md` approved and actionable.
3. Successful runs:
   - `artifacts/results/natal_failover_pathcheck2_20260301_162554`
   - `artifacts/results/natal_failover_pathcheck_full_20260301_162828`
