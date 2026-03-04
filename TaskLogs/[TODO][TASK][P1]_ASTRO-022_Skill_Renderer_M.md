# Task Log: ASTRO-022 - Skill: renderer

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

Create the `renderer` skill that generates visual chart representations (SVG/PNG) from normalized chart data. This skill produces chart wheels, aspect grids, and house diagrams for delivery packs and analyst review.

## Skill Location

```
.qwen/skills/renderer/
├── SKILL.md
├── scripts/
│   ├── render_wheel.py
│   ├── render_aspect_grid.py
│   └── render_house_diagram.py
├── templates/
│   ├── chart_wheel.svg
│   └── aspect_grid.svg
└── references/
    ├── glyph-reference.md
    └── color-palette.md
```

## SKILL.md Frontmatter

```yaml
---
name: renderer
description: Generates visual chart representations (SVG/PNG) from chart data. Creates chart wheels with planets/houses/aspects, aspect grids, house diagrams. Use when user requests "draw chart", "generate wheel", "show aspect grid", or needs visual for delivery pack.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output-formats: SVG, PNG
---
```

## Implementation Steps

### Step 1: Load Chart Data

Parse chart-project outputs:

```python
# Load positions
positions = load_csv('charts/<id>/outputs/planets_primary.csv')
# Columns: name, longitude, sign, sign_degree, house, retrograde

# Load houses
houses = load_csv('charts/<id>/outputs/houses_placidus.csv')
# Columns: house_number, cusp_longitude, sign, cusp_degree

# Load aspects
aspects = load_json('charts/<id>/outputs/natal_aspects.json')
# Fields: planet1, planet2, type, angle, orb, applying
```

### Step 2: Define Coordinate System

Chart wheel uses polar coordinates:

```
- Center: (0, 0)
- 0° Aries: right (3 o'clock position)
- Angles increase counter-clockwise
- 360° = full circle
- Radius layers (from center outward):
  - R1: Center point (optional label)
  - R2: Inner ring (house divisions)
  - R3: Planet ring (planet glyphs)
  - R4: Outer ring (zodiac signs)
```

### Step 3: Render Chart Wheel

**SVG Structure:**
```svg
<svg viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
  <!-- Outer ring: Zodiac signs -->
  <g id="zodiac-ring">
    <path d="..." class="sign sign-1" />  <!-- Aries -->
    <path d="..." class="sign sign-2" />  <!-- Taurus -->
    ...
  </g>
  
  <!-- House cusps -->
  <g id="house-cusps">
    <line x1="400" y1="400" x2="..." y2="..." class="house-cusp house-1" />
    ...
  </g>
  
  <!-- Planets -->
  <g id="planets">
    <text x="..." y="..." class="planet-glyph sun">♉</text>
    ...
  </g>
  
  <!-- Aspect lines -->
  <g id="aspects">
    <line x1="..." y1="..." x2="..." y2="..." class="aspect trine" />
    ...
  </g>
</svg>
```

### Step 4: Planet Glyphs

Use Unicode astrological glyphs:

| Planet | Glyph | Unicode |
|---|---|---|
| Sun | ☉ | U+2609 |
| Moon | ☽ | U+263D |
| Mercury | ☿ | U+263F |
| Venus | ♀ | U+2640 |
| Mars | ♂ | U+2642 |
| Jupiter | ♃ | U+2643 |
| Saturn | ♄ | U+2644 |
| Uranus | ♅ | U+2645 |
| Neptune | ♆ | U+2646 |
| Pluto | ♇ | U+2647 |

**Position calculation:**
```python
def planet_to_cartesian(longitude_deg, radius):
    """Convert ecliptic longitude to SVG coordinates."""
    angle_rad = math.radians(longitude_deg)
    # 0° Aries = 0 rad, angles increase counter-clockwise
    x = center_x + radius * math.cos(angle_rad)
    y = center_y - radius * math.sin(angle_rad)  # SVG Y is inverted
    return (x, y)
```

### Step 5: Zodiac Sign Ring

Render 12 sign sectors (30° each):

```python
def render_zodiac_ring(svg, center, outer_radius, inner_radius):
    for sign_num in range(12):
        start_angle = sign_num * 30  # 0 = Aries
        end_angle = start_angle + 30
        
        # Create arc path
        path = create_arc_path(center, outer_radius, inner_radius, 
                               start_angle, end_angle)
        
        # Add sign glyph at center of sector
        sign_glyph = ZODIAC_GLYPHS[sign_num]
        glyph_angle = start_angle + 15
        glyph_pos = polar_to_cartesian(center, (outer_radius + inner_radius) / 2, 
                                       glyph_angle)
        
        svg.add_element('path', d=path, class_=f'sign sign-{sign_num + 1}')
        svg.add_element('text', x=glyph_pos[0], y=glyph_pos[1], 
                       text=sign_glyph, class_='sign-glyph')
```

### Step 6: House Cusps (Placidus)

Draw house division lines:

```python
def render_house_cusps(svg, houses, center, radius):
    for house in houses:
        cusp_lon = house['cusp_longitude']
        end_pos = polar_to_cartesian(center, radius, cusp_lon)
        
        svg.add_element('line', 
                       x1=center[0], y1=center[1],
                       x2=end_pos[0], y2=end_pos[1],
                       class_=f'house-cusp house-{house["number"]}')
```

### Step 7: Aspect Lines

Draw aspect connections between planets:

```python
def render_aspects(svg, aspects, positions, center, radius):
    # Aspect colors and styles
    aspect_styles = {
        'conjunction': {'color': '#FF6B6B', 'width': 2, 'dash': None},
        'opposition': {'color': '#4ECDC4', 'width': 2, 'dash': '5,5'},
        'trine': {'color': '#45B7D1', 'width': 2, 'dash': None},
        'square': {'color': '#FFA07A', 'width': 2, 'dash': '10,5'},
        'sextile': {'color': '#98D8C8', 'width': 1, 'dash': None},
    }
    
    for aspect in aspects:
        p1_lon = positions[aspect['planet1']]['longitude']
        p2_lon = positions[aspect['planet2']]['longitude']
        
        p1_pos = polar_to_cartesian(center, radius, p1_lon)
        p2_pos = polar_to_cartesian(center, radius, p2_lon)
        
        style = aspect_styles.get(aspect['type'], aspect_styles['sextile'])
        
        svg.add_element('line',
                       x1=p1_pos[0], y1=p1_pos[1],
                       x2=p2_pos[0], y2=p2_pos[1],
                       stroke=style['color'],
                       stroke_width=style['width'],
                       stroke_dasharray=style['dash'],
                       class_=f"aspect {aspect['type']}")
```

### Step 8: Render Aspect Grid

Create table showing all aspects:

```
Aspect Grid (SVG table):

        ☉     ☽     ☿     ♀     ♂     ♃     ♄     ♅     ♆     ♇
☉           □     *     △           △                 □
☽                 □           *           △     □
☿                       □     △           □     *
...

Legend:
  △ = Trine (120°)
  □ = Square (90°)
  * = Sextile (60°)
  ☍ = Opposition (180°)
  ☌ = Conjunction (0°)
```

### Step 9: Render House Diagram

Quadrant view showing planet distribution:

```
House Diagram (Placidus):

      X MC
      |
  IV  |  I
------|------ ASC X
 III  |  II
      |
      X IC

Planets by house:
I:   ☉ ☿
II:  ♀
III: 
IV:  ☽
...
```

### Step 10: Export Formats

**SVG (primary):**
- Scalable, editable
- Text remains selectable
- Small file size

**PNG (derived):**
```python
# Convert SVG to PNG using cairo or PIL
from cairosvg import svg2png

svg2png(url='chart_wheel.svg', write_to='chart_wheel.png', 
        output_width=800, output_height=800)
```

## Important Nuances

### 1. Coordinate System

- SVG Y-axis is inverted (0 at top)
- Astrological charts: 0° Aries at right (3 o'clock), counter-clockwise
- Standard math: 0° at right, counter-clockwise (matches!)

### 2. Glyph Fonts

- Use Unicode glyphs (widely supported)
- Fallback: Use SVG paths for glyphs
- Font recommendation: "Segoe UI Symbol", "Arial Unicode MS"

### 3. Aspect Orbs

- Only draw aspects within orb (default 6°)
- Tighter orbs for conjunctions/oppositions (3°)
- Configurable via parameter

### 4. Color Palette

| Element | Color | Usage |
|---|---|---|
| Fire signs | #FF6B6B | Aries, Leo, Sagittarius |
| Earth signs | #98D8C8 | Taurus, Virgo, Capricorn |
| Air signs | #45B7D1 | Gemini, Libra, Aquarius |
| Water signs | #4ECDC4 | Cancer, Scorpio, Pisces |
| Aspect trine | #45B7D1 | Harmonious |
| Aspect square | #FFA07A | Challenging |
| Aspect opposition | #4ECDC4 | Tension |

### 5. Responsive Sizing

SVG viewBox allows scaling:
```svg
<svg viewBox="0 0 800 800" preserveAspectRatio="xMidYMid meet">
```

### 6. Retrograde Indicator

Mark retrograde planets:
```svg
<text x="..." y="..." class="planet-glyph retrograde">
  ☿<tspan class="retrograde-marker">℞</tspan>
</text>
```

## Examples

### Example 1: Basic Chart Wheel

**User says:** "Generate chart wheel for trump_19460614_105400_jamaica_ny"

**Actions:**
1. Load positions, houses, aspects
2. Create SVG with zodiac ring
3. Add house cusps
4. Place planet glyphs
5. Draw aspect lines
6. Save as charts/<id>/outputs/chart_wheel.svg

**Result:**
```
charts/trump_19460614_105400_jamaica_ny/outputs/chart_wheel.svg
  - 800x800 viewBox
  - 12 sign sectors
  - 12 house cusps
  - 10 planets
  - 14 aspect lines
```

### Example 2: Aspect Grid

**User says:** "Show aspect grid"

**Actions:**
1. Load aspects
2. Create SVG table (10x10 grid)
3. Fill cells with aspect symbols
4. Add legend
5. Save as charts/<id>/outputs/aspect_grid.svg

### Example 3: Delivery Pack PNG

**User says:** "Generate PNG for client delivery"

**Actions:**
1. Generate SVG wheel
2. Convert to PNG (800x800)
3. Copy to packs/<pack_id>/04_interpretation/

**Result:**
```
packs/.../04_interpretation/chart_wheel.png
```

## Troubleshooting

### Error: Glyphs not displaying

- **Cause:** Font not available on system
- **Solution:** Embed SVG paths for glyphs, or use web font

### Error: Aspect lines misaligned

- **Cause:** Coordinate calculation error (Y inversion)
- **Solution:** Check SVG Y coordinate (inverted from Cartesian)

### Error: House cusps wrong positions

- **Cause:** Longitude not converted to polar correctly
- **Solution:** Verify polar_to_cartesian function

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-009 | Renderer module — this skill implements the renderer |
| ASTRO-005 | Client output packs — skill generates visuals for packs |
| ASTRO-010 | Obsidian integration — skill outputs compatible with Obsidian |

## Available Code / Tools

### Data Sources
- `charts/<id>/outputs/planets_primary.csv` — Planet positions for glyphs
- `charts/<id>/outputs/houses_placidus.csv` — House cusps for diagram
- `charts/<id>/outputs/natal_aspects.json` — Aspect lines

### Reference (from anthropics-skills repo)
- `.qwen/skills-source/anthropics-skills/skills/canvas-design/SKILL.md` — Visual design patterns
- `.qwen/skills-source/anthropics-skills/skills/renderer/` — Reference implementations

### Planet Glyphs (Unicode)
- Sun ☉ (U+2609), Moon ☽ (U+263D)
- Mercury ☿ (U+263F), Venus ♀ (U+2640), Mars ♂ (U+2642)
- Jupiter ♃ (U+2643), Saturn ♄ (U+2644)
- Uranus ♅ (U+2645), Neptune ♆ (U+2646), Pluto ♇ (U+2647)

### Zodiac Glyphs (Unicode)
- Aries ♈, Taurus ♉, Gemini ♊, Cancer ♋, Leo ♌, Virgo ♍
- Libra ♎, Scorpio ♏, Sagittarius ♐, Capricorn ♑, Aquarius ♒, Pisces ♓

### Color Palette (from project conventions)
- Fire signs: #FF6B6B, Earth: #98D8C8, Air: #45B7D1, Water: #4ECDC4
- Aspects: trine #45B7D1, square #FFA07A, opposition #4ECDC4

### Export Tools
- Python: `cairosvg` library for SVG→PNG conversion
- SVG native for wheel/grid rendering

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/renderer/`
- [ ] Chart wheel SVG generated with all rings (zodiac, houses, planets)
- [ ] Planet glyphs positioned correctly by longitude
- [ ] Aspect lines drawn between correct planets
- [ ] Aspect grid table rendered
- [ ] House diagram (quadrant view) rendered
- [ ] PNG export from SVG works
- [ ] Output files saved to chart-project outputs/

