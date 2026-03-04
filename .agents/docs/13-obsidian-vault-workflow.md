# 13 Obsidian Vault Workflow

Goal: export chart artifacts into a lightweight Obsidian vault without copying the repository.

## A. Why this exists

- Many users keep Obsidian vault outside project root.
- Canvas file nodes require vault-relative paths.
- `run_obsidian_export.ps1` supports `-VaultRoot` and `-VaultSubdir` for this.

## B. One-command bootstrap

```powershell
pwsh artifacts/mcp-recipes/init_obsidian_vault.ps1 `
  -VaultRoot D:\AstrolabVault `
  -ChartId trump_19460614_105400_jamaica_ny_renderer
```

Produces:

- `D:\AstrolabVault\.obsidian\`
- `D:\AstrolabVault\Astrolab\exports\<chart_id>\*.md`
- `D:\AstrolabVault\Astrolab\exports\<chart_id>\*.canvas`
- `D:\AstrolabVault\Astrolab\exports\<chart_id>\attachments\*.svg`

## C. Export into existing vault

```powershell
pwsh artifacts/mcp-recipes/run_obsidian_export.ps1 `
  -ChartId trump_19460614_105400_jamaica_ny_renderer `
  -VaultRoot D:\ExistingVault `
  -VaultSubdir Astrolab/exports
```

## D. Open in Obsidian

1. Open `VaultRoot` folder as vault.
2. Open `Astrolab/exports/<chart_id>/<chart_id>_canvas.canvas`.
3. Ensure core plugin `Canvas` is enabled.

## E. Rules for agents

1. Do not commit user-local vault content.
2. Keep export paths deterministic (`Astrolab/exports` default).
3. Prefer recipe wrappers over direct script invocation for reproducibility.
