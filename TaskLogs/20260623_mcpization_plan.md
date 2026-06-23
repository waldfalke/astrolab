# TaskLog — MCPization plan: expose the instrumentarium as headless MCP functions + gap audit

- **Date:** 2026-06-23
- **Cynefin:** Complicated (the inventory is knowable; classification + gap-finding is analysis. The
  transport choice has a Complex edge — a real architecture fork, see Gap 5).
- **Status:** PLAN. Audit done; gaps named; staged plan below. No MCP server built yet.
- **Graph anchor:** hint #109 (headless MCP-exposure) under contour #102, bianhua #112.

## Why this log
Owner asked to plan the MCPization of the built code and find the gaps. This is the concrete work
behind hint #109 — turning recipes into headless functions for agents (aA2A), the forgotten product
half. Recorded so the build doesn't re-derive the classification.

## Key reframe (what MCPization actually is here)
Raw chart math is ALREADY MCP: `swissremote` exposes `calculate_planetary_positions / solar_revolution
/ transits / synastry` natively. So MCPization is NOT re-exposing swiss — it is exposing the
**derived value astrolab adds on top**: failover+QC, secondary progressions, solar-arc, rising-hands,
dignities/sect, carrier-windows, phase (copyright — excluded). The product is the method-added-value,
not the ephemeris.

## Audit — 33 recipes classified for MCPization

**A. Atomic computations → MCP-function candidates (clean input → numbers):**
- `run_natal_snapshot` · `run_house_layer_placidus` · `run_transits_to_natal` · `run_solar_revolution`
  · `run_secondary_progressions` · `run_solar_arc` · `run_synastry_matrix` · `run_forecast_delta`
  · `run_natal_with_failover` · `run_cross_provider_qc` · `run_rising_hands` (data-only hands)
- These take typed params (Lat/Lon/DateTimeUtc/…) → emit numbers. Closest to a function contract.

**B. Orchestrators → NOT MCP-functions (multi-step, twin-gate, emergent prose):**
- `run_solar_gift` · `run_transit_day` · `run_mundane_day` (twin-gated, need the LLM organ) ·
  `run_full_workbench` · `build_chart_project` · `build_coverage_ledger` · `run_sphere_ledger` ·
  `run_assemble_report`. These are agent-orchestrated; exposing them as one function would hide the
  gate. (A *higher-level* "compute a full chart project" function is possible later, but it returns
  data, never prose.)

**C. Infra / management → not astro-functions (out of MCP-product scope):**
- `check_chart_provenance` · `validate_chart_project` · `archive_runs` · `build_pack_manifest` ·
  `check_artifact_conformance` · `run_renderer` (SVG visual) · `run_obsidian_*` · `run_canvas_*` ·
  `run_*_probe` / `_e2e`.

**D. Copyright / working-layer → MUST NOT be exposed publicly:**
- `run_phase_vectors` (Zakharian phase — working layer, copyright). Excluded from any public surface.

## Gaps (what blocks MCPization)

| # | Gap | Scope | Severity |
|---|-----|-------|----------|
| G1 | **Output = files, not return value.** Every recipe writes `artifacts/results/<…>/*.csv+json`; an MCP function must RETURN typed JSON. | all of A | blocking |
| G2 | **No typed input schema.** PowerShell `param()` blocks exist but no JSON `inputSchema` (MCP requires it). | all of A | blocking |
| G3 | **Stateful by design.** Recipes persist by caseId+timestamp; an MCP function should be stateless (input→output, no side-files). Need a compute-only / no-persist mode. | all of A | blocking |
| G4 | **Transport mismatch: PowerShell scripts ≠ MCP server.** Recipes run via `pwsh`; MCP needs a stdio/http server process. Either (a) a thin server that shells recipes in no-persist mode, or (b) extract the compute core into the server. **This is the real architecture fork.** | systemic | blocking |
| G5 | **Provider is local.** `swissremote` = local Docker `:8000`, not public. Remote/agent access needs a hosted swiss (or bundled ephemeris). | infra | blocks remote |
| G6 | **No exportable/working-layer marking.** Nothing in the recipes flags copyright (phase) vs free-to-expose. Need an allow-list at the server boundary. | D | blocking for public |
| G7 | **README stale.** `artifacts/mcp-recipes/README.md` still names dead providers (theme-astral.me); `.mcp.json` has the live set (swissremote/ephem/vedastro). Doc drift. | doc | minor |
| G8 | **No billing hooks.** L402 monetization (hint #111) not started; depends on G4 first. | product | deferred |

## Plan — staged (anantara order)

**Stage 0 — Language/transport decision (resolves G4+G5). DECIDED: rewrite compute cores in Python.**
A PowerShell-shim (a) only lacquers slow `pwsh` and keeps the swissremote dependency. Instead rewrite
the atomic-function compute cores in **Python + `pyswisseph`** (Swiss Ephemeris in-process → kills the
external-provider dependency, resolves G5) served via **FastMCP** (typed `inputSchema` from annotations
→ resolves G2). NOT all at once — one function at a time; the PowerShell recipe stays the **golden
reference** (Python output == PS output on a fixture). Orchestrators (twin-gate) are NOT exposed.
`phase_vectors` is copyright — excluded.

**Stage 1 — First function in Python (resolves G1+G3 by construction).** A Python function returns
typed JSON and persists nothing — stateless by default, no `-EmitJson/-NoPersist` retrofit needed.
Pick `run_rising_hands` — atomic, clean input (place+moment), not copyright, our freshest product, no
natal PII.

**Stage 2 — First function surface + golden test (resolves G2).** Expose it as MCP tool
`astro.rising_hands(date, lat, lon, tz)` via FastMCP; add the golden test (Python == PowerShell recipe
on a fixture). Prove an agent can call it and get numbers. MVP of the headless product + the bottom
test layer in one slice.

**Stage 3 — Widen the surface.** Add the rest of class A behind the same shim + allow-list (G6 excludes
phase). Order by derived-value: rising-hands → transits-to-natal → solar-revolution → progressions →
solar-arc → dignities/sect. Skip anything swiss already exposes raw unless we add value.

**Stage 4 — Remote host (resolves G5).** Public swiss host (or ephemeris bundle) so agents reach it
off-box. This is where "headless" becomes truly remote, not just local-stdio.

**Stage 5 — L402 billing (hint #111, G8).** Lightning pay-per-call gate over the hosted surface; bridge
the l402-proof-of-vision subproject (billing proven on dummy-API) to the real astro functions.

**Quick win, independent:** fix G7 (README dead providers) now — 5 minutes, removes a live lie.

## First concrete target
`run_rising_hands` → `-EmitJson -NoPersist` → MCP tool `astro.rising_hands(date, lat, lon, tz)` →
returns watches/objects/moon-hand as JSON. Atomic, no PII, no copyright, our own product. Proves
Stage 0–2 in one vertical slice.

## Done Definition
- [x] 33 recipes audited + classified (A/B/C/D).
- [x] 8 gaps named with scope + severity.
- [x] Staged plan with anantara order + first concrete target.
- [ ] Plan reflected in graph under hint #109 (when NKS server is back — it dropped mid-session).
- [ ] Stage 0 transport decision made with the owner (the one real fork).

## Self-Check
- Did I propose duplicating swiss? No — MCPize derived value only (the reframe).
- Did I expose copyright? No — phase (D) excluded, G6 allow-list named.
- Did I hide the twin-gate? No — orchestrators (B) explicitly NOT exposed as functions.
- Is the first target atomic + PII-free + ours? Yes — rising_hands.
