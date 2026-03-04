---
name: obsidian-export
description: Exports chart data to Obsidian notes and Canvas format. Creates structured notes with chart metadata, positions, aspects; generates Canvas files for visual chart mapping. Use when user requests "export to Obsidian", "create note", or needs chart context in knowledge base.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output-format: Markdown (notes), JSON (Canvas)
---

# Obsidian Export

Export chart data to Obsidian notes and Canvas format.

## Quick Start

**Input:**
```yaml
chart_id: tuapse_19820613_133910
export_type: note | canvas | both
include_phase_analysis: true
```

**Output:**
```yaml
note_file: charts/<id>/obsidian/<id>_natal.md
canvas_file: charts/<id>/obsidian/<id>_canvas.json
attachments: [chart_wheel.svg, aspect_grid.svg]
```

## Core Workflow

### 1. Load Chart Data

```
charts/<id>/
  chart.yaml        → metadata
  INDEX.yaml        → provenance
  outputs/*.csv     → positions, houses, aspects
```

### 2. Generate Note

Use `templates/chart-note-template.md`:
- Frontmatter with tags
- Birth data table
- Planetary positions
- House cusps
- Aspects
- Phase analysis (optional)
- Bidirectional links

### 3. Generate Canvas

Use `templates/canvas-template.json`:
- Nodes: chart center, planets, angles
- Edges: aspect connections
- Labels: aspect types

### 4. Copy Attachments

```
obsidian/attachments/
  chart_wheel.svg
  aspect_grid.svg
```

### 5. Create Links

```markdown
## Related Charts
- Progressed: [[<id>_progressed_2026]]
- Solar return: [[<id>_solar_return_2026]]
```

## Templates

- `templates/chart-note-template.md`
- `templates/canvas-template.json`

## Scripts

- `scripts/generate_note.py` — Generate note from chart data

## Reference Documents

- `docs/ASTRO_GLOSSARY.md` — Term definitions for links
- `.qwen/skills-source/anthropics-skills/skills/canvas-design/SKILL.md`

## Obsidian Format

**Note links:** `[[filename]]`

**Canvas JSON:**
```json
{
  "nodes": [{"id": "...", "type": "text", "x": 0, "y": 0}],
  "edges": [{"fromNode": "...", "toNode": "..."}]
}
```

## Examples

**Natal export:** `Note + Canvas + attachments`

**Forecast note:** `Progressed table with deltas`

**Synastry:** `Two charts, comparison note`
