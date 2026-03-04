# Task Log: ASTRO-017 - Agent Skills Architecture

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

Define and implement a skills architecture for agent-driven workflows in CATMEastrolab. Skills are specialized sub-agents that can be invoked for specific task domains, enabling modular, repeatable, and composable astrology processing pipelines.

## Motivation

Current workflow relies on:
1. PowerShell recipes (imperative scripts)
2. Manual orchestration between runs
3. Implicit knowledge in task logs

A skills layer would provide:
1. **Explicit capability boundaries** — each skill has a clear purpose and interface
2. **Composable workflows** — skills can be chained for complex tasks
3. **Handoff-ready context** — skills produce structured outputs for downstream agents
4. **Separation of concerns** — calculation vs. rendering vs. validation vs. knowledge

## Existing Skills Inventory

### Secret / Proprietary

| Skill | Location | Status | Notes |
|---|---|---|---|
| `astro-engineering-scanner` | `.codex/skills/astro-engineering-scanner/SKILL.md` | ✅ Implemented | Zakharian phase-vector methodology. **Confidential** — author requested non-disclosure. Do not share externally. |

### Public Skills (To Be Implemented)

| ID | Skill | Purpose | Priority | Linked Tasks |
|---|---|---|---|---|
| SKILL-001 | `chart-data-preparator` | Build chart-project structure: call MCP methods, copy raw to `methods/`, generate `INDEX.yaml`, curate `outputs/` | P0 | ASTRO-007, ASTRO-011 |
| SKILL-002 | `chart-analyst` | Parse chart.yaml + INDEX.yaml, extract positions/aspects/houses, apply interpretation rules | P1 | ASTRO-012 |
| SKILL-003 | `provider-orchestrator` | Manage MCP provider calls with failover, QC, provenance tracking | P0 | ASTRO-003, ASTRO-011 |
| SKILL-004 | `artifact-builder` | Assemble delivery packs, validate schemas, build manifests, archive runs | P1 | ASTRO-001, ASTRO-005, ASTRO-015 |
| SKILL-005 | `renderer` | Generate SVG/PNG chart wheels, aspect grids, house diagrams | P1 | ASTRO-009 |
| SKILL-006 | `knowledge-ingestion` | Process RU/EN methodology sources, extract terms, update glossary + vector store | P2 | ASTRO-006 |
| SKILL-007 | `schema-validator` | Validate chart.yaml / INDEX.yaml contracts, check provenance integrity | P1 | ASTRO-014, ASTRO-016 |
| SKILL-008 | `run-planner` | Generate explicit execution plans with dependencies and metadata tracking | P1 | ASTRO-012 |
| SKILL-009 | `obsidian-export` | Export chart data to Obsidian notes + Canvas format | P1 | ASTRO-010 |

## Skill Interface Specification (Official Anthropic Format)

Based on the official `anthropics/skills` repository template.

### Folder Structure

```
<skill-name>/
├── SKILL.md              # Required - main skill file with YAML frontmatter
├── scripts/              # Optional - executable code
│   ├── process_data.py
│   └── validate.sh
├── references/           # Optional - documentation
│   ├── api-guide.md
│   └── examples/
└── assets/               # Optional - templates, resources
    └── report-template.md
```

### SKILL.md Frontmatter

```yaml
---
name: skill-name-in-kebab-case
description: What it does + when to use it (trigger phrases). <1024 chars, no XML tags.
license: Optional - MIT, Apache-2.0, etc.
metadata:
  author: Optional
  version: Optional
---
```

### Field Requirements

| Field | Required | Rules |
|---|---|---|
| `name` | ✅ | kebab-case only, no spaces/capitals, should match folder name |
| `description` | ✅ | What it does + trigger phrases, <1024 chars, no `<` or `>` |
| `license` | Optional | MIT, Apache-2.0, etc. |
| `metadata` | Optional | Custom key-value pairs (author, version, etc.) |

### SKILL.md Body Structure

```markdown
# Skill Name

## Instructions

Clear step-by-step instructions for the skill.

### Step 1: [First Major Step]

Explanation with optional code blocks:

```bash
python scripts/fetch_data.py --project-id PROJECT_ID
```

Expected output: [describe success]

## Examples

### Example 1: [common scenario]
- **User says:** "Trigger phrase"
- **Actions:** 1. Step one, 2. Step two
- **Result:** Expected outcome

## Troubleshooting

### Error: [Common error message]
- **Cause:** [Why it happens]
- **Solution:** [How to fix]
```

## Proposed Skill Locations

```
.qwen/skills/
├── astro-engineering-scanner/   # Existing (secret) - KEEP IN .codex/skills/
│   └── SKILL.md
├── chart-data-preparator/
│   └── SKILL.md
├── chart-analyst/
│   └── SKILL.md
├── provider-orchestrator/
│   └── SKILL.md
├── artifact-builder/
│   └── SKILL.md
├── renderer/
│   └── SKILL.md
├── knowledge-ingestion/
│   └── SKILL.md
├── schema-validator/
│   └── SKILL.md
├── run-planner/
│   └── SKILL.md
└── obsidian-export/
    └── SKILL.md
```

## Official Resources

- **Template:** `.qwen/skills-source/anthropics-skills/template/SKILL.md`
- **Examples:** `.qwen/skills-source/anthropics-skills/skills/`
- **Spec:** `.qwen/skills-source/anthropics-skills/spec/`
- **Docs:** https://support.claude.com/en/articles/12512198-creating-custom-skills

## Agent Workflow Example

```
User: "Натал + прогноз для trump_19460614_105400_jamaica_ny"

Workflow:
1. run-planner → generates execution plan with method order
2. provider-orchestrator → calls MCP (primary/backup), tracks provenance
3. chart-data-preparator → builds chart-project:
   - copies raw outputs to methods/<method>/<run>/
   - generates INDEX.yaml with canonical_source mappings
   - curates outputs/ files
4. schema-validator → validates chart.yaml / INDEX.yaml contracts
5. chart-analyst → applies phase analysis + interpretation rules
6. renderer → generates wheel SVG + aspect grid
7. obsidian-export → creates canvas + notes for analyst review
8. artifact-builder → assembles delivery pack with QC report
```

## Implementation Plan

### Phase 1: Core Infrastructure (P0)
1. `provider-orchestrator` — extract from `run_natal_with_failover.ps1`
2. `chart-data-preparator` — extract from `build_chart_project.ps1` + provider calls
3. `schema-validator` — extract from `validate_chart_project.ps1`

### Phase 2: Analysis & Rendering (P1)
4. `chart-analyst` — new capability (includes `astro-engineering-scanner` as sub-module)
5. `renderer` — new capability (ASTRO-009)
6. `run-planner` — new capability (ASTRO-012)

### Phase 3: Integration & Knowledge (P1/P2)
7. `artifact-builder` — extract from `build_pack_manifest.ps1` + `archive_runs.ps1`
8. `obsidian-export` — new capability (ASTRO-010)
9. `knowledge-ingestion` — new capability (ASTRO-006)

## Security & Confidentiality Notes

1. **`astro-engineering-scanner`** is proprietary methodology from a seminar. Author explicitly requested non-disclosure.
   - Keep in `.codex/skills/` (private directory)
   - Do not copy to `.qwen/skills/` (shared/public)
   - Do not reference in public documentation without permission

2. All other skills are project-internal but not confidential.

3. Client data in chart projects should remain local; skills should not transmit birth data externally except via configured MCP providers.

## Acceptance Criteria

- [ ] Official Anthropic skills repo cloned to `.qwen/skills-source/anthropics-skills/` ✅
- [ ] SKILL.md files created for all 9 public skills using official template
- [ ] Each skill follows official frontmatter format (name, description, optional license/metadata)
- [ ] Workflow example documented end-to-end
- [ ] Secret skill (`astro-engineering-scanner`) kept isolated in `.codex/skills/`
- [ ] Skills placed in `.qwen/skills/` for discovery
- [ ] At least one skill invoked successfully in live session
- [ ] `chart-data-preparator` can build a complete chart-project from birth data

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-008 | Target modular architecture — skills are the module boundaries |
| ASTRO-011 | Core backbone extraction — skills encapsulate backbone capabilities |
| ASTRO-012 | Agent orchestrator — skills are the units the orchestrator calls |
| ASTRO-009 | Renderer module — becomes `renderer` skill |
| ASTRO-010 | Obsidian integration — becomes `obsidian-export` skill |
| ASTRO-006 | Knowledge ingestion — becomes `knowledge-ingestion` skill |

## Open Questions

1. Should skills be PowerShell-based, Python-based, or pure prompt-engineering agents?
2. How should skills communicate state between invocations (files, context, database)?
3. Should there be a skill registry file (e.g., `.qwen/skills/REGISTRY.md`)?

---

**Next Action:** Create SKILL.md templates for Phase 1 skills (provider-orchestrator, schema-validator, artifact-builder).

