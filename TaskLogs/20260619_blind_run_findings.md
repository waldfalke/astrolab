# Blind control-run findings — owner solar 2026 (2026-06-19)

The first full end-to-end run through the complete harness (front + model + teeth + assembler) on the
owner's chart. The fresh model produced a technically-complete report but a **thinner, de-fleshed**
text than the earlier iterated run, and gave an unusually honest self-report. This log captures the
findings so they aren't lost; triage + fixes follow across sessions.

## A. Real substrate bugs (fix once → every future run benefits)

| # | Bug | Status |
|---|---|---|
| A1 | **Gate looks at the wrong dir.** `Assert-DeliverableReady` checks `coverage_dispositions.csv` in `_model_input/`, but `build_coverage_ledger` writes it to `packs/` and BRIEF says fill `../packs/`. A model that follows BRIEF hits "GATE FAILED: missing" on the sanctioned `-ModelAdapter` path. The fresh model only dodged it by assembling by hand. **Latent break in the canonical path.** | OPEN — high prio |
| A2 | **`basis` contract self-contradicts.** BRIEF: basis = "короткое почему + factor_id via `;`" (prose+id mixed). Validator: splits basis by `;` and requires every token be a real factor_id → dangling-basis if you follow BRIEF literally. | OPEN |
| A3 | **carrier_windows bloated (54).** ~~Jupiter in SLOW_CARRIERS~~ — NOT the cause (Jupiter is frequent on ALL charts by mechanics, and carries real Jupiter-to-angle themes; cutting it = overfit, pitfall #13). Real cause: un-merged retro passes (one theme touching a point in Nov+Jan+Jul = 3 windows). | FIXED — merge by theme (body+target+aspect), all passes → one theme with N dates. Verified on 3 charts: 54→40 (owner), 36 (Lissa), 26 (Mitya); max passes 3 everywhere (retro merge works); planet-agnostic. Further cut to ~carrying = zones #84 + model selection, not merge. |
| A4 | **All 7 spheres charged=True.** `charged` is set by presence of ANY routed factor, not by weight/載-bearing — so the domain axis never says "тихий". Undermines the honest-empty-sphere signal we built. Threshold should be by carrying strength. | OPEN |
| A5 | **prose-style burned the astro-language.** Model read Principle #0 ("no jargon the client doesn't know") as "remove planet NAMES everywhere" → de-fleshed portrait/year/windows into "ум/струна/ветер". Planet names are FLESH, not jargon; #0 targets meta-jargon only; planets fade only in spheres. | FIXED (prose-style §0 explicit) |
| A6 | `chart.yaml` stores `timezone: +04:00` though `Europe/Moscow` was passed. Number correct (1982 decree+DST), but IANA zone lost; `+04:00` for Moscow reads as an error. Semantic drift in presentation. | OPEN — minor |
| A7 | Natal Sun has two values across pipelines: `natal_longitudes.csv` 82.05186° vs SR summary `NATAL_SUN_LONGITUDE` 82.05255° (~2.5″, epoch/nutation handling). Doesn't affect reading; ironic for a SHA-pinned-provenance project. | OPEN — minor |
| A8 | libuv `Assertion failed !(handle->flags & UV_HANDLE_CLOSING)` ×6 from the renderer, exit 0, wheels fine (Node-25 болячка). Swallowed, not cured. | KNOWN — tolerated |
| A9 | BRIEF (~15 KB) duplicates reading-discipline + report-standards that travel in the SAME package — violates "add, don't move / single source". | OPEN — slim it |

## B. Model under-delivery (needs a RULE or a TOOTH, not a substrate fix)

- **B1 — Method layer (the signature) didn't reach prose.** Zakharian stages per body (●, book-verified)
  + the 12 monthly phase-segments — both in twin, neither in the report. PHASE_NOTE is a vague "год
  дышит по стадиям" that doesn't match its own heading. **This is what distinguishes us from a horoscope
  generator — it cannot be the "if I have time" item.** → ROOT CAUSE (good-text model): the phase files
  weren't even in the package — `12_monthly_phase_windows.csv` buried in the SR run-dir, model had to
  guess the path. FIXED: orchestrator copies phase_vectors + zakharian_dignities + 12_monthly_phase_windows
  into the package; BRIEF marks the method layer MANDATORY (stages of key bodies in plain words + bind
  each window-chapter to its year phase-segment). Tooth (lint "carrying phases in prose?") still TODO.
- **B2 — Dispositions stamped, not weighed.** 192 rows filled in one pass; 11 SR-declinations + repeat
  transits copy-pasted "— фон" to clear the gate. → BEST fix (good-text model): it's a COGNITIVE-ORDER
  problem. Knowing 200 rows await, the model reads the chart in enumeration mode → prose comes out as a
  methodichka. Fix the ORDER: read the chart as a SYSTEM first (portrait→theme→windows→spheres), write
  prose from understanding, THEN fill dispositions as a RETROACTIVE check ("what did I use, what did I
  consciously drop, why"). Changes the gate's meaning from "enumerate before prose" to "after the live
  reading, confirm nothing was lost." FIXED in BRIEF (Порядок работы: twin→prose→dispositions; gate
  still verifies before assembly). The anti-skid threshold note (tight dir/prog) complements it.
- **B3 — Versions log (gate 3) empty by design-dodge.** Model chose poles in prose (Mercury "за",
  Sept "risk", Venus "за с оговоркой") but left valence_resolved blank in all 192 → the silent
  pole-collapse the discipline warns against. → require coverage_versions where a pole was taken.
- **B4 — Weak spheres near Barnum** (self/money/love) — rode tone over specifics. → anti-Barnum tooth.
- **B5 — dispositor-sinks faked from fluency** — wrote "сходятся к Меркурию и Венере" without tracing
  chains; missed the third sink (Jupiter). → not reproducible from operators (gate-1 fails).
- **B6 — No visual proof.** Read HTML markup, never looked at the PDF (advisor asked). → tooth:
  auto-screenshot page 1 so the model is forced to SEE the artifact.
- **B7 — TaskLog not written** (hard-constraint #3) — rationalized away. (This file discharges it.)

## C. Highest-leverage next step (model's own verdict, and I agree)

**Get the method layer (phases + Zakharian stages) into the prose** (B1). Without it the report is
technically clean but loses the one thing that separates this project from any horoscope generator.
Plus the visual-proof step (B6) and computed dispositions to fixpoint (B2).

## Priority order (proposed)
1. A1 (gate dir) — silently breaks the sanctioned path for the next model. Cheapest, highest blast radius.
2. A5 (astro-language) — DONE; the de-fleshing was the visible quality regression.
3. B1 + B2 — method layer to prose + computed salience (the signature + honest registry).
4. A3, A4 (Jupiter speed-split, sphere charged threshold) — sharpen the axes.
5. A9 (slim BRIEF), A2 (basis contract), the minors.

> Pending: advice from the EARLIER (good-text) model — incorporate before finalizing the fix order.
