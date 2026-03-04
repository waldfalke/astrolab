# Skills Review - 2026-03-04

## Snapshot

Current visible skill set in `.codex/skills`:

- artifact-builder
- chart-analyst
- chart-data-preparator
- knowledge-ingestion
- obsidian-export
- provider-orchestrator
- renderer
- run-planner
- schema-validator
- astro-engineering-scanner (private; excluded from public)

Execution reality:

- Runnable scripts exist only in `schema-validator` and `obsidian-export`.
- The other skills are currently prompt-specs (`SKILL.md` + references/evals), not executable modules.

## Critical-Think Output

**ПервичнаяГипотеза (confidence: 0.83):**
For project value, keep all skill specs, but prioritize production hardening of 4 orchestration-critical skills:

1. `run-planner`
2. `provider-orchestrator`
3. `artifact-builder`
4. `chart-data-preparator`

Reasoning:

- They form the backbone from input -> provider execution -> artifact normalization.
- Product-level skills (`renderer`, `obsidian-export`, `chart-analyst`) should consume a stable backbone, not replace it.
- Current backlog already matches this dependency direction (ASTRO-008/011/012 then product modules).

**АльтернативныеИнтерпретации:**

1. Product-first approach
   Focus on `renderer + obsidian-export + chart-analyst` for faster demo impact.
   Tradeoff: fragile integration, duplicated logic, higher rework.

2. Minimal-core approach
   Build only `run-planner + schema-validator`, postpone the rest.
   Tradeoff: too narrow; does not solve provider failover and artifact build quality.

3. Full parallel build
   Try to harden all 9 skills simultaneously.
   Tradeoff: context switching overhead, weak test depth per skill.

**МетаРефлексия:**

- We moved from "how many skills do we have" to "which ones create stable throughput".
- Main risk in my hypothesis: underestimating stakeholder need for visual output quickly.

**Усиление Противоречий:**

If immediate user value is measured by visible deliverables, product-first may outperform backbone-first in the short term. A generated wheel/notes demo can unlock feedback and funding even with imperfect internals.

What would change my recommendation:

- If next 1-2 weeks goal is external demo, switch priority to `renderer + chart-analyst` hardening.
- If goal is repeatable operations and scale, keep backbone-first order.

## Recommended Skill Roadmap

### Wave A (must-run core)

- `run-planner`: implement executable planner (`scripts/plan_run.py`) that resolves method DAG and emits run plan.
- `provider-orchestrator`: add executable failover runner (`scripts/execute_with_failover.ps1|py`) and provider profile validation.
- `artifact-builder`: add pack assembler script with manifest and checksums.
- `chart-data-preparator`: add input normalization script (birth/location/timezone validation).

Exit criteria for each skill:

- Has runnable script
- Has one smoke command
- Has one deterministic sample output
- Has one failure-case test

### Wave B (product surfaces)

- `renderer`: generate deterministic SVG from normalized chart outputs.
- `chart-analyst`: deterministic object-by-object scan output (no synthesis by default).
- `obsidian-export`: keep as adapter over validated normalized outputs (already partly hardened).

### Wave C (knowledge and enrichment)

- `knowledge-ingestion`: term extraction + glossary diff + report
- `schema-validator`: promote from utility to mandatory gate in delivery flow

## Immediate Actions

1. Add `scripts/` implementation skeletons for Wave A skills.
2. Create one `docs/SKILL_SMOKE_TESTS.md` with copy-paste commands for all runnable skills.
3. Wire a single orchestrated smoke pipeline: `prepare -> validate -> run-plan -> artifact-build -> obsidian-export`.
