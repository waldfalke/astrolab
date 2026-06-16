param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$BirthLatitude,
  [Parameter(Mandatory = $true)][double]$BirthLongitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][int]$ReturnYear,
  [double]$ReturnLatitude = [double]::NaN,
  [double]$ReturnLongitude = [double]::NaN,
  [double]$Orb = 2.0,
  [double]$DeclinationOrb = 1.0,
  [string]$DignityScheme = "modern",
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
$scriptVersion = "1.2.0"
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
  declination_orb = $DeclinationOrb
  dignity_scheme = $DignityScheme
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

# Essential dignity of the return planets (tabular).
$returnDignities = @(Get-EssentialDignities -Rows $returnPlanets -Scheme $DignityScheme)
Write-InvariantCsv -Rows @($returnDignities | Sort-Object body) -Path (Join-Path $runDir "10_return_dignities.csv")

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

# 4. Declination layer (parallels / contraparallel / out-of-bounds). The primary swiss engine
# returns longitude only; declination depends on ecliptic latitude (why Moon/Pluto go OOB), so it
# is sourced from the ephem backup. Non-fatal: if ephem is unreachable the layer is marked
# NOT_COMPUTED and the CSVs are emitted empty rather than silently skipped (recipe contract).
$declinationStatus = "FULL"
$obliquity = $null
$returnDeclRows = @()
$declAspectRows = @()
$oobBodies = @()
try {
  $returnEphem = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{ latitude = $effReturnLat; longitude = $effReturnLon; datetime = $returnInstantIso }
  $natalEphem = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{ latitude = $BirthLatitude; longitude = $BirthLongitude; datetime = $BirthDateTimeUtc }

  $obliquity = Get-MeanObliquityDeg -DateTimeUtc $returnInstantIso
  $returnDecl = @(Get-EphemDeclinations -Ephemeris $returnEphem)
  $natalDecl = @(Get-EphemDeclinations -Ephemeris $natalEphem)

  if ($returnDecl.Count -eq 0) { throw "ephem returned no usable declinations for the return chart" }

  Write-JsonFile -Data ([pscustomobject]@{ return_ephem = $returnEphem; natal_ephem = $natalEphem; mean_obliquity_deg = $obliquity; declination_orb = $DeclinationOrb }) -Path (Join-Path $runDir "09_declination_raw.json")

  foreach ($d in $returnDecl) {
    $absDec = [math]::Abs([double]$d.declination_deg)
    $returnDeclRows += [pscustomobject]@{
      body = [string]$d.body
      declination_deg = [double]$d.declination_deg
      abs_declination = [math]::Round($absDec, 6)
      out_of_bounds = ($absDec -gt $obliquity)
    }
  }
  $oobBodies = @($returnDeclRows | Where-Object { $_.out_of_bounds } | ForEach-Object { $_.body })

  $declInternal = @(Get-DeclinationAspects -FromRows $returnDecl -ToRows $returnDecl -Orb $DeclinationOrb -FromPrefix "return:" -ToPrefix "return:" -Scope "return-internal" -SameSet $true)
  $declCross = @(Get-DeclinationAspects -FromRows $returnDecl -ToRows $natalDecl -Orb $DeclinationOrb -FromPrefix "return:" -ToPrefix "natal:" -Scope "return-natal" -SameSet $false)
  # Drop the defining return:sun <-> natal:sun parallel (identical longitude by construction => trivial).
  $declCross = @($declCross | Where-Object { -not (($_.from_object -eq "return:sun") -and ($_.to_object -eq "natal:sun")) })

  $declAspectRows = @(@($declInternal) + @($declCross) | Sort-Object scope, orb, from_object, to_object)
} catch {
  $declinationStatus = "NOT_COMPUTED"
  Write-Warning "Declination layer not computed: $($_.Exception.Message)"
  $returnDeclRows = @()
  $declAspectRows = @()
  $oobBodies = @()
}

$declColumns = @("body", "declination_deg", "abs_declination", "out_of_bounds")
if ($returnDeclRows.Count -gt 0) {
  Write-InvariantCsv -Rows @($returnDeclRows | Sort-Object body) -Path (Join-Path $runDir "07_return_declinations.csv")
} else {
  Write-InvariantCsv -Rows @() -Path (Join-Path $runDir "07_return_declinations.csv") -Columns $declColumns
}

$declAspectColumns = @("scope", "from_object", "to_object", "type", "from_decl", "to_decl", "orb", "orb_limit", "is_exact")
if ($declAspectRows.Count -gt 0) {
  Write-InvariantCsv -Rows $declAspectRows -Path (Join-Path $runDir "08_declination_aspects.csv")
} else {
  Write-InvariantCsv -Rows @() -Path (Join-Path $runDir "08_declination_aspects.csv") -Columns $declAspectColumns
}

# 5. Timing layer of the solar year (recipe step 11):
#   (a) 12 monthly phase windows from the birthday — segment N is colored by phase N
#       (1 Impulse at the start ... 12 Archive at the close);
#   (b) Sun-activation dates — the calendar date when the transiting Sun reaches each SR planet's
#       longitude = the trigger of that planet's theme (stable year-to-year +/-1-2 days). Solved by
#       mean Sun motion + a few Newton refinements against the engine (cheap, sub-0.1-day accuracy).
$yearDays = 365.2422
$segLen = $yearDays / 12.0
$phaseNames = @("Импульс", "Ресурс", "Связь", "Основа", "Игра", "Служение", "Зеркало", "Превращение", "Стратегия", "Результат", "Оптимизация", "Архив")
$windowRows = @()
for ($k = 0; $k -lt 12; $k++) {
  $ws = $returnInstant.AddDays($k * $segLen)
  $we = $returnInstant.AddDays(($k + 1) * $segLen)
  $windowRows += [pscustomobject]@{
    segment = $k + 1
    phase = $k + 1
    phase_name = $phaseNames[$k]
    start_date = $ws.ToString("yyyy-MM-dd")
    end_date = $we.ToString("yyyy-MM-dd")
  }
}
Write-InvariantCsv -Rows $windowRows -Path (Join-Path $runDir "12_monthly_phase_windows.csv")

$angleLons = @()
foreach ($pt in $returnPoints) {
  if ([string]$pt.point -in @("Ascendant", "Midheaven", "IC", "Descendant")) { $angleLons += [double]$pt.longitude }
}
$meanSpeed = 360.0 / $yearDays
$activationRows = @()
foreach ($pl in $returnPlanets) {
  $L = [double]$pl.longitude
  $approxDays = (((($L - $returnSunLon) % 360.0) + 360.0) % 360.0) / $meanSpeed
  $t = $returnInstant.AddDays($approxDays)
  for ($it = 0; $it -lt 3; $it++) {
    $sunLon = Get-SunLonAtUtc -T $t
    $err = Get-SignedDelta360 -From $sunLon -To $L
    $t = $t.AddDays($err / $meanSpeed)
  }
  $isAngular = $false
  foreach ($al in $angleLons) { if ((Get-MinDelta360 -A $L -B $al) -le 5.0) { $isAngular = $true; break } }
  $activationRows += [pscustomobject]@{
    body = [string]$pl.body
    sr_sign = [string]$pl.sign
    sr_longitude = [math]::Round($L, 4)
    activation_date = $t.ToString("yyyy-MM-dd")
    days_from_return = [math]::Round((($t - $returnInstant).TotalDays), 1)
    near_angle = $isAngular
  }
}
$activationRows = @($activationRows | Sort-Object days_from_return)
Write-InvariantCsv -Rows $activationRows -Path (Join-Path $runDir "11_sun_activation_dates.csv")

# 6. Annual profection (whole-sign timelord for the solar year). The profected sign/house and the
#    Lord of Year are pure arithmetic from the natal ASC + age; we also locate the Lord natally
#    (sign + whole-sign house) so the reading can foreground its condition. Whole-sign frame =>
#    house numbers here are NOT the Placidus houses (the reading must flag the divergence).
$profectionRows = @()
$profSign = ""
$profHouse = ""
$lordOfYear = ""
$ageYears = $ReturnYear - $birthDt.Year
$natalAsc = $null
if ($null -ne $natalChart.chart_points -and ($natalChart.chart_points.PSObject.Properties.Name -contains "Ascendant")) {
  $natalAsc = [double]$natalChart.chart_points.Ascendant.longitude
}
if ($null -ne $natalAsc) {
  $prof = Get-AnnualProfection -AscLongitude $natalAsc -AgeYears $ageYears
  $profSign = $prof.profected_sign
  $profHouse = $prof.profected_house
  $lordOfYear = $prof.lord_of_year
  $ascSignIdx = [int][math]::Floor((Normalize-Longitude -Longitude $natalAsc) / 30.0)

  # Locate the Lord of Year natally (sign + whole-sign house from the natal ASC).
  $lordRow = $natalPlanets | Where-Object { ([string]$_.body).ToLowerInvariant() -eq $lordOfYear } | Select-Object -First 1
  $lordNatalSign = ""
  $lordNatalWsHouse = ""
  if ($null -ne $lordRow) {
    $lordCoord = Convert-LongitudeToSignDegree -Longitude ([double]$lordRow.longitude)
    $lordNatalSign = [string]$lordCoord.sign
    $lordSignIdx = [int][math]::Floor((Normalize-Longitude -Longitude ([double]$lordRow.longitude)) / 30.0)
    $lordNatalWsHouse = ((($lordSignIdx - $ascSignIdx) % 12) + 12) % 12 + 1
  }

  $profectionRows += [pscustomobject]@{
    age_years = $prof.age_years
    asc_sign = $prof.asc_sign
    profected_house = $prof.profected_house
    profected_sign = $profSign
    lord_of_year = $lordOfYear
    lord_natal_sign = $lordNatalSign
    lord_natal_wholesign_house = $lordNatalWsHouse
    house_frame = "whole_sign"
  }
}
$profectionCols = @("age_years", "asc_sign", "profected_house", "profected_sign", "lord_of_year", "lord_natal_sign", "lord_natal_wholesign_house", "house_frame")
if ($profectionRows.Count -gt 0) {
  Write-InvariantCsv -Rows $profectionRows -Path (Join-Path $runDir "13_annual_profection.csv")
} else {
  Write-InvariantCsv -Rows @() -Path (Join-Path $runDir "13_annual_profection.csv") -Columns $profectionCols
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
$summaryFields["DECLINATION_STATUS"] = $declinationStatus
$summaryFields["DECLINATION_ORB"] = $DeclinationOrb
$summaryFields["MEAN_OBLIQUITY_DEG"] = if ($null -ne $obliquity) { [math]::Round([double]$obliquity, 6) } else { "" }
$summaryFields["RETURN_DECLINATION_COUNT"] = $returnDeclRows.Count
$summaryFields["RETURN_OOB_BODIES"] = ($oobBodies -join ",")
$summaryFields["DECLINATION_ASPECT_COUNT"] = $declAspectRows.Count
$summaryFields["DIGNITY_SCHEME"] = $DignityScheme
$summaryFields["RETURN_DIGNITY_COUNT"] = $returnDignities.Count
$summaryFields["SUN_ACTIVATION_COUNT"] = $activationRows.Count
$summaryFields["PHASE_WINDOW_COUNT"] = $windowRows.Count
$summaryFields["PROFECTION_AGE_YEARS"] = $ageYears
$summaryFields["PROFECTED_SIGN"] = $profSign
$summaryFields["PROFECTED_HOUSE_WHOLESIGN"] = $profHouse
$summaryFields["LORD_OF_YEAR"] = $lordOfYear
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
