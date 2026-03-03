# [TODO][TASK][P1] ASTRO-009 - Renderer Module (Chart Wheel)

## Goal

Implement independent renderer that produces chart visuals from normalized data.

## Scope

1. SVG wheel generation (zodiac ring, houses, planets, aspects).
2. Optional PNG export.
3. Render manifest with source/version metadata.

## Done Definition

1. `src/products/renderer` module created.
2. CLI/API entrypoint for natal wheel render.
3. Deterministic render output for same input and settings.
