---
name: chart-analyst
description: Analyzes chart data from chart.yaml + INDEX.yaml. Extracts positions/aspects/houses, applies phase analysis (Zakharian model), finds aspect patterns, generates structured interpretations. Use when user requests chart analysis, interpretation, or "read this chart".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.2.0
  requires: reading-discipline; astro-engineering-scanner (secret, .codex/skills/)
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

## Instrument Reading Layers (v0.2)

How to **read** the classical layers, not how to compute them — computation is in the recipes
(via `provider-orchestrator` / `chart-data-preparator`); this section only loads their outputs and
says how to weight them. Apply `reading-discipline` throughout (two-axis strength, anti-patterns,
level discipline, observe-don't-narrate). Each layer: **LOAD** (output file) · **READ** · **CAVEAT**.

### Natal-structure layers (delineate freely)

**Essential dignity** — LOAD `outputs/natal_dignities.csv` (body, sign, dignity). READ: dignity is a
**strength source** (third axis with aspect-SNR + angularity). domicile > exaltation; detriment/fall
weaken; peregrine = neutral. CAVEAT: exaltation/fall is **tabular, not phase geometry** (anti-pattern
#11); domicile/detriment is geometric. Canonical: `Get-EssentialDignities`, NKS #33.

**Sect** — LOAD `outputs/natal_sect.csv` (body, sign, planet_team, above_horizon, placement, role).
READ: day/night **reassesses strength beyond dignity**. in-sect = supported/constructive, out-of-sect
= harsher. Roles: sect light; benefic/malefic of-sect vs contrary; the **in-sect malefic is
constructive**, the **out-of-sect malefic is harsh**. Mercury joins by orientality. CAVEAT: outers
carry no sect; this is a **whole-sign** judgement — flag where it diverges from Placidus houses
(anti-pattern #13). Canonical: `Get-Sect`, NKS #42.

**Declination / out-of-bounds** — LOAD `outputs/natal_declinations.csv` (+ `_declination_aspects.csv`).
READ: **parallel ≈ conjunction**, **contraparallel ≈ opposition** (latitudinal, independent of the
longitude aspect grid); **OOB** (|δ| > mean obliquity ≈ 23.44°) = unregulated / extreme expression of
that body. CAVEAT: a separate channel — don't double-count a parallel that just echoes a conjunction.
Canonical: declination helpers, NKS #36.

### Timing layers (frame, not event — observe, don't narrate)

**Annual profection** — LOAD `outputs/solar_return_<year>_profection.csv` (profected sign/house,
lord_of_year, lord natal sign/house). READ: a **timing frame** — foreground the profected-house topics
+ the **lord of year**; weight transits / solar-return contacts to the lord of year more heavily.
CAVEAT: **whole-sign** (≠ Placidus — flag it); reranks priority, **does not date a week**; forward =
observed, not narrated. Canonical: `Get-AnnualProfection`, NKS #43.

**Solar arc — applying / separating** — LOAD the solar-arc aspect outputs (status applying|separating,
tense future|past, perfection_year). READ: **applying = future / maturing**, **separating = past /
worked-out**. CAVEAT: the **sign of the offset decides direction, not the orb magnitude** (anti-pattern
#9 — a separating arc is past even at a tight orb); year-resolution frame, doesn't trigger a week.
Canonical: `run_solar_arc.ps1`.

**Solar-return timing sub-layer** (optional) — `..._activation_dates.csv` (Sun reaches each SR planet's
longitude) + `..._phase_windows.csv` (12 monthly phase segments). READ as **when** the year's themes
get triggered; still framing, fast transits do the actual dating.

## Reference Documents

- `references/phase-analysis-reference.md` — Full phase methodology
- `docs/semantic-base.md` — interpretation discipline (canonical; via `reading-discipline` skill)
- `docs/solar-return-reading-recipe.md` — worked reading with strength + dignity + declination layers
- `docs/methodology-roadmap.md` — instrument queue + what is built vs deferred
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

