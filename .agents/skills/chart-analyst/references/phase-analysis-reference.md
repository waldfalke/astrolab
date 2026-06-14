# Phase Analysis Reference (Zakharian Model)

## Core Concepts

### State Vector Notation

```
P <Z.z : H.h : D>

Where:
  P  = Planet
  Z  = Phase from domicile (sign vector), 1-12
  z  = Microphase within sign, 1-12
  H  = Phase from ASC (house vector), 1-12
  h  = Microphase within house, 1-12
  D  = Phase of dispositor planet
```

---

## Phase Dictionary (1-12)

| Phase | Name | Keywords | Element |
|---|---|---|---|
| 1 | Impulse | Initiation, breakthrough, self-start | Fire |
| 2 | Resource | Accumulation, foundation, values | Earth |
| 3 | Link | Communication, connection, learning | Air |
| 4 | Base | Stability, home, security | Water |
| 5 | Play | Creativity, expression, risk | Fire |
| 6 | Service | Refinement, health, duty | Earth |
| 7 | Mirror | Partnership, projection, balance | Air |
| 8 | Transformation | Crisis, rebirth, shared resources | Water |
| 9 | Strategy | Vision, expansion, philosophy | Fire |
| 10 | Result | Achievement, status, career | Earth |
| 11 | Optimization | Innovation, community, future | Air |
| 12 | Archive | Completion, release, subconscious | Water |

---

## Calculation Formulas

### Z-Phase (Sign Vector)

```
Z = ((sign_index − domicile_index) mod 12) + 1
  — counted FORWARD through the zodiac; domicile = phase 1 (planet "at rest" / at home).

Why this direction + indexing are fixed: the 12 phase keywords map 1:1 onto the sign
archetypes counted from Aries (1 Impulse = Aries, 2 Resource = Taurus, … 12 Archive = Pisces).
So "phase N from domicile" = the archetype of the Nth sign starting at the planet's home.
Self-check: phase 7 (Mirror) = the sign OPPOSITE the domicile (detriment).

Example:
  Sun domicile = Leo (5); Sun in Gemini (3): Z = ((3 − 5) mod 12) + 1 = 11 (Optimization)
  Sun in Aquarius (opposite Leo): Z = ((11 − 5) mod 12) + 1 = 7 (Mirror) — detriment
```

> CORRECTION (reconstructed): the prior worked example here was internally inconsistent
> ("Sun in Gemini → Z = 7" does not satisfy the rule — Z = 7 is Aquarius, Leo's opposite).
> The convention above is reconstructed from the phase-keyword ↔ sign-archetype isomorphism;
> treat as **anumita** (inferred), not **pramanita** (verified against the primary source).

### z-Microphase (Within Sign)

```
z = ceil(deg_in_sign / 2.5)

Where:
  deg_in_sign = 0 to 30
  2.5 = microphase size (30° / 12)
  ceil = always round up

Example:
  Sun at 22° Gemini
  z = ceil(22 / 2.5) = ceil(8.8) = 9
```

### H-Phase (House Vector)

```
H = house number (1-12)

Example:
  Sun in 10th house
  H = 10 (Result)
```

### h-Microphase (Within House)

```
h = ceil(12 * (planet_lon - house_cusp) / house_length)

Where:
  planet_lon = planet's ecliptic longitude
  house_cusp = longitude of house cusp
  house_length = next_cusp - current_cusp

Example:
  Sun at 285°, 10th house cusp at 270°, house length 15°
  h = ceil(12 * (285 - 270) / 15) = ceil(12 * 1) = 12
```

### D-Vector (Dispositor Phase)

```
D = the Z-phase of the planet that RULES the current sign, computed from ITS own domicile.

Example:
  Sun in Gemini → ruler of Gemini = Mercury (NOT Venus).
  Take Mercury's own sign-phase Z → that value is D for the Sun.
```

> CORRECTION: the prior example had two transcription errors — it named Venus as the ruler of
> Gemini (Gemini is ruled by **Mercury**), and used an inconsistent sign count. Dispositor uses
> the chosen rulership scheme (traditional | modern); **modern** gives every planet a domicile
> (outers included: Aquarius→Uranus, Pisces→Neptune, Scorpio→Pluto), so the sign-layer is fully
> computable. Dual-ruler planets (Mercury: Gemini/Virgo; Venus: Taurus/Libra) — compute both,
> use nearest domicile as the representative.

---

## Dispositor Relationships

### Traditional Rulers

| Sign | Ruler |
|---|---|
| Aries | Mars |
| Taurus | Venus |
| Gemini | Mercury |
| Cancer | Moon |
| Leo | Sun |
| Virgo | Mercury |
| Libra | Venus |
| Scorpio | Mars |
| Sagittarius | Jupiter |
| Capricorn | Saturn |
| Aquarius | Saturn (traditional) / Uranus (modern) |
| Pisces | Jupiter (traditional) / Neptune (modern) |

### Dispositor Chain

```
Planet A in sign X → dispositor = Planet B
Planet B in sign Y → dispositor = Planet C
...

Track up to 3 levels:
  Level 1: Primary dispositor
  Level 2: Secondary dispositor
  Level 3: Tertiary dispositor

Termination:
  - Domicile (planet in own sign) → chain ends
  - Mutual reception → loop detected
```

---

## Directed Aspect Notation

### Format

```
P1 --(Phase)--> P2 / (Angle)

Example:
Sun --(7-Mirror)--> Venus / 72°
```

### Aspect Types

| Aspect | Angle | Orb |
|---|---|---|
| Conjunction | 0° | 6° |
| Sextile | 60° | 4° |
| Square | 90° | 6° |
| Trine | 120° | 6° |
| Opposition | 180° | 6° |
| Quincunx | 150° | 3° |

### Direction Rule

```
Faster planet → Slower planet

Example:
  Sun (faster) --(...)--> Saturn (slower)
  NOT: Saturn --(...)--> Sun
```

---

## Synthesis Rules

### When to Synthesize

Only produce synthesis after explicit command:
- `SYNTHESIS`
- `СИНТЕЗ`
- "Give me the full reading"

### Synthesis Structure

1. **Summary table** — All planets with state vectors
2. **Dominant phases** — Which numbers appear most
3. **Central planets** — Most aspected, most connections
4. **Interpretation** — Phase dictionary terms only

### Example Synthesis

```
SYNTHESIS TABLE:

| Planet | Z.z  | H.h  | D    | Phase Name      |
|--------|------|------|------|-----------------|
| Sun    | 7.9  | 10.8 | 5.2  | Mirror-Result   |
| Moon   | 4.2  | 10.5 | 3.1  | Base-Result     |
| Mercury| 7.11 | 11.2 | 5.2  | Mirror-Optimize |

Dominant phases: 7 (Mirror) x4, 10 (Result) x3
Central planet: Venus (6 connections)

Summary:
  Theme: Relationships (Mirror) through career achievement (Result)
  Expression: Creative play sanctions identity (Venus D=5)
```

---

## Constants

```
sign_phase_size = 30 deg
micro_phase_size = 2.5 deg
rounding = ceil (always round up)
object_notation = P <Z.z : H.h : D>
```
