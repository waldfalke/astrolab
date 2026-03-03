# Task Log: ASTRO-026 - Skill: obsidian-export

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Skill Location

```
.qwen/skills/obsidian-export/
├── SKILL.md
├── scripts/
│   ├── export_note.py
│   └── export_canvas.py
└── templates/
    ├── chart-note-template.md
    └── canvas-template.json
```

## SKILL.md Frontmatter

```yaml
---
name: obsidian-export
description: Exports chart data to Obsidian notes and Canvas format. Creates structured notes with chart metadata, positions, aspects; generates Canvas files for visual chart mapping. Use when user requests "export to Obsidian", "create note", or needs chart context in knowledge base.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output-format: Markdown (notes), JSON (Canvas)
---
```

## Implementation Steps

### Step 1: Load Chart Data

Parse chart-project outputs:

```python
def load_chart_data(chart_id):
    """Load all chart data for export."""
    
    chart_dir = f'charts/{chart_id}'
    
    # Load metadata
    chart_yaml = load_yaml(f'{chart_dir}/chart.yaml')
    
    # Load positions
    positions = load_csv(f'{chart_dir}/outputs/planets_primary.csv')
    
    # Load houses
    houses = load_csv(f'{chart_dir}/outputs/houses_placidus.csv')
    
    # Load aspects
    aspects = load_json(f'{chart_dir}/outputs/natal_aspects.json')
    
    return {
        'metadata': chart_yaml,
        'positions': positions,
        'houses': houses,
        'aspects': aspects
    }
```

### Step 2: Generate Chart Note

Create structured markdown note:

```markdown
---
tags: [chart, natal]
chart_id: tuapse_19820613_133910
birth_date: 1982-06-13
birth_time: 13:39
birth_place: Tuapse
created: 2026-03-04
---

# Natal Chart: Tuapse 1982-06-13 13:39

## Birth Data

| Field | Value |
|---|---|
| Date | 1982-06-13 |
| Time | 13:39:10 (UTC+4) |
| UTC | 1982-06-13T09:39:10Z |
| Location | Tuapse (44.100833, 39.083333) |

## Planetary Positions

| Planet | Longitude | Sign | Degree | House | Retrograde |
|---|---|---|---|---|---|
| Sun | 72.45° | Gemini | 22°27' | X | |
| Moon | 156.89° | Virgo | 6°53' | X | |
| Mercury | 85.23° | Gemini | 25°14' | XI | |
| Venus | 52.18° | Taurus | 22°11' | IX | |
| Mars | 15.67° | Aries | 15°40' | VII | |
...

## House Cusps (Placidus)

| House | Cusp | Sign | Degree |
|---|---|---|---|
| I (ASC) | 256.34° | Sagittarius | 16°20' |
| II | 286.12° | Capricorn | 16°07' |
| III | 319.45° | Aquarius | 19°27' |
| IV (IC) | 352.78° | Pisces | 22°47' |
| V | 23.56° | Aries | 23°34' |
| VI | 51.23° | Taurus | 21°14' |
| VII (DSC) | 76.34° | Gemini | 16°20' |
| VIII | 106.12° | Cancer | 16°07' |
| IX | 139.45° | Leo | 19°27' |
| X (MC) | 172.78° | Virgo | 22°47' |
| XI | 203.56° | Libra | 23°34' |
| XII | 231.23° | Scorpio | 21°14' |

## Major Aspects

| Planet 1 | Planet 2 | Aspect | Angle | Orb | Applying |
|---|---|---|---|---|---|
| Sun | Moon | Sextile | 84.44° | 5.56° | Yes |
| Sun | Mercury | Conjunction | 12.78° | 2.78° | No |
| Venus | Mars | Sextile | 36.51° | 3.51° | Yes |
...

## Analysis Notes

<!-- Add interpretation notes here -->

## Related Files

- [[chart_wheel.svg]]
- [[aspect_grid.svg]]
- [[PACK_MANIFEST.yaml]]
```

### Step 3: Generate Obsidian Canvas

Create JSON canvas file:

```json
{
  "nodes": [
    {
      "id": "chart_center",
      "type": "text",
      "x": 400,
      "y": 300,
      "width": 200,
      "height": 100,
      "text": "# Chart: tuapse_19820613_133910\n\n1982-06-13 13:39\nTuapse"
    },
    {
      "id": "sun_node",
      "type": "text",
      "x": 650,
      "y": 200,
      "width": 150,
      "height": 80,
      "text": "## ☉ Sun\n\n22° Gemini\nHouse X\n\nState: <7.3 : 10.8 : D=5.2>"
    },
    {
      "id": "moon_node",
      "type": "text",
      "x": 650,
      "y": 350,
      "width": 150,
      "height": 80,
      "text": "## ☽ Moon\n\n6° Virgo\nHouse X\n\nState: <4.2 : 10.5 : D=3.1>"
    },
    {
      "id": "aspect_sun_moon",
      "type": "text",
      "x": 850,
      "y": 275,
      "width": 100,
      "height": 50,
      "text": "Sextile\n84.44°\nOrb: 5.56°"
    }
  ],
  "edges": [
    {
      "id": "edge_sun_moon",
      "fromNode": "sun_node",
      "toNode": "moon_node",
      "fromSide": "right",
      "toSide": "left",
      "label": "sextile"
    }
  ]
}
```

### Step 4: Create File Structure

```
charts/<chart_id>/obsidian/
├── <chart_id>_natal.md       # Main note
├── <chart_id>_canvas.json    # Canvas file
├── <chart_id>_forecast.md    # Forecast note (if applicable)
└── attachments/
    ├── chart_wheel.svg       # Linked image
    └── aspect_grid.svg       # Linked image
```

### Step 5: Link Related Notes

Create bidirectional links:

```markdown
## Related Charts

- Parent chart: [[tuapse_19820613_133910_natal]]
- Solar return: [[tuapse_19820613_solar_return_2026]]
- Progressed: [[tuapse_19820613_progressed_2026]]

## Client Notes

- [[Client - Ivan Petrov]]
- [[Consultation 2026-03-04]]
```

### Step 6: Embed Phase Analysis

Include state vectors:

```markdown
## Phase Analysis (Zakharian Model)

### Sun: P <7.3 : 10.8 : D=5.2>

**Z-phase (Sign): 7 - Mirror**
- Microphase: 3 - Link
- From domicile (Leo): Gemini is 7th sign
- Interpretation: External focus through partnerships

**H-phase (House): 10 - Result**
- Microphase: 8 - Transformation
- In 10th house from ASC
- Interpretation: Career/public status as life focus

**D-sanction (Dispositor): 5 - Play**
- Venus in Aries, 5th from Libra
- Interpretation: Creative expression sanctions identity

### Moon: P <4.2 : 10.5 : D=3.1>
...
```

### Step 7: Generate Index Note

Create vault-level index:

```markdown
# Chart Index

## Natal Charts

| Chart ID | Birth Date | Name | Created |
|---|---|---|---|
| [[tuapse_19820613_133910_natal]] | 1982-06-13 | Tuapse Natal | 2026-03-04 |
| [[moscow_19900515_083000_natal]] | 1990-05-15 | Moscow Natal | 2026-03-01 |

## Forecast Charts

| Chart ID | Type | Target Date | Created |
|---|---|---|---|
| [[tuapse_19820613_progressed_2026]] | Progressed | 2026-03-04 | 2026-03-04 |
| [[tuapse_19820613_solar_2026]] | Solar Return | 2026-06-13 | 2026-03-04 |

## Synastry Charts

| Chart ID | Chart 1 | Chart 2 | Created |
|---|---|---|---|
| [[synastry_tuapse_moscow]] | tuapse_... | moscow_... | 2026-03-02 |
```

## Important Nuances

### 1. Obsidian URI Scheme

Use Obsidian URI for deep links:

```
obsidian://open?vault=MyVault&file=charts/tuapse_19820613_133910_natal
```

### 2. Canvas File Format

Obsidian Canvas uses specific JSON format:
- `nodes`: Array of cards (text, file, link, web)
- `edges`: Connections between nodes
- `view`: Viewport settings

### 3. Frontmatter Standards

Use consistent frontmatter:
```yaml
---
tags: [chart, natal, forecast]
aliases: ["Tuapse Natal", "Натал Туапсе"]
chart_id: tuapse_19820613_133910
created: 2026-03-04
updated: 2026-03-04
---
```

### 4. File Naming Convention

```
<chart_id>_<type>.md

Examples:
- tuapse_19820613_133910_natal.md
- tuapse_19820613_133910_forecast.md
- synastry_tuapse_moscow.md
```

### 5. Attachment Handling

- Copy SVG/PNG to `attachments/` folder
- Use relative links in notes
- Canvas files reference attachments by path

### 6. Template System

Support custom templates:
```python
def load_template(template_name):
    """Load note template from templates/"""
    with open(f'templates/{template_name}.md', 'r') as f:
        return Template(f.read())
```

## Examples

### Example 1: Export Natal Chart

**User says:** "Export tuapse_19820613_133910 to Obsidian"

**Actions:**
1. Load chart data
2. Generate natal note with template
3. Create Canvas JSON
4. Copy attachments
5. Save to charts/<id>/obsidian/

**Result:**
```
charts/tuapse_19820613_133910/obsidian/
├── tuapse_19820613_133910_natal.md
├── tuapse_19820613_133910_canvas.json
└── attachments/
    ├── chart_wheel.svg
    └── aspect_grid.svg
```

### Example 2: Export Forecast

**User says:** "Create forecast note with progressions"

**Actions:**
1. Load progressed positions
2. Generate forecast note
3. Include delta table (natal → progressed)
4. Link to natal note

**Result:**
```markdown
# Forecast: Tuapse 1982-06-13

## Secondary Progressions (2026-03-04)

| Planet | Natal | Progressed | Delta |
|---|---|---|---|
| Sun | 22° Gemini | 25° Cancer | +3° |
| Moon | 6° Virgo | 12° Libra | +6° |
...
```

### Example 3: Synastry Export

**User says:** "Export synastry for tuapse and moscow"

**Actions:**
1. Load both natal charts
2. Load synastry aspects
3. Generate comparison note
4. Create Canvas with both charts

**Result:**
```markdown
# Synastry: Tuapse & Moscow

## Chart A: Tuapse Natal
- Sun: 22° Gemini
- Moon: 6° Virgo
- ASC: 16° Sagittarius

## Chart B: Moscow Natal
- Sun: 15° Taurus
- Moon: 23° Leo
- ASC: 10° Cancer

## Synastry Aspects
- A Sun conjunct B Venus (3° orb)
- A Moon trine B Moon (2° orb)
...
```

## Troubleshooting

### Error: Canvas file not loading

- **Cause:** JSON format invalid
- **Solution:** Validate JSON, check node/edge structure

### Error: Links broken in Obsidian

- **Cause:** File path incorrect
- **Solution:** Use Obsidian's relative path format [[file]]

### Error: Attachments not showing

- **Cause:** Files not in vault or path wrong
- **Solution:** Copy attachments to vault, update links

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-010 | Obsidian integration module — this skill implements the export |
| ASTRO-005 | Client output packs — skill creates notes for delivery |
| ASTRO-017 | Skills architecture — this is an integration skill |

## Available Code / Tools

### Data Sources
- `charts/<id>/chart.yaml` — Birth metadata for note frontmatter
- `charts/<id>/INDEX.yaml` — Provenance for related files
- `charts/<id>/outputs/*.csv` — Positions, houses, aspects tables

### Reference Documents
- `docs/ASTRO_GLOSSARY.md` — Term definitions for note links
- `docs/HANDOFF_PROMPT_NEXT_AI.md` — Phase analysis for note content

### Obsidian Format Reference
- `.qwen/skills-source/anthropics-skills/skills/canvas-design/SKILL.md` — Canvas JSON format
- Obsidian Canvas spec: JSON with `nodes` and `edges` arrays

### Templates (to be created)
- `.qwen/skills/obsidian-export/templates/chart-note-template.md`
- `.qwen/skills/obsidian-export/templates/canvas-template.json`

### File Conventions
- Note naming: `<chart_id>_natal.md`, `<chart_id>_forecast.md`
- Canvas naming: `<chart_id>_canvas.json`
- Attachments: `attachments/chart_wheel.svg`, `attachments/aspect_grid.svg`
- Links: Obsidian `[[filename]]` format

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/obsidian-export/`
- [ ] Chart note generated with all sections (metadata, positions, houses, aspects)
- [ ] Canvas JSON created with nodes for planets and aspects
- [ ] Files saved to correct folder structure
- [ ] Attachments copied and linked correctly
- [ ] Bidirectional links created between related notes
- [ ] Phase analysis included in notes
- [ ] Index note updated with new chart entry
