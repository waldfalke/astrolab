# AGENTS_INDEX.md

Graph-style map of agent instruction files in this repository.

## Node Map

- `AGENTS.md` -> root entrypoint and global defaults
- `.agents/AGENTS.md` -> canonical playbook, read order, hard constraints
- `artifacts/AGENTS.md` -> recipe execution policy and output contracts
- `charts/AGENTS.md` -> chart-project structure and mutation rules
- `docs/AGENTS.md` -> public/private docs policy and redaction rules

## Edge Map (Inheritance / Navigation)

1. `AGENTS.md` -> `.agents/AGENTS.md` (mandatory deep playbook)
2. `AGENTS.md` -> `AGENTS_INDEX.md` (this file)
3. `AGENTS.md` -> local directory `AGENTS.md` (closest-scope rules)
4. `artifacts/AGENTS.md` -> `artifacts/mcp-recipes/README.md` (recipe catalog)
5. `charts/AGENTS.md` -> `charts/<chart_id>/INDEX.yaml` (provenance map)
6. `docs/AGENTS.md` -> `docs/public/` policy and sensitive-doc handling

## Conflict Resolution

1. System/developer instructions
2. Root `AGENTS.md`
3. `.agents/AGENTS.md`
4. Closest local `AGENTS.md`
5. File-level comments/instructions

When rules conflict at the same level, choose the stricter reproducibility/privacy constraint.
