param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$DateTimeUtc,
  [double]$CustomPointOrb = 2.0,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$scriptId = "run_house_layer_placidus"
$scriptVersion = "1.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("house_placidus_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  latitude = $Latitude
  longitude = $Longitude
  datetime_utc = $DateTimeUtc
  custom_point_orb = $CustomPointOrb
}

$primary = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $DateTimeUtc
  latitude = $Latitude
  longitude = $Longitude
}

Write-JsonFile -Data $primary -Path (Join-Path $runDir "01_primary_positions.json")

$houseRows = @()
foreach ($n in (1..12)) {
  $k = [string]$n
  if ($primary.houses.PSObject.Properties.Name -contains $k) {
    $h = $primary.houses.$k
    $houseRows += [pscustomobject]@{
      house = $n
      longitude = [double]$h.longitude
      sign = [string]$h.sign
      degree = [double]$h.degree
    }
  }
}
Write-InvariantCsv -Rows @($houseRows | Sort-Object house) -Path (Join-Path $runDir "02_houses_placidus.csv")

$pointRows = @()
foreach ($p in @("Ascendant", "Midheaven", "IC", "Descendant", "Vertex", "ARMC")) {
  if ($primary.chart_points.PSObject.Properties.Name -contains $p) {
    $node = $primary.chart_points.$p
    $pointRows += [pscustomobject]@{
      point = $p
      longitude = [double]$node.longitude
      sign = [string]$node.sign
      degree = [double]$node.degree
    }
  }
}
Write-InvariantCsv -Rows $pointRows -Path (Join-Path $runDir "03_chart_points.csv")

$planetRows = Get-SwissBodyLongitudes -SwissData $primary
Write-InvariantCsv -Rows @($planetRows | Sort-Object body) -Path (Join-Path $runDir "04_planets_primary.csv")

$extraPointRows = @()
$extraPointRows += Get-SwissNodePoints -SwissData $primary
$extraPointRows += Get-GalacticCenterPoint -DateTimeUtc $DateTimeUtc
Write-InvariantCsv -Rows @($extraPointRows | Sort-Object point) -Path (Join-Path $runDir "05_additional_points.csv")

$customPointAspects = @(Get-CustomPointAspects -PlanetRows $planetRows -PointRows $extraPointRows -Orb $CustomPointOrb)
$customAspectPath = Join-Path $runDir "06_custom_point_aspects.csv"
if ($customPointAspects.Count -gt 0) {
  Write-InvariantCsv -Rows $customPointAspects -Path $customAspectPath
} else {
  Write-InvariantCsv -Rows @() -Path $customAspectPath -Columns @("point", "body", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["DATETIME_UTC"] = $DateTimeUtc
$summaryFields["LATITUDE"] = $Latitude
$summaryFields["LONGITUDE"] = $Longitude
$summaryFields["PROVIDER"] = "swissremote"
$summaryFields["HOUSE_SYSTEM"] = "Placidus"
$summaryFields["HOUSE_COUNT"] = $houseRows.Count
$summaryFields["POINT_COUNT"] = $pointRows.Count
$summaryFields["PLANET_COUNT"] = $planetRows.Count
$summaryFields["EXTRA_POINT_COUNT"] = $extraPointRows.Count
$summaryFields["CUSTOM_POINT_ORB"] = $CustomPointOrb
$summaryFields["CUSTOM_POINT_ASPECT_COUNT"] = $customPointAspects.Count
$summaryFields["GALACTIC_CENTER_MODEL"] = "TROPICAL_APPROX_PRECESSION"
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

Write-Output "House-layer Placidus completed: $runDir"
