param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$ChartsRoot = "",
  [string]$SolarReturnRunDir = "",
  [string]$TransitTimelineCsv = "",
  [string]$FactorsPath = "",
  [string]$DispositionsPath = "",
  [string]$VersionsPath = "",
  [string]$ReportPath = ""
)

# Coverage ledger builder — keyed-contract scheme (semantic-base.md «Полнота обхода», acceptance gate 2).
#
# Three artifacts, one contract = factor_id:
#   1. factors.csv       — MACHINE. Every factor enumerated from the data, with a stable factor_id.
#                          Regenerated freely on every run (anti-cherry-pick: factors come from data, not memory).
#   2. dispositions.csv  — SEMANTIC. factor_id → salience / valence_resolved / basis / note. The MODEL owns it.
#                          The script NEVER rewrites existing rows — it only APPENDS rows for factor_ids it has
#                          not seen before (auto-quiet rows seeded with salience=тихий). Hand edits survive regen.
#   2b.versions.csv      — VERSION LOG. factor_id → pole / status(taken|parked|dropped) / basis / note. MODEL owns it
#                          (append-only; the script only creates the header if absent, never rewrites rows). Makes the
#                          discarding of interpretive branches VISIBLE: a collapsed fan must log each genuinely-afforded
#                          pole as taken / parked(live) / dropped(+basis). Silent disappearance = anti-pattern #2/#14 at
#                          the branch level — previously the model's invisible burden, now auditable. (Cannot catch a
#                          pole that NEVER surfaced; that is mitigated by reading the fan from the operator tables.)
#   3. coverage_report.md— VERIFIER (read-only). JOINs the two by factor_id and runs the structural checks:
#                            • completeness  — every factor has a non-blank salience (else: hole / «лысый соляр»)
#                            • orphans       — disposition whose factor vanished from the data
#                            • basis integrity — every factor_id cited in a basis exists in factors.csv
#                                                (anti-FABRICATED-basis: catches phantom corroboration; it does
#                                                 NOT catch selective demotion — that stays the model's burden)
#                            • pole⇒basis    — valence_resolved=yes ⇒ basis non-empty (no «nice» pole-collapse)
#                          Plus the full joined table (human-readable ledger) and tallies.
#
# factor_id discipline: NEVER sort aspect endpoints. Cross-frame aspects (sr2n / transit / prog2n / dir2n) carry
# direction (SR-Saturn→natal-Moon ≠ natal-Saturn→SR-Moon); sorting would symmetrize the directed (anti-pattern #5).
# Stability comes from deterministic enumeration over the same source file, not from sorting.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\lib\mcp_helpers.ps1"   # for Get-ZakharianDignity / Resolve-SignIndex (phase-model dignity)

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)
$chartDir = Join-Path $ChartsRoot $ChartId
if (-not (Test-Path $chartDir)) { throw "Chart project not found: $chartDir" }

$outputsDir = Join-Path $chartDir "outputs"
$methodsDir = Join-Path $chartDir "methods"
$packDir    = Join-Path $chartDir "packs"

if ([string]::IsNullOrWhiteSpace($FactorsPath))      { $FactorsPath      = Join-Path $packDir "coverage_factors.csv" }
if ([string]::IsNullOrWhiteSpace($DispositionsPath)) { $DispositionsPath = Join-Path $packDir "coverage_dispositions.csv" }
if ([string]::IsNullOrWhiteSpace($VersionsPath))     { $VersionsPath     = Join-Path $packDir "coverage_versions.csv" }
if ([string]::IsNullOrWhiteSpace($ReportPath))       { $ReportPath       = Join-Path $packDir "coverage_report.md" }

# Resolve a data file: prefer outputs/, else search methods/** for the basename.
function Resolve-ChartFile {
  param([string[]]$Names, [string]$ExternalDir = "")
  foreach ($n in $Names) {
    if (-not [string]::IsNullOrWhiteSpace($ExternalDir)) {
      $ep = Join-Path $ExternalDir $n
      if (Test-Path $ep) { return $ep }
    }
    $op = Join-Path $outputsDir $n
    if (Test-Path $op) { return $op }
  }
  foreach ($n in $Names) {
    $hit = Get-ChildItem -Path $methodsDir -Recurse -Filter $n -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.FullName }
  }
  return $null
}

function Import-CsvSafe { param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) { return @() }
  return @(Import-Csv -Path $Path)
}

# Slugify one id component: collapse any non-letter/digit run to a single dash, trim, lowercase.
# Dashes already inside a component (the from-to pair) are preserved.
function Slug { param([string]$s)
  if ($null -eq $s) { return "" }
  return ((("$s") -replace '[^\p{L}\p{Nd}]+','-').Trim('-').ToLower())
}
# Build a dotted factor_id from parts (each slugged) and guarantee uniqueness deterministically.
$script:idSeen = @{}
function New-FactorId { param([string[]]$Parts)
  $id = (($Parts | ForEach-Object { Slug $_ }) -join ".")
  if ($script:idSeen.ContainsKey($id)) {
    $script:idSeen[$id]++
    $id = "$id~$($script:idSeen[$id])"
    $script:idSeen[$id] = 1
  } else {
    $script:idSeen[$id] = 1
  }
  return $id
}

$rows = New-Object System.Collections.Generic.List[object]
function Add-Row { param($Tech, [string[]]$IdParts, $Factor, $Data, $Auto)
  $rows.Add([pscustomobject]@{ id = (New-FactorId $IdParts); tech = $Tech; factor = $Factor; data = $Data; auto = $Auto })
}

# ---------- NATAL ----------
$natalPlanets = Import-CsvSafe (Resolve-ChartFile @("planets_primary.csv","04_planets_primary.csv"))
$natalLong    = Import-CsvSafe (Resolve-ChartFile @("natal_longitudes.csv","02_primary_longitudes.csv","06_backup_longitudes.csv"))
$dignities    = Import-CsvSafe (Resolve-ChartFile @("natal_dignities.csv","07_natal_dignities.csv"))
$sect         = Import-CsvSafe (Resolve-ChartFile @("natal_sect.csv","07_natal_sect.csv"))
$decl         = Import-CsvSafe (Resolve-ChartFile @("natal_declinations.csv","08_natal_declinations.csv"))
$houses       = Import-CsvSafe (Resolve-ChartFile @("houses_placidus.csv","02_houses_placidus.csv"))
$points       = Import-CsvSafe (Resolve-ChartFile @("chart_points.csv","03_chart_points.csv"))
$addPoints    = Import-CsvSafe (Resolve-ChartFile @("additional_points.csv","05_additional_points.csv"))

# Dignity comes from ZAKHARIAN's verified table (lib Get-ZakharianDignity), computed from the object's
# sign — uniformly for natal AND solar-return — NOT the engine's generic scheme. The engine's dignity
# rows are used only as a sign source / fallback. (Phase model: outers exalt/fall, ☿↑Aquarius… — differs.)
$dignMap = @{}
foreach ($d in $dignities) {
  $z = Get-ZakharianDignity -Body $d.body -Sign $d.sign
  $dignMap[("$($d.body)").ToLower()] = if ($z) { $z } else { $d.dignity }
}
$sectMap = @{}; foreach ($s in $sect) { $sectMap[$s.body] = "$($s.planet_team)/$($s.placement)/$($s.role)" }
$declMap = @{}; foreach ($d in $decl) { $oob = if ($d.out_of_bounds -eq "TRUE") { " OOB!" } else { "" }; $declMap[$d.body] = "$($d.declination_deg)$oob" }
# Phase vector (Zakharian) — base object property like dignity/sect. Z is grounded (book Table 2.2);
# z/H/h/D ride along but are anumita (operator+attested, source-unverifiable). Authorial → working layer only.
$phaseLayer = Import-CsvSafe (Resolve-ChartFile @("phase_vectors.csv"))
$phaseMap = @{}; foreach ($pv in $phaseLayer) { $phaseMap[("$($pv.body)").ToLower()] = $pv }

$bodyList = if ($natalPlanets.Count) { $natalPlanets } else { $natalLong }
foreach ($p in $bodyList) {
  $b = $p.body
  $sd = if ($p.PSObject.Properties['sign']) { "$($p.sign) $([math]::Round([double]($p.degree -replace ',','.'),1))" } else { $p.longitude }
  $dg = $dignMap[$b]; $sc = $sectMap[$b]; $dc = $declMap[$b]
  $ph = $phaseMap[("$b").ToLower()]
  $phStr = if ($ph) { " · фаза=$($ph.vector) [Z сверено; z/H/h/D anumita]" } else { "" }
  Add-Row "натал" @("natal","obj",$b) "объект: $b" "$sd · dign=$dg · sect=$sc · decl=$dc$phStr" ""
}
foreach ($d in $decl) { if ($d.out_of_bounds -eq "TRUE") { Add-Row "натал" @("natal","oob",$d.body) "OOB: $($d.body)" "δ=$($d.declination_deg)" "флаг: вне границ" } }

# Houses (arena) — occupancy from natal planets
$occByHouse = @{}
foreach ($p in $bodyList) {
  if ($p.PSObject.Properties['longitude']) {
    $plon = [double]($p.longitude -replace ',','.')
    for ($h = 0; $h -lt $houses.Count; $h++) {
      $c1 = [double]($houses[$h].longitude -replace ',','.')
      $c2 = [double]($houses[($h+1) % $houses.Count].longitude -replace ',','.')
      $inb = if ($c1 -lt $c2) { ($plon -ge $c1 -and $plon -lt $c2) } else { ($plon -ge $c1 -or $plon -lt $c2) }
      if ($inb) { $hn = $houses[$h].house; if (-not $occByHouse[$hn]) { $occByHouse[$hn] = @() }; $occByHouse[$hn] += $p.body }
    }
  }
}
foreach ($h in $houses) {
  $occ = $occByHouse[$h.house]
  $auto = if ($occ) { "" } else { "тихий (пусто)" }
  $occStr = if ($occ) { ($occ -join ",") } else { "—" }
  Add-Row "натал" @("natal","house",$h.house) "дом $($h.house)" "$($h.sign) $([math]::Round([double]($h.degree -replace ',','.'),1)) · занят: $occStr" $auto
}

# Points / nodes / angles
foreach ($pt in $points) { if ($pt.point -in @("Ascendant","Midheaven")) { Add-Row "натал" @("natal","angle",$pt.point) "угол: $($pt.point)" "$($pt.sign) $([math]::Round([double]($pt.degree -replace ',','.'),1))" "" } }
foreach ($pt in $addPoints) { Add-Row "натал" @("natal","point",$pt.point) "точка: $($pt.point)" "$($pt.sign) $([math]::Round([double]($pt.degree -replace ',','.'),1))" "" }

# Aspects (from JSON) — endpoint order preserved (directed), NEVER sorted
$aspPath = Resolve-ChartFile @("natal_aspects.json","04_backup_aspects.json")
if ($aspPath) {
  $aj = Get-Content -Raw $aspPath | ConvertFrom-Json
  foreach ($a in $aj.aspects) {
    $ex = if ($a.exact) { " ТОЧНО" } else { "" }
    $star = if ($a.body1 -in @("sirius") -or $a.body2 -in @("sirius")) { "звезда — scope?" } else { "" }
    Add-Row "натал" @("natal","asp","$($a.body1)-$($a.body2)",$a.aspect) "аспект: $($a.body1) $($a.aspect) $($a.body2)" "орб $([math]::Round([double]$a.orb,2))°$ex" $star
  }
}
# Declination aspects
$declAsp = Import-CsvSafe (Resolve-ChartFile @("natal_declination_aspects.csv","09_natal_declination_aspects.csv"))
foreach ($a in $declAsp) { Add-Row "натал" @("natal","declasp","$($a.from_object)-$($a.to_object)",$a.type) "склон.аспект: $($a.from_object) $($a.type) $($a.to_object)" "орб $($a.orb)°" "" }

# Derived
$ruler = ($points | Where-Object { $_.point -eq "Ascendant" } | Select-Object -First 1)
Add-Row "натал-производное" @("natal","derived","chart-ruler") "управитель карты" "по ASC $($ruler.sign)" "суждение"
Add-Row "натал-производное" @("natal","derived","sect-light") "светило секты" "см. natal_sect role=sect_light" "суждение"
Add-Row "натал-производное" @("natal","derived","element-balance") "баланс стихий/крестов" "посчитать по знакам" "суждение"
Add-Row "натал-производное" @("natal","derived","dispositor-sinks") "диспозиторные стоки" "проследить цепочки" "суждение"

# ---------- SOLAR RETURN ----------
if (-not [string]::IsNullOrWhiteSpace($SolarReturnRunDir) -and (Test-Path $SolarReturnRunDir)) {
  $srP = Import-CsvSafe (Join-Path $SolarReturnRunDir "02_return_planets.csv")
  $srH = Import-CsvSafe (Join-Path $SolarReturnRunDir "03_return_houses.csv")
  $srA = Import-CsvSafe (Join-Path $SolarReturnRunDir "06_return_to_natal_aspects.csv")
  $srD = Import-CsvSafe (Join-Path $SolarReturnRunDir "10_return_dignities.csv")
  $srPts = Import-CsvSafe (Join-Path $SolarReturnRunDir "04_return_chart_points.csv")
  $srProf = Import-CsvSafe (Join-Path $SolarReturnRunDir "13_annual_profection.csv")
  # SR dignity from Zakharian's table too (sign-based), uniform with natal — not the engine's scheme.
  $srDignMap = @{}; foreach ($d in $srD) { $z = Get-ZakharianDignity -Body $d.body -Sign $d.sign; $srDignMap[$d.body] = if ($z) { $z } else { $d.dignity } }
  # SR house of each SR planet
  $srOcc = @{}
  foreach ($p in $srP) {
    $plon = [double]($p.longitude -replace ',','.')
    for ($h = 0; $h -lt $srH.Count; $h++) {
      $c1 = [double]($srH[$h].longitude -replace ',','.')
      $c2 = [double]($srH[($h+1) % $srH.Count].longitude -replace ',','.')
      $inb = if ($c1 -lt $c2) { ($plon -ge $c1 -and $plon -lt $c2) } else { ($plon -ge $c1 -or $plon -lt $c2) }
      if ($inb) { $srOcc[$p.body] = $srH[$h].house }
    }
  }
  foreach ($p in $srP) { Add-Row "соляр" @("sr","obj",$p.body) "объект: $($p.body)" "$($p.sign) $([math]::Round([double]($p.degree -replace ',','.'),1)) · дом соляра $($srOcc[$p.body]) · dign=$($srDignMap[$p.body])" "" }
  # SR houses occupancy
  $srByHouse = @{}; foreach ($b in $srOcc.Keys) { $hn = $srOcc[$b]; if (-not $srByHouse[$hn]) { $srByHouse[$hn]=@() }; $srByHouse[$hn]+=$b }
  foreach ($h in $srH) { $occ=$srByHouse[$h.house]; $auto= if($occ){""}else{"тихий (пусто)"}; $os= if($occ){($occ -join ",")}else{"—"}; Add-Row "соляр" @("sr","house",$h.house) "дом соляра $($h.house)" "$($h.sign) · занят: $os" $auto }
  foreach ($pt in $srPts) { if ($pt.point -in @("Ascendant","Midheaven")) { Add-Row "соляр" @("sr","angle",$pt.point) "угол соляра: $($pt.point)" "$($pt.sign) $([math]::Round([double]($pt.degree -replace ',','.'),1))" "" } }
  foreach ($a in $srA) { $ex= if($a.is_exact -eq "TRUE"){" ТОЧНО"}else{""}; Add-Row "соляр→натал" @("sr2n","$($a.from_object)-$($a.to_object)",$a.aspect) "$($a.from_object) $($a.aspect) $($a.to_object)" "орб $([math]::Round([double]($a.orb -replace ',','.'),2))°$ex" "" }
  foreach ($pr in $srProf) { Add-Row "профекция" @("profection","lord-of-year") "хозяин года" "возраст $($pr.age_years) · дом $($pr.profected_house) · $($pr.profected_sign) · lord=$($pr.lord_of_year)" "несущий?" }
  # SR declination layer (parallels/contraparallels + OOB) — first-class, same as natal, so it isn't lost.
  $srDeclPath = Join-Path $SolarReturnRunDir "07_return_declinations.csv"
  if (Test-Path $srDeclPath) { foreach ($d in (Import-CsvSafe $srDeclPath)) { if ($d.out_of_bounds -eq "TRUE") { Add-Row "соляр" @("sr","oob",$d.body) "OOB соляра: $($d.body)" "δ=$($d.declination_deg)" "флаг: вне границ" } } }
  $srDeclAspPath = Join-Path $SolarReturnRunDir "08_declination_aspects.csv"
  if (Test-Path $srDeclAspPath) { foreach ($a in (Import-CsvSafe $srDeclAspPath)) { Add-Row "соляр-склонение" @("sr","declasp","$($a.from_object)-$($a.to_object)",$a.type) "склон.аспект соляра: $($a.from_object) $($a.type) $($a.to_object)" "орб $($a.orb)°" "" } }
}

# ---------- PROGRESSIONS ----------
$progDelta = Import-CsvSafe (Resolve-ChartFile @("secondary_progressions_planet_deltas.csv","progressed_planet_deltas_2026.csv","03_progressed_planet_deltas.csv"))
$progAsp   = Import-CsvSafe (Resolve-ChartFile @("secondary_progressions_aspects.csv","progressed_to_natal_aspects_2026.csv","07_progressed_to_natal_aspects.csv"))
foreach ($p in $progDelta) {
  $changed = ($p.natal_sign -ne $p.progressed_sign)
  $auto = if ($changed) { "сменил знак — отметить" } else { "тихий (без смены знака)" }
  Add-Row "прогрессии" @("prog","obj",$p.body) "прогр. $($p.body)" "$($p.natal_sign) $($p.natal_degree) → $($p.progressed_sign) $($p.progressed_degree)" $auto
}
foreach ($a in $progAsp) { Add-Row "прогрессии→натал" @("prog2n","$($a.from_body)-$($a.to_body)",$a.aspect) "$($a.from_body) $($a.aspect) натал $($a.to_body)" "орб $([math]::Round([double]($a.orb -replace ',','.'),2))°" "" }

# ---------- DIRECTIONS (solar arc) ----------
$saP = Import-CsvSafe (Resolve-ChartFile @("solar_arc_planet_aspects.csv","solar_arc_2026_planet_aspects.csv","04_directed_to_natal_planets_aspects.csv"))
$saPt = Import-CsvSafe (Resolve-ChartFile @("solar_arc_point_aspects.csv","solar_arc_2026_point_aspects.csv","05_directed_to_natal_points_aspects.csv"))
foreach ($a in @($saP) + @($saPt)) {
  $st = "$($a.status)/$($a.tense)"
  Add-Row "дирекции→натал" @("dir2n","$($a.from_object)-$($a.to_object)",$a.aspect) "$($a.from_object) $($a.aspect) натал $($a.to_object)" "орб $([math]::Round([double]($a.orb -replace ',','.'),2))° · $st · перф $($a.perfection_year)" ""
}

# ---------- TRANSITS — TWO LAYERS, not a filter (balloon is a sin of PROSE, not registry size) ----
# Walk ALL transit passes (slow carriers + fast triggers); never drop a real pass from the registry —
# that would break completeness and hide chains/atypical couplings (a fast trigger closing a charged
# slow point). Split by speed onto the tech field, and AUTO-QUIET the trigger layer (like empty houses):
#   транзиты-несущие  (slow: jupiter…pluto) — the year's themes; judged like any factor.
#   транзиты-триггеры (fast: sun/moon/mercury/venus/mars) — daters; seeded тихий, promoted to несущий
#     ONLY by corroboration (lands on a carrier-charged point / is a chain link) — dynamic salience,
#     not a guess. Prose narrates only the promoted ones; the rest stay walked-but-quiet.
# Completeness here is SCOPE-RELATIVE (depends on orb/bodies/range) — the timeline summary declares it.
$slowTransit = @("jupiter", "saturn", "uranus", "neptune", "pluto")
if (-not [string]::IsNullOrWhiteSpace($TransitTimelineCsv) -and (Test-Path $TransitTimelineCsv)) {
  $tr = Import-CsvSafe $TransitTimelineCsv
  foreach ($t in $tr) {
    $isSlow = $slowTransit -contains ("$($t.transit_body)").ToLower()
    $tech = if ($isSlow) { "транзиты-несущие" } else { "транзиты-триггеры" }
    $auto = if ($isSlow) { "" } else { "тихий (триггер — поднять по корроборации)" }
    Add-Row $tech @("transit","$($t.transit_body)-$($t.natal_target)",$t.aspect) "$($t.transit_body) $($t.aspect) натал $($t.natal_target)" "точно $($t.exact_date) · орб $($t.min_orb_deg)° · окно $($t.window_start)…$($t.window_end)" $auto
  }
}

# ---------- ARTIFACT 1: factors.csv (machine, regenerated freely) ----------
if (-not (Test-Path $packDir)) { New-Item -ItemType Directory -Force -Path $packDir | Out-Null }
$rows | Select-Object id, tech, factor, data, auto | Export-Csv -Path $FactorsPath -NoTypeInformation -Encoding UTF8

# ---------- ARTIFACT 2: dispositions.csv (semantic, model-owned — APPEND-ONLY, never rewrite existing) ----------
$existingDisp = Import-CsvSafe $DispositionsPath
$existingIds = @{}; foreach ($r in $existingDisp) { $existingIds[$r.factor_id] = $r }
$newRows = New-Object System.Collections.Generic.List[object]
foreach ($r in $rows) {
  if (-not $existingIds.ContainsKey($r.id)) {
    $sal = if ($r.auto -like "тихий*") { "тихий" } else { "" }   # auto-quiet (empty houses) seeded; rest blank for judgement
    $newRows.Add([pscustomobject]@{ factor_id = $r.id; salience = $sal; valence_resolved = ""; basis = ""; note = "" })
  }
}
if (-not (Test-Path $DispositionsPath)) {
  $newRows | Export-Csv -Path $DispositionsPath -NoTypeInformation -Encoding UTF8
} elseif ($newRows.Count) {
  # genuine append: existing rows (with their hand edits) are never read-rewritten
  $lines = $newRows | ConvertTo-Csv -NoTypeInformation | Select-Object -Skip 1
  Add-Content -Path $DispositionsPath -Value $lines -Encoding UTF8
}

# ---------- ARTIFACT 2b: versions.csv (version log — model-owned, append-only; script only seeds the header) ----------
# status ∈ {taken, parked, dropped}. The script does NOT enumerate poles (the fan is model judgment, read from the
# operator tables, not the data) — it only guarantees the file exists so the model has a keyed place to log branches.
if (-not (Test-Path $VersionsPath)) {
  "factor_id,pole,status,basis,note" | Set-Content -Path $VersionsPath -Encoding UTF8
}

# ---------- ARTIFACT 3: coverage_report.md (verifier — read-only JOIN + structural checks) ----------
$dispNow = Import-CsvSafe $DispositionsPath
$versNow = Import-CsvSafe $VersionsPath
$dispMap = @{}; foreach ($r in $dispNow) { $dispMap[$r.factor_id] = $r }
$factorIds = @{}; foreach ($r in $rows) { $factorIds[$r.id] = $true }

$holes = @(); $orphans = @(); $dangling = @(); $unsupported = @()
# completeness: every factor has a non-blank salience
foreach ($r in $rows) {
  $d = $dispMap[$r.id]
  if ($null -eq $d -or [string]::IsNullOrWhiteSpace($d.salience)) { $holes += $r.id }
}
# orphans: disposition whose factor vanished
foreach ($r in $dispNow) { if (-not $factorIds.ContainsKey($r.factor_id)) { $orphans += $r.factor_id } }
# basis integrity + pole⇒basis
foreach ($r in $dispNow) {
  $basisIds = @()
  if (-not [string]::IsNullOrWhiteSpace($r.basis)) { $basisIds = @($r.basis -split '\s*;\s*' | Where-Object { $_ }) }
  foreach ($bid in $basisIds) { if (-not $factorIds.ContainsKey($bid)) { $dangling += "$($r.factor_id) → $bid" } }
  $resolved = ("$($r.valence_resolved)".Trim().ToLower() -in @("yes","да","true","1"))
  if ($resolved -and $basisIds.Count -eq 0) { $unsupported += $r.factor_id }
}

# ---- VERSION LOG checks (gate 3 — no silent branch-collapse) ----
$verOrphans = @(); $verDropNoBasis = @(); $verDangling = @(); $resolvedNoVersion = @()
$versByFactor = @{}
foreach ($v in $versNow) {
  if (-not $factorIds.ContainsKey($v.factor_id)) { $verOrphans += $v.factor_id; continue }
  $st = "$($v.status)".Trim().ToLower()
  if (-not [string]::IsNullOrWhiteSpace($st)) {
    if (-not $versByFactor.ContainsKey($v.factor_id)) { $versByFactor[$v.factor_id] = 0 }
    $versByFactor[$v.factor_id]++
  }
  $vbasis = @(); if (-not [string]::IsNullOrWhiteSpace($v.basis)) { $vbasis = @($v.basis -split '\s*;\s*' | Where-Object { $_ }) }
  foreach ($bid in $vbasis) { if (-not $factorIds.ContainsKey($bid)) { $verDangling += "$($v.factor_id)/$($v.pole) → $bid" } }
  if ($st -eq "dropped" -and $vbasis.Count -eq 0) { $verDropNoBasis += "$($v.factor_id)/$($v.pole)" }
}
# a collapsed pole must show its branch work: valence_resolved=yes ⇒ ≥1 non-blank version row for that factor
foreach ($r in $dispNow) {
  $resolved = ("$($r.valence_resolved)".Trim().ToLower() -in @("yes","да","true","1"))
  if ($resolved -and $factorIds.ContainsKey($r.factor_id) -and -not $versByFactor.ContainsKey($r.factor_id)) {
    $resolvedNoVersion += $r.factor_id
  }
}

$techOrder = @("натал","натал-производное","соляр","соляр→натал","профекция","прогрессии","прогрессии→натал","дирекции→натал","транзиты-несущие","транзиты-триггеры")
$total = $rows.Count
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Coverage report — $ChartId")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("> Read-only. Generated by build_coverage_ledger.ps1 — JOIN of coverage_factors.csv × coverage_dispositions.csv by factor_id.")
[void]$sb.AppendLine("> Edit dispositions in **coverage_dispositions.csv** (the model owns it); re-run to refresh this report.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Acceptance checks (gate 2 — structural)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Check | Count | Verdict |")
[void]$sb.AppendLine("|---|---|---|")
[void]$sb.AppendLine("| Completeness — factors without a salience (holes / «лысый соляр») | $($holes.Count) | $(if($holes.Count){'❌ FILL'}else{'✅'}) |")
[void]$sb.AppendLine("| Orphans — dispositions whose factor vanished | $($orphans.Count) | $(if($orphans.Count){'⚠ review'}else{'✅'}) |")
[void]$sb.AppendLine("| Basis integrity — cited factor_id not in data (anti-fabricated-basis) | $($dangling.Count) | $(if($dangling.Count){'❌ FIX'}else{'✅'}) |")
[void]$sb.AppendLine("| Pole resolved without basis (no «nice» collapse) | $($unsupported.Count) | $(if($unsupported.Count){'❌ JUSTIFY'}else{'✅'}) |")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("> Structural net = completeness + basis integrity + pole⇒basis. NOTE: none of these catch *selective demotion*")
[void]$sb.AppendLine("> (a real factor quietly made тихий to dodge it) — that stays the model's burden, not the script's.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Acceptance checks (gate 3 — version log: no silent branch-collapse)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Check | Count | Verdict |")
[void]$sb.AppendLine("|---|---|---|")
[void]$sb.AppendLine("| Resolved pole without a logged version (silent collapse) | $($resolvedNoVersion.Count) | $(if($resolvedNoVersion.Count){'❌ LOG'}else{'✅'}) |")
[void]$sb.AppendLine("| Dropped version without basis | $($verDropNoBasis.Count) | $(if($verDropNoBasis.Count){'❌ JUSTIFY'}else{'✅'}) |")
[void]$sb.AppendLine("| Version basis cites a factor not in data | $($verDangling.Count) | $(if($verDangling.Count){'❌ FIX'}else{'✅'}) |")
[void]$sb.AppendLine("| Version rows whose factor vanished | $($verOrphans.Count) | $(if($verOrphans.Count){'⚠ review'}else{'✅'}) |")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("> Catches the visible part: a resolved pole must show logged branch work, a dropped branch must cite a basis.")
[void]$sb.AppendLine("> It still cannot catch a pole that NEVER surfaced — read the fan from the operator tables, not from fluency.")
[void]$sb.AppendLine("")
if ($holes.Count)       { [void]$sb.AppendLine("**Holes:** $([string]::Join(', ', $holes))"); [void]$sb.AppendLine("") }
if ($orphans.Count)     { [void]$sb.AppendLine("**Orphans:** $([string]::Join(', ', $orphans))"); [void]$sb.AppendLine("") }
if ($dangling.Count)    { [void]$sb.AppendLine("**Dangling basis:** $([string]::Join('; ', $dangling))"); [void]$sb.AppendLine("") }
if ($unsupported.Count) { [void]$sb.AppendLine("**Pole resolved, basis empty:** $([string]::Join(', ', $unsupported))"); [void]$sb.AppendLine("") }
if ($resolvedNoVersion.Count) { [void]$sb.AppendLine("**Resolved without version log:** $([string]::Join(', ', $resolvedNoVersion))"); [void]$sb.AppendLine("") }
if ($verDropNoBasis.Count)    { [void]$sb.AppendLine("**Dropped without basis:** $([string]::Join(', ', $verDropNoBasis))"); [void]$sb.AppendLine("") }
if ($verDangling.Count)       { [void]$sb.AppendLine("**Version dangling basis:** $([string]::Join('; ', $verDangling))"); [void]$sb.AppendLine("") }
if ($verOrphans.Count)        { [void]$sb.AppendLine("**Version orphans:** $([string]::Join(', ', $verOrphans))"); [void]$sb.AppendLine("") }

# Tally by salience
$salTally = @{}; foreach ($r in $dispNow) { if ($factorIds.ContainsKey($r.factor_id)) { $k = if([string]::IsNullOrWhiteSpace($r.salience)){"(пусто)"}else{$r.salience}; $salTally[$k] = 1 + [int]$salTally[$k] } }
[void]$sb.AppendLine("## Tally by salience")
[void]$sb.AppendLine("")
foreach ($k in ($salTally.Keys | Sort-Object)) { [void]$sb.AppendLine("- $k — $($salTally[$k])") }
[void]$sb.AppendLine("")

# Full joined ledger (human-readable view)
foreach ($tech in $techOrder) {
  $g = $rows | Where-Object { $_.tech -eq $tech }
  if (-not $g) { continue }
  [void]$sb.AppendLine("## $tech ($($g.Count))")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("| factor_id | Фактор | Данные | Авто | Вес | Полюс | Основание | Примечание |")
  [void]$sb.AppendLine("|---|---|---|---|---|---|---|---|")
  foreach ($r in $g) {
    $d = $dispMap[$r.id]
    $sal = if ($d) { $d.salience } else { "" }
    $vr  = if ($d) { $d.valence_resolved } else { "" }
    $bs  = if ($d) { $d.basis } else { "" }
    $nt  = if ($d) { $d.note } else { "" }
    [void]$sb.AppendLine("| $($r.id) | $($r.factor) | $($r.data) | $($r.auto) | $sal | $vr | $bs | $nt |")
  }
  [void]$sb.AppendLine("")
}
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("FACTORS_TOTAL=$total")
[void]$sb.AppendLine("HOLES=$($holes.Count)")
[void]$sb.AppendLine("ORPHANS=$($orphans.Count)")
[void]$sb.AppendLine("DANGLING_BASIS=$($dangling.Count)")
[void]$sb.AppendLine("UNSUPPORTED_POLE=$($unsupported.Count)")
[void]$sb.AppendLine("RESOLVED_NO_VERSION=$($resolvedNoVersion.Count)")
[void]$sb.AppendLine("VERSION_DROP_NO_BASIS=$($verDropNoBasis.Count)")
[void]$sb.AppendLine("VERSION_DANGLING_BASIS=$($verDangling.Count)")
[void]$sb.AppendLine("VERSION_ORPHANS=$($verOrphans.Count)")

Set-Content -Path $ReportPath -Value $sb.ToString() -Encoding UTF8

Write-Host "factors      → $FactorsPath  ($total factors)"
Write-Host "dispositions → $DispositionsPath  (+$($newRows.Count) new keys appended)"
Write-Host "versions     → $VersionsPath"
Write-Host "report       → $ReportPath"
Write-Host "HOLES=$($holes.Count)  ORPHANS=$($orphans.Count)  DANGLING_BASIS=$($dangling.Count)  UNSUPPORTED_POLE=$($unsupported.Count)"
Write-Host "RESOLVED_NO_VERSION=$($resolvedNoVersion.Count)  VERSION_DROP_NO_BASIS=$($verDropNoBasis.Count)  VERSION_DANGLING_BASIS=$($verDangling.Count)  VERSION_ORPHANS=$($verOrphans.Count)"
