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

If a step conflicts with ad-hoc reasoning, follow docs first.

## 1. Canonical Agent Layer

- Canonical skills root: `.agents/skills/`
- Do not author new canonical skills under `.codex/skills` or `.qwen/skills`.
- Private skill `astro-engineering-scanner` is intentionally excluded from canonical tracked set.

## 2. Sync Rules

Use `.agents/scripts/sync-skills.ps1`.

```powershell
# canonical -> codex
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents

# canonical -> codex + qwen
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeQwen

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
python .codex/skills/obsidian-export/scripts/generate_note.py --chart-id trump_19460614_105400_jamaica_ny --output artifacts/skill-smoke/obsidian
```

