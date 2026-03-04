# RUNBOOK

Operational commands for local validation and smoke testing.

## 1) Validate Chart Project

Command:

```powershell
python .codex/skills/schema-validator/scripts/validate_chart.py --chart-id trump_19460614_105400_jamaica_ny --json
```

Expected result:

- `"valid": true`
- `"chart_yaml_valid": true`
- `"provenance_valid": true`

## 2) Generate Obsidian Note

Command:

```powershell
python .codex/skills/obsidian-export/scripts/generate_note.py --chart-id trump_19460614_105400_jamaica_ny --output artifacts/skill-smoke/obsidian
```

Output file:

- `artifacts/skill-smoke/obsidian/trump_19460614_105400_jamaica_ny_natal.md`

## 3) Run MCP Recipes (manual)

Examples:

```powershell
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1
pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartDir charts/trump_19460614_105400_jamaica_ny
```

## 4) Skill Pack Structural Check

Check skill folders and metadata:

```powershell
Get-ChildItem .codex/skills -Directory
Get-ChildItem .codex/skills -Recurse -Filter SKILL.md
```

Validate eval JSON files:

```powershell
Get-ChildItem .codex/skills -Recurse -Filter evals.json |
  ForEach-Object { Get-Content -Raw $_.FullName | ConvertFrom-Json | Out-Null; "OK $($_.FullName)" }
```

## 5) Public-Ready Check Before Push

```powershell
git status -sb --ignored
```

Confirm:

- `.codex/skills/astro-engineering-scanner/` is ignored
- `.tools/` is ignored
- runtime outputs in `artifacts/result-packs|results|skill-smoke|tmp` are ignored
- no uncommitted tracked changes

