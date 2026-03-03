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
Z = distance from domicile to current sign (1-12)

Example:
  Sun domicile = Leo
  Sun in Gemini = 7 signs from Leo (counting counter-clockwise)
  Z = 7 (Mirror)
```

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
D = phase of dispositor planet from ITS own domicile

Example:
  Sun in Gemini → dispositor = Venus
  Venus in Aries → 5 signs from Libra (Venus domicile)
  D = 5 (Play)
```

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
