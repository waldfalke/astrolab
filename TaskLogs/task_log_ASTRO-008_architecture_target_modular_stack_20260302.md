# Task Log: ASTRO-008 - Target Modular Architecture (Backbone + Methods + Products + Agent)

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Planned

## Objective

Define stable architecture boundaries so calculations, integrations, rendering, and agent orchestration evolve independently.

## Current Problem

1. Method logic and integration concerns are mixed in recipe scripts.
2. No formal backbone module for shared domain contracts and provider adapters.
3. Renderer and Obsidian integration are not isolated as product modules.
4. Agent orchestration is script-driven without explicit service boundaries.

## Target Architecture

```text
src/
  core/                # domain models, time/coords, normalization, provenance
  providers/           # MCP/API adapters and failover/QC transport policies
  methods/             # astrology methodologies built on core + providers
  products/
    renderer/          # chart wheel and visual primitives (SVG/Canvas)
    obsidian/          # markdown/canvas export and vault sync contracts
  agent/               # orchestration flows and run pipelines
charts/                # chart projects (chart.yaml, INDEX.yaml, methods/, outputs/)
artifacts/             # run outputs and recipe utilities
```

## Dependency Rules

1. `core` has no dependency on `products` or `agent`.
2. `providers` depend on `core`, but not on `products`.
3. `methods` depend on `core` + `providers`.
4. `products/*` consume normalized outputs from `core/methods` only.
5. `agent` orchestrates; it must not contain domain calculation logic.

## Data Contracts (must stay stable)

1. `charts/<chart_id>/chart.yaml` - chart identity and source metadata.
2. `charts/<chart_id>/INDEX.yaml` - provenance map from outputs to raw method runs.
3. `methods/*` raw outputs are immutable.
4. `outputs/*` are curated, stable analyst-facing files.

## Phased Rollout

1. Phase A: Extract shared utility code from recipes into `src/core` + `src/providers`.
2. Phase B: Wrap existing recipes as `methods` module entrypoints.
3. Phase C: Add `products/renderer` and `products/obsidian`.
4. Phase D: Introduce `agent` orchestration layer over module APIs.

## Risks

1. Regression risk if recipe behavior changes during extraction.
2. Contract drift if `INDEX.yaml` schema is not validated.
3. Tight coupling may reappear if module boundaries are not enforced.

## Quality Gates

1. Existing recipe outputs remain byte-compatible where expected.
2. Every module emits artifacts with explicit provenance.
3. New module interfaces documented with input/output schemas.
