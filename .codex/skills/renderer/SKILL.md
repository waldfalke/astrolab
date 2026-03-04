---
name: renderer
description: Generates visual chart representations (SVG/PNG) from chart data. Creates chart wheels with planets/houses/aspects, aspect grids, house diagrams. Use when user requests "draw chart", "generate wheel", "show aspect grid", or needs visual for delivery pack.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output-formats: SVG, PNG
---

# Renderer

Generate visual chart representations (SVG/PNG) from normalized chart data.

## Quick Start

**Input:**
```yaml
chart_id: trump_19460614_105400_jamaica_ny
render_type: wheel | aspect_grid | house_diagram | all
output_format: svg | png
size: 800
```

**Output:**
```yaml
files:
  - chart_wheel.svg (800x800)
  - aspect_grid.svg (600x600)
  - house_diagram.svg (400x400)
```

## Core Workflow

### 1. Load Data

```
charts/<id>/outputs/
  planets_primary.csv  → positions
  houses_placidus.csv  → cusps
  natal_aspects.json   → aspects
```

### 2. Coordinate System

```
- 0° Aries: right (3 o'clock)
- Angles: counter-clockwise
- SVG Y: inverted
```

### 3. Render Wheel

Layers (center → outer):
1. Center label
2. House divisions
3. Planet glyphs
4. Zodiac signs
5. Aspect lines (overlay)

### 4. Planet Glyphs

| Planet | Glyph |
|---|---|
| Sun | ☉ |
| Moon | ☽ |
| Mercury | ☿ |
| Venus | ♀ |
| Mars | ♂ |

### 5. Aspect Lines

| Aspect | Color | Style |
|---|---|---|
| Trine | #45B7D1 | solid |
| Square | #FFA07A | dashed |
| Opposition | #4ECDC4 | dotted |

### 6. Export PNG

```python
from cairosvg import svg2png
svg2png(url='chart_wheel.svg', write_to='chart_wheel.png')
```

## Reference Documents

- `.qwen/skills-source/anthropics-skills/skills/canvas-design/SKILL.md`

## Unicode Glyphs

- Zodiac: ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓
- Planets: ☉ ☽ ☿ ♀ ♂ ♃ ♄ ♅ ♆ ♇

## Examples

**Chart wheel:** `SVG with zodiac, houses, planets, aspects`

**Aspect grid:** `Table with glyphs and aspect symbols`

**PNG export:** `800x800 for delivery pack`

