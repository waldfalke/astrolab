param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$BirthLatitude,
  [Parameter(Mandatory = $true)][double]$BirthLongitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][int]$ReturnYear,
  [double]$ReturnLatitude = [double]::NaN,
  [double]$ReturnLongitude = [double]::NaN,
  [double]$Orb = 2.0,
  [string]$OutputBase = ""
)

# Solar return (solar revolution): the chart for the moment the Sun returns to its natal
# longitude in $ReturnYear. Houses/angles are cast for the RETURN location (relocation), which
# defaults to the birth location when $ReturnLatitude/$ReturnLongitude are not supplied.
#
# IMPORTANT: the provider's calculate_solar_revolution is naive — it casts the chart at the
# birth time-of-day on the birthday of $ReturnYear, NOT the true Sun-return instant (observed
# ~9h error => meaningless Ascendant/houses). This recipe instead SOLVES for the exact return
# instant by bisection on the Sun's longitude using calculate_planetary_positions, then casts
# the chart at that instant for the return location. Reproducible: raw JSON + hashes.

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$scriptId = "run_solar_revolution"
$scriptVersion = "1.0.0"
$runStartedAt = (Get-Date).ToUniversalTime()
Reset-SwissRetryTelemetry

$useReturnLoc = -not ([double]::IsNaN($ReturnLatitude) -or [double]::IsNaN($ReturnLongitude))
$effReturnLat = if ($useReturnLoc) { $ReturnLatitude } else { $BirthLatitude }
$effReturnLon = if ($useReturnLoc) { $ReturnLongitude } else { $BirthLongitude }

function Get-SwissHouseRows {
  param([Parameter(Mandatory = $true)]$SwissChart)
  $rows = @()
  if ($null -eq $SwissChart.houses) { return $rows }
  foreach ($n in 1..12) {
    $k = [string]$n
    if ($SwissChart.houses.PSObject.Properties.Name -contains $k) {
      $h = $SwissChart.houses.$k
      $rows += [pscustomobject]@{
        house = $n
        longitude = [double]$h.longitude
        sign = [string]$h.sign
        degree = [double]$h.degree
      }
    }
  }
  return $rows
}

function Get-SwissChartPointRows {
  param([Parameter(Mandatory = $true)]$SwissChart)
  $rows = @()
  if ($null -eq $SwissChart.chart_points) { return $rows }
  foreach ($p in @("Ascendant", "Midheaven", "IC", "Descendant", "Vertex", "ARMC")) {
    if ($SwissChart.chart_points.PSObject.Properties.Name -contains $p) {
      $node = $SwissChart.chart_points.$p
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

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("solar_return_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  birth_latitude = $BirthLatitude
  birth_longitude = $BirthLongitude
  birth_datetime_utc = $BirthDateTimeUtc
  return_year = $ReturnYear
  return_latitude = $effReturnLat
  return_longitude = $effReturnLon
  orb = $Orb
}

# 1. Natal chart + natal Sun longitude (the return target).
$natalChart = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $BirthDateTimeUtc
  latitude = $BirthLatitude
  longitude = $BirthLongitude
}
$natalSunLon = [double]$natalChart.planets.Sun.longitude

# 2. Solve the true return instant: bisect Sun longitude around the birthday in $ReturnYear.
$birthDt = [datetime]::Parse($BirthDateTimeUtc, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal)
$approx = [datetime]::new($ReturnYear, $birthDt.Month, $birthDt.Day, $birthDt.Hour, $birthDt.Minute, $birthDt.Second, [DateTimeKind]::Utc)

function Get-SunLonAtUtc {
  param([datetime]$T)
  $iso = $T.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  $r = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = $iso; latitude = $effReturnLat; longitude = $effReturnLon }
  return [double]$r.planets.Sun.longitude
}

$lo = $approx.AddDays(-2)
$hi = $approx.AddDays(2)
$flo = Get-SignedDelta360 -From $natalSunLon -To (Get-SunLonAtUtc -T $lo)
$fhi = Get-SignedDelta360 -From $natalSunLon -To (Get-SunLonAtUtc -T $hi)
if (($flo -lt 0) -eq ($fhi -lt 0)) {
  throw "Solar return not bracketed in [$($lo.ToString('o')), $($hi.ToString('o'))]: flo=$flo fhi=$fhi"
}
for ($i = 0; $i -lt 40; $i++) {
  $mid = [datetime]::new([long](($lo.Ticks + $hi.Ticks) / 2), [DateTimeKind]::Utc)
  $fm = Get-SignedDelta360 -From $natalSunLon -To (Get-SunLonAtUtc -T $mid)
  if ([math]::Abs($fm) -lt 0.00005) { $lo = $mid; $hi = $mid; break }
  if (($flo -lt 0) -eq ($fm -lt 0)) { $lo = $mid; $flo = $fm } else { $hi = $mid; $fhi = $fm }
}
$returnInstant = [datetime]::new([long](($lo.Ticks + $hi.Ticks) / 2), [DateTimeKind]::Utc)
$returnInstantIso = $returnInstant.ToString("yyyy-MM-ddTHH:mm:ssZ")

# 3. Cast the return chart at the true instant for the return location.
$returnChart = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $returnInstantIso
  latitude = $effReturnLat
  longitude = $effReturnLon
}
$returnSunLon = [double]$returnChart.planets.Sun.longitude

Write-JsonFile -Data ([pscustomobject]@{ natal_chart = $natalChart; solar_return_chart = $returnChart; return_instant_utc = $returnInstantIso; natal_sun_longitude = $natalSunLon; return_sun_longitude = $returnSunLon }) -Path (Join-Path $runDir "01_solar_revolution_raw.json")

# Return chart serialization
$returnPlanets = @(Get-SwissBodyLongitudes -SwissData $returnChart)
Write-InvariantCsv -Rows @($returnPlanets | Sort-Object body) -Path (Join-Path $runDir "02_return_planets.csv")

$returnHouses = @(Get-SwissHouseRows -SwissChart $returnChart)
Write-InvariantCsv -Rows @($returnHouses | Sort-Object house) -Path (Join-Path $runDir "03_return_houses.csv")

$returnPoints = @(Get-SwissChartPointRows -SwissChart $returnChart)
Write-InvariantCsv -Rows @($returnPoints) -Path (Join-Path $runDir "04_return_chart_points.csv")

# Natal planets (reference) + return->natal aspects
$natalPlanets = @(Get-SwissBodyLongitudes -SwissData $natalChart)
Write-InvariantCsv -Rows @($natalPlanets | Sort-Object body) -Path (Join-Path $runDir "05_natal_planets.csv")

$fromReturn = @()
foreach ($p in $returnPlanets) { $fromReturn += [pscustomobject]@{ object = ("return:" + [string]$p.body); longitude = [double]$p.longitude } }
$toNatal = @()
foreach ($p in $natalPlanets) { $toNatal += [pscustomobject]@{ object = ("natal:" + [string]$p.body); longitude = [double]$p.longitude } }

$aspectRows = @()
foreach ($a in $fromReturn) {
  foreach ($b in $toNatal) {
    $angle = Get-MinDelta360 -A ([double]$a.longitude) -B ([double]$b.longitude)
    $hit = Get-ClosestMajorAspect -Angle $angle -Orb $Orb
    if ($null -eq $hit) { continue }
    $aspectRows += [pscustomobject]@{
      from_object = [string]$a.object
      to_object = [string]$b.object
      aspect = [string]$hit.aspect
      actual_angle = [math]::Round([double]$angle, 6)
      exact_angle = [double]$hit.exact_angle
      orb = [math]::Round([double]$hit.delta, 6)
      orb_limit = [double]$Orb
      is_exact = ([double]$hit.delta -le 0.2)
    }
  }
}
$aspectRows = @($aspectRows | Sort-Object orb, from_object, to_object)
$aspectPath = Join-Path $runDir "06_return_to_natal_aspects.csv"
if ($aspectRows.Count -gt 0) {
  Write-InvariantCsv -Rows $aspectRows -Path $aspectPath
} else {
  Write-InvariantCsv -Rows @() -Path $aspectPath -Columns @("from_object", "to_object", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$sunMatchDelta = Get-MinDelta360 -A $natalSunLon -B $returnSunLon

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["METHOD"] = "SOLAR_REVOLUTION"
$summaryFields["BIRTH_UTC"] = $BirthDateTimeUtc
$summaryFields["BIRTH_LATITUDE"] = $BirthLatitude
$summaryFields["BIRTH_LONGITUDE"] = $BirthLongitude
$summaryFields["RETURN_YEAR"] = $ReturnYear
$summaryFields["RETURN_LATITUDE"] = $effReturnLat
$summaryFields["RETURN_LONGITUDE"] = $effReturnLon
$summaryFields["RETURN_LOCATION_MODE"] = if ($useReturnLoc) { "RELOCATED" } else { "BIRTHPLACE" }
$summaryFields["RETURN_INSTANT_UTC"] = $returnInstantIso
$summaryFields["RETURN_INSTANT_SOLVER"] = "BISECTION_SUN_LONGITUDE"
$summaryFields["NATAL_SUN_LONGITUDE"] = [math]::Round($natalSunLon, 9)
$summaryFields["RETURN_SUN_LONGITUDE"] = [math]::Round($returnSunLon, 9)
$summaryFields["SUN_MATCH_DELTA_DEG"] = [math]::Round([double]$sunMatchDelta, 9)
$summaryFields["RETURN_PLANET_COUNT"] = $returnPlanets.Count
$summaryFields["RETURN_HOUSE_COUNT"] = $returnHouses.Count
$summaryFields["RETURN_TO_NATAL_ASPECT_COUNT"] = $aspectRows.Count
$summaryFields["ORB"] = $Orb
$retryTelemetry = Get-SwissRetryTelemetry
$summaryFields["SWISS_RETRY_TOTAL"] = $retryTelemetry.total_retries
$summaryFields["SWISS_RETRY_BY_TOOL"] = $retryTelemetry.by_tool
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

Write-Output "Solar revolution completed: $runDir"
