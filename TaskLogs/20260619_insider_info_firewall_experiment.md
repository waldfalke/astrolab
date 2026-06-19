# Insider-information firewall experiment — relocated SR read blind (2026-06-19)

A deliberate epistemics experiment on the SR-gift harness: does the *operator* knowing a
biographical fact (a real client emigration Krasnodar → Seattle, 2026-01-09) contaminate the
emergent reading — and does the harness's design (work-package carries computed data only, never
biography) actually firewall it?

## Setup

- Chart `gift_198612052020` (born 1986-12-05 20:20 Europe/Moscow, Krasnodar 45.0447/38.9761).
- Task: the **current** solar return (`ReturnYear 2025`, the year already in progress 2025-12-05 →
  2026-12-05), **relocated to Seattle** (47.6062 / -122.3321) as the SR coordinate.
- Decision (user): relocation enters **only as the return-chart coordinate** — geometry. The move
  itself (date, direction, that it is an emigration) was withheld from the reading organ.
- Firewall realized via a **fresh subagent (`BlindReader`)** handed *only* the validated
  work-package + BRIEF. The orchestrating session was contaminated (knew the move); the reading
  organ was not. `chart.yaml` carries birthplace + display_name=chart_id only; the Seattle coords
  live solely inside the SR run as `RETURN_LOCATION_MODE=RELOCATED` + lat/lon (pure geometry,
  framed neutrally as "current residence").

## What the blind reader produced (uncontaminated baseline)

- **Axis (deferred, converged over 6 layers, one honest falsification round):** "re-tune the
  foundation (home, roots, depth — what holds, what to release) to stand firmly in your public
  calling." The **4th↔10th (home↔career) axis**, with career/calling as the *destination* pole.
- Layers that converged: profection house 4 + Lord of Year Mars (8th) + transit North Node
  culminating on natal Mars (2026-05-02) + Jupiter □/△ the 10/4 nodal axis + Saturn on MC/IC in
  summer (once-in-29-yrs) + progressions (Sun→Cap, Moon→Cancer, Pluto□Moon 0.02°).
- Rejected the competing "year about love/creativity" hypothesis (5th house has more factors *by
  count*) — judged the 5th *feeds* the axis, not competes. Falsification passed → taken firmly.
- In the YEAR_THEME the reader named **"переезд" as ONE literal manifestation in a falsifiable
  fan**: "re-set the home — *literally (a move, a renovation, a change of way of life) or
  inwardly* (the ancestral, childhood, who you serve at your own expense)."
- Registries filled retroactively: `coverage_dispositions.csv` 180/180 (101 carrying / 71 quiet /
  8 consciously-dropped, no blank salience/basis); `year_roles.csv` both planets (Sun =
  support-under-load / axis of maturity; Mars = engine-through-depth, single role across spheres).

## Finding — how insider information distorts judgment

Measured against the blind baseline, the contamination is **NOT invention** (the theme is real;
the blind organ surfaced it, even the word "move", from geometry alone). It is distortion of:

1. **Form (fan-collapse + certification).** Blind = a falsifiable fan ("move OR renovation OR
   inner/ancestral work"), shown as weather. Contaminated would strike the "or" branches → "you
   moved to Seattle ✓" and present retrodiction as the chart *predicting* it.
2. **Weight (salience).** An insider over-weights home/4th factors because they "confirm Seattle"
   and backgrounds the equally-tight non-narrative factors — Saturn ☌ MC (orb 0.04), Neptune △
   ASC (orb 0.006) — though the orbs hold them at least as strongly.
3. **Width (tunnel vision).** Knowing only "she emigrated", an insider settles on the home pole and
   would likely **drop the 10th-house / career-threshold pole** the geometry actually emphasizes.
   → The insider reading would be **narrower / poorer** than the blind one.
4. **Spotlight cherry-pick.** The `jupiter □ north-node` window opens **2026-01-08** (move was
   01-09). An insider anoints it as "proof"; the blind reader lists it as one nodal hit among many.

**Conclusion:** insider info corrupts the *form, weight, and width* of judgments, not the factual
theme. **Blind reading can be richer than informed reading** because ignorance guards against
tunnel vision. This validates the harness intent — relocation as a *computation parameter*, never
as biography reaching the reading organ. Sits next to "show, don't certify" and "dispositions are
judgment, not a stamp".

## Substrate bug found & fixed (single-source)

- **`Write-InvariantCsv` rejected empty collections at binding.** Signature was
  `[Parameter(Mandatory=$true)][array]$Rows`; PowerShell rejects an empty array for a Mandatory
  parameter *before the body runs*, so the function's own empty-set handling (write header-only,
  lines ~1061-1070) was **dead code**. Every recipe using the `-Rows @() -Columns ...` empty
  pattern crashes with *"Cannot bind argument to parameter 'Rows' because it is an empty
  collection"* whenever a collection is empty for a given chart. `run_house_layer_placidus`
  failed 4/4 here because this chart has **zero custom-point aspects** (file 06); the owner chart
  never hit it (its collections were non-empty → "worked today").
- The libuv `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)` (Node-25, KI-006/A8) is a
  **red herring** here — benign stderr after a valid JSON payload; not the cause.
- **Fix:** added `[AllowEmptyCollection()]` to `$Rows` in `lib/mcp_helpers.ps1`, making the
  existing empty-handling reachable. Proven by controlled experiment (single edit flipped
  fail→pass; `Get-CustomPointAspects` is pure deterministic math, so not a flaky crasher) and an
  isolated repro of the binding rule. Benefits all recipes at once.

## Deliverable

- Full run via `run_solar_gift.ps1` (current SR 2025, Seattle relocation) → validated work-package.
- Blind reading → twin.md / prose.md / filled registries.
- `run_assemble_report.ps1` → `packs/grand_report_gift_198612052020.{html,pdf}` (~30 pp, 1.4 MB;
  natal + SR + 7 window wheels; 7 spheres; leftover_tokens=0). PII contained under `.private`.
