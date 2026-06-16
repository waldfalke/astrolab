param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$ChartsRoot = "",
  [string]$OutputBase = "",
  # Biwheel (outer ring) — optional. When OuterPlanetsCsv is set, the wheel gets a second ring:
  # outer planets (e.g. transits) + outer->natal aspect chords. Reusable for any technique overlay.
  [string]$OuterPlanetsCsv = "",
  [string]$OuterAspectsCsv = "",
  [string]$OuterLabel = ""
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
$scriptVersion = "0.2.0"
$runStartedAt = (Get-Date).ToUniversalTime()

# Resolve optional biwheel inputs up front (fail fast on bad paths).
$outerPlanetsResolved = ""
$outerAspectsResolved = ""
if (-not [string]::IsNullOrWhiteSpace($OuterPlanetsCsv)) {
  if (-not (Test-Path $OuterPlanetsCsv)) { throw "OuterPlanetsCsv not found: $OuterPlanetsCsv" }
  $outerPlanetsResolved = [System.IO.Path]::GetFullPath((Resolve-Path $OuterPlanetsCsv).Path)
}
if (-not [string]::IsNullOrWhiteSpace($OuterAspectsCsv)) {
  if (-not (Test-Path $OuterAspectsCsv)) { throw "OuterAspectsCsv not found: $OuterAspectsCsv" }
  $outerAspectsResolved = [System.IO.Path]::GetFullPath((Resolve-Path $OuterAspectsCsv).Path)
}
$isBiwheel = -not [string]::IsNullOrWhiteSpace($outerPlanetsResolved)

$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("renderer_" + $ChartId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  chart_id = $ChartId
  chart_dir = $chartDir
  outer_planets = $outerPlanetsResolved
  outer_aspects = $outerAspectsResolved
  outer_label = $OuterLabel
}

$renderScript = Join-Path $PSScriptRoot "..\renderer\render_chart.py"
$renderArgs = @("--chart-dir", $chartDir, "--output-dir", $runDir)
if ($isBiwheel) { $renderArgs += @("--outer-planets", $outerPlanetsResolved) }
if (-not [string]::IsNullOrWhiteSpace($outerAspectsResolved)) { $renderArgs += @("--outer-aspects", $outerAspectsResolved) }
if (-not [string]::IsNullOrWhiteSpace($OuterLabel)) { $renderArgs += @("--outer-label", $OuterLabel) }
python $renderScript @renderArgs
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
$summaryFields["METHOD"] = if ($isBiwheel) { "RENDERER_SVG_BIWHEEL" } else { "RENDERER_SVG_MVP" }
$summaryFields["BIWHEEL"] = if ($isBiwheel) { "TRUE" } else { "FALSE" }
$summaryFields["OUTER_PLANETS_CSV"] = $outerPlanetsResolved
$summaryFields["OUTER_ASPECTS_CSV"] = $outerAspectsResolved
$summaryFields["OUTER_LABEL"] = $OuterLabel
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
