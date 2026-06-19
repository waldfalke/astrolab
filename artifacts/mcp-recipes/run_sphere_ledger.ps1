param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$ChartsRoot = "",
  [string]$CoverageFactorsCsv = "",   # default: <chart>/packs/coverage_factors.csv
  [string]$SolarReturnRunDir = "",    # optional: lets sr.obj.* route by the natal house the SR planet falls in
  [string]$OutDir = ""                # default: <chart>/packs
)

# ============================================================================================
# Sphere ledger — the DOMAIN-axis projection of coverage, twin to carrier_windows (the TIME axis).
#
#   carrier_windows cuts factors by WHEN (dated transits -> chapters).
#   sphere_ledger  cuts the SAME factors by WHERE-IN-LIFE (house/ruler/significator -> spheres).
#
# WHY (blind run 2026-06-19, NKS astrolab #80/#81/#82): hand-routing factor->sphere DRIFTS —
#   spheres got inverted out of windows, a year-ruler read as 3 contradictory roles, empty spheres
#   padded with Barnum. The ROUTING (longitude in house · planet rules house · natural significator)
#   is MECHANICAL and must not be left to the model. So this recipe SUGGESTS sphere membership
#   (deterministic candidates) for every factor + flags which spheres are actually CHARGED; the
#   model still owns the *meaning* (canon: "membership is a disposition, not a machine fact" — we
#   propose candidates, we do not dictate the reading). Completeness becomes structural: no factor
#   is silently homeless, and an empty sphere is VISIBLE ("тихий год") instead of padded.
#
# Sourcing: needs no new ephemeris — pure re-sort of already-computed natal longitudes + house
#   cusps + (optional) SR longitudes. Rulership is TRADITIONAL (pinned, like dispositors/profection;
#   NOT modern — H7 Pisces -> Jupiter, not Neptune).
# ============================================================================================

$ErrorActionPreference = "Stop"
$scriptId = "run_sphere_ledger"; $scriptVersion = "0.1.0"

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) { $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts" }
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)
$chartDir = Join-Path $ChartsRoot $ChartId
$outputsDir = Join-Path $chartDir "outputs"
if ([string]::IsNullOrWhiteSpace($OutDir)) { $OutDir = Join-Path $chartDir "packs" }
if ([string]::IsNullOrWhiteSpace($CoverageFactorsCsv)) { $CoverageFactorsCsv = Join-Path $OutDir "coverage_factors.csv" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Import-CsvSafe { param([string]$Path) if (-not (Test-Path $Path)) { return @() } return @(Import-Csv -Path $Path) }
function ParseNum { param($v) [double](("$v") -replace ',', '.') }

# --- traditional sign ruler (pinned; no outers) ---------------------------------------------
$SignRulerTrad = @{
  "Aries"="mars"; "Taurus"="venus"; "Gemini"="mercury"; "Cancer"="moon"; "Leo"="sun"; "Virgo"="mercury"
  "Libra"="venus"; "Scorpio"="mars"; "Sagittarius"="jupiter"; "Capricorn"="saturn"; "Aquarius"="saturn"; "Pisces"="jupiter"
}

# --- sphere -> houses (many-to-many on purpose; all 12 houses covered) -----------------------
#   self  H1,H6   mind H3,H9   love H5,H7,H8   work H10,H6   money H2,H8   home H4   meaning H9,H11,H12
$SphereHouses = [ordered]@{
  "self"    = @(1,6)
  "mind"    = @(3,9)
  "love"    = @(5,7,8)
  "work"    = @(10,6)
  "money"   = @(2,8)
  "home"    = @(4)
  "meaning" = @(9,11,12)
}
$SphereTitle = @{
  "self"="Я · тело · витальность"; "mind"="Ум · слово · связи · учёба"; "love"="Близость · партнёрство"
  "work"="Дело · призвание · карьера"; "money"="Деньги · ресурс"; "home"="Дом · семья · корни"
  "meaning"="Смысл · мировоззрение · рост"
}
# house -> spheres (inverted)
$HouseSpheres = @{}
foreach ($s in $SphereHouses.Keys) { foreach ($h in $SphereHouses[$s]) { if (-not $HouseSpheres[$h]) { $HouseSpheres[$h] = @() }; $HouseSpheres[$h] += $s } }

# --- natural significators (SOFT secondary signal — tagged via=significator) -----------------
$Significator = @{
  sun=@("self","work"); moon=@("home","self"); mercury=@("mind"); venus=@("love","money")
  mars=@("self","work"); jupiter=@("meaning","money"); saturn=@("work"); uranus=@("mind")
  neptune=@("meaning","home"); pluto=@("love","money")
}

# --- natal geometry: planet -> occupied house, planet -> ruled houses ------------------------
$cusps = Import-CsvSafe (Join-Path $outputsDir "houses_placidus.csv")
if ($cusps.Count -lt 12) { throw "need 12 house cusps (houses_placidus.csv) — got $($cusps.Count)" }
$cuspLon = @{}; foreach ($c in $cusps) { $cuspLon[[int]$c.house] = ParseNum $c.longitude }

function House-Of-Longitude { param([double]$Lon)
  for ($h = 1; $h -le 12; $h++) {
    $c1 = $cuspLon[$h]; $c2 = $cuspLon[($h % 12) + 1]
    $inb = if ($c1 -lt $c2) { ($Lon -ge $c1 -and $Lon -lt $c2) } else { ($Lon -ge $c1 -or $Lon -lt $c2) }
    if ($inb) { return $h }
  }
  return 0
}

# planet -> ruled houses (sign on each cusp -> its traditional ruler)
$ruledHouses = @{}
foreach ($c in $cusps) {
  $r = $SignRulerTrad[[string]$c.sign]
  if ($r) { if (-not $ruledHouses[$r]) { $ruledHouses[$r] = @() }; $ruledHouses[$r] += [int]$c.house }
}

# planet -> occupied natal house (natal planets + nodes)
$occHouse = @{}
foreach ($r in (Import-CsvSafe (Join-Path $outputsDir "natal_longitudes.csv"))) {
  $occHouse[([string]$r.body).ToLowerInvariant()] = House-Of-Longitude (ParseNum $r.longitude)
}
foreach ($r in (Import-CsvSafe (Join-Path $outputsDir "additional_points.csv"))) {
  $nm = ([string]$r.point).ToLowerInvariant() -replace '\s+','-'
  $occHouse[$nm] = House-Of-Longitude (ParseNum $r.longitude)
}

# SR planet -> natal house it falls in (optional, only if SR run given)
$srFallHouse = @{}
if (-not [string]::IsNullOrWhiteSpace($SolarReturnRunDir)) {
  foreach ($r in (Import-CsvSafe (Join-Path $SolarReturnRunDir "02_return_planets.csv"))) {
    $srFallHouse[([string]$r.body).ToLowerInvariant()] = House-Of-Longitude (ParseNum $r.longitude)
  }
}

# --- map a natal planet/point/angle to its candidate spheres --------------------------------
$Angles = @{ "ascendant"=1; "asc"=1; "midheaven"=10; "mc"=10; "ic"=4; "descendant"=7; "dsc"=7; "armc"=10 }
function Spheres-For-Body { param([string]$Body, [bool]$AsSR = $false)
  $b = $Body.ToLowerInvariant()
  $houses = @()
  if ($AsSR -and $srFallHouse.ContainsKey($b)) { $houses += $srFallHouse[$b] }   # where the SR body lands
  if ($occHouse.ContainsKey($b)) { $houses += $occHouse[$b] }                    # natal occupancy
  if ($ruledHouses.ContainsKey($b)) { $houses += $ruledHouses[$b] }              # houses it rules
  $sph = @(); $via = @()
  foreach ($h in ($houses | Select-Object -Unique)) { if ($HouseSpheres[$h]) { $sph += $HouseSpheres[$h]; $via += "h$h" } }
  if ($Significator.ContainsKey($b)) { $sph += $Significator[$b]; $via += "sig" }
  return @{ spheres = @($sph | Select-Object -Unique); via = @($via | Select-Object -Unique) }
}

# extract the natal anchors named in a factor_id, then route ---------------------------------
$script:_sph = @(); $script:_via = @()
function Add-Body { param([string]$Body, [bool]$Sr = $false)
  $r = Spheres-For-Body -Body $Body -AsSR:$Sr
  $script:_sph += $r.spheres; $script:_via += $r.via
}
# Light routing for a PAIR factor's NATAL endpoint: occupancy + significator only — NOT ruled houses.
# (Ruled houses are right for "planet as a theme" obj/point factors, but on a pair they explode the
# cartesian union and every sphere reads charged, killing the тихий-год signal.)
function Add-Body-Light { param([string]$Body)
  $b = $Body.ToLowerInvariant()
  if ($Angles.ContainsKey($b)) { $h = $Angles[$b]; if ($HouseSpheres[$h]) { $script:_sph += $HouseSpheres[$h]; $script:_via += "ang$h" }; return }
  if ($occHouse.ContainsKey($b) -and $HouseSpheres[$occHouse[$b]]) { $script:_sph += $HouseSpheres[$occHouse[$b]]; $script:_via += "h$($occHouse[$b])" }
  if ($Significator.ContainsKey($b)) { $script:_sph += $Significator[$b]; $script:_via += "sig" }
}
function Route-Factor { param([string]$Id)
  $parts = $Id -split '\.'
  $script:_sph = @(); $script:_via = @()
  switch -regex ($Id) {
    '^natal\.house\.(\d+)' { $h = [int]$Matches[1]; if ($HouseSpheres[$h]) { $script:_sph += $HouseSpheres[$h]; $script:_via += "h$h" }; break }
    '^sr\.house\.(\d+)'    { $h = [int]$Matches[1]; if ($HouseSpheres[$h]) { $script:_sph += $HouseSpheres[$h]; $script:_via += "srH$h" }; break }
    '^(natal|sr)\.angle\.(\w+)' { $a = $Matches[2]; if ($Angles[$a]) { $h = $Angles[$a]; if ($HouseSpheres[$h]) { $script:_sph += $HouseSpheres[$h]; $script:_via += "ang$h" } }; break }
    '^natal\.obj\.(\w+)'   { Add-Body $Matches[1] $false; break }
    '^sr\.obj\.(\w+)'      { Add-Body $Matches[1] $true;  break }
    '^prog\.obj\.(\w+)'    { Add-Body $Matches[1] $false; break }
    '^(natal|sr)\.oob\.(\w+)' { Add-Body $Matches[2] ($Matches[1] -eq 'sr'); break }
    '^(natal|sr)\.point\.([\w-]+)' { Add-Body $Matches[2] ($Matches[1] -eq 'sr'); break }
    # pair factors (sr2n / transit / dir2n / prog2n / declasp / natal.asp): route by the NATAL endpoint
    # (where the year lands), light. detail = everything between tech and the trailing aspect.
    default {
      $detail = if ($parts.Count -ge 3) { ($parts[1..($parts.Count - 2)] -join '-') } else { "" }
      $natalToks = @()
      if ($detail -match 'natal-') {
        # explicit natal markers (sr2n / dir2n / sr.declasp): the receiving end(s)
        foreach ($m in [regex]::Matches($detail, 'natal-([a-z]+(?:-node)?)')) { $natalToks += $m.Groups[1].Value }
      } elseif ($parts[0] -eq 'natal') {
        # natal.asp / natal.declasp — both ends are natal
        foreach ($tok in (($detail -replace '^(asp|declasp)-?', '') -split '-')) { if ($tok -and $tok -notin @('natal')) { $natalToks += $tok } }
      } else {
        # transit.TBODY-NTARGET, prog2n.PROG-NATAL, sr-internal: the LAST planet token is the natal/received end
        $toks = @($detail -split '-' | Where-Object { $_ -and $_ -notin @('return','directed','transit','progressed','natal','node') })
        $toks = @($toks | ForEach-Object { $_ -replace '^(north|south)$', '$1-node' })
        if ($toks.Count) { $natalToks += $toks[-1] }
      }
      foreach ($t in ($natalToks | Select-Object -Unique)) {
        $tt = $t.Trim().ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($tt) -or $tt -in @("sirius","galactic","center","chiron")) { continue }
        Add-Body-Light $tt
      }
    }
  }
  return @{ spheres = @($script:_sph | Select-Object -Unique | Where-Object { $_ }); via = (@($script:_via | Select-Object -Unique) -join '+') }
}

# --- run ------------------------------------------------------------------------------------
$factors = Import-CsvSafe $CoverageFactorsCsv
if ($factors.Count -eq 0) { throw "no coverage factors at $CoverageFactorsCsv (run build_coverage_ledger first)" }

$routeRows = @()
$sphereCount = @{}; foreach ($s in $SphereHouses.Keys) { $sphereCount[$s] = 0 }
$homeless = 0
foreach ($f in $factors) {
  $res = Route-Factor $f.id
  $sphereStr = ($res.spheres -join ';')
  if ($res.spheres.Count -eq 0) { $homeless++ } else { foreach ($s in $res.spheres) { if ($null -ne $sphereCount[$s]) { $sphereCount[$s]++ } } }
  $routeRows += [pscustomobject]@{ factor_id = $f.id; tech = $f.tech; spheres = $sphereStr; via = $res.via; factor = $f.factor }
}

$routePath = Join-Path $OutDir "sphere_routing.csv"
$routeRows | Export-Csv -Path $routePath -NoTypeInformation -Encoding UTF8

# summary: one row per sphere, charged flag, honest empty note
$sumRows = @()
foreach ($s in $SphereHouses.Keys) {
  $n = $sphereCount[$s]
  $charged = $n -gt 0
  $note = if (-not $charged) { "ТИХИЙ — ни один фактор не роутится сюда; честно скажи «спокойный год по этой сфере», не заливай" } else { "" }
  $sumRows += [pscustomobject]@{
    sphere = $s; title = $SphereTitle[$s]; houses = ($SphereHouses[$s] -join ',')
    factor_count = $n; charged = $charged; note = $note
  }
}
$sumPath = Join-Path $OutDir "sphere_summary.csv"
$sumRows | Export-Csv -Path $sumPath -NoTypeInformation -Encoding UTF8

Write-Host "sphere ledger  $routePath"
Write-Host "               $sumPath"
Write-Host ("  factors routed: {0}  · homeless: {1}  · rulership=traditional" -f $factors.Count, $homeless)
Write-Host "  charged spheres:"
foreach ($r in ($sumRows | Sort-Object factor_count -Descending)) {
  $flag = if ($r.charged) { "" } else { "  ← ТИХИЙ" }
  Write-Host ("    {0,-9} {1,3} factors{2}" -f $r.sphere, $r.factor_count, $flag)
}
