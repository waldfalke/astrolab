param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$LatA,
  [Parameter(Mandatory = $true)][double]$LonA,
  [Parameter(Mandatory = $true)][string]$DateAUtc,
  [Parameter(Mandatory = $true)][double]$LatB,
  [Parameter(Mandatory = $true)][double]$LonB,
  [Parameter(Mandatory = $true)][string]$DateBUtc,
  [double]$Orb = 6,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)

function Get-MinDelta360 {
  param([double]$A, [double]$B)
  $d = [math]::Abs($A - $B)
  if ($d -gt 180) { $d = 360 - $d }
  return $d
}

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("synastry_" + $CaseId)

$chartA = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $LatA
  longitude = $LonA
  datetime = $DateAUtc
}

$chartB = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $LatB
  longitude = $LonB
  datetime = $DateBUtc
}

Write-JsonFile -Data $chartA -Path (Join-Path $runDir "01_chart_A_ephemeris.json")
Write-JsonFile -Data $chartB -Path (Join-Path $runDir "02_chart_B_ephemeris.json")

$bodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
$targets = @(
  @{ name = "conjunction"; deg = 0.0 },
  @{ name = "sextile"; deg = 60.0 },
  @{ name = "square"; deg = 90.0 },
  @{ name = "trine"; deg = 120.0 },
  @{ name = "opposition"; deg = 180.0 }
)

$positionsA = Get-BodyLongitudes -Ephemeris $chartA -Bodies $bodies
$positionsB = Get-BodyLongitudes -Ephemeris $chartB -Bodies $bodies

$mapA = @{}
$mapB = @{}
foreach ($row in $positionsA) { $mapA[$row.body] = [double]$row.longitude }
foreach ($row in $positionsB) { $mapB[$row.body] = [double]$row.longitude }

$matches = @()
foreach ($a in $bodies) {
  foreach ($b in $bodies) {
    if (-not $mapA.ContainsKey($a) -or -not $mapB.ContainsKey($b)) { continue }
    $delta = Get-MinDelta360 -A $mapA[$a] -B $mapB[$b]
    $best = $null
    $bestOrb = 999.0
    foreach ($target in $targets) {
      $o = [math]::Abs($delta - [double]$target.deg)
      if ($o -lt $bestOrb) {
        $best = $target
        $bestOrb = $o
      }
    }
    if ($bestOrb -le $Orb) {
      $matches += [pscustomobject]@{
        body_a = $a
        body_b = $b
        longitude_a = [math]::Round($mapA[$a], 6)
        longitude_b = [math]::Round($mapB[$b], 6)
        delta = [math]::Round($delta, 6)
        aspect = [string]$best.name
        target_deg = [double]$best.deg
        orb = [math]::Round($bestOrb, 6)
      }
    }
  }
}

$sortedMatches = @($matches | Sort-Object orb)
if ($sortedMatches.Count -gt 0) {
  Write-InvariantCsv -Rows $sortedMatches -Path (Join-Path $runDir "03_synastry_aspect_matrix.csv")
} else {
  Write-InvariantCsv -Rows @() -Path (Join-Path $runDir "03_synastry_aspect_matrix.csv") -Columns @("body_a", "body_b", "longitude_a", "longitude_b", "delta", "aspect", "target_deg", "orb")
}
Write-JsonFile -Data $matches -Path (Join-Path $runDir "04_synastry_aspect_matrix.json")

$summary = @()
$summary += "CASE_ID=$CaseId"
$summary += "DATE_A_UTC=$DateAUtc"
$summary += "DATE_B_UTC=$DateBUtc"
$summary += "A_LAT_LON=$LatA,$LonA"
$summary += "B_LAT_LON=$LatB,$LonB"
$summary += "ORB=$Orb"
$summary += "MATCH_COUNT=" + $matches.Count
$summary += "OUTPUT_DIR=$runDir"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Synastry matrix completed: $runDir"
