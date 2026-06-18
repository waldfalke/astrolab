# TaskLog — What the harness is, and where its top half is still open

- **Date:** 2026-06-18
- **Cynefin:** Complex (the activity being served — chart reading — is emergent; this is an
  architecture *decision record*, not an implementation run).
- **Status:** DESIGN / decision record. No code shipped this session; captures the architecture
  as-derived-from-repo plus the design conclusions to act on next.

## Why this log
A long working session kept colliding with one question: *what are we, architecturally, and where
does the LLM legitimately sit?* The answer matters because the same confusion produced a bad reflex
(see "The reflex error" below). Pinning it so the next agent doesn't re-derive it from scratch.

## What we are (derived from the repo, not memory)
Not an MCP-app, not a single fat skill, not a multi-agent workflow. We are a **recipe-centric
provenance harness with a contract + canon layer, driven by ONE orchestrating agent through skills.**

Layer stack (centre of gravity is at the bottom; the LLM is a thin top layer):

```
[ Orchestrating agent ]  one LLM. NOT multi-agent. Reads AGENTS.md→docs, pulls recipes/skills,
        │ invokes        does the irreducibly-semantic read.
[ Skills ] .agents/skills/* (10) → mirrored to .claude/.codex/.qwen via sync-skills.ps1
        │ call           thin entry points (spec + script), most still "spec-first", NOT agents.
[ Recipes + renderers ]  artifacts/mcp-recipes/*.ps1 (~25) + artifacts/renderer/*.py
        │ wrap           ★ THE HARNESS. determinism, swiss→ephem failover, retry, QC, raw JSON,
        ▼                hashes/provenance. No LLM in the loop.
[ MCP providers ]        .mcp.json: swissremote(:8000 local Docker, primary), ephem(backup),
                         vedastro(probe). Native mcp__ tools are PROBE-ONLY, never production.

  cross-cutting:
[ Contracts + data ]  charts/<id>/ (methods/outputs/packs + provenance), coverage_*.csv keyed
                      contract, schema/provenance validation, the twin/datasheet format.
[ Method canon ]      docs/ (semantic-base, chart-datasheet, report-standards, prose-style);
                      REGISTRIES.md / AGENTS_INDEX.md; NKS realm `astrolab` (concept graph).
```

## The core insight: interpretation is emergent, not scriptable
Chart *computation* was automated in the 1980s — every astro-processor nails positions. Real
*interpretation* was never scripted in 40 years despite a flood of "cookbook" software that emits
garbage. Reason: meaning in a chart is **emergent** — it arises from the configuration as a whole,
not as a sum of factors looked up in a table. It is gestalt recognition over an arbitrarily-complex
system. That is precisely the task only an emergent machine (an LLM) can even attempt.

Therefore the LLM is **not a weak link to be scripted away — it is the organ that does the reading.**
The harness's job is to serve and constrain its *context*, not to replace its *judgement*.

## The reflex error (recorded so it isn't repeated)
Under pressure to make reading trustworthy/reproducible, the default reflex was "push it into a
deterministic script" — including the *interpretation*. Two concrete mistakes:
1. Proposing to feed the interpreter ONLY `coverage_factors.csv` (a flattened factor list). That
   **kills the gestalt** — an emergent reader needs the whole chart as a configuration; the factor
   table is for *afterwards* (did the eye see everything?), not as the read's input.
2. Conflating *orchestration* with *scripting*. Orchestration is NOT a pipeline that scripts the
   meaning; it is the arrangement of **emergent reads in relation**.

## Role reset (the corrected division of labour)
- **Scripts / recipes** = substrate only: accurate natal/houses/SR/transits + provenance. Solved,
  uninteresting, deterministic.
- **Emergent reading** = the LLM, working on **whole charts and their relations**, kept whole.
  Method lives in the *relations between* holistic reads: natal-as-whole → deepen with directions /
  profections → solar return ONLY against the natal → transit windows → time-lords. (Each step a
  gestalt act; the craft is the relation — "соотношение, не изоляция", already canon in semantic-base.)
- **Coverage ledger** = demoted to an **eye-checklist** ("was everything in the chart seen?"). It
  guarantees completeness-of-attention, NOT meaning. It does not author the read.

## Trust in an emergent domain (reconciles the contamination thread)
You cannot verify an emergent read against a ground truth — there is none. So trust is NOT bought by
determinizing the read (that destroys it). It is bought by:
1. **Ensemble of independent blind reads** — several passes (different models/seeds), each seeing
   only the chart, none seeing the conversation. Blind convergence = signal; divergence = honest
   spread. This *is* the de-contamination protocol, done by design rather than ad hoc.
2. **Context control** — the skill engineers *what each reader sees* (whole chart + method + frame,
   nothing leaking). Clean input, free read.
3. **Reproducible scaffolding, not reproducible meaning** — inputs and process are pinned and
   re-runnable (which chart, which order, which passes, provenance); the meaning stays emergent.

## Rules storage: NKS authors, a snapshot serves
The method rules are relational, so a **graph** (NKS realm `astrolab`) is the right *authoring* home —
relations, growth, navigation by tension. But the production read must NOT hard-depend on the live
graph:
- it is an external, token-bound, sometimes-down service (it disconnected mid-session — live proof);
- a mutable graph queried at runtime breaks reproducibility;
- docs/ is already the canonical text — a second runtime canon = drift (against REGISTRIES' single-owner rule).

**Shape:** NKS authors+relates → **export a pinned, versioned snapshot** that the skill loads into the
reader's context at read-time. Graph richness + reproducibility + zero live dependency. Stamp the run
with the method version, exactly like the ephemeris: `read by rules@<hash>` alongside `computed by swiss@<hash>`.
→ Live-NKS for whoever *grows* the method; pinned snapshot for whoever (or whatever) *runs* a read.

## Current state — honest
- **Bottom (compute):** solid. Deterministic, swiss+ephem cross-checked to arc-seconds, provenance.
- **Middle (contract + verifier):** built. coverage keyed-contract + twin format + schema/provenance
  validation exist (see 20260615 log).
- **Top (orchestration as an enforced flow):** NOT closed. Still part-prompt — relies on the agent
  "playing along". The gap is the upper half of the loop:
  `compute → coverage(eye-checklist) → WHOLE-CHART emergent read(s), context-controlled → verifier
  gate → report`. Seed already exists: `run_full_workbench.ps1` (natal→house→forecast→synastry→QC→pack).
- Registry debt: `docs/EXTERNAL_CAPABILITIES_MAP.md` stale (names dead theme-astral.me as primary;
  swiss is local Docker now) — logged in REGISTRIES.md.

## Decision / next steps
1. Make the **skill** the home of orchestration: subordinate recipes to it; its spine is the
   relational read-order, not a factor checklist; recipes are pulled on demand by the emergent flow.
2. Build the **ensemble blind-read** harness (N independent context-controlled passes + a
   convergence view) as the trust mechanism — not a determinizer.
3. Wire the **rules snapshot**: export the `astrolab` method-rules to a versioned bundle the skill
   loads; stamp runs with `rules@<hash>`.
4. Keep coverage as the **eye-checklist** gate, explicitly not a meaning source.

## Self-check
- [x] Architecture claims derived from actual repo files (.mcp.json, AGENTS.md, REGISTRIES.md,
      skills glob, recipes), not memory.
- [x] No client identifiers / PII in this log (the chart work that prompted it stays in `.private/`).
- [x] Records the reflex error as a reusable principle, not as narrative.
- [ ] Next: mirror the load-bearing principles into NKS realm `astrolab` (separate step).
