# Task Log: ASTRO-010 - Obsidian Integration Module (Vault + Canvas Export)

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Planned (module not implemented)

## Objective

Build Obsidian export integration that maps chart projects into markdown notes and `.canvas` boards.

## Why This Module

1. Needed alternative to proprietary board APIs.
2. Obsidian format is local, text-based, and versionable.
3. Enables "many charts on infinite canvas" workflow with provenance links.

## Scope

1. Generate card note per chart:
   - summary
   - links to `chart.yaml`, `INDEX.yaml`, `outputs/*`
2. Generate/update board file:
   - `astrolab.canvas`
   - nodes for charts/method outputs/sticky notes
   - edges for relationships
3. Support idempotent re-export without node duplication.

## Out of Scope (initial)

1. Obsidian plugin runtime UI.
2. Bidirectional sync from vault back to raw methods.
3. Real-time collaborative editing protocol.

## Interfaces

1. `exportChartToObsidian(chartProjectPath, vaultPath, options)`
2. `buildOrUpdateCanvas(vaultPath, boardId, nodes, edges)`

## Quality Gates

1. Export rerun does not corrupt existing vault notes.
2. Every exported node keeps link to source artifact.
3. Canvas JSON validates and opens in Obsidian without manual fixes.

## Deliverables

1. `src/products/obsidian/*`
2. export CLI script (single chart and batch mode)
3. canvas/node schema docs and mapping rules
