# TaskLog — Methodology reading layer + chart-project re-index

- **Date:** 2026-06-14
- **Chart:** personal test chart (lives only in `.private/` + `obsidian-vault/`, both gitignored)
- **Cynefin:** Complicated (known craft, codified into recipes) with a Clear closing gate (validation/index).
- **Status:** DONE

## Scope
Close the whole astrology *reading-methodology* layer built across 2026-06-13/14 and run the
chart-project closing gate that had been skipped.

## What was built (recipes — zero new scripts, extended existing)
- `lib/mcp_helpers.ps1`: `Get-EssentialDignities`, declination helpers (`Get-MeanObliquityDeg`,
  `Get-EphemDeclinations`, `Get-DeclinationAspects`), `Get-Sect`, `Get-AnnualProfection`.
- `run_natal_with_failover.ps1` — dignity + declination/OOB layers.
- `run_secondary_progressions.ps1` — progressed dignities.
- `run_solar_revolution.ps1` — dignities, declination, monthly phase windows, Sun-activation dates,
  **annual profection** (whole-sign, traditional rulers).
- `run_house_layer_placidus.ps1` — **sect** (day/night, in/out-of-sect, benefic/malefic-of-sect;
  Mercury orientality via signed Sun→planet angle).
- `run_transits_to_natal.ps1` — range-scan mode (exact passes as orb-minima with parabolic refine).
- `run_solar_arc.ps1` — applying/separating + tense via signed offset.

## Readings written (Russian, personal → obsidian only)
natal, progressions, solar return, solar arc, transits timeline, **sect**, **profection**.
Discipline enforced: two-axis strength, no "cheap confirmation" stacks (Venus = mixed, not a stack;
Mercury = the real rule-of-three), whole-sign≠Placidus flagged, forward windows OBSERVED not narrated.

## Result highlights (this chart)
- Day chart. Sect: Saturn (exalt+in-sect), Mars (detriment+out-of-sect), Mercury (domicile+in-sect+angular).
- Age-44 profection: 9th whole-sign = Taurus → Lord of Year **Venus** (also dispositor-sink), mixed signature.

## Root cause recorded (the actual "done on the cheap")
Method runs across this layer were **promoted by hand-copy from `D:\Temp\claude\…` into
`methods/`**, bypassing the canonical pipeline (`build_chart_project.ps1` / `archive_runs.ps1`).
Consequences that accumulated:
1. `INDEX.yaml` stale since 2026-03-02 — none of declination/dignity/solar-return/transits/
   solar-arc-2026/sect/profection were indexed.
2. `TaskLogs/` was empty (hard-constraint #3 violated) — this file fixes that.
3. Schema/provenance validation never run after promotions (hard-constraint #4).

**Why `build_chart_project.ps1` was NOT used for the fix:** it only knows 5 methods (no
`solar_return`/`transit_timeline`), copies a fixed output set, and fully overwrites INDEX — it would
have produced a *poorer* index. Re-index was done by an inline generator that maps each `outputs/`
file to its real backing run **by content-hash match** (honest provenance, not green-by-listing),
with `external_source: n/a` (a legal state under `canonical_source_v1`, per `check_chart_provenance`).

## Closing gate (this session)
- `validate_chart_project.ps1` → PASS
- `check_chart_provenance.ps1` → PASS (canonical refs all resolve; external = n/a, legal)
- Containment re-checked after re-index: `git status` clean of `tuapse|private|obsidian`.

## Self-check
- [x] Reproducible packs (summary+hashes) for every run; outputs hash-traceable to a run.
- [x] Personal data never left `.private/` + `obsidian-vault/`.
- [x] No new scripts; existing recipes extended.
- [x] Numbers + reading discipline reviewed by advisor.
- [x] Root cause (hand-promote bypass) recorded, not just the symptom.

## Follow-ups (backlog → docs/methodology-roadmap.md)
Natal-structure batch (fixed stars, lots, midpoints/antiscia, minor dignities/almuten, whole-sign
overlay, derived houses); timing batch (eclipses, lunar returns, progressed lunation, ZR/firdaria,
**void-of-course Moon** — transiting electional + progressed "between-chapters", NOT in arc directions).
Process fix: prefer routing future runs through the pipeline (or extend it to the new methods) so the
index does not drift again.
