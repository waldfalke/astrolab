param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$OutputBase = ""
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

python $scriptPath --chart-id $ChartId --output $OutputBase
if ($LASTEXITCODE -ne 0) {
  throw "Obsidian export failed."
}

$bundleDir = Join-Path $OutputBase $ChartId
Write-Output "Obsidian export completed: $bundleDir"
