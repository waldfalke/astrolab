# TaskLog — NKS capability audit + weaving the unused baggage into hooks & process

- **Date:** 2026-06-23
- **Cynefin:** Complicated (the capabilities are knowable and the gaps are diagnosable by the graph's
  own detectors — this is analysis + organizing, not emergent discovery). The *process-design* part
  (which rituals belong in hooks vs skills vs `/save`) carries a Complex edge — trade-offs, not one
  right answer.
- **Status:** DONE (core). Reconnaissance + inventory + weaving acts + crystallization + process-weave
  all shipped this session. Standing backlog (11 grundsatz + 2 vollzug) consciously left for a focused
  design pass — see Outcome.

## Why this log
We have used NKS mostly as "read overview + write nodes". The system has whole layers we never
touched, and — more importantly — the graph has been silently accumulating **17 standing tensions**
(14 weave · 3 address) that no session ever swept. The point of this log: (1) inventory the unused
capability so it stops being invisible, (2) triage the standing tensions, (3) wire a *recurring*
tension-sweep + crystallization ritual into the hooks/process so the graph doesn't drift again.

## The unused baggage (inventory)

**`nks_orient` lenses we never ran** (we almost always took the no-lens overview):
- `lens="tensions"` — 21-detector structural health. *Never swept.* → see findings below.
- `lens="bianhua"` — the forest of transformations (形), the owner-facing map. *Never read as a map.*
- `lens="trace"` — walk a phenomenon's estafeta (birth→use→consume) to see if a lifecycle closes.
- `lens="topology"` — structural net around a node.
- `lens="path"` — path between two nodes (e.g. how #93 clock connects to #67 harness).
- `lens="vimarshas"` — the grouped field of open inquiry.

**Tools we never used:**
- `nks_history` — node history + `revert`/`invert` (the graph's time machine).
- `nks_semantic_search` — embedding search (we leaned on keyword `nks_search`, which misses
  differently-phrased duplicates).

**Skills we never invoked:**
- `weaving` — repairs existing structure: close lifecycle, write sense on arrows, split two-actor
  kriyas. *Directly answers the 14 weave tensions.*
- `integrity` — propagate a new bianhua's telos through the graph, mark the "затронуто ли?" wavefront.
- `inquiry` — per-genre vimarsha resolution (resolution / death / crystallization).
- `methodology-work` — evolving the `methodology` realm itself (meta, highest stakes).

**Concepts we never exercised:**
- **Crystallization** (vimarsha → `bildung` phenomenon): a session should leave *understandings*,
  not only new questions. We have spawned questions; we have never crystallized one.
- **Vimarsha genres** beyond `samshaya`/`hint`/`prati-paksha`: `vyabhichara` (counterexample),
  `hetu-dosha` (reasoning error), `semantic-drift`.
- **`anantara` ordering** of bianhua — the critical path "B possible only after A".

## Reconnaissance findings (2026-06-23)

### Tensions — astrolab: 14 weave · 3 address
**WEAVE (close structure):**
- `relay-gap` ×1 — `⚙️ SR-карта (Краснодар, истинный момент) (#3)`: has ahara, no utpatti. Likely a
  **realm inlet** (the chart comes from a swiss computation *outside* the realm) → probably sanctioned
  boundary, not a real gap. Verify with `lens="trace"` on the consuming kriya.
- `dead-recipe-vollzug` ×2 — methods without `upadhi`: `#92` (transit-event fan→corroboration),
  `#90` (transit "day" reading). A method exists by being *applied* → link `upadhi` from the kriya
  that uses it. These are our own recently-built methods → real, closeable.
- `declarative-grundsatz` ×11 — principles without `upadhi`: `#62 #63 #64 #66 #68 #69 #70 #71 #85 #86`
  +1. A principle exists by *constraining* a kriya. **Open question:** are these genuinely unapplied,
  or is "a reading principle with no single owning kriya" a sanctioned state the detector over-flags?
  This is the Complex edge — decide per-principle, don't blanket-link.

**ADDRESS (answer/close inquiry):**
- `unanchored` vimarshas ×3 — no `vimarsha_of` (the inquiry isn't attached to what it's about):
  - `#65` ❓ how phases apply to transits & aspect cycles
  - `#83` 🔍 semantic QC-verifier (cheap model checks the reading)
  - `#84` 🌗 breathing forecast frame — swings along the event arc (the zones/tail theme from this
    session's work). **Cleanest fix:** anchor each to the node it's about.

### Bianhua — astrolab: 4 transformations
- `#26` committed — phase method gains solar-return reading (0/6✓)
- `#55` ready — reading becomes complete & self-checking (1/6✓)
- `#96` ready — rising-sign clock: general elections → conjunction with natal (0/5✓) ← **our product**
- `#78` blocked after #55 — reading machine closes into a harness (0/4✓)
Note: the rising-clock work this session (mundane standard + `run_mundane_day`) advances `#96` but
none of its 5 driving vimarshas were marked ✓ — the map is stale vs the work. Candidate for a
crystallization + progress update.

## Plan

1. **Triage & weave the real tensions** (use `weaving` skill):
   - Anchor the 3 unanchored vimarshas (`#65 #83 #84`) via `vimarsha_of`.
   - Link `upadhi` for the 2 dead-recipe methods (`#90 #92`) from their applying kriyas.
   - Per-principle decide the 11 grundsatz: link `upadhi` where a real owning kriya exists; leave
     (consciously, documented) where "ambient principle" is the honest state.
   - Confirm `#3` is a sanctioned inlet (trace) — leave if so.
2. **Crystallize** the rising-clock understanding onto `#96` (mundane product is now a standing
   capability) and update its driving-vimarsha progress.
3. **Weave the rituals into hooks & process** so this never silts up again:
   - `SessionStart` hook → already orients; add a one-line "end-session: sweep `lens=tensions`,
     weave new gaps, crystallize one bildung".
   - `PostToolUse`/git-push hook → already reminds to update NKS; extend to "run `lens=tensions`,
     close what this push opened".
   - `/save` skill (CURRENT_WORK persistence) → add a tension-sweep + crystallization step so
     end-of-session always leaves the graph swept.
   - `/load` → surface `lens=bianhua` (the map) and standing tensions, not just CURRENT_WORK.

## Outcome (2026-06-23)

**Used the unused lenses/skills (not just listed them):**
- Ran `lens="tensions"` (first sweep ever) and `lens="bianhua"` (read the forest) — found the 17
  standing tensions and the stalled `#96`.
- Wove via `nks_arrow` (weaving-style repair): anchored the 3 unanchored vimarshas with `vimarsha_of`
  — `#65→#5` (phase operator), `#83→#30` (discipline contour), `#84→#1` (solar-reading contour).
  ADDRESS tensions **3 → 0**.
- Crystallized the rising-clock Stage-1 understanding as `bildung` phenomenon **#101** (`arose_from`
  #91/#97, `context` #93) — the session leaves an understanding, not only questions (#435).

**Consciously LEFT (tensions are truthful — not zeroed with fake arrows):**
- `relay-gap #3` (SR-карта) — sanctioned realm **inlet** (chart comes from swiss outside the realm).
- `dead-recipe-vollzug` ×2 (#90 #92) + `declarative-grundsatz` ×11 — these need an `upadhi` from an
  **applying kriya that exists as a node**; in a concept-realm the application often lives in
  recipes/skills (files, not nodes), so linking = *creating a kriya* = a design pass, not a light-fix.
  Per-principle decision (pitfall #85: don't blanket-link). Deferred to a focused `design`/`weaving`
  session — and the new sweep ritual will keep surfacing them.

**Process-weave (the durable deliverable):**
- `/save` → new Step 6 "NKS sweep": tensions sweep + weave own gaps + crystallize ≥1 bildung +
  update bianhua progress. End-of-session graph ritual (時-cycle 忠).
- `/load` → new Step 2 "Read the NKS map": orient + `lens=bianhua` + `lens=tensions`, not just WIP.
- `PostToolUse`/git-push hook → reminder extended from "update NKS" to "sweep tensions + crystallize
  + update bianhua progress".
- `SessionStart` hook (from prior verstakify) already orients — left as is.

## Done Definition
- [x] Inventory recorded.
- [x] 17 standing tensions triaged: 3 closed (anchors), 14 consciously left with reasons (above).
- [x] Rising-clock capability crystallized onto the graph (#101); `#96` understanding recorded.
- [x] Hook + `/save` + `/load` changes applied so tension-sweep + crystallization is routine.
- [x] No client PII entered the graph (only file/recipe references + computation context, never biography).

## Self-Check
- Am I *using* the unused lenses/skills, or just listing them? (The weave/crystallize acts must
  actually run `weaving`/`inquiry`, not be described.)
- Did I blanket-link the 11 grundsatz (automation of discrimination, pitfall #85) or decide
  per-principle? Per-principle is mandatory.
- Did the session leave an *understanding* (bildung), not only new questions? (#435.)
- Hooks: do the new reminders change what the next agent *does*, or are they decoration?
