# Task Log: ASTRO-019 - Skill: chart-analyst

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

Create the `chart-analyst` skill that parses chart-project data (chart.yaml + INDEX.yaml), extracts planetary positions/aspects/houses, and applies interpretation rules including the proprietary phase analysis methodology.

## Skill Location

```
.qwen/skills/chart-analyst/
├── SKILL.md
├── scripts/
│   └── phase_calculator.py (optional - computation helper)
└── references/
    ├── phase-dictionary.md
    └── aspect-patterns.md
```

## SKILL.md Frontmatter

```yaml
---
name: chart-analyst
description: Analyzes chart data from chart.yaml + INDEX.yaml. Extracts positions/aspects/houses, applies phase analysis (Zakharian model), finds aspect patterns, generates structured interpretations. Use when user requests chart analysis, interpretation, or "read this chart".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  requires: astro-engineering-scanner (secret, in .codex/skills/)
---
```

## Implementation Steps

### Step 1: Load Chart Data

Parse chart-project structure:

```python
# Load chart identity
chart_yaml = load_yaml('charts/<id>/chart.yaml')

# Load provenance index
index_yaml = load_yaml('charts/<id>/INDEX.yaml')

# Load output files
positions = load_csv('charts/<id>/outputs/planets_primary.csv')
houses = load_csv('charts/<id>/outputs/houses_placidus.csv')
aspects = load_json('charts/<id>/outputs/natal_aspects.json')
```

### Step 2: Normalize Data Structure

Create unified data model:

```python
class Planet:
    name: str
    longitude: float  # 0-360
    sign: str
    sign_degree: float  # 0-30
    house: int  # 1-12
    house_degree: float  # position within house
    retrograde: bool
    dispositor: str  # ruler of sign

class House:
    number: int
    cusp_longitude: float
    sign: str
    cusp_degree: float
    length: float  # house size in degrees

class Aspect:
    planet1: str
    planet2: str
    type: str  # conjunction, sextile, square, trine, opposition
    angle: float
    orb: float
    applying: bool  # true if planets moving toward exact aspect
```

### Step 3: Compute Phase Vectors

For each planet, calculate `P <Z.z : H.h : D>`:

**Z-phase (Sign Vector):**
```
Z = distance from domicile to current sign (1-12)
z = ceil(deg_in_sign / 2.5)  # microphase 1-12
```

**H-phase (House Vector):**
```
H = house number (1-12)
h = ceil(12 * (position - cusp) / house_length)  # microphase 1-12
```

**D-vector (Dispositor):**
```
D = phase of dispositor planet from its own domicile
```

### Step 4: Find Aspect Patterns

Detect configurations:

| Pattern | Definition |
|---|---|
| **Conjunction** | 2+ planets within orb (0°) |
| **Opposition** | 2 planets ~180° |
| **Square** | 2 planets ~90° |
| **Trine** | 2 planets ~120° |
| **Sextile** | 2 planets ~60° |
| **Grand Trine** | 3 planets in trine (equilateral triangle) |
| **T-Square** | 2 planets opposite, both square to third |
| **Grand Cross** | 4 planets in square (cross pattern) |
| **Yod** | 2 planets sextile, both quincunx to third (150°) |
| **Stellium** | 3+ planets in same sign/house |

### Step 5: Apply Phase Dictionary

Map phase numbers to meanings:

| Phase | Name | Keywords |
|---|---|---|
| 1 | Impulse | Initiation, breakthrough, self-start |
| 2 | Resource | Accumulation, foundation, values |
| 3 | Link | Communication, connection, learning |
| 4 | Base | Stability, home, security |
| 5 | Play | Creativity, expression, risk |
| 6 | Service | Refinement, health, duty |
| 7 | Mirror | Partnership, projection, balance |
| 8 | Transformation | Crisis, rebirth, shared resources |
| 9 | Strategy | Vision, expansion, philosophy |
| 10 | Result | Achievement, status, career |
| 11 | Optimization | Innovation, community, future |
| 12 | Archive | Completion, release, subconscious |

### Step 6: Generate Interpretation

**Per-Planet Output:**
```
OBJECT: Sun

COORDINATES: 22° Gemini

STATE VECTOR:
P <7.3 : 10.8 : D=5.2>

CALCULATION:
Z-phase (from Leo): 7
z-micro (in sign): 22/2.5 => 9 => 3
H-phase (from ASC): 10
h-micro (in house): (285-270)/15*12 => 8
D-sanction (Venus): 5

NETWORK RESONANCE:
Sun --(7-Mirror)--> Venus / 72°
Sun --(3-Link)--> Saturn / 118°
```

**Synthesis Output (after SYNTHESIS command):**
- Summary table of all planets with state vectors
- Key patterns identified
- Dominant phases (which numbers appear most)
- Centers of gravity (most aspected planets)

## Important Nuances

### 1. Separation of Calculation and Interpretation

- **Calculation phase:** Pure computation, no interpretation
- **Synthesis phase:** Only after explicit `SYNTHESIS` or `СИНТЕЗ` command
- This prevents premature conclusions and maintains analytical rigor

### 2. Directed Aspect Notation

Use asymmetric notation (not bidirectional):

```
# Correct:
Sun --(7-Mirror)--> Moon / 182°

# Incorrect (symmetric):
Sun <-> Moon / 182°
```

Rationale: Aspects have direction (faster → slower planet) and phase meaning depends on direction.

### 3. Microphase Precision

- Microphases use `ceil()` (always round up)
- Range is `1..12` within each sign/house
- 2.5° per microphase in signs (30° / 12)
- Variable microphase size in houses (depends on house length)

### 4. Dispositor Chain Depth

- Primary dispositor: ruler of planet's sign
- Secondary dispositor: ruler of primary dispositor's sign
- Track chains up to 3 levels deep
- Note if chain terminates (domicile) or loops (mutual reception)

### 5. House System Consistency

- Always use Placidus for H-phase calculations
- Record house system in chart.yaml
- If Placidus unavailable (polar regions), note fallback system

### 6. Orb Sensitivity

- Default orb: 6° for major aspects
- Tighter orb (3°) for conjunctions/oppositions
- Wider orb (8°) for Sun/Moon aspects
- Record actual orb in aspect output

### 7. Retrograde Handling

- Mark retrograde planets distinctly
- Consider retrograde status in dispositor calculations
- Note: retrograde planets may have modified phase interpretations

## Examples

### Example 1: Single Planet Analysis

**User says:** "Analyze Sun in chart tuapse_19820613_133910"

**Actions:**
1. Load chart data
2. Extract Sun position (longitude, sign, house)
3. Compute Z.z, H.h, D vectors
4. Find aspects from/to Sun
5. Output structured analysis

**Result:**
```
OBJECT: Sun

COORDINATES: 22° Gemini

STATE VECTOR:
P <7.3 : 10.8 : D=5.2>

CALCULATION:
Z-phase (from Leo): Gemini is 7th from Leo => 7
z-micro (in sign): 22°/2.5 => ceil(8.8) => 9
H-phase (from ASC Sagittarius): 10th house => 10
h-micro (in house): (285°-270°)/15°*12 => ceil(9.6) => 8
D-sanction (Venus, ruler of Gemini): Venus in Aries, 5th from Libra => 5

NETWORK RESONANCE:
Sun --(7-Mirror)--> Venus / 72° (applying)
Sun --(3-Link)--> Saturn / 118° (separating)
```

### Example 2: Full Chart Synthesis

**User says:** "СИНТЕЗ" (after analyzing all planets)

**Actions:**
1. Compile all planet state vectors
2. Identify dominant phases
3. Find central planets (most connections)
4. Generate summary table

**Result:**
```
SYNTHESIS TABLE:

| Planet | Z.z  | H.h  | D    | Phase Name      |
|--------|------|------|------|-----------------|
| Sun    | 7.9  | 10.8 | 5.2  | Mirror-Result   |
| Moon   | 2.4  | 3.6  | 7.1  | Resource-Link   |
| Mercury| 6.11 | 9.2  | 5.2  | Service-Strategy|
...

Dominant phases: 7 (Mirror) x4, 10 (Result) x3
Central planet: Venus (6 connections)
```

## Troubleshooting

### Error: Missing output files

- **Cause:** Chart-project not built, files not in outputs/
- **Solution:** Run `chart-data-preparator` skill first

### Error: House calculation fails

- **Cause:** Birth location in polar region, Placidus undefined
- **Solution:** Fall back to Equal houses, note in output

### Error: Dispositor not found

- **Cause:** Planet in sign with no traditional ruler (modern planets)
- **Solution:** Use co-ruler or note "no traditional dispositor"

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-012 | Agent orchestrator — this skill is called by orchestrator |
| ASTRO-008 | Modular architecture — skill encapsulates analysis logic |
| ASTRO-017 | Skills architecture — this is one of the core skills |

## Available Code / Tools

### Secret Skills (Proprietary)
- `.codex/skills/astro-engineering-scanner/SKILL.md` — Zakharian phase analysis
  - Phase dictionary (1..12)
  - State vector calculation (Z.z, H.h, D)
  - Directed aspect notation

### Reference Documents
- `docs/ASTRO_GLOSSARY.md` — Term definitions
- `docs/HANDOFF_PROMPT_NEXT_AI.md` — Phase analysis methodology

### Data Sources
- `charts/<id>/outputs/planets_primary.csv` — Planet positions
- `charts/<id>/outputs/houses_placidus.csv` — House cusps
- `charts/<id>/outputs/natal_aspects.json` — Aspects data

### Phase Analysis Constants
- `sign_phase_size = 30 deg`
- `micro_phase_size = 2.5 deg`
- `rounding = ceil` (always round up)
- `object_notation = P <Z.z : H.h : D>`

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/chart-analyst/`
- [ ] Skill can parse chart.yaml + INDEX.yaml and load all data
- [ ] Phase vectors (Z.z, H.h, D) computed correctly for all planets
- [ ] Aspect patterns detected (grand trine, T-square, Yod, etc.)
- [ ] Per-planet output follows structured format
- [ ] Synthesis only produced after explicit command
- [ ] Phase dictionary applied consistently
- [ ] Directed aspect notation used (not symmetric)
