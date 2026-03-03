# Task Log: ASTRO-009 - Renderer Module (Chart Wheel Imaging)

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Planned (module not implemented)

## Objective

Create independent rendering module to generate chart visuals (SVG/PNG) from normalized chart data.

## Why This Module

1. Current MCP/API stack provides positions and aspects, not chart images.
2. Visual layer is required for analyst workflow and board/canvas usage.
3. Rendering must be decoupled from computation and provider transport.

## Scope

1. Input: normalized chart payload (houses, planets, points, aspects, metadata).
2. Output:
   - `chart_wheel.svg`
   - optional `chart_wheel.png`
   - `render_manifest.json` (settings + version + source hash)
3. Layout primitives:
   - zodiac ring
   - house cusps
   - glyph placement with collision handling
   - aspect lines

## Out of Scope (initial)

1. Rich interactive editor.
2. Theme marketplace.
3. Heavy animation or 3D effects.

## Interfaces

1. `renderNatalWheel(input, options) -> artifact paths`
2. `renderSynastryWheel(inputA, inputB, options) -> artifact paths`

## Quality Gates

1. Deterministic output for same input/settings.
2. No overlap beyond threshold in glyph placement.
3. Render completes under target runtime for batch mode.

## Deliverables

1. `src/products/renderer/*`
2. renderer CLI wrapper for batch export
3. schema docs for renderer input contract
