# Task Log: ASTRO-027 - Donald Trump chart (natal + directions + progressions + current transit)

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** DONE
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

1. Verify online birth data for Donald Trump (current US president as of 2026-03-04).
2. Build chart via project software stack (not manual calculation).
3. Produce directions, progressions, and current transit artifacts.
4. Capture oddities/problems encountered during execution.

## Online Birth Data (with sources)

### Used for run

- Name: Donald John Trump
- Birth date: 1946-06-14
- Birth time: **10:54** (local)
- Timezone at birth: **-04:00**
- Birth place: Jamaica, Queens, New York, USA (Jamaica Hospital area)
- Coordinates used in run: **40.7000, -73.8164**
- UTC used in run: **1946-06-14T14:54:00Z**

### Sources checked

- Astro-Databank profile (time and place; Rodden AA, with note about disputed alternative times in record comments):
  - https://www.astro.com/astro-databank/Trump,_Donald
- Britannica biography (date/place context):
  - https://www.britannica.com/biography/Donald-Trump

## Run Context

- Current transit timestamp used: **2026-03-04T06:29:42Z**
- Case base: `trump_19460614_1054`
- Output base: `artifacts/results`

## Executed Recipes (project software)

1. `run_natal_with_failover.ps1`
2. `run_house_layer_placidus.ps1`
3. `run_secondary_progressions.ps1`
4. `run_solar_arc.ps1`
5. `run_synastry_matrix.ps1` (used as transit-to-natal aspect matrix at current timestamp)
6. `build_chart_project.ps1`
7. `check_chart_provenance.ps1`
8. `validate_chart_project.ps1`

## Produced Artifacts

### Method run directories

- `artifacts/results/natal_failover_trump_19460614_1054_20260304_092952`
- `artifacts/results/house_placidus_trump_19460614_1054_20260304_093011`
- `artifacts/results/secondary_progressions_trump_19460614_1054_progressions_now_20260304_093022`
- `artifacts/results/solar_arc_trump_19460614_1054_solar_arc_now_20260304_093238`
- `artifacts/results/synastry_trump_19460614_1054_transit_now_20260304_093239`

### Chart project

- `charts/trump_19460614_105400_jamaica_ny`
- Validation:
  - `check_chart_provenance.ps1`: PASS
  - `validate_chart_project.ps1`: PASS

### Key summary counts

- Natal failover: `ASPECT_COUNT=16`, `RUN_STATUS=FULL`, `PROVIDER_USED=swissremote`
- Secondary progressions: `PROGRESSED_TO_NATAL_ASPECT_COUNT=6`
- Solar arc: `DIRECTED_TO_NATAL_PLANET_ASPECT_COUNT=11`, `DIRECTED_TO_NATAL_POINT_ASPECT_COUNT=2`
- Current transit (synastry matrix, orb=1): `MATCH_COUNT=2`

## Oddities / Problems / Nonsense encountered

1. **Provider instability signals despite successful completion**
   - During `run_secondary_progressions.ps1` and `run_solar_arc.ps1`, logs showed:
     - `swissremote appears offline (504 Gateway)`
     - `swissremote.calculate_planetary_positions responded with HTTP 400`
   - Both runs still completed and wrote full artifacts.
   - Implication: retry/fallback logging behavior is noisy and potentially misleading for operators.

2. **Timezone parameter parsing bug on negative offsets in PowerShell invocation**
   - First `build_chart_project.ps1` call failed at `-BirthTimezone "-04:00"` with missing argument parsing.
   - Workaround used: assign timezone to variable (`$tz='-04:00'`) and pass variable.

3. **Transit method gap in recipe naming**
   - There is no explicit dedicated `run_transits_to_natal.ps1` recipe.
   - Current transit was produced via `run_synastry_matrix.ps1` using natal datetime as chart A and current datetime as chart B.
   - It works, but semantics are indirect and not obvious from script name.

4. **Locale formatting inconsistency in transit CSV**
   - `03_synastry_aspect_matrix.csv` contains comma decimals (e.g., `82,928095`), while many other CSV outputs are dot-decimal.
   - Risk: parsing issues in downstream tooling expecting invariant decimal point.

5. **Birth time ambiguity exists in public astrological records**
   - Astro-Databank page includes comments about alternative reported times; selected run uses 10:54 (AA-rated entry).
   - This should be recorded for reproducibility and interpretation caution.

## Notes

- Task requested "honestly via our software"; all calculations were executed through local project recipes and generated artifacts under `artifacts/results` and `charts/`.
- No manual post-computation of astrological positions was used.
