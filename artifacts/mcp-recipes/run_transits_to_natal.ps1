param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][string]$TransitDateTimeUtc,
  [double]$Orb = 1,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("transit_to_natal_" + $CaseId)

$chartNatal = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $BirthDateTimeUtc
}

$chartTransit = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $TransitDateTimeUtc
}

Write-JsonFile -Data $chartNatal -Path (Join-Path $runDir "01_natal_ephemeris.json")
Write-JsonFile -Data $chartTransit -Path (Join-Path $runDir "02_transit_ephemeris.json")

$bodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")

$natalRows = @(Get-BodyLongitudes -Ephemeris $chartNatal -Bodies $bodies)
$transitRows = @(Get-BodyLongitudes -Ephemeris $chartTransit -Bodies $bodies)

$natalMap = @{}
$transitMap = @{}
foreach ($row in $natalRows) { $natalMap[$row.body] = [double]$row.longitude }
foreach ($row in $transitRows) { $transitMap[$row.body] = [double]$row.longitude }

$matches = @()
foreach ($t in $bodies) {
  foreach ($n in $bodies) {
    if (-not $transitMap.ContainsKey($t) -or -not $natalMap.ContainsKey($n)) { continue }

    $angle = Get-MinDelta360 -A $transitMap[$t] -B $natalMap[$n]
    $hit = Get-ClosestMajorAspect -Angle $angle -Orb $Orb
    if ($null -eq $hit) { continue }

    $matches += [pscustomobject]@{
      transit_body = $t
      natal_body = $n
      transit_longitude = [math]::Round($transitMap[$t], 6)
      natal_longitude = [math]::Round($natalMap[$n], 6)
      angle = [math]::Round($angle, 6)
      aspect = [string]$hit.aspect
      exact_angle = [double]$hit.exact_angle
      orb = [math]::Round([double]$hit.delta, 6)
      orb_limit = [double]$Orb
      is_exact = ([double]$hit.delta -le 0.2)
    }
  }
}

$sorted = @($matches | Sort-Object orb)
$csvPath = Join-Path $runDir "03_transit_to_natal_aspects.csv"
if ($sorted.Count -gt 0) {
  Write-InvariantCsv -Rows $sorted -Path $csvPath
} else {
  Write-InvariantCsv -Rows @() -Path $csvPath -Columns @("transit_body", "natal_body", "transit_longitude", "natal_longitude", "angle", "aspect", "exact_angle", "orb", "orb_limit", "is_exact")
}
Write-JsonFile -Data $sorted -Path (Join-Path $runDir "04_transit_to_natal_aspects.json")

$summary = @()
$summary += "CASE_ID=$CaseId"
$summary += "METHOD=TRANSITS_TO_NATAL"
$summary += "BIRTH_UTC=$BirthDateTimeUtc"
$summary += "TRANSIT_UTC=$TransitDateTimeUtc"
$summary += "LATITUDE=$Latitude"
$summary += "LONGITUDE=$Longitude"
$summary += "ORB=$Orb"
$summary += "MATCH_COUNT=" + $sorted.Count
$summary += "OUTPUT_DIR=$runDir"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Transit-to-natal completed: $runDir"
