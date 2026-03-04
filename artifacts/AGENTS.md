# AGENTS.md

Local rules for `artifacts/`.

## Scope

- Applies to all files under `artifacts/`.

## Rules

1. Prefer recipe wrappers in `artifacts/mcp-recipes/` over ad-hoc one-off scripts.
2. Keep run outputs deterministic: one run dir, one summary, raw provider outputs, normalized tables.
3. Do not rewrite historical run artifacts unless task explicitly requires migration/archive.
4. For Obsidian export, use:
   - `artifacts/mcp-recipes/run_obsidian_export.ps1`
   - `artifacts/mcp-recipes/init_obsidian_vault.ps1`
5. Update `artifacts/mcp-recipes/README.md` whenever new recipe is added or CLI contract changes.
