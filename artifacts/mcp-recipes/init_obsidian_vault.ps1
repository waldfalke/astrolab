param(
  [string]$VaultRoot = "",
  [string]$VaultSubdir = "Astrolab/exports",
  [string]$ChartId = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($VaultRoot)) {
  $VaultRoot = Join-Path (Get-Location) "obsidian-vault"
}
$VaultRoot = [System.IO.Path]::GetFullPath($VaultRoot)

$obsidianDir = Join-Path $VaultRoot ".obsidian"
New-Item -ItemType Directory -Force -Path $obsidianDir | Out-Null

# Minimal defaults so Obsidian opens vault cleanly and canvas is enabled.
Set-Content -Encoding UTF8 -Path (Join-Path $obsidianDir "app.json") -Value '{"promptDelete":false}'
Set-Content -Encoding UTF8 -Path (Join-Path $obsidianDir "core-plugins.json") -Value '["file-explorer","global-search","backlink","page-preview","outline","canvas"]'

Write-Output "Vault initialized: $VaultRoot"
Write-Output "Export subdir: $VaultSubdir"

if (-not [string]::IsNullOrWhiteSpace($ChartId)) {
  $exportRecipe = Join-Path $PSScriptRoot "run_obsidian_export.ps1"
  if (-not (Test-Path $exportRecipe)) {
    throw "Export recipe not found: $exportRecipe"
  }

  & $exportRecipe -ChartId $ChartId -VaultRoot $VaultRoot -VaultSubdir $VaultSubdir
  if ($LASTEXITCODE -ne 0) {
    throw "Obsidian export failed for chart: $ChartId"
  }
}

Write-Output "Done."
