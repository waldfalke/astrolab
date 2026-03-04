param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$ChartsRoot = "",
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)

$chartDir = Join-Path $ChartsRoot $ChartId
if (-not (Test-Path $chartDir)) {
  throw "Chart directory not found: $chartDir"
}

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null

$scriptId = "run_renderer"
$scriptVersion = "0.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()

$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("renderer_" + $ChartId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  chart_id = $ChartId
  chart_dir = $chartDir
}

$renderScript = Join-Path $PSScriptRoot "..\renderer\render_chart.py"
python $renderScript --chart-dir $chartDir --output-dir $runDir
if ($LASTEXITCODE -ne 0) {
  throw "Renderer python script failed."
}

$manifestPath = Join-Path $runDir "03_render_manifest.json"
if (-not (Test-Path $manifestPath)) {
  throw "Renderer manifest missing: $manifestPath"
}
$manifest = Get-Content -Raw $manifestPath | ConvertFrom-Json

$summaryFields = [ordered]@{}
$summaryFields["CHART_ID"] = $ChartId
$summaryFields["METHOD"] = "RENDERER_SVG_MVP"
$summaryFields["CHART_DIR"] = $chartDir
$summaryFields["PLANET_COUNT"] = $manifest.counts.planets
$summaryFields["HOUSE_COUNT"] = $manifest.counts.houses
$summaryFields["POINT_COUNT"] = $manifest.counts.points
$summaryFields["ASPECT_COUNT"] = $manifest.counts.aspects
$summaryFields["OUTPUT_DIR"] = $runDir

$runFinishedAt = (Get-Date).ToUniversalTime()
$outputHash = Get-RunOutputHash -RunDir $runDir -ExcludeFiles @("00_summary.txt")
Write-RunSummary `
  -Path (Join-Path $runDir "00_summary.txt") `
  -ScriptId $scriptId `
  -ScriptVersion $scriptVersion `
  -RunStartedAtUtc $runStartedAt `
  -RunFinishedAtUtc $runFinishedAt `
  -InputHash $inputHash `
  -OutputHash $outputHash `
  -Fields $summaryFields

Write-Output "Renderer completed: $runDir"
