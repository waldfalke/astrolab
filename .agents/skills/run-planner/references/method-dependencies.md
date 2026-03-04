# Method Dependencies

## Dependency Graph

```
natal_failover ─┬─→ secondary_progressions
                └─→ solar_arc

house_placidus ─┴─→ (independent, can run anytime)

synastry_matrix → natal_failover (for both charts)
```

---

## Method Specifications

### natal_failover

**Purpose:** Calculate planetary positions with failover

**Requires:** Nothing (base method)

**Provides:**
- `positions` — Planetary longitudes
- `aspects` — Major aspects
- `moon_phase` — Moon phase info

**Output Files:**
- `00_summary.txt`
- `01_primary_positions.json` (if primary available)
- `03_backup_ephemeris.json`
- `04_backup_aspects.json`
- `06_backup_longitudes.csv`

**Provider:** Swiss Ephemeris (primary), Ephemeris (backup)

---

### house_placidus

**Purpose:** Calculate Placidus house cusps

**Requires:** Nothing (base method)

**Provides:**
- `houses` — 12 house cusps
- `chart_points` — ASC, MC, DSC, IC
- `planets_primary` — Planet positions with houses

**Output Files:**
- `00_summary.txt`
- `02_houses_placidus.csv`
- `03_chart_points.csv`
- `04_planets_primary.csv`
- `05_additional_points.csv`

**Provider:** Swiss Ephemeris

---

### secondary_progressions

**Purpose:** Calculate progressed positions (1 day = 1 year)

**Requires:**
- `natal_failover` — For natal comparison

**Provides:**
- `progressed_positions` — Planets at progressed date
- `progression_aspects` — Progressed to natal aspects

**Output Files:**
- `00_summary.txt`
- `03_progressed_planet_deltas.csv`
- `07_progressed_to_natal_aspects.csv`

**Parameters:**
- `birth_utc` — Birth datetime
- `target_utc` — Date to progress to

---

### solar_arc

**Purpose:** Calculate solar arc directed positions

**Requires:**
- `natal_failover` — For natal comparison

**Provides:**
- `directed_positions` — Solar arc planets
- `solar_arc_aspects` — Directed to natal aspects

**Output Files:**
- `00_summary.txt`
- `03_solar_arc_directed_positions.csv`
- `04_directed_to_natal_planets_aspects.csv`
- `05_directed_to_natal_points_aspects.csv`

**Parameters:**
- `birth_utc` — Birth datetime
- `target_utc` — Date to direct to

---

### synastry_matrix

**Purpose:** Cross-chart aspect matrix

**Requires:**
- `natal_failover` (Chart A)
- `natal_failover` (Chart B)

**Provides:**
- `synastry_aspects` — Cross-chart aspects

**Output Files:**
- `00_summary.txt`
- `synastry_matrix.csv`

---

## Parallel Execution Groups

```
Group A (can run together):
  - natal_failover
  - house_placidus

Group B (can run together, after A):
  - secondary_progressions
  - solar_arc

Group C (requires specific prereqs):
  - synastry_matrix (needs both natal charts)
```

---

## File Naming Conventions

### Run Directory

```
<method>_<chart_id>_<timestamp>

Example:
natal_failover_trump_19460614_105400_jamaica_ny_20260304_141520
```

### Summary File

```
<run_dir>/00_summary.txt

Key fields:
  CASE_ID: <chart_id>
  RUN_STATUS: FULL | DEGRADED | FAILED
  PROVIDER_USED: swissremote | ephemeris
```

---

## Execution Order

For "Натал + прогноз":

```
1. natal_failover (Group A)
2. house_placidus (Group A, parallel with 1)
3. secondary_progressions (Group B, after 1)
4. solar_arc (Group B, after 1)
```

Total estimated time: ~2 minutes (with parallel execution)

