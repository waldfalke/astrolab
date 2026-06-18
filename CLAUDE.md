# CLAUDE.md

Claude Code entry pointer for CATMEastrolab. The canonical playbook is **AGENTS.md** —
this file only records Claude-specific deltas on top of it. Do not duplicate the playbook here.

## Read order (mandatory)

1. `AGENTS.md` → `.agents/AGENTS.md` (canonical machine playbook; §1a = what the harness IS —
   recipe-centric provenance harness, LLM as the emergent-read organ; full map in
   `TaskLogs/20260618_harness_architecture.md`, graph contour NKS `astrolab` #67/#78)
2. `AGENTS_INDEX.md` (graph of local AGENTS files)
3. `REGISTRIES.md` (index of all registries — sources, recipes, capabilities, methodology, graph)
4. `.agents/docs/00-mission.md` … `14-l402-lightning-stack.md` (full read order in `.agents/AGENTS.md`)
5. Nearest local `AGENTS.md` in the directory you are editing (adds local constraints)
6. `CURRENT_WORK.md` (active WIP; restore via `/load`)

## Building a client report — the sanctioned entry

To produce a solar-return / natal **gift report** for a client, the ONE entry is the orchestrator
`artifacts/mcp-recipes/run_solar_gift.ps1`. It forces the frame a fresh model won't self-enforce:
natal is computed BEFORE the solar return (an SR is read **against** the natal, never alone), all
numbers come ONLY from recipes (never hand-author a chart value), client data lives ONLY under
`.private/charts/` (never the public `charts/`), and a schema+provenance gate runs before the
deliverable. The orchestrator emits a work-package `.private/charts/<id>/_model_input/` with a
`BRIEF.md`; do the emergent step (twin → prose) by **following that BRIEF**, using only the computed
data. Do NOT improvise a custom pipeline or build the report by hand — that is exactly how the
deliverable gets fabricated numbers and how client PII leaks into the repo.

## Claude-specific deltas

### Skills

Project skills are mirrored into `.claude/skills/` so the Skill tool can discover them.
**Canonical source stays `.agents/skills/`** — never hand-edit `.claude/skills/`. After changing a
skill, re-mirror:

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeClaude
```

The private `astro-engineering-scanner` skill is intentionally excluded from this mirror.

### MCP providers — production boundary

`.mcp.json` registers the public no-auth astrology providers as native MCP servers:
`swissremote` (primary), `ephem` (backup), `vedastro` (probe-only).

- **Native MCP tools** (`mcp__swissremote__*`, `mcp__ephem__*`, `mcp__vedastro__*`) are for
  **probe / schema-discovery / exploration only**. No failover, no retry, no QC, no provenance.
- **Reproducible work** (anything landing in `charts/<chart_id>/` or `artifacts/results/`) MUST go
  through the recipe wrappers (`artifacts/mcp-recipes/*.ps1`, via `lib/mcp_helpers.ps1`), which
  enforce swiss→ephem failover (per `provider_profile.yaml`), retry/backoff, and raw-JSON
  persistence. `vedastro` is probe-only and is **not** part of the production failover chain.

### MCP servers intentionally NOT in `.mcp.json`

- **obsidian-mcp** (stdio) — uses a machine-specific vault path, `obsidian-vault/` is gitignored,
  and the project marks it "optional, user-chosen". Use the recipe wrappers
  (`run_obsidian_mcp_probe.ps1`, `run_obsidian_export.ps1`) or the global `obsidian-interaction`
  skill instead.
- User-global servers (`nks`, `pencil`, `figma`, Google) carry live tokens / per-user auth and
  belong in user scope, not the project file.

See the `provider-orchestrator` skill for the full provider rule.

### Slash commands

- `/load` — restore session context from `CURRENT_WORK.md` + active tasklogs.
- `/save` — persist session state before ending.

## Hard constraints (from `.agents/AGENTS.md`)

1. Use recipes in `artifacts/mcp-recipes/` for astrology computations.
2. Keep reproducible outputs under `artifacts/results/` and/or `charts/<chart_id>/`.
3. Record non-trivial work in `TaskLogs/`.
4. Before finalizing a chart project: run schema/provenance validation.

## Language policy

Artifacts (code, docs, commits, this file) — English. Live chat with the user — Russian.
