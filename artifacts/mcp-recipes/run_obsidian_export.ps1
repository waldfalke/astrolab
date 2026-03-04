param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$OutputBase = "",
  [string]$VaultRoot = "",
  [string]$VaultSubdir = "Astrolab/exports"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\skill-smoke\obsidian"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null

$scriptPath = Join-Path $PSScriptRoot "..\..\.codex\skills\obsidian-export\scripts\generate_note.py"
if (-not (Test-Path $scriptPath)) {
  throw "Obsidian export script not found: $scriptPath"
}

$argsList = @("--chart-id", $ChartId, "--output", $OutputBase)
if (-not [string]::IsNullOrWhiteSpace($VaultRoot)) {
  $argsList += @("--vault-root", $VaultRoot, "--vault-subdir", $VaultSubdir)
}

python $scriptPath @argsList
if ($LASTEXITCODE -ne 0) {
  throw "Obsidian export failed."
}

$bundleBase = $OutputBase
if (-not [string]::IsNullOrWhiteSpace($VaultRoot)) {
  $bundleBase = Join-Path ([System.IO.Path]::GetFullPath($VaultRoot)) $VaultSubdir
}
$bundleDir = Join-Path $bundleBase $ChartId
Write-Output "Obsidian export completed: $bundleDir"
