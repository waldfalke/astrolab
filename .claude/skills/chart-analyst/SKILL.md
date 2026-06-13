---
name: chart-analyst
description: Analyzes chart data from chart.yaml + INDEX.yaml. Extracts positions/aspects/houses, applies phase analysis (Zakharian model), finds aspect patterns, generates structured interpretations. Use when user requests chart analysis, interpretation, or "read this chart".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: astro-engineering-scanner (secret, .codex/skills/)
---

# Chart Analyst

Analyze chart data with phase analysis methodology.

## Quick Start

**Input:**
```yaml
chart_id: trump_19460614_105400_jamaica_ny
analysis_type: natal | forecast | synastry
include_phase_analysis: true
synthesis: false
```

**Output:**
```yaml
planets:
  - name: Sun
    state_vector: {Z: 7, z: 9, H: 10, h: 8, D: 5}
    aspects: [...]
patterns: [Stellium, Grand Trine]
synthesis_ready: false
```

## Core Workflow

### 1. Load Chart Data

```
charts/<id>/outputs/
  planets_primary.csv
  houses_placidus.csv
  natal_aspects.json
```

### 2. Compute Phase Vectors

```
P <Z.z : H.h : D>

Z = sign phase from domicile (1-12)
z = microphase in sign (ceil(deg/2.5))
H = house number (1-12)
h = microphase in house
D = dispositor phase
```

### 3. Find Patterns

- Stellium (3+ in same sign/house)
- Grand Trine (equilateral triangle)
- T-Square (opposition + square)
- Yod (sextile + quincunxes)

### 4. Generate Output

Per-planet:
```
OBJECT: Sun
COORDINATES: 22° Gemini
STATE VECTOR: P <7.9 : 10.8 : D=5.2>
NETWORK RESONANCE:
  Sun --(7-Mirror)--> Venus / 72°
```

### 5. Synthesis (On Command)

Only after `SYNTHESIS` or `СИНТЕЗ`:
- Summary table
- Dominant phases
- Central planets

## Reference Documents

- `references/phase-analysis-reference.md` — Full methodology
- `.codex/skills/astro-engineering-scanner/SKILL.md` — Secret skill

## Phase Dictionary

| Phase | Name | Keywords |
|---|---|---|
| 1 | Impulse | Initiation |
| 7 | Mirror | Partnership |
| 10 | Result | Career |
| 12 | Archive | Completion |

## Examples

**Single planet:** `Sun analysis with state vector`

**Full chart:** `10 planets, no synthesis`

**Synthesis command:** `Summary table + interpretation`

