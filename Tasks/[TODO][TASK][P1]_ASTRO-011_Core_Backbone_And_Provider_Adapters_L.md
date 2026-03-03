# [TODO][TASK][P1] ASTRO-011 - Core Backbone and Provider Adapters

## Goal

Extract shared domain and provider logic from scripts into reusable modules.

## Scope

1. `src/core`:
   - time/coordinate normalization
   - longitude/sign/aspect math
   - provenance contracts
2. `src/providers`:
   - MCP adapter abstraction
   - retry/failover/error mapping
   - provider-specific connectors

## Done Definition

1. Existing recipes consume extracted modules without behavioral regressions.
2. Provider error model standardized.
3. Shared test fixtures cover primary and backup MCP responses.
