# AGENTS.md

Machine-oriented entrypoint for AI agents working in this repository.

## 0. Read Order (mandatory)

1. `.agents/docs/00-mission.md`
2. `.agents/docs/01-quickstart.md`
3. `.agents/docs/02-workflows.md`
4. `.agents/docs/03-skills-map.md`
5. `.agents/docs/04-troubleshooting.md`
6. `.agents/docs/05-smoke-tests.md`
7. `.agents/docs/06-tasklog-template.md`
8. `.agents/docs/07-fail-fast-rules.md`
9. `.agents/docs/08-known-issues.md`
10. `.agents/docs/09-powershell-style.md`
11. `.agents/docs/10-mcporter-usage.md`
12. `.agents/docs/11-antipatterns.md`
13. `.agents/docs/12-external-capabilities-map.md`
14. `.agents/docs/13-obsidian-vault-workflow.md`
15. `.agents/docs/14-l402-lightning-stack.md`

If a step conflicts with ad-hoc reasoning, follow docs first.

## 1. Canonical Agent Layer

- Canonical skills root: `.agents/skills/`
- Do not author new canonical skills under `.codex/skills` or `.qwen/skills`.
- Private skill `astro-engineering-scanner` is intentionally excluded from canonical tracked set.

### 1a. Architecture (what the harness is)

We are a **recipe-centric provenance harness + contract/canon layer, orchestrated by ONE agent through
skills** — not an MCP-app, not a fat skill, not a multi-agent workflow. Centre of gravity is the
deterministic recipe layer; the LLM is the thin top that does the **emergent** chart read (un-scriptable
— that is the irreducible value, not a liability to script away). Full map + design conclusions:
`TaskLogs/20260618_harness_architecture.md`. In the graph: NKS realm `astrolab`, contour #67 (харнес)
+ transformation #78 (замыкание в харнес, after #55).

## 2. Sync Rules

Use `.agents/scripts/sync-skills.ps1`.

```powershell
# canonical -> codex
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents

# canonical -> codex + qwen
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeQwen

# canonical -> codex + claude (Claude Code mirror; never carries the private scanner)
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeClaude

# codex -> canonical refresh
pwsh .agents/scripts/sync-skills.ps1 -Direction to-agents
```

## 3. Hard Constraints

- Use project recipes from `artifacts/mcp-recipes/` for astrology computations.
- Keep reproducible outputs under `artifacts/results/` and/or `charts/<chart_id>/`.
- Record non-trivial work in `TaskLogs/`.
- Before finalizing: run schema/provenance validation for produced chart projects.

### 3a. Claim discipline (anti-overclaim — rationale: NKS #125)

- Before any *done / passing / verified / fixed* claim — run `verification-before-completion`
  (Superpowers) as an explicit isolated agent. Evidence before assertion; don't claim from optimism.
- Report PROJECT state, not your machine's: clean-checkout / CI result, never an ad-hoc local install.
  (why: a green suite on your box with optional deps installed lies on a fresh clone.)
- *Verified* = you ran it and saw the output. Never "a subagent said". Subagent findings (maps, scans,
  spikes) are unverified until you re-check them against source.
- Golden tests are the only number-oracle. An agreement test that can't run (optional engine absent)
  must FAIL LOUD or warn — never silent skip-green. (why: skip-green hides an unverified claim.)
- Set NKS `pratyakshita`/`pramanita` only with evidence in hand. built≠trustworthy applies to the graph
  itself — a generous mode launders optimism as rigor.
- Where an oracle is buildable, build it (test that screams, CI on clean checkout); where the claim is
  judgemental (coverage, a map, a mode), no gate exists — use an independent adversary, not your word.

### 3b. Execution & skill-invocation discipline (rationale: NKS #125/#126 — same root: bypassing the checking layer)

- Multi-step build → use the Superpowers chain, don't hand-roll a bespoke workflow: `writing-plans`
  (requirements → plan before code) → `subagent-driven-development` / `executing-plans` (independent
  tasks via subagents, review checkpoints) → `verification-before-completion` per checkpoint.
- Run discipline skills (TDD, verification, brainstorming, plans, debugging) as EXPLICIT isolated
  subagents — a FLEET — never inlined as read-and-do instructions. (why: an inlined skill is goodwill,
  skipped under optimism; an isolated subagent makes the discipline actually run — this is the #1
  recurring failure the owner has to flag.)
- To RESCOPE, run `verstak:assembly` over the realm — it produces the bianhua map + the transcendent-will
  agenda (the owner's calls, e.g. #124). Don't hand-roll scope from local focus.

## 4. First Smoke Check

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 -ChartId trump_19460614_105400_jamaica_ny_renderer
pwsh artifacts/mcp-recipes/run_obsidian_mcp_probe.ps1 -VaultRoot D:\Dev\CATMEastrolab\obsidian-vault -ServerName "obsidian"
pwsh artifacts/mcp-recipes/run_obsidian_mcp_e2e.ps1 -VaultRoot D:\Dev\CATMEastrolab\obsidian-vault -ServerName "obsidian"
```

