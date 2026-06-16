param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [string]$TransitDateTimeUtc = "",
  # Range-scan mode (a "transit timeline" over an arbitrary period). When both are set, the script
  # samples the range at $StepDays and emits dated aspect EVENTS (exact date, orb window, multiple
  # passes on retrograde) instead of a single-instant snapshot.
  [string]$RangeStartUtc = "",
  [string]$RangeEndUtc = "",
  [double]$StepDays = 7,
  [string]$TransitBodies = "",
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

# ---------------------------------------------------------------------------------------------
# RANGE-SCAN MODE — a textual "transit timeline" over an arbitrary period.
# Samples the range at $StepDays (swiss, the natal angles need chart_points), then per
# (transit body × natal target × major aspect) detects each exact pass as a local minimum of the
# orb series and refines the date by parabolic interpolation (no extra engine calls). Retrograde
# triple-passes surface as separate minima. Natal targets = natal planets + ASC/MC/IC/DSC.
# ---------------------------------------------------------------------------------------------
$scanMode = (-not [string]::IsNullOrWhiteSpace($RangeStartUtc)) -and (-not [string]::IsNullOrWhiteSpace($RangeEndUtc))
if ($scanMode) {
  Reset-SwissRetryTelemetry
  $runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("transit_timeline_" + $CaseId)

  $transitBodyList = if ([string]::IsNullOrWhiteSpace($TransitBodies)) {
    @("sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
  } else {
    @($TransitBodies.Split(",") | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
  }

  # Natal targets: planets + angles (swiss carries chart_points).
  $natalChart = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = $BirthDateTimeUtc; latitude = $Latitude; longitude = $Longitude }
  $natalTargets = [ordered]@{}
  foreach ($r in (Get-SwissBodyLongitudes -SwissData $natalChart)) { $natalTargets[[string]$r.body] = [double]$r.longitude }
  $angleMap = [ordered]@{ Ascendant = "ASC"; Midheaven = "MC"; IC = "IC"; Descendant = "DSC" }
  foreach ($k in $angleMap.Keys) {
    if (($null -ne $natalChart.chart_points) -and ($natalChart.chart_points.PSObject.Properties.Name -contains $k)) {
      $natalTargets[$angleMap[$k]] = [double]$natalChart.chart_points.$k.longitude
    }
  }

  $rangeStart = Get-UtcDateTime -DateTimeUtc $RangeStartUtc
  $rangeEnd = Get-UtcDateTime -DateTimeUtc $RangeEndUtc
  if ($rangeEnd -le $rangeStart) { throw "RangeEndUtc must be later than RangeStartUtc." }

  $times = @()
  $series = @{}
  foreach ($b in $transitBodyList) { $series[$b] = @() }
  $cursor = $rangeStart
  while ($cursor -le $rangeEnd) {
    $iso = $cursor.ToString("yyyy-MM-ddTHH:mm:ssZ")
    $chart = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = $iso; latitude = $Latitude; longitude = $Longitude }
    $m = @{}
    foreach ($r in (Get-SwissBodyLongitudes -SwissData $chart)) { $m[[string]$r.body] = [double]$r.longitude }
    $times += $cursor
    foreach ($b in $transitBodyList) { $series[$b] += , ([double]$(if ($m.ContainsKey($b)) { $m[$b] } else { [double]::NaN })) }
    $cursor = $cursor.AddDays($StepDays)
  }
  $nSamples = $times.Count

  $aspects = @(
    [pscustomobject]@{ name = "conjunction"; a = 0.0 },
    [pscustomobject]@{ name = "sextile"; a = 60.0 },
    [pscustomobject]@{ name = "square"; a = 90.0 },
    [pscustomobject]@{ name = "trine"; a = 120.0 },
    [pscustomobject]@{ name = "opposition"; a = 180.0 }
  )

  $events = @()
  foreach ($b in $transitBodyList) {
    $lons = $series[$b]
    foreach ($tn in $natalTargets.Keys) {
      $nlon = [double]$natalTargets[$tn]
      if (($b -eq $tn) -and ($natalTargets.Contains($tn))) { } # transit-to-own-natal allowed (returns)
      foreach ($asp in $aspects) {
        $g = New-Object 'double[]' $nSamples
        for ($i = 0; $i -lt $nSamples; $i++) {
          $sep = Get-MinDelta360 -A ([double]$lons[$i]) -B $nlon
          $g[$i] = [math]::Abs($sep - [double]$asp.a)
        }
        for ($i = 1; $i -lt $nSamples - 1; $i++) {
          if (($g[$i] -le $Orb) -and ($g[$i - 1] -ge $g[$i]) -and ($g[$i] -le $g[$i + 1])) {
            $y0 = $g[$i - 1]; $y1 = $g[$i]; $y2 = $g[$i + 1]
            $denom = ($y0 - (2.0 * $y1) + $y2)
            $delta = if ([math]::Abs($denom) -gt 1e-9) { 0.5 * ($y0 - $y2) / $denom } else { 0.0 }
            if ($delta -gt 1.0) { $delta = 1.0 }; if ($delta -lt -1.0) { $delta = -1.0 }
            $exactT = $times[$i].AddDays($delta * $StepDays)
            $minOrb = $y1 - (0.25 * ($y0 - $y2) * $delta)
            if ($minOrb -lt 0.0) { $minOrb = 0.0 }
            $L = $i; while (($L - 1 -ge 0) -and ($g[$L - 1] -le $Orb)) { $L-- }
            $R = $i; while (($R + 1 -lt $nSamples) -and ($g[$R + 1] -le $Orb)) { $R++ }
            $events += [pscustomobject]@{
              transit_body = $b
              natal_target = $tn
              aspect = [string]$asp.name
              exact_date = $exactT.ToString("yyyy-MM-dd")
              min_orb_deg = [math]::Round($minOrb, 3)
              window_start = $times[$L].ToString("yyyy-MM-dd")
              window_end = $times[$R].ToString("yyyy-MM-dd")
            }
          }
        }
      }
    }
  }
  $events = @($events | Sort-Object exact_date, transit_body, natal_target)

  $eventCols = @("exact_date", "transit_body", "aspect", "natal_target", "min_orb_deg", "window_start", "window_end")
  $tlPath = Join-Path $runDir "01_transit_timeline.csv"
  if ($events.Count -gt 0) { Write-InvariantCsv -Rows $events -Path $tlPath -Columns $eventCols }
  else { Write-InvariantCsv -Rows @() -Path $tlPath -Columns $eventCols }

  $natalTargetRows = @()
  foreach ($k in $natalTargets.Keys) { $natalTargetRows += [pscustomobject]@{ target = $k; longitude = [math]::Round([double]$natalTargets[$k], 6) } }
  Write-InvariantCsv -Rows $natalTargetRows -Path (Join-Path $runDir "02_natal_targets.csv")

  $retry = Get-SwissRetryTelemetry
  $scanSummary = @()
  $scanSummary += "CASE_ID=$CaseId"
  $scanSummary += "METHOD=TRANSIT_TIMELINE_RANGE_SCAN"
  $scanSummary += "BIRTH_UTC=$BirthDateTimeUtc"
  $scanSummary += "RANGE_START_UTC=$($rangeStart.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
  $scanSummary += "RANGE_END_UTC=$($rangeEnd.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
  $scanSummary += "STEP_DAYS=$StepDays"
  $scanSummary += "SAMPLE_COUNT=$nSamples"
  $scanSummary += "TRANSIT_BODIES=$([string]::Join(',', $transitBodyList))"
  $scanSummary += "NATAL_TARGET_COUNT=$($natalTargets.Count)"
  $scanSummary += "ORB=$Orb"
  $scanSummary += "EVENT_COUNT=$($events.Count)"
  $scanSummary += "SWISS_RETRY_TOTAL=$($retry.total_retries)"
  $scanSummary += "OUTPUT_DIR=$runDir"
  Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $scanSummary

  Write-Output "Transit timeline (range scan) completed: $runDir"
  return
}

if ([string]::IsNullOrWhiteSpace($TransitDateTimeUtc)) {
  throw "Provide -TransitDateTimeUtc (single-instant mode) or -RangeStartUtc/-RangeEndUtc (range-scan mode)."
}
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
