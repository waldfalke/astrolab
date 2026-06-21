param(
  [Parameter(Mandatory = $true)][string]$Date,            # day to scan, yyyy-MM-dd
  [Parameter(Mandatory = $true)][double]$Latitude,        # observation location
  [Parameter(Mandatory = $true)][double]$Longitude,
  [double]$TzOffsetHours = 0,                              # local-time display offset (e.g. +3 for Krasnodar)
  [int]$StepMin = 6,                                       # grid step. 6 = #97 precise; 10 = lighter (fewer swiss calls)
  [string]$NatalPointsCsv = "",                            # optional: CSV name,longitude — enables rising crossings + Moon timing to natal
  [string]$OutputBase = ""
)

# =====================================================================================================
# run_rising_hands — the FLOATING intraday "hands" instrument (rising-sign clock core, NKS astrolab #93).
#
#   This is the STANDALONE hands tool. transit-day-to-natal (#90) CONSUMES it (pass -NatalPointsCsv);
#   it does NOT compute transit→natal aspects (that is run_transits_to_natal's job — snapshot for a day).
#
# FLOATING is the foundation (#93): ASC / MC / houses / Moon are recomputed at EVERY grid step — a
#   noon-snapshot is FALSE for the hands (ASC moves 1°/4min). Engineering params from #97:
#     • grid step 6 min (compromise: sign-change of ASC vs Moon-aspect precision)
#     • watch (=rising-sign) boundary: located between grid samples (ASC ~linear over a 6-min step,
#       so we interpolate the 30°-boundary crossing — cheaper than swiss-bisection, same precision here)
#     • Moon timing & rising crossings: interpolated between samples (same method)
#
# THREE HANDS produced (#91):
#   minute  → 03_watches.csv      : when the rising SIGN changes (the "караул" units) + its ruler(s)
#   fine    → 04_rising_cross.csv : transiting ASC/MC crossing natal points (only with -NatalPointsCsv)
#   hour    → 05_moon_timing.csv  : Moon's exact aspects to natal points over the day (with -NatalPointsCsv)
#   (raw floating grid → 02_grid.csv for audit)
#
# Output is DATA only (the floor): prose/PDF is the model's, never scripted here (#73/#85, observe-don't-narrate).
# =====================================================================================================

$ErrorActionPreference = "Stop"
$scriptId = "run_rising_hands"; $scriptVersion = "0.1.0"
. "$PSScriptRoot\lib\mcp_helpers.ps1" | Out-Null

# --- sign + ruler tables (traditional + modern; dual rulers per #97) ---------------------------------
$Signs = @("Овен","Телец","Близнецы","Рак","Лев","Дева","Весы","Скорпион","Стрелец","Козерог","Водолей","Рыбы")
$RulerTrad = @("mars","venus","mercury","moon","sun","mercury","venus","mars","jupiter","saturn","saturn","jupiter")
# modern ruler differs only for Scorpio/Aquarius/Pisces; empty = same as trad
$RulerModern = @("","","","","","","","pluto","","","uranus","neptune")
$Aspects = [ordered]@{ "☌"=0; "⚹"=60; "□"=90; "△"=120; "☍"=180 }

function SignIdx([double]$lon){ [int]([math]::Floor((($lon % 360 + 360) % 360) / 30.0)) }
function LocalStr([double]$utcMin){
  $loc = (($utcMin + $TzOffsetHours*60) % 1440 + 1440) % 1440
  # floor BOTH fields — [int] in PowerShell rounds half-to-even (59.5 -> 60), which yields "HH:60"
  return ("{0:D2}:{1:D2}" -f [int][math]::Floor($loc/60), [int][math]::Floor($loc % 60))
}
# forward arc a->b passes through target? return fraction 0..1 within the step, else -1
function Cross([double]$a,[double]$b,[double]$target){
  $da = ((($target - $a) % 360) + 360) % 360
  $db = ((($b - $a) % 360) + 360) % 360
  if ($db -le 0 -or $db -gt 180) { return -1 }   # guard against backward/retro big jumps
  if ($da -ge 0 -and $da -le $db) { return $da / $db } else { return -1 }
}

# --- output dir -------------------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($OutputBase)) { $OutputBase = Join-Path $PSScriptRoot "..\results" }
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$stamp = ($Date -replace '-','')
$runDir = Join-Path $OutputBase ("rising_hands_{0}_{1}" -f $stamp, ([math]::Round($Latitude,2)))
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

# --- FLOATING SCAN: ASC/MC/Moon recomputed at every step -------------------------------------------
$nSteps = [int](1440 / $StepMin)
$grid = @()
for ($k = 0; $k -lt $nSteps; $k++) {
  $utcMin = $k * $StepMin
  $iso = ("{0}T{1:D2}:{2:D2}:00Z" -f $Date, [int][math]::Floor($utcMin/60), [int]($utcMin % 60))
  $c = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = $iso; latitude = $Latitude; longitude = $Longitude }
  $grid += [pscustomobject]@{
    utcMin = $utcMin
    asc    = [double]$c.chart_points.Ascendant.longitude
    mc     = [double]$c.chart_points.Midheaven.longitude
    moon   = [double]$c.planets.Moon.longitude
  }
}
Write-InvariantCsv -Rows @($grid | ForEach-Object { [pscustomobject]@{ utc_min=$_.utcMin; local=(LocalStr $_.utcMin); asc=[math]::Round($_.asc,3); asc_sign=$Signs[(SignIdx $_.asc)]; mc=[math]::Round($_.mc,3); moon=[math]::Round($_.moon,3) } }) `
  -Path (Join-Path $runDir "02_grid.csv") -Columns @("utc_min","local","asc","asc_sign","mc","mc_sign","moon")

# --- MINUTE HAND: watches (rising-sign changes) -----------------------------------------------------
$watches = @()
$curSign = SignIdx $grid[0].asc
$watchStartMin = 0.0
for ($i = 0; $i -lt $grid.Count - 1; $i++) {
  $s2 = SignIdx $grid[$i+1].asc
  if ($s2 -ne $curSign) {
    # boundary degree = next 30° multiple ahead of asc[i]; interpolate its time within the step
    $bDeg = ([math]::Floor($grid[$i].asc / 30.0) + 1) * 30.0
    $f = Cross $grid[$i].asc $grid[$i+1].asc ($bDeg % 360)
    $bMin = if ($f -ge 0) { $grid[$i].utcMin + $f * $StepMin } else { $grid[$i+1].utcMin }
    $watches += [pscustomobject]@{
      start_local = (LocalStr $watchStartMin); asc_sign = $Signs[$curSign]
      ruler_trad = $RulerTrad[$curSign]; ruler_modern = $RulerModern[$curSign]
      end_local = (LocalStr $bMin); duration_min = [int]($bMin - $watchStartMin)
    }
    $curSign = $s2; $watchStartMin = $bMin
  }
}
# final open watch to end of day
$watches += [pscustomobject]@{
  start_local = (LocalStr $watchStartMin); asc_sign = $Signs[$curSign]
  ruler_trad = $RulerTrad[$curSign]; ruler_modern = $RulerModern[$curSign]
  end_local = (LocalStr 1440); duration_min = [int](1440 - $watchStartMin)
}
Write-InvariantCsv -Rows $watches -Path (Join-Path $runDir "03_watches.csv") `
  -Columns @("start_local","asc_sign","ruler_trad","ruler_modern","end_local","duration_min")

# --- with natal points: FINE hand (rising crossings) + HOUR hand (Moon timing) ----------------------
$natal = [ordered]@{}
if (-not [string]::IsNullOrWhiteSpace($NatalPointsCsv) -and (Test-Path $NatalPointsCsv)) {
  foreach ($r in (Import-Csv $NatalPointsCsv)) { $natal[[string]$r.name] = [double](("$($r.longitude)") -replace ',','.') }
}

$crossRows = @()
$moonRows = @()
if ($natal.Count -gt 0) {
  foreach ($name in $natal.Keys) {
    $tgt = $natal[$name]
    # FINE: transiting ASC crosses the point (theme RISES) ; MC crosses it (theme CULMINATES)
    for ($i = 0; $i -lt $grid.Count - 1; $i++) {
      $fa = Cross $grid[$i].asc $grid[$i+1].asc $tgt
      if ($fa -ge 0) { $crossRows += [pscustomobject]@{ point=$name; kind="ASC↑ восходит"; time_local=(LocalStr ($grid[$i].utcMin + $fa*$StepMin)); point_lon=[math]::Round($tgt,2) }; break }
    }
    for ($i = 0; $i -lt $grid.Count - 1; $i++) {
      $fm = Cross $grid[$i].mc $grid[$i+1].mc $tgt
      if ($fm -ge 0) { $crossRows += [pscustomobject]@{ point=$name; kind="MC⊤ кульминирует"; time_local=(LocalStr ($grid[$i].utcMin + $fm*$StepMin)); point_lon=[math]::Round($tgt,2) }; break }
    }
    # HOUR: Moon makes each major aspect to the point during the day
    foreach ($an in $Aspects.Keys) {
      # conjunction (0°) has a single target; ±0 would duplicate the row
      $offs = if ($Aspects[$an] -eq 0) { @(0) } else { @($Aspects[$an], -$Aspects[$an]) }
      foreach ($off in $offs) {
        $atgt = (($tgt + $off) % 360 + 360) % 360
        for ($i = 0; $i -lt $grid.Count - 1; $i++) {
          $fM = Cross $grid[$i].moon $grid[$i+1].moon $atgt
          if ($fM -ge 0) { $moonRows += [pscustomobject]@{ time_local=(LocalStr ($grid[$i].utcMin + $fM*$StepMin)); aspect=$an; point="натал-$name"; sort=($grid[$i].utcMin + $fM*$StepMin) }; break }
        }
      }
    }
  }
}
$crossRows = @($crossRows | Sort-Object { [int]($_.time_local -replace ':','') })
Write-InvariantCsv -Rows $crossRows -Path (Join-Path $runDir "04_rising_cross.csv") -Columns @("point","kind","time_local","point_lon")
$moonRows = @($moonRows | Sort-Object sort | ForEach-Object { [pscustomobject]@{ time_local=$_.time_local; aspect=$_.aspect; point=$_.point } })
Write-InvariantCsv -Rows $moonRows -Path (Join-Path $runDir "05_moon_timing.csv") -Columns @("time_local","aspect","point")

# --- summary ----------------------------------------------------------------------------------------
$sum = @()
$sum += "SCRIPT=$scriptId v$scriptVersion"
$sum += "METHOD=FLOATING_INTRADAY_HANDS"
$sum += "DATE=$Date  LAT=$Latitude  LON=$Longitude  TZ=+$TzOffsetHours"
$sum += "STEP_MIN=$StepMin  GRID_SAMPLES=$($grid.Count)"
$sum += "WATCH_COUNT=$($watches.Count)"
$sum += "NATAL_MODE=$(if($natal.Count -gt 0){"ON ($($natal.Count) points)"}else{"OFF (general mode)"})"
$sum += "RISING_CROSSINGS=$($crossRows.Count)  MOON_TIMINGS=$($moonRows.Count)"
$sum += "NOTE=floating recompute every step; watch boundary interpolated (ASC ~linear per step)"
[System.IO.File]::WriteAllLines((Join-Path $runDir "00_summary.txt"), $sum, [System.Text.UTF8Encoding]::new($false))

Write-Host "rising hands -> $runDir"
$sum | ForEach-Object { Write-Host "  $_" }
