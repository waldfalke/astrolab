# TaskLog — Composites MCPization: full feature map + plan

- **Date:** 2026-06-24
- **Cynefin:** Complicated (the composites already exist as recipes — this is wrapping + classification,
  knowable; the per-composite trust/PII/copyright calls have a judgement edge).
- **Status:** FEATURE MAP + PLAN. Studied first (Explore over recipes+docs), recorded whole before
  decomposing. NO code yet. Next: decompose into NKS subtasks, then build via explicit Superpowers subagents.
- **Graph anchor:** contour #102 (instrumentarium), bianhua #112; element/composite/scenario from #116–123.

## Why this log
Owner's process: study what exists → record the WHOLE feature → decompose subtasks (with NKS) → build via
explicit Superpowers runs. NOT grab-a-piece-and-code. This log is the "study + whole feature" step.

## Key finding (reframe)
**All 13 composites already exist as PowerShell recipes.** So the feature is NOT "build natal from scratch"
— it is **expose existing recipe-composites as headless MCP functions**, the same conveyor proven on
`rising_hands`: golden (from the recipe) → Python → FastMCP tool. The math is built and verified; we are
re-surfacing produced value, not re-deriving astrology.

**HONEST CORRECTION (owner caught this):** "wrapping, not re-deriving" was wrong. `rising_hands.py` was a
**PORT** — the watch-scan logic was rewritten in Python, not wrapped. For 13 composites that multiplies.
This is the unresolved **port-vs-shell-out fork (G4)** I failed to carry over — see the section below.
Do NOT start porting natal on autopilot; the fork is decided consciously (like the engine fork #113),
not assumed.

## The three levels (element → composite → scenario)
- **ELEMENT** (indivisible compute): `compute_asc` (done), planet longitude, house cusp, aspect, dignity.
  Engine-agnostic seam #115 already covers ASC; other elements need the same seam treatment.
- **COMPOSITE** (assembly of elements into a chart structure): the 13 below.
- **SCENARIO** (how a consumer chains composites): natal → transits-to-it → forecast (CJM, hint #120).

## The 13 composites (from the study — recipe-backed)

| # | Composite | Assembles from | Produces | Recipe | Doc | Status |
|---|-----------|----------------|----------|--------|-----|--------|
| 1 | **Натал** | 10 planets+nodes+lilith+PoF+Chiron longitudes · Placidus cusps · angles · dignities · aspects · sect · Mercury orientality | chart.yaml + methods/natal_failover + houses + chart_points (CSV/JSON) | run_natal_with_failover + run_house_layer_placidus | semantic-base, chart-datasheet | ✅ full code |
| 2 | **Соляр (SR)** | natal Sun → true-instant bisection + relocation · 10 bodies@instant · cusps · SR↔SR/SR↔natal aspects · dignities · profection | methods/solar_revolution + 13_annual_profection + RETURN_INSTANT_UTC | run_solar_revolution (in run_solar_gift) | solar-return-reading-recipe.md | ✅ full code+doc |
| 3 | **Синастрия** | chart A × chart B longitudes → major aspects + direction | inter-chart aspect matrix CSV | run_synastry_matrix | datasheet (partial) | ✅ code, ⚠️ reading recipe partial |
| 4 | **Прогрессии** | natal + days→years → progressed bodies + cusps + progressed→natal aspects | methods/secondary_progressions | run_secondary_progressions | overlay on SR (no standalone) | ✅ code |
| 5 | **Дирекции (solar arc)** | natal Sun arc → all bodies/angles shifted → directed→natal aspects | methods/solar_arc | run_solar_arc | roadmap (priority, reading=TODO) | ✅ code, ⚠️ reading recipe TODO |
| 6 | **Транзиты↔натал** | transit bodies (range/snapshot) × natal → aspects + carrier windows (tail/core/horizon) | transit timeline CSV + carrier_windows | run_transits_to_natal | transit-day-reading | ✅ full code |
| 7 | **Часы восходящего** | date+loc grid → ASC/MC/Moon per step → 12 watches + rulers + phase | 03_watches + grid (+natal: cross/moon/coincidence) | run_rising_hands (+Python port astro/) | rising-sign-clock-spec | ✅ code (data); **element layer MCP-started** |
| 8 | **Транзит-день↔натал** | natal + day + observer loc → transits-to-natal + rising-hands → TWIN-gate → prose → PDF | _model_input pack + PDF | run_transit_day (orchestrator+gate) | transit-day-reading, NKS #90 | ✅ code (twin-gated) |
| 9 | **Mundane-день** | date+loc → rising-hands general → 12 watches + spheres + VoC → TWIN-gate → PDF | mday_* pack + PDF | run_mundane_day | rising-sign-clock-spec | ✅ code (twin-gated) |
| 10 | **Фаза-слой** | object × (Z sign / H house) × scales → Φ operator → P⟨Z.z:H.h:D⟩ | phase_vectors CSV | run_phase_vectors (self-test 144/144) | semantic-base, roadmap | ✅ code+self-test; **COPYRIGHT — NOT exposed** |
| 11 | **Профекция года** | natal ASC sign + age → profected sign + ruler | 13_annual_profection CSV | helper in run_solar_revolution | roadmap §2 | ✅ code |
| 12 | **Покрытие/полнота** | all factors (natal+SR+transit) → factor_id contract → coverage ledger | coverage_factors/dispositions/versions/report | build_coverage_ledger | semantic-base §Полнота | ✅ code (gate) |
| 13 | **Скоростные окна** | full timeline → slow/fast split → windows (tail/core/horizon) | carrier_windows CSV | in run_solar_gift flow | semantic-base, README §5 | ✅ code |

**chart-project contract** (the natal-structure form): `charts/<id>/` → chart.yaml + INDEX.yaml (provenance)
+ methods/ + outputs/ + packs/. This IS the normalized composite structure for #118.

## Constraints (carry into every subtask)
- **Reframe holds:** MCPize PRODUCED value (composites/derived), not raw swiss positions (already MCP).
- **Copyright (LIFTED 2026-06-24):** фаза-слой (#10) — копирайт-запрет СНЯТ владельцем; свободна к экспозиции/продукту/монетизации. Эпистемика (z/h/D anumita) остаётся — качество знания, не запрет. Graph #50 retired (visarjana).
- **PII:** golden ONLY on the public Trump fixture (`charts/trump_19460614_105400_jamaica_ny`); client
  sets (CLIENTS.yaml) stay in `.private`, never in golden/git/graph.
- **Engine-agnosticism (#115):** every element-compute goes through the seam; B1 default, A optional.
- **Output contract (G1/G3):** MCP function RETURNS typed JSON, stateless — recipes currently write files;
  the wrap must emit return-value, not persist (or a no-persist mode).
- **Orchestrators with TWIN-gate (#8/#9) are NOT plain functions** — they need the gate + emergent prose;
  expose their DATA composite (the chart structure), never the gated prose, as a function.

## Open fork I missed: PORT vs SHELL-OUT (G4 — the real one for composites)
How does a recipe's logic reach Python? Two answers, decided consciously per-class (not assumed):

- **PORT** — rewrite the recipe's derived-logic in Python (what `rising_hands.py` actually did).
  - Ephemeris ELEMENTS (positions/houses/aspects/SR/synastry) are NOT ported — taken from the engine
    (#115: swiss-mcp B1 / pyswisseph A). Only the DERIVED layer is ported: dignities, sect, profection,
    SR-instant bisection, solar-arc, carrier-windows, phase(excluded). Plus the assembly.
  - Cost: logic DUPLICATED (PS1 stays source-of-truth → two codebases drift; golden catches NUMBERS but
    not logic divergence). Benefit: clean typed JSON, no pwsh at runtime, stateless by construction.
- **SHELL-OUT** — FastMCP server invokes the pwsh recipe in a no-persist/emit-json mode, parses output.
  - Cost: pwsh in the product's RUNTIME (deploy weight on the hosted node, G5), file-output parsing,
    weaker typing. Benefit: ONE source of truth (PS1), zero logic duplication, least re-derivation.
- **Likely answer: split by composite complexity** — port the thin/atomic (rising_hands done; dignities,
  profection are small) where duplication is cheap; shell-out the heavy multi-layer ones (natal, SR,
  solar-gift) where re-porting is large and drift-prone. But MEASURE before fixing (like #113): try one
  natal slice both ways, compare effort + deploy weight + drift surface, then decide. This fork is a
  samshaya to record in the graph, NOT a decision to make blind.

## Plan shape (NOT yet decomposed — that's the next step, in NKS)
1. **Decompose into NKS subtasks** (next): per composite, a node/hint under #102 — element-deps, golden
   source (recipe + Trump), output contract, copyright/PII flag, engine note. Order by value.
2. **Build via explicit Superpowers subagents** (after decomposition): per subtask, golden RED → wrap/port
   behind seam → FastMCP tool → verify GREEN myself. One composite at a time.
3. Likely first composites: **натал** (#1 — ядро, full recipe, Trump golden) and the **часы element layer**
   already in progress. Phase (#10) excluded. Orchestrators (#8/#9) expose data-composite only.

## Done Definition (this log)
- [x] Studied existing composites (Explore over recipes+docs) — 13 mapped with status.
- [x] Whole feature recorded (this map), not a piece.
- [ ] Decomposed into NKS subtasks (next step).
- [ ] Built per-subtask via explicit Superpowers runs (after decomposition).

## Self-Check
- Did I record the WHOLE feature before coding? Yes — 13 composites mapped.
- Did I grab a piece to build? No — this is study+map; build comes after NKS decomposition.
- PII/copyright carried? Yes — Trump-only golden, phase excluded.
- Reframe honored? Yes — wrap existing produced-value composites, not duplicate swiss.
