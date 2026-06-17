---
name: reading-discipline
description: Interpretation discipline for chart reading — semantic composition operators, non-commutativity, the anti-pattern catalog, two-axis strength, ritual order, level discipline, and the observe-don't-narrate rule. Use when reading or interpreting any chart (natal, progressions, solar return, directions, transits) to keep delineation honest and reproducible.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.5.0
  canonical: docs/semantic-base.md
---

# Reading Discipline

The guardrails for *interpreting* a chart, separate from computing it. This file is a **compact
digest + pointers** — it is NOT the source of truth.

> **Canonical source: `docs/semantic-base.md`. Edit the methodology THERE, not here.**
> This skill and the NKS realm `astrolab` (holon #30) carry digests that point back to it; if they
> disagree with `semantic-base.md`, the doc wins. (Add, don't move — single source of truth.)

## When to apply
Whenever you read/interpret a chart at any level. Mechanical extraction (phase vectors, patterns)
is `chart-analyst`; this skill governs how the extracted facts become a responsible reading.

## Domain routing (Cynefin) — pick the mode per sub-task, not per reading
A reading runs all three domains at once; **route each sub-task**, don't treat the whole reading as one.
- **Clear** — look up a symbol's **range/fan** (Venus→{draw-close, value}; Gemini→{air, mutable}). Clear is
  describing the *elements*, NOT a verdict on the placement. The atom is **already a fan**; the moment you
  compose elements and pick a pole you have **left Clear** (picking a pole here = anti-pattern #1).
- **Complicated** — weigh one object/event's full condition (dignity, sect, phase, declination, orbs):
  sense→**analyze**→respond. Several valid weightings; expertise picks. (Two-axis strength lives here.)
- **Complex** — a theme, or **the whole chart** (it always works in full): probe→sense→respond. This **is**
  the coverage model — every factor on the table → corroboration → re-rank. **Cherry-pick is a complex-domain
  sin**: picking factors destroys the emergent whole (an atom can be stated alone; a *theme* cannot).

**Two orthogonal axes — never merge them.** *script ↔ model* = **who** (fact/computation vs meaning/judgment).
*Cynefin* = **how much emergence** (the model's mode + what the script may verify). Every domain has both:
even Venus-in-Gemini, the script gives the position and the model picks the meaning; even a complex theme,
the script still enumerates + verifies. Cynefin sets the model's **mode**, not who does the work.

**Default failure = Disorder.** Unsure which domain → you fall into your favorite. A reading model's favorite
is *categorize into a training-data cliché* (= fake-Clear) — that is the «лысый соляр» / cherry-pick mechanism.
**Routing presumption, both ways:** suspect **more** emergence than appears (a theme is complex even when a
factor looks simple) — and the symmetric guard: don't inflate an atom into drama (balloon, #4).

## Roles (composition inputs)
- planet = **agent** (verb / motive) · sign = **reservoir** (style / element-mode) · house = **arena**
  (life area) · aspect = **directed link** · dignity = **strength** · declination/OOB = **in-bounds / out**.
- A meaning is a **fan**, not a string. **Valence is not predetermined** — observation picks the pole.

## Composition operators (directed — order and role are fixed)
1. planet ⊗ sign · 2. planet ⊗ house · 3. ruler(A) → B (disposition) · 4. aspect faster → slower ·
5. Nth-from-X (derived house). Result of any composition is a fan. **Store operators, never
enumerate the product** (don't write the planet×sign×house grid).

## Non-commutativity (fundamental)
- **Semantic:** "link 2→8" ≠ "link 8→2" even when the derived house is the same — the path differs.
  Same for aspect direction, disposition (ruler A in B ≠ B in A), derivation (Nth *from* X).
- **Procedural:** reading order changes the result — solar-return→natal ≠ natal→solar-return
  (what is read first sets the frame).

## Two-axis strength
Rate a signal on **reliability (SNR)** × **directness** (direct vs through-dispositor). The **rule of
three** (corroborate with three independent instruments) applies **only to weak/indirect** signals;
a fast trigger is not a slow confirmation. Distinguish essentially dignified from accidentally
supported — do not stack collapsed facts (one configuration ≠ several strength-votes).

## Anti-pattern catalog (one line each)
1. Deterministic collapse (placement → one fixed event). 2. Single-valence (8th = only death).
3. Predetermined valence (good/bad before observation). 4. Enumerating the product (cells, not
operators). 5. Symmetrizing the directed (2↔8 / aspect / disposition read as commutative).
6. Level confusion (natal "shows" a current situation). 7. Postdiction-fitting (symbol bent to
known biography). 8. Cheap confirmation (weak/fast signal taken as full). 9. Orb without sign
(separating read as applying). 10. Empty definitional (SR-Sun ☌ natal-Sun carries no signal).
11. Geometry instead of table (exaltation from phase geometry — it is tabular). 12. Premature
synthesis (before all factors are surveyed). 13. Foreign-system import (mixing house systems /
levels / schools in one step). 14. **Cherry-pick** (selective surfacing of convenient factors/poles,
silently dropping inconvenient ones) — distinct from #2/#3: selection *across the reading*, not the
valence of one factor. Cured by coverage (every factor gets an explicit disposition).

## Ritual order (non-commutative)
- **"Understand the person":** natal only (structure), no timing.
- **"Year ahead":** natal (frame) → profection (lord of year) → solar return (year theme) →
  solar arc (multi-year frame) → progressions (timer) → transits (fine timing). Each is read
  *inside* the frame of the previous; framing layers don't date a week, fast ones do.
- **Re-entrant, not linear.** Order sets the frame, but passes **repeat**: a theme seen in
  directions/transits sends you back to re-rank the shared ledger. Loop until ranks converge.

## Level discipline + observe-don't-narrate
- **Natal = standing structure** (delineate freely). **Timing** (transit/progression/direction/
  return) answers *when*. Never let natal "show" a dated event or transient situation.
- Forward windows are **observed, not pre-narrated**. Fix the structure, watch the window, verify —
  do not fit the chart to a foretold story.

## Coverage (completeness) — the chart walked in full
A chart is read **in full** when **every factor present in the data has an explicit disposition** —
none dropped silently. Three dispositions: **load-bearing** (folded into the reading) · **quiet**
(present but low-salience — marked, not deleted) · **out-of-scope** (excluded by a scope decision:
minor aspects, lots, stars). **Walk all, write the salient, mark the quiet** — the walk is exhaustive,
the prose selective, the gap explicit. Factor set is **bounded** (cardinality of data, not the
product — else anti-pattern #4): objects + states (sign · house · dignity · sect · retro · decl/OOB),
aspects (**from the list, not memory**), configurations, derived (chart ruler · sect light ·
dispositor sinks · balances), and **per technique the same walk again** + cross-links to natal.
- **Balloon (#4) = a sin of PROSE, not registry size.** Dropping real factors from the *walk* to stay
  short breaks completeness (silent cherry-pick); the guard governs the *text*, not the опись. Test:
  does the factor flood prose, or just sit in the registry for analysis? Latter → keep it тихий.
- **Continuous layers = two sub-layers, not a filter.** Hundreds of real transit passes/year: split by
  speed (slow carriers = themes, judged; fast triggers = daters, **auto-quiet**, promoted to несущий
  only by corroboration — charged point / chain link). Keeps chains + atypical couplings walkable; prose
  stays clean. Never pre-pick "only fast ones on a charged point" — atypical surfaces from the walk.
  Continuous-layer completeness is **scope-relative** (orb·bodies·range) — declare scope in the summary.

- **Salience is dynamic — set by corroboration**, not by a factor in isolation. Disposition is **not
  write-once**: each new instrument may raise / lower / re-open it. One **shared living ledger** over
  the whole knowledge mass; techniques are **passes** that read+write it, **not silos** (isolation is
  how the solar-return stellium got lost).
- **Two narrowings, only one legitimate:** *which arena* collapses legitimately (confirmation of
  absence — quiet houses drop); *which pole inside a live arena* does **not** self-collapse in a
  forecast — both poles live until a **basis** (cross-instrument corroboration or biographical
  observation, never "nice") licenses it. Unwarranted pole-collapse = cherry-pick (#14).
- **Done = ledger stabilized**, not "every box ticked once" and not "nothing left to investigate" —
  a fresh pass no longer shifts ranks **significantly** (fixpoint by budget).
- **Artifact — keyed-contract coverage ledger, three files** (`build_coverage_ledger.ps1`), shared key
  `factor_id` = the script↔model seam: **`coverage_factors.csv`** (machine, regenerated freely) ·
  **`coverage_dispositions.csv`** (semantic, model-owned — script **appends new keys only, never rewrites**,
  so hand edits survive regen) · **`coverage_report.md`** (verifier: JOIN + checks + tallies). Aspect keys
  are **directed — endpoints never sorted** (cross-frame sr2n/transit/prog2n/dir2n carry direction;
  sorting = anti-pattern #5). Three structural checks: **completeness** (every factor → non-blank salience)
  · **basis integrity** (every cited `factor_id` exists — anti-**fabricated**-basis, NOT anti-cherry-pick:
  selective demotion stays the model's burden) · **pole⇒basis** (`valence_resolved` ⇒ `basis` non-empty).
  Quiet & excluded kept **visible**; a blank disposition = a silent hole, fix before ship.

## Version log (visible branch-discarding)
Coverage audits *factors*; the fan-collapse to a pole happens **inside** a factor and is silently
fluency-driven (the convenient pole surfaces, the real alternatives often don't) — #2/#14 at the **branch**
level, which the ledger's structural checks can't see. So a collapsed fan **logs each genuinely-afforded
pole**: `taken` · `parked` (left **live**, legitimate) · `dropped` (**basis required**). Read the fan
**from the operator tables, not fluency** (ties to gate 1). Artifact: **`coverage_versions.csv`** — 4th
keyed-contract file, **model-owned, append-only** (script only seeds the header). Gate-3 checks:
`valence_resolved=yes` ⇒ a version is logged · `dropped` ⇒ basis non-empty · version-basis integrity ·
orphans. Honest ceiling: cannot catch a pole that **never surfaced** — paired with the reproducibility gate.

## Sphere × lens reading (year forecast)
The year reading composes on **two axes**: *spheres* (life-domains = houses folded into recognizable
areas) × *lenses* (instruments). Synthesize down each sphere column; **the solar return is the assembly
frame** (no new plumbing — the year layer already leads with the SR).
- **Lens roles:** natal = baseline (what the area *is*) · profection = year's spotlight (profected house
  **+ its lord's placement** → links 2–3 spheres = the year's rhymes) · solar return = charge
  distribution across spheres + nodes (SR→natal hard aspects) · progressions = slow sign-change shift ·
  solar-arc = point perfection (dated node) · transit windows = timing (*when* the node fires).
- **Sparse, weighted matrix** — a lens speaks to a sphere only where it lights it; filling all cells =
  Barnum (domain-projection of #4/#14).
- **Per-sphere checklist (domain-axis completeness):** baseline → year-charge → slow-shift →
  **tension-node** → **what's-on-offer**. Second cut of the same mass: the ledger cuts by *factor*, this
  by *area*; the domain cut is the **model's burden** (no tooling).
- **Sphere membership = disposition, not a machine factor** (many-to-many, interpretive) — model-side,
  never a `coverage_factors.csv` tag.
- **Axis separation (no double-coverage):** windows own time+astrology (when, transit, dates); spheres
  own the domain (area · node · on-offer) — **no dates, no planet names** in sphere prose. Test: strip
  planet names — if it still works, it's a real sphere sentence.
- **Delivery bar = named pressure + open outcome** (concrete node, probabilistic, never foreclosing).
  Not vague "domain-meaning", not event-prediction.
- **Count = checklist, not quota:** keep the 7 backstage for completeness; **present by the chart** —
  lead with lit, **merge rhyming spheres into themes**, quiet ones a line. Themes presented follow the
  chart (3–5), not the grid.
- Full process: `semantic-base.md` § "Чтение по сферам".

## Acceptance check (three independent gates)
1. **Reproducible:** the reading can be **re-derived from the doc alone** (operators + tables in
   `semantic-base.md`). Where it can't, a gap was silently filled from memory — fix the operator/table.
2. **Complete:** the coverage ledger is **closed** — every factor has a non-blank disposition, quiet
   marked quiet (not dropped), ranks stabilized. A blank = silent skip; fix before ship.
3. **Versions visible:** a collapsed pole shows its branch work in the version log
   (`taken`/`parked`/`dropped`+basis); no silent collapse. (See Version log.)
   Gate 1 catches "filled from memory"; gate 2 catches "skipped / cherry-picked a **factor**"; gate 3
   catches "silently collapsed a **branch** inside a factor".

## Pointers (canonical sources — read these, don't restate them)
- `docs/semantic-base.md` — **full** roles / operators / non-commutativity / value tables / anti-patterns / ritual / acceptance check.
- `docs/methodology-roadmap.md` — instrument queue + level notes (what's built, what's deferred).
- `docs/solar-return-reading-recipe.md` — worked reading procedure with the strength + dignity + declination layers.
- NKS realm `astrolab`, holon #30 (interpretation discipline) + nodes #39 non-commutativity, #40 anti-patterns, #41 operators, #42 sect, #43 profection — the structural map.
- Computation lives in `artifacts/mcp-recipes/*.ps1` (via `provider-orchestrator` / `chart-data-preparator`) — not here.
