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

## 4. First Smoke Check

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 -ChartId trump_19460614_105400_jamaica_ny_renderer
pwsh artifacts/mcp-recipes/run_obsidian_mcp_probe.ps1 -VaultRoot D:\Dev\CATMEastrolab\obsidian-vault -ServerName "obsidian"
pwsh artifacts/mcp-recipes/run_obsidian_mcp_e2e.ps1 -VaultRoot D:\Dev\CATMEastrolab\obsidian-vault -ServerName "obsidian"
```

