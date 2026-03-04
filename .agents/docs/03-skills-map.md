# 03 Skills Map

Canonical skills live in `.agents/skills/`.

## Runnable now

1. `schema-validator`
   - script: `.agents/skills/schema-validator/scripts/validate_chart.py`
2. `obsidian-export`
   - script: `.agents/skills/obsidian-export/scripts/generate_note.py`

## Spec-first (needs implementation hardening)

- `artifact-builder`
- `chart-analyst`
- `chart-data-preparator`
- `knowledge-ingestion`
- `provider-orchestrator`
- `renderer`
- `run-planner`

## Priority hardening order

1. `run-planner`
2. `provider-orchestrator`
3. `artifact-builder`
4. `chart-data-preparator`

Definition of done per skill:

- runnable script in `scripts/`
- one smoke command documented
- deterministic output sample
- one failure-path test
