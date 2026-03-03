# [TODO][TASK][P1] ASTRO-010 - Obsidian Integration Module

## Goal

Export chart projects to Obsidian as markdown cards and canvas boards.

## Scope

1. Per-chart note export (`.md`) with links to chart artifacts.
2. Board export/update (`.canvas`) with nodes and edges.
3. Idempotent rerun behavior (no duplicated entities).

## Done Definition

1. `src/products/obsidian` module created.
2. CLI supports single-chart and batch export.
3. Exported `.canvas` opens in Obsidian without manual edits.
