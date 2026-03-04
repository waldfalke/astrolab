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

## 2) Generate Obsidian Bundle (Note + Canvas + Attachments)

Command:

```powershell
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 -ChartId trump_19460614_105400_jamaica_ny_renderer
```

Output files:

- `artifacts/skill-smoke/obsidian/<chart_id>/<chart_id>_natal.md`
- `artifacts/skill-smoke/obsidian/<chart_id>/<chart_id>_canvas.canvas`
- `artifacts/skill-smoke/obsidian/<chart_id>/attachments/chart_wheel.svg`

Standalone vault bootstrap (for users without existing Obsidian vault):

```powershell
pwsh artifacts/mcp-recipes/init_obsidian_vault.ps1 `
  -VaultRoot D:\AstrolabVault `
  -ChartId trump_19460614_105400_jamaica_ny_renderer
```

## 3) Canvas Collaboration Loop

Extract `[DO]` tasks from canvas:

```powershell
pwsh artifacts/mcp-recipes/run_canvas_do_extract.ps1 `
  -CanvasPath D:\AstrolabVault\Astrolab\exports\trump_19460614_105400_jamaica_ny_renderer\trump_19460614_105400_jamaica_ny_renderer_canvas.canvas `
  -OutJson artifacts/skill-smoke/canvas/do_extract.json
```

Write AI status back to canvas:

```powershell
pwsh artifacts/mcp-recipes/run_canvas_ai_update.ps1 `
  -CanvasPath D:\AstrolabVault\Astrolab\exports\trump_19460614_105400_jamaica_ny_renderer\trump_19460614_105400_jamaica_ny_renderer_canvas.canvas `
  -TargetNodeId <node_id> `
  -Status in_progress `
  -Message "Started implementation" `
  -Label "ai-status"
```
## 4) Run MCP Recipes (manual)

Examples:

```powershell
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1
pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartDir charts/trump_19460614_105400_jamaica_ny
```

## 5) Skill Pack Structural Check

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

## 6) Public-Ready Check Before Push

```powershell
git status -sb --ignored
```

Confirm:

- `.codex/skills/astro-engineering-scanner/` is ignored
- `.tools/` is ignored
- runtime outputs in `artifacts/result-packs|results|skill-smoke|tmp` are ignored
- no uncommitted tracked changes

