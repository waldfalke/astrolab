param(
  [Parameter(Mandatory = $true)][string]$Date,            # day to scan, yyyy-MM-dd
  [Parameter(Mandatory = $true)][double]$Latitude,        # observation location
  [Parameter(Mandatory = $true)][double]$Longitude,
  [double]$TzOffsetHours = 0,                              # local-time display offset (e.g. +3 for Krasnodar)
  [int]$StepMin = 6,                                       # grid step. 6 = #97 precise; 10 = lighter (fewer swiss calls)
  [int]$CoincWindowMin = 30,                               # coincidence window: events within this gap cluster into one node (#98)
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

# Sphere profiles (7 spheres, same set as sphere_ledger) for GENERAL-mode time-quality scoring (#97).
# Floor only: the script tallies WHICH spheres each watch leans toward (by sign + начкар + Moon hits);
# the model reads salience. Russian sphere keys: self/mind/love/work/money/home/meaning.
$SignSphere = @(
  @("self"), @("money"), @("mind"), @("home"), @("self","love"), @("work","mind"),
  @("love"), @("love","money"), @("meaning"), @("work"), @("meaning"), @("meaning","home"))   # Овен..Рыбы
$BodySphere = @{
  sun=@("self","work"); moon=@("home"); mercury=@("mind"); venus=@("love","money"); mars=@("self","work")
  jupiter=@("meaning","money"); saturn=@("work"); pluto=@("love"); uranus=@("mind"); neptune=@("meaning") }
$DignityWeight = @{ "домицил"=1; "экзальтация"=1; "падение"=-1; "изгнание"=-1; "перегрин"=0 }

# Zakharian PHASE operator P⟨Z.z:H.h:D⟩ — same operator as the эталонный run_phase_vectors (self-tested
# vs book Table 2.2). MODERN domiciles (phase axiom). Applied to the watch ruler: Z/z by sign, H/h from
# the watch's ASC (equal-house), D = dispositor's Z. Working layer only — never the client report.
$PhDomicile = @{ sun=5; moon=4; mercury=3; venus=2; mars=1; jupiter=9; saturn=10; uranus=11; neptune=12; pluto=8 }
$PhSignRuler = @("mars","venus","mercury","moon","sun","mercury","venus","pluto","jupiter","saturn","uranus","neptune")  # modern ruler of sign 1..12
function PhOp([int]$pointIdx1, [int]$anchorIdx1) { return ((($pointIdx1 - $anchorIdx1) % 12 + 12) % 12) + 1 }  # 1-based
function PhMicro([double]$x) { $m = [int][math]::Floor($x / 2.5) + 1; if ($m -gt 12) { $m = 12 }; if ($m -lt 1) { $m = 1 }; return $m }
function PhaseVec([string]$body, [double]$lon, [double]$ascLon, $g) {
  $b = $body.ToLowerInvariant(); if (-not $PhDomicile.ContainsKey($b)) { return "" }
  $L = ((($lon % 360) + 360) % 360)
  $sIdx0 = [int][math]::Floor($L / 30.0)                     # 0..11 sign of the body
  $degIn = $L - $sIdx0 * 30.0
  # NOTE: PowerShell variables are CASE-INSENSITIVE — $Z and $z are the SAME variable. Use distinct names.
  $signPhase  = PhOp ($sIdx0 + 1) $PhDomicile[$b]            # Z = sign phase from domicile
  $signMicro  = PhMicro $degIn                               # z
  $off = ((($L - $ascLon) % 360) + 360) % 360                # ecliptic offset from the EXACT ASC longitude
  $housePhase = [int][math]::Floor($off / 30.0) + 1          # H = equal-house from ASC (эталон run_phase_vectors)
  $houseMicro = PhMicro ($off - [math]::Floor($off / 30.0) * 30.0)  # h
  # D = Z of the dispositor, computed from the DISPOSITOR's own position (эталон), taken from the ribbon.
  $disp = $PhSignRuler[$sIdx0]                               # dispositor = modern ruler of the body's sign
  $dispPhase = ""
  if ($PhDomicile.ContainsKey($disp) -and $null -ne $g -and $g.PSObject.Properties[$disp]) {
    $dL = ((([double]$g.$disp % 360) + 360) % 360)
    $dispPhase = PhOp ([int][math]::Floor($dL / 30.0) + 1) $PhDomicile[$disp]
  }
  return ("P⟨{0}.{1}:{2}.{3}:{4}⟩" -f $signPhase, $signMicro, $housePhase, $houseMicro, $dispPhase)
}

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
  # FULL chart per step (#98): keep ALL bodies, not just ASC/MC/Moon. Unlocks Moon→transit-planet
  # (general secondary hand) and feeds the general optic; costs nothing (swiss already returns them).
  $row = [ordered]@{
    utcMin = $utcMin
    asc    = [double]$c.chart_points.Ascendant.longitude
    mc     = [double]$c.chart_points.Midheaven.longitude
    moon   = [double]$c.planets.Moon.longitude
  }
  foreach ($b in @("Sun","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto")) {
    $row[$b.ToLowerInvariant()] = [double]$c.planets.$b.longitude
  }
  $grid += [pscustomobject]$row
}
# RETRO CLIMATE (#91) — swiss here returns no retro flag, so derive DIRECTION from the ribbon:
# a body whose longitude DECREASES across the day is retrograde (signed delta, wrap-safe).
$retroBodies = @()
foreach ($b in @("mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto")) {
  $d = (((([double]$grid[-1].$b - [double]$grid[0].$b) + 180) % 360) + 360) % 360 - 180
  if ($d -lt 0) { $retroBodies += $b }
}
$planetCols = @("sun","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto")
Write-InvariantCsv -Rows @($grid | ForEach-Object {
    $g = $_; $o = [ordered]@{ utc_min=$g.utcMin; local=(LocalStr $g.utcMin); asc=[math]::Round($g.asc,3); asc_sign=$Signs[(SignIdx $g.asc)]; mc=[math]::Round($g.mc,3); moon=[math]::Round($g.moon,3) }
    foreach ($pc in $planetCols) { $o[$pc] = [math]::Round($g.$pc,3) }
    [pscustomobject]$o
  }) -Path (Join-Path $runDir "02_grid.csv") -Columns (@("utc_min","local","asc","asc_sign","mc","moon") + $planetCols)

# --- НАЧКАР helpers: investigate the watch RULER from the ribbon (not just a label) -----------------
# The ruler of the rising sign IS the "начкар" — who commands the watch. From the ribbon we know WHERE
# it is each moment, so we read its sign and its aspect to the Moon (tone of the watch). #97/#88.
function GridAt([double]$utcMin) {
  $idx = [int][math]::Round($utcMin / $StepMin)
  if ($idx -ge $grid.Count) { $idx = $grid.Count - 1 }; if ($idx -lt 0) { $idx = 0 }
  return $grid[$idx]
}
function ClosestAsp([double]$a, [double]$b, [double]$orb = 6) {
  $sep = [math]::Abs(($a - $b) % 360); if ($sep -gt 180) { $sep = 360 - $sep }
  $best = ""; $bestOrb = 999
  foreach ($asp in @(@{n="☌";d=0}, @{n="⚹";d=60}, @{n="□";d=90}, @{n="△";d=120}, @{n="☍";d=180})) {
    $o = [math]::Abs($sep - $asp.d); if ($o -lt $bestOrb) { $bestOrb = $o; $best = $asp.n }
  }
  if ($bestOrb -le $orb) { return ("{0} {1:N1}°" -f $best, $bestOrb) } else { return "" }
}
function WatchRow($curSign, $startMin, $endMin) {
  $midMin = ($startMin + $endMin) / 2.0
  $g = GridAt $midMin
  $rk = $RulerTrad[$curSign]                              # classical ruler key, e.g. "mercury"
  $rlon = [double]$g.$rk
  $rIdx = SignIdx $rlon
  # SECOND страж — the modern co-ruler (Scorpio→pluto, Aquarius→uranus, Pisces→neptune), investigated
  # the same way when present (#97 dual ruler = two scenarios). Empty for the other 9 signs.
  $rm = $RulerModern[$curSign]
  $mSign = ""; $mDig = ""; $mMoon = ""
  if ($rm) {
    $mlon = [double]$g.$rm; $mIdx = SignIdx $mlon
    $mSign = $Signs[$mIdx]
    $mDig = Get-ZakharianDignity -Body $rm -Sign ($mIdx + 1)
    $mMoon = ClosestAsp $mlon ([double]$g.moon)
  }
  $mPhase = if ($rm) { PhaseVec $rm ([double]$g.$rm) ([double]$g.asc) $g } else { "" }
  [pscustomobject]@{
    start_local = (LocalStr $startMin); asc_sign = $Signs[$curSign]
    ruler_trad = $rk; ruler_sign = $Signs[$rIdx]
    ruler_dignity = (Get-ZakharianDignity -Body $rk -Sign ($rIdx + 1))   # dignity word (domicile/exalt/fall…)
    ruler_phase = (PhaseVec $rk $rlon ([double]$g.asc) $g)               # FULL phase P⟨Z.z:H.h:D⟩ of the начкар
    ruler_to_moon = (ClosestAsp $rlon ([double]$g.moon))                 # tone: classical ruler's aspect to Moon
    ruler_modern = $rm; ruler_modern_sign = $mSign
    ruler_modern_dignity = $mDig
    ruler_modern_phase = $mPhase
    ruler_modern_to_moon = $mMoon
    end_local = (LocalStr $endMin); duration_min = [int]($endMin - $startMin)
  }
}

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
    $watches += (WatchRow $curSign $watchStartMin $bMin)
    $curSign = $s2; $watchStartMin = $bMin
  }
}
# final open watch to end of day
$watches += (WatchRow $curSign $watchStartMin 1440)
# 12 watches, NOT 13: a full 24h turns the ASC through all 12 signs; the same sign opens AND closes the
# scan (wraps through midnight). Merge that edge pair into one watch so the круг = 12.
if ($watches.Count -ge 2 -and $watches[0].asc_sign -eq $watches[-1].asc_sign) {
  $watches[0].start_local = $watches[-1].start_local      # the watch actually began before midnight
  $watches = @($watches[0..($watches.Count - 2)])
}
Write-InvariantCsv -Rows $watches -Path (Join-Path $runDir "03_watches.csv") `
  -Columns @("start_local","asc_sign","ruler_trad","ruler_sign","ruler_dignity","ruler_phase","ruler_to_moon","ruler_modern","ruler_modern_sign","ruler_modern_dignity","ruler_modern_phase","ruler_modern_to_moon","end_local","duration_min")

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
      # conjunction (0°) and opposition (180°) have a single target; ±offset would duplicate the row
      $offs = if ($Aspects[$an] -eq 0 -or $Aspects[$an] -eq 180) { @($Aspects[$an]) } else { @($Aspects[$an], -$Aspects[$an]) }
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

# --- GENERAL secondary hand: Moon aspects to TRANSIT planets (not natal) — #98 ----------------------
# The clock's "second hand" in GENERAL mode (no natal): when the Moon perfects an aspect to a transit
# planet over the day. Planets come from the ribbon (kept per-step). Feeds the general optic.
$m2p = @()
$AspG = [ordered]@{ "☌"=0; "⚹"=60; "□"=90; "△"=120; "☍"=180 }
foreach ($pc in $planetCols) {
  foreach ($an in $AspG.Keys) {
    $offs = if ($AspG[$an] -eq 0 -or $AspG[$an] -eq 180) { @($AspG[$an]) } else { @($AspG[$an], -$AspG[$an]) }
    foreach ($off in $offs) {
      for ($i = 0; $i -lt $grid.Count - 1; $i++) {
        $tgt = ((([double]$grid[$i].$pc + $off) % 360) + 360) % 360
        $fr = Cross $grid[$i].moon $grid[$i+1].moon $tgt
        if ($fr -ge 0) { $m2p += [pscustomobject]@{ time_local=(LocalStr ($grid[$i].utcMin + $fr*$StepMin)); aspect=$an; planet=$pc; sort=($grid[$i].utcMin + $fr*$StepMin) }; break }
      }
    }
  }
}
$m2p = @($m2p | Sort-Object sort | ForEach-Object { [pscustomobject]@{ time_local=$_.time_local; aspect=$_.aspect; planet=$_.planet } })
Write-InvariantCsv -Rows $m2p -Path (Join-Path $runDir "07_moon_to_planets.csv") -Columns @("time_local","aspect","planet")

# --- GENERAL: which transit OBJECTS rise / culminate — "карта момента" (objects on the ASC/MC) #91/#93
# The тонкая стрелка for the natal-free clock: transit ASC crosses a planet → that planet RISES (выходит
# на горизонт); transit MC crosses it → CULMINATES (наверху). This is what "objects on the ASC" means here.
$riseObj = @()
foreach ($pc in (@("moon") + $planetCols)) {
  for ($i = 0; $i -lt $grid.Count - 1; $i++) {
    $f = Cross $grid[$i].asc $grid[$i+1].asc ([double]$grid[$i].$pc)
    if ($f -ge 0) { $riseObj += [pscustomobject]@{ time_local=(LocalStr ($grid[$i].utcMin + $f*$StepMin)); object=$pc; kind="восходит (ASC)"; sort=($grid[$i].utcMin + $f*$StepMin) }; break }
  }
  for ($i = 0; $i -lt $grid.Count - 1; $i++) {
    $f = Cross $grid[$i].mc $grid[$i+1].mc ([double]$grid[$i].$pc)
    if ($f -ge 0) { $riseObj += [pscustomobject]@{ time_local=(LocalStr ($grid[$i].utcMin + $f*$StepMin)); object=$pc; kind="кульминирует (MC)"; sort=($grid[$i].utcMin + $f*$StepMin) }; break }
  }
}
$riseObj = @($riseObj | Sort-Object sort | ForEach-Object { [pscustomobject]@{ time_local=$_.time_local; object=$_.object; kind=$_.kind } })
Write-InvariantCsv -Rows $riseObj -Path (Join-Path $runDir "10_rising_objects.csv") -Columns @("time_local","object","kind")

# --- COINCIDENCE DETECTOR (#98 genuinely-new): cluster day-events into NODES where layers converge ----
# Events: watch changes (GENERAL layer) + rising activations + Moon aspects (PERSONAL layer). A node =
# events within CoincWindowMin of each other (chain-linked). "Carrying" if it spans BOTH layers or >=3
# events. Score = sum(point weights) × (2 if both layers) — the FLOOR ranks (#85); the model reads which
# node carries the day. This is what lets the woven axis surface (e.g. the noon ASC=MC cluster) by itself.
function ParseLocalMin([string]$hhmm) { $p = $hhmm -split ':'; return [int]$p[0]*60 + [int]$p[1] }
function LocalFromMin([int]$m) { return ("{0:D2}:{1:D2}" -f [int][math]::Floor($m/60), ($m % 60)) }
function PointWeight([string]$name) {
  $n = $name.ToLowerInvariant()
  if ($n -match 'asc|mc|ic|dsc') { return 3 }       # angles — first-class (#88)
  if ($n -match 'солнц|лун')      { return 3 }       # luminaries
  if ($n -match 'меркур|венер|марс') { return 2 }    # personal planets / chart ruler
  return 1
}
$ev = @()
foreach ($w in ($watches | Select-Object -Skip 1)) { $ev += [pscustomobject]@{ min=(ParseLocalMin $w.start_local); layer="general"; kind="караул→$($w.asc_sign)"; weight=2 } }
foreach ($r in $crossRows) { $ev += [pscustomobject]@{ min=(ParseLocalMin $r.time_local); layer="personal"; kind="$($r.point) $($r.kind)"; weight=(PointWeight $r.point) } }
foreach ($m in $moonRows)  { $ev += [pscustomobject]@{ min=(ParseLocalMin $m.time_local); layer="personal"; kind="Луна $($m.aspect) $($m.point)"; weight=(PointWeight $m.point) } }
$ev = @($ev | Sort-Object min)

$coinc = @()
if ($ev.Count -gt 0) {
  $cluster = [System.Collections.ArrayList]@($ev[0])
  for ($i = 1; $i -le $ev.Count; $i++) {
    $brk = ($i -eq $ev.Count) -or (($ev[$i].min - $cluster[$cluster.Count-1].min) -gt $CoincWindowMin)
    if ($brk) {
      $layers = @($cluster | ForEach-Object { $_.layer } | Select-Object -Unique)
      $both = ($layers.Count -ge 2)
      if ($cluster.Count -ge 2 -and ($both -or $cluster.Count -ge 3)) {
        $coinc += [pscustomobject]@{
          window = ("{0}-{1}" -f (LocalFromMin $cluster[0].min), (LocalFromMin $cluster[$cluster.Count-1].min))
          span_min = ($cluster[$cluster.Count-1].min - $cluster[0].min)
          n = $cluster.Count
          layers = ($layers -join '+')
          score = (($cluster | Measure-Object weight -Sum).Sum * $(if ($both) { 2 } else { 1 }))
          events = (($cluster | ForEach-Object { "$(LocalFromMin $_.min) $($_.kind)" }) -join ' · ')
        }
      }
      if ($i -lt $ev.Count) { $cluster = [System.Collections.ArrayList]@($ev[$i]) }
    } else { [void]$cluster.Add($ev[$i]) }
  }
}
$coinc = @($coinc | Sort-Object score -Descending)
Write-InvariantCsv -Rows $coinc -Path (Join-Path $runDir "06_coincidences.csv") -Columns @("window","span_min","n","layers","score","events")

# --- SPHERE QUALITY per watch (#97 general-mode): which life-spheres each watch leans toward ----------
# Floor: tally spheres by sign + начкар (with its dignity strength) + Moon hits in the window. Model reads.
$sphRows = @()
foreach ($w in $watches) {
  $sIdx = [array]::IndexOf($Signs, $w.asc_sign)
  $score = [ordered]@{ self=0; mind=0; love=0; work=0; money=0; home=0; meaning=0 }
  if ($sIdx -ge 0) { foreach ($sp in $SignSphere[$sIdx]) { $score[$sp] += 2 } }
  if ($BodySphere.ContainsKey($w.ruler_trad)) {
    $dw = if ($DignityWeight.ContainsKey($w.ruler_dignity)) { $DignityWeight[$w.ruler_dignity] } else { 0 }
    foreach ($sp in $BodySphere[$w.ruler_trad]) { $score[$sp] += (1 + $dw) }
  }
  $ws = ParseLocalMin $w.start_local; $we = ParseLocalMin $w.end_local; if ($we -lt $ws) { $we += 1440 }
  foreach ($m in $m2p) {
    $mm = ParseLocalMin $m.time_local; if ($mm -lt $ws) { $mm += 1440 }
    if ($mm -ge $ws -and $mm -le $we -and $BodySphere.ContainsKey($m.planet)) {
      foreach ($sp in $BodySphere[$m.planet]) { $score[$sp] += 1 }
    }
  }
  $top = (@($score.GetEnumerator() | Where-Object { $_.Value -gt 0 } | Sort-Object Value -Descending | ForEach-Object { "$($_.Key):$($_.Value)" })) -join " "
  $sphRows += [pscustomobject]@{ start_local=$w.start_local; asc_sign=$w.asc_sign; spheres=$top }
}
Write-InvariantCsv -Rows $sphRows -Path (Join-Path $runDir "08_sphere_quality.csv") -Columns @("start_local","asc_sign","spheres")

# --- VoC: Moon void of course — no major aspect to a CLASSICAL planet before leaving its sign (#91) --
# Минутная стрелка (караулы) идёт всегда; на VoC ВСТАЁТ ТОЛЬКО СЕКУНДНАЯ (аспекты Луны). Режим "без
# последствий": рутина/завершение, не старт. Empty if the Moon doesn't change sign on the day.
$classicalP = @("sun","mercury","venus","mars","jupiter","saturn")
$mClass = @($m2p | Where-Object { $classicalP -contains $_.planet } | ForEach-Object { ParseLocalMin $_.time_local } | Sort-Object)
$vocRows = @()
for ($i = 0; $i -lt $grid.Count - 1; $i++) {
  $s1 = [int][math]::Floor(((($grid[$i].moon % 360) + 360) % 360) / 30)
  $s2 = [int][math]::Floor(((($grid[$i+1].moon % 360) + 360) % 360) / 30)
  if ($s1 -ne $s2) {
    $chgLocal = (ParseLocalMin (LocalStr $grid[$i+1].utcMin))
    $lastAsp = @($mClass | Where-Object { $_ -lt $chgLocal }) | Select-Object -Last 1
    if ($null -ne $lastAsp) {
      $vocRows += [pscustomobject]@{ voc_start=(LocalFromMin $lastAsp); voc_end=(LocalStr $grid[$i+1].utcMin); note="Луна без курса — секундная стрелка встала; рутина/завершение, не старт" }
    }
  }
}
Write-InvariantCsv -Rows $vocRows -Path (Join-Path $runDir "09_void_of_course.csv") -Columns @("voc_start","voc_end","note")

# --- summary ----------------------------------------------------------------------------------------
$sum = @()
$sum += "SCRIPT=$scriptId v$scriptVersion"
$sum += "METHOD=FLOATING_INTRADAY_HANDS"
$sum += "DATE=$Date  LAT=$Latitude  LON=$Longitude  TZ=+$TzOffsetHours"
$sum += "STEP_MIN=$StepMin  GRID_SAMPLES=$($grid.Count)"
$sum += "WATCH_COUNT=$($watches.Count)"
$sum += "NATAL_MODE=$(if($natal.Count -gt 0){"ON ($($natal.Count) points)"}else{"OFF (general mode)"})"
$sum += "RISING_CROSSINGS=$($crossRows.Count)  MOON_TIMINGS=$($moonRows.Count)"
$sum += "COINCIDENCE_NODES=$($coinc.Count)  (window=${CoincWindowMin}min)"
$sum += "RETROGRADE=$(if($retroBodies.Count){[string]::Join(',', $retroBodies)}else{'none'})  (seasonal climate, #91)"
$sum += "VOID_OF_COURSE_PERIODS=$($vocRows.Count)"
$sum += "NOTE=floating recompute every step; watch boundary interpolated (ASC ~linear per step)"
[System.IO.File]::WriteAllLines((Join-Path $runDir "00_summary.txt"), $sum, [System.Text.UTF8Encoding]::new($false))

Write-Host "rising hands -> $runDir"
$sum | ForEach-Object { Write-Host "  $_" }
