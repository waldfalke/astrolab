# Task Log: ASTRO-011 - Core Backbone and Provider Adapter Module

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Planned (module not implemented)

## Objective

Create reusable backbone for domain operations and provider transport, replacing duplicated script utilities.

## Why This Module

1. Utility logic is currently spread across multiple scripts.
2. Provider retry/error handling should be centralized and testable.
3. Method modules need stable contracts for provider data access.

## Scope

1. `core`:
   - datetime/timezone normalization
   - longitude/sign conversion
   - aspect math helpers
   - chart artifact metadata/provenance contracts
2. `providers`:
   - MCP HTTP adapters (swissremote, ephem, vedastro)
   - retry/failover policy abstraction
   - normalized error model

## Out of Scope (initial)

1. Replacing all recipes in one pass.
2. External DB persistence layer.
3. Web API surface.

## Interfaces

1. `ProviderClient.call(tool, args, options)`
2. `AstroCore.normalizeChart(rawProviderPayload)`
3. `AstroCore.computeAspects(objects, orb, aspectSet)`

## Quality Gates

1. Existing recipes can consume new module without output regressions.
2. Provider errors map to explicit categories (transport/tool/validation).
3. Cross-provider QC logic remains reproducible.

## Deliverables

1. `src/core/*`
2. `src/providers/*`
3. adapter test fixtures against current MCP responses
