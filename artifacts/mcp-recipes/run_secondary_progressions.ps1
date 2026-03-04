param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][string]$TargetDateUtc,
  [double]$Orb = 1.0,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$scriptId = "run_secondary_progressions"
$scriptVersion = "1.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()

function Parse-UtcDateTime {
  param([Parameter(Mandatory = $true)][string]$Value)
  return [datetime]::Parse(
    $Value,
    [System.Globalization.CultureInfo]::InvariantCulture,
    [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal
  )
}

function Get-SwissHouseRows {
  param([Parameter(Mandatory = $true)]$SwissData)
  $rows = @()
  foreach ($n in 1..12) {
    $k = [string]$n
    if ($SwissData.houses.PSObject.Properties.Name -contains $k) {
      $h = $SwissData.houses.$k
      $rows += [pscustomobject]@{
        house = $n
        longitude = [double]$h.longitude
        sign = [string]$h.sign
        degree = [double]$h.degree
      }
    }
  }
  return ($rows | Sort-Object house)
}

function Get-SwissChartPointRows {
  param([Parameter(Mandatory = $true)]$SwissData)
  $rows = @()
  foreach ($p in @("Ascendant", "Midheaven", "IC", "Descendant", "Vertex", "ARMC")) {
    if ($SwissData.chart_points.PSObject.Properties.Name -contains $p) {
      $node = $SwissData.chart_points.$p
      $rows += [pscustomobject]@{
        point = $p
        longitude = [double]$node.longitude
        sign = [string]$node.sign
        degree = [double]$node.degree
      }
    }
  }
  return $rows
}

function Get-BodyToBodyAspects {
  param(
    [Parameter(Mandatory = $true)][array]$FromRows,
    [Parameter(Mandatory = $true)][array]$ToRows,
    [Parameter(Mandatory = $true)][string]$FromLabel,
    [Parameter(Mandatory = $true)][string]$ToLabel,
    [double]$Orb = 1.0
  )

  $rows = @()
  foreach ($a in $FromRows) {
    foreach ($b in $ToRows) {
      $angle = Get-MinDelta360 -A ([double]$a.longitude) -B ([double]$b.longitude)
      $hit = Get-ClosestMajorAspect -Angle $angle -Orb $Orb
      if ($null -eq $hit) { continue }

      $rows += [pscustomobject]@{
        from_set = $FromLabel
        from_body = [string]$a.body
        to_set = $ToLabel
        to_body = [string]$b.body
        aspect = [string]$hit.aspect
        actual_angle = [math]::Round([double]$angle, 6)
        exact_angle = [double]$hit.exact_angle
        orb = [math]::Round([double]$hit.delta, 6)
        orb_limit = [double]$Orb
        is_exact = ([double]$hit.delta -le 0.2)
      }
    }
  }
  return ($rows | Sort-Object orb, from_body, to_body)
}

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("secondary_progressions_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  latitude = $Latitude
  longitude = $Longitude
  birth_datetime_utc = $BirthDateTimeUtc
  target_datetime_utc = $TargetDateUtc
  orb = $Orb
}

$birthDt = Parse-UtcDateTime -Value $BirthDateTimeUtc
$targetDt = Parse-UtcDateTime -Value $TargetDateUtc
if ($targetDt -le $birthDt) {
  throw "TargetDateUtc must be later than BirthDateTimeUtc."
}

$ageDays = ($targetDt - $birthDt).TotalDays
$ageYears = $ageDays / 365.2422
$progressedDt = $birthDt.AddDays($ageYears)

$birthUtcIso = $birthDt.ToString("yyyy-MM-ddTHH:mm:ssZ")
$targetUtcIso = $targetDt.ToString("yyyy-MM-ddTHH:mm:ssZ")
$progressedUtcIso = $progressedDt.ToString("yyyy-MM-ddTHH:mm:ssZ")

$natal = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $birthUtcIso
  latitude = $Latitude
  longitude = $Longitude
}

$progressed = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $progressedUtcIso
  latitude = $Latitude
  longitude = $Longitude
}

Write-JsonFile -Data $natal -Path (Join-Path $runDir "01_birth_positions.json")
Write-JsonFile -Data $progressed -Path (Join-Path $runDir "02_progressed_positions.json")

$natalPlanets = @(Get-SwissBodyLongitudes -SwissData $natal)
$progressedPlanets = @(Get-SwissBodyLongitudes -SwissData $progressed)
$progressedMap = @{}
foreach ($r in $progressedPlanets) { $progressedMap[[string]$r.body] = $r }

$planetDeltaRows = @()
foreach ($n in $natalPlanets | Sort-Object body) {
  $body = [string]$n.body
  if (-not $progressedMap.ContainsKey($body)) { continue }
  $p = $progressedMap[$body]
  $forward = Normalize-Longitude -Longitude ([double]$p.longitude - [double]$n.longitude)
  $shortestSigned = if ($forward -le 180.0) { $forward } else { -1.0 * (360.0 - $forward) }

  $planetDeltaRows += [pscustomobject]@{
    body = $body
    natal_longitude = [math]::Round([double]$n.longitude, 9)
    progressed_longitude = [math]::Round([double]$p.longitude, 9)
    delta_forward_deg = [math]::Round([double]$forward, 9)
    delta_shortest_signed_deg = [math]::Round([double]$shortestSigned, 9)
    natal_sign = [string]$n.sign
    natal_degree = [double]$n.degree
    progressed_sign = [string]$p.sign
    progressed_degree = [double]$p.degree
  }
}
Write-InvariantCsv -Rows $planetDeltaRows -Path (Join-Path $runDir "03_progressed_planet_deltas.csv")

$progressedHouses = @(Get-SwissHouseRows -SwissData $progressed)
Write-InvariantCsv -Rows $progressedHouses -Path (Join-Path $runDir "04_progressed_houses.csv")

$progressedPoints = @(Get-SwissChartPointRows -SwissData $progressed)
Write-InvariantCsv -Rows $progressedPoints -Path (Join-Path $runDir "05_progressed_chart_points.csv")

$progressedExtraPoints = @()
$progressedExtraPoints += Get-SwissNodePoints -SwissData $progressed
$progressedExtraPoints += Get-GalacticCenterPoint -DateTimeUtc $progressedUtcIso
Write-InvariantCsv -Rows @($progressedExtraPoints | Sort-Object point) -Path (Join-Path $runDir "06_progressed_additional_points.csv")

$p2nAspects = @(Get-BodyToBodyAspects -FromRows $progressedPlanets -ToRows $natalPlanets -FromLabel "progressed" -ToLabel "natal" -Orb $Orb)
$p2nPath = Join-Path $runDir "07_progressed_to_natal_aspects.csv"
if ($p2nAspects.Count -gt 0) {
  Write-InvariantCsv -Rows $p2nAspects -Path $p2nPath
} else {
  Write-InvariantCsv -Rows @() -Path $p2nPath -Columns @("from_set", "from_body", "to_set", "to_body", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["METHOD"] = "SECONDARY_PROGRESSIONS_1DAY_PER_1YEAR"
$summaryFields["BIRTH_UTC"] = $birthUtcIso
$summaryFields["TARGET_UTC"] = $targetUtcIso
$summaryFields["PROGRESSED_UTC"] = $progressedUtcIso
$summaryFields["LATITUDE"] = $Latitude
$summaryFields["LONGITUDE"] = $Longitude
$summaryFields["AGE_YEARS"] = [math]::Round($ageYears, 9)
$summaryFields["PROGRESSED_DAYS"] = [math]::Round($ageYears, 9)
$summaryFields["ORB"] = $Orb
$summaryFields["PLANET_DELTA_COUNT"] = $planetDeltaRows.Count
$summaryFields["PROGRESSED_HOUSE_COUNT"] = $progressedHouses.Count
$summaryFields["PROGRESSED_POINT_COUNT"] = $progressedPoints.Count
$summaryFields["PROGRESSED_EXTRA_POINT_COUNT"] = $progressedExtraPoints.Count
$summaryFields["PROGRESSED_TO_NATAL_ASPECT_COUNT"] = $p2nAspects.Count
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

Write-Output "Secondary progressions completed: $runDir"
