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
  # Solar-year anchor for carrier-window ZONE classification (NKS astrolab #84). When set (= the SR
  # instant), each carrier window gets zone = tail | core | horizon by where its PEAK falls relative
  # to the solar year [anchor, anchor+365.25d], and windows that close BEFORE the anchor are dropped
  # (last year's themes). This is a date PROPERTY of the window (#85), not its role. Decoupled from the
  # scan range on purpose: the scan must reach ~3mo BEFORE the anchor for tail to be sampled at all.
  # Empty => generic transit run, no zone, no year-filter.
  [string]$SolarYearStartUtc = "",
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
# Orb-ingress/egress per pass are refined to sub-step precision by linear interpolation.
# Two artifacts: 01_transit_timeline.csv = every pass (carriers AND fast triggers, as points);
# 03_carrier_windows.csv = slow carriers only, with retrograde passes merged into ONE
# open->exact(s)->close span (the window's real length; see docs/report-standards.md §4.1).
# Use a fine $StepDays (≈2–3) for clean carrier windows; the slow movers barely move per day.
# ---------------------------------------------------------------------------------------------
$scanMode = (-not [string]::IsNullOrWhiteSpace($RangeStartUtc)) -and (-not [string]::IsNullOrWhiteSpace($RangeEndUtc))
if ($scanMode) {
  Reset-SwissRetryTelemetry
  $runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("transit_timeline_" + $CaseId)

  $transitBodyList = if ([string]::IsNullOrWhiteSpace($TransitBodies)) {
    # "north node" = the lunar nodal axis (transiting). ONLY North Node is tracked: SN is exactly
    # NN+180°, so conj/opp of the single NN carrier captures BOTH ends of BOTH axes — adding SN would
    # only flood duplicates. Sourced via Get-SwissNodePoints (chart_points), not Get-SwissBodyLongitudes.
    @("sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "north node")
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
  # Natal nodal axis as a target (North Node only — the axis; SN is its antipode, covered by opp).
  foreach ($np in (Get-SwissNodePoints -SwissData $natalChart)) {
    if ($np.point -eq "North Node") { $natalTargets["north node"] = [double]$np.longitude }
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
    foreach ($np in (Get-SwissNodePoints -SwissData $chart)) { if ($np.point -eq "North Node") { $m["north node"] = [double]$np.longitude } }
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
            # Refine orb-ingress/egress to sub-step precision by linear interpolation across the
            # bracketing samples where the orb series crosses $Orb (no extra engine calls).
            $openT = $times[$L]
            if (($L - 1 -ge 0) -and ($g[$L - 1] -gt $Orb)) {
              $den = ($g[$L - 1] - $g[$L]); $f = if ([math]::Abs($den) -gt 1e-9) { ($g[$L - 1] - $Orb) / $den } else { 0.0 }
              if ($f -lt 0.0) { $f = 0.0 }; if ($f -gt 1.0) { $f = 1.0 }
              $openT = $times[$L - 1].AddDays($f * $StepDays)
            }
            $closeT = $times[$R]
            if (($R + 1 -lt $nSamples) -and ($g[$R + 1] -gt $Orb)) {
              $den = ($g[$R + 1] - $g[$R]); $f = if ([math]::Abs($den) -gt 1e-9) { ($Orb - $g[$R]) / $den } else { 0.0 }
              if ($f -lt 0.0) { $f = 0.0 }; if ($f -gt 1.0) { $f = 1.0 }
              $closeT = $times[$R].AddDays($f * $StepDays)
            }
            $events += [pscustomobject]@{
              transit_body = $b
              natal_target = $tn
              aspect = [string]$asp.name
              exact_date = $exactT.ToString("yyyy-MM-dd")
              min_orb_deg = [math]::Round($minOrb, 3)
              window_start = $openT.ToString("yyyy-MM-dd")
              window_end = $closeT.ToString("yyyy-MM-dd")
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

  # ---- Carrier windows: a slow mover's window is ONE span, not a set of points -----------------
  # Methodology (docs/report-standards.md §4.1): the length of a transit window is set by the slow
  # CARRIER — its orb-period, with retrograde multi-passes merged into a single open->exact(s)->close
  # span. Fast movers (Sun/Moon/Mercury/Venus/Mars) are point-triggers inside the window, not spans,
  # so they stay in the timeline and are deliberately NOT aggregated here.
  $slowCarriers = @("jupiter", "saturn", "uranus", "neptune", "pluto", "north node")
  $carrierWindows = @()
  foreach ($grp in ($events | Where-Object { $slowCarriers -contains $_.transit_body } | Group-Object transit_body, natal_target, aspect)) {
    # MERGE BY THEME — all passes of one (transit_body, natal_target, aspect) are ONE theme with N
    # dates, even across out-of-orb gaps. A retro planet touching a natal point in Nov + Jan + Jul is
    # ONE theme ("Jupiter trine IC: 3 passes"), not three windows — the cause of window-bloat is
    # un-merged retro passes, not any one planet (planet-agnostic; HARNESS_PITFALLS #13). The window
    # spans the full arc (earliest open -> latest close); peaks listed; passes counted. Zone
    # classification (core/horizon/tail) and overhang presentation sit ON the theme downstream — the
    # script gives the facts, the reading is the model's (NKS astrolab #84, floor-not-cage).
    $passes = @($grp.Group)
    $opens = @($passes | ForEach-Object { Get-UtcDateTime -DateTimeUtc ($_.window_start + "T00:00:00Z") })
    $closes = @($passes | ForEach-Object { Get-UtcDateTime -DateTimeUtc ($_.window_end + "T00:00:00Z") })
    $exacts = @($passes | Sort-Object exact_date | ForEach-Object { $_.exact_date })
    $tight = ($passes | ForEach-Object { [double]$_.min_orb_deg } | Measure-Object -Minimum).Minimum
    $windowClose = (($closes | Sort-Object) | Select-Object -Last 1)
    # PEAK of the theme = the date of its TIGHTEST pass (smallest orb) — that is what the year is read
    # against, not the first or last touch.
    $peakPass = $passes | Sort-Object { [double]$_.min_orb_deg } | Select-Object -First 1
    $peakDate = Get-UtcDateTime -DateTimeUtc ($peakPass.exact_date + "T00:00:00Z")
    # ZONE (NKS astrolab #84) — only when a solar-year anchor is given. tail/core/horizon by peak vs
    # the year [anchor, anchor+365.25d]; a window closing before the anchor is last year's theme (drop).
    $zone = ""
    if (-not [string]::IsNullOrWhiteSpace($SolarYearStartUtc)) {
      $syStart = Get-UtcDateTime -DateTimeUtc $SolarYearStartUtc
      $syEnd = $syStart.AddDays(365.25)
      if ($windowClose -lt $syStart) { continue }            # finished before the year opened — skip
      elseif ($peakDate -lt $syStart) { $zone = "tail" }     # peaked before SR, still in orb at open
      elseif ($peakDate -le $syEnd)   { $zone = "core" }     # peaks inside the solar year
      else                            { $zone = "horizon" }  # peaks past next SR; approach is in-year
    }
    $carrierWindows += [pscustomobject]@{
      window_open = (($opens | Sort-Object) | Select-Object -First 1).ToString("yyyy-MM-dd")
      window_close = $windowClose.ToString("yyyy-MM-dd")
      transit_body = $grp.Group[0].transit_body
      aspect = $grp.Group[0].aspect
      natal_target = $grp.Group[0].natal_target
      zone = $zone
      passes = $passes.Count
      exact_dates = [string]::Join("; ", $exacts)
      tightest_orb_deg = [math]::Round([double]$tight, 3)
    }
  }
  $carrierWindows = @($carrierWindows | Sort-Object window_open, transit_body, natal_target)
  $cwCols = @("window_open", "window_close", "transit_body", "aspect", "natal_target", "zone", "passes", "exact_dates", "tightest_orb_deg")
  $cwPath = Join-Path $runDir "03_carrier_windows.csv"
  if ($carrierWindows.Count -gt 0) { Write-InvariantCsv -Rows $carrierWindows -Path $cwPath -Columns $cwCols }
  else { Write-InvariantCsv -Rows @() -Path $cwPath -Columns $cwCols }

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
  $scanSummary += "CARRIER_WINDOW_COUNT=$($carrierWindows.Count)"
  $scanSummary += "SLOW_CARRIERS=$([string]::Join(',', $slowCarriers))"
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
