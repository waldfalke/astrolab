param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [string]$ChartsRoot = "",
  [string]$LongitudesCsv = "",   # optional standalone: columns body,longitude (0..360)
  [string]$AscLongitude = "",    # optional standalone: ASC ecliptic longitude (0..360)
  [string]$OutputCsv = "",
  [string]$OutputBase = ""       # provenance run-dir base (default artifacts/results)
)

# ============================================================================================
# Phase vectors (Zakharian model) — built FROM THE OPERATOR, not from a lookup table.
#
# THE OPERATOR (one, fractal):  Φ(point, anchor) = ((point_idx − anchor_idx) mod 12) + 1
#   The whole apparatus is this single 12-cycle counted from a reference point, applied across
#   {frame: domicile→Z, ASC→H} × {scale: 30° sign → Z/H, 2.5° micro → z/h} + dispositor recursion (D).
#
#   P ⟨ Z.z : H.h : D ⟩
#     Z = sign phase     — ((sign_idx − domicile_idx) mod 12)+1   [VERIFIED vs book Table 2.2]
#     z = micro in sign  — floor(deg_in_sign / 2.5)+1             [first-principles, anumita]
#     H = house phase    — equal-house from ASC: floor(off/30)+1  [first-principles; H verified-by-analogy]
#     h = micro in house — floor((off mod 30)/2.5)+1              [first-principles, anumita]
#     D = dispositor Z   — Z of the sign-ruler, from ITS domicile [first-principles recursion]
#
# EPISTEMIC TIERS (permanent — sourcing ceiling: books give only Z; z/h were seminars + lost software):
#   Z, H  = grounded (Z literally reproduces book Table 2.2; H is the same operator on the ASC frame).
#   z,h,D = derived from the same operator + author-attested (seminars), NOT source-verifiable. Marked anumita.
#
# SELF-TEST: the literal book Table 2.2 is embedded as an ORACLE. The operator must reproduce every
#   cell (10 bodies + dual Mercury/Venus cycles). Any mismatch → the recipe THROWS. The table is the
#   product; we store the operator and use the table only to verify it (anti-balloon discipline).
#
# Rulership axiom: MODERN (outers get domiciles; phase-ruler cycle 1 Mars…12 Neptune needs it).
#   This is a declared input, and it differs from the TRADITIONAL scheme used in profections.
# Output is internal to the working reading + coverage. Zakharian is copyright — NEVER the client report.
# ============================================================================================

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\lib\mcp_helpers.ps1"
$scriptId = "run_phase_vectors"; $scriptVersion = "0.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()

# --- sign / rulership constants (Aries=1 … Pisces=12) ---------------------------------------
$SignNames = @("Овен","Телец","Близнецы","Рак","Лев","Дева","Весы","Скорпион","Стрелец","Козерог","Водолей","Рыбы")

# Modern domicile index per body. Mercury & Venus are DUAL (two homes → two Z).
$Domicile = [ordered]@{
  sun=@(5); moon=@(4); mercury=@(3,6); venus=@(2,7); mars=@(1)
  jupiter=@(9); saturn=@(10); uranus=@(11); neptune=@(12); pluto=@(8)
}
# Modern ruler of each sign (1..12) — for the dispositor recursion.
$SignRuler = @("mars","venus","mercury","moon","sun","mercury","venus","pluto","jupiter","saturn","uranus","neptune")

# ZAKHARIAN dignity (verified table) lives in the shared lib (mcp_helpers.ps1, dot-sourced above) —
# single source, used by both this recipe and the coverage ledger: Get-ZakharianDignity, Resolve-SignIndex.

# The 12 archetype alphabet (stored ONCE, reused on every axis). Phase ruler = modern ruler of Nth sign.
$PhaseName  = @("Импульс","Ресурс","Связь","База","Творчество","Служение","Зеркало","Трансформация","Стратегия","Результат","Оптимизация","Архив")
$PhaseRuler = @("Марс","Венера","Меркурий","Луна","Солнце","Меркурий","Венера","Плутон","Юпитер","Сатурн","Уран","Нептун")

# The operator.
function Get-Phase { param([int]$PointIdx, [int]$AnchorIdx)
  return (((($PointIdx - $AnchorIdx) % 12) + 12) % 12) + 1
}
function Get-SignIdx { param([double]$Lon) return [int][math]::Floor((($Lon % 360) + 360) % 360 / 30.0) + 1 }
function Get-DegInSign { param([double]$Lon) return ((($Lon % 360) + 360) % 360) - ([math]::Floor((($Lon % 360) + 360) % 360 / 30.0) * 30.0) }
function Get-Micro { param([double]$DegIn) $m = [int][math]::Floor($DegIn / 2.5) + 1; if ($m -gt 12) { $m = 12 }; if ($m -lt 1) { $m = 1 }; return $m }

# --- SELF-TEST: embed book Table 2.2 (the oracle) and assert the operator reproduces it -------
# Each row: label → @(domicile_idx, 12 phase numbers for signs Aries..Pisces) verbatim from the book.
$Table22 = [ordered]@{
  "sun"          = @(5,  @(9,10,11,12,1,2,3,4,5,6,7,8))
  "moon"         = @(4,  @(10,11,12,1,2,3,4,5,6,7,8,9))
  "mercury_gem"  = @(3,  @(11,12,1,2,3,4,5,6,7,8,9,10))
  "mercury_vir"  = @(6,  @(8,9,10,11,12,1,2,3,4,5,6,7))
  "venus_tau"    = @(2,  @(12,1,2,3,4,5,6,7,8,9,10,11))
  "venus_lib"    = @(7,  @(7,8,9,10,11,12,1,2,3,4,5,6))
  "mars"         = @(1,  @(1,2,3,4,5,6,7,8,9,10,11,12))
  "jupiter"      = @(9,  @(5,6,7,8,9,10,11,12,1,2,3,4))
  "saturn"       = @(10, @(4,5,6,7,8,9,10,11,12,1,2,3))
  "uranus"       = @(11, @(3,4,5,6,7,8,9,10,11,12,1,2))
  "neptune"      = @(12, @(2,3,4,5,6,7,8,9,10,11,12,1))
  "pluto"        = @(8,  @(6,7,8,9,10,11,12,1,2,3,4,5))
}
$mismatch = @()
foreach ($k in $Table22.Keys) {
  $dom = [int]$Table22[$k][0]
  $row = $Table22[$k][1]
  for ($s = 1; $s -le 12; $s++) {
    $got = Get-Phase -PointIdx $s -AnchorIdx $dom
    $exp = [int]$row[$s-1]
    if ($got -ne $exp) { $mismatch += "$k sign=$s expected=$exp operator=$got" }
  }
}
if ($mismatch.Count -gt 0) {
  throw "SELF-TEST FAILED — operator disagrees with book Table 2.2:`n" + ($mismatch -join "`n")
}
Write-Host "Self-test PASS: operator reproduces book Table 2.2 (144/144 cells, 10 bodies + dual cycles)."

# --- resolve chart data ----------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ChartsRoot)) { $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts" }
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)
$chartDir = Join-Path $ChartsRoot $ChartId
$outputsDir = Join-Path $chartDir "outputs"

function Resolve-One { param([string[]]$Names)
  foreach ($n in $Names) { $p = Join-Path $outputsDir $n; if (Test-Path $p) { return $p } }
  return $null
}
function Import-CsvSafe { param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) { return @() }
  return @(Import-Csv -Path $Path)
}
function ParseNum { param($v) return [double]($("$v") -replace ',', '.') }

# Longitudes: standalone CSV overrides; else read from the chart project.
$lonMap = [ordered]@{}
if (-not [string]::IsNullOrWhiteSpace($LongitudesCsv)) {
  foreach ($r in (Import-CsvSafe $LongitudesCsv)) { $lonMap[("$($r.body)").ToLower()] = ParseNum $r.longitude }
} else {
  $lonRows = Import-CsvSafe (Resolve-One @("natal_longitudes.csv","02_primary_longitudes.csv","06_backup_longitudes.csv"))
  foreach ($r in $lonRows) { if ($r.PSObject.Properties['longitude']) { $lonMap[("$($r.body)").ToLower()] = ParseNum $r.longitude } }
}
if ($lonMap.Count -eq 0) { throw "No longitudes found (need natal_longitudes.csv in $outputsDir or -LongitudesCsv)." }

# ASC longitude: standalone param; else house-1 cusp (= ASC) from Placidus cusps.
$ascLon = $null
if (-not [string]::IsNullOrWhiteSpace($AscLongitude)) { $ascLon = ParseNum $AscLongitude }
else {
  $houses = Import-CsvSafe (Resolve-One @("houses_placidus.csv","02_houses_placidus.csv"))
  $h1 = $houses | Where-Object { "$($_.house)" -eq "1" } | Select-Object -First 1
  if ($h1 -and $h1.PSObject.Properties['longitude']) { $ascLon = ParseNum $h1.longitude }
}
if ($null -eq $ascLon) { throw "No ASC longitude (need houses_placidus.csv house 1 cusp or -AscLongitude)." }

# --- compute the vector for each body --------------------------------------------------------
$bodies = @("sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto")
$rows = @()
foreach ($b in $bodies) {
  if (-not $lonMap.Contains($b)) { continue }
  $lon = [double]$lonMap[$b]
  $sIdx = Get-SignIdx $lon
  $degIn = Get-DegInSign $lon
  $z = Get-Micro $degIn

  # Z (dual for Mercury/Venus): one phase per domicile.
  $zList = @(); foreach ($dom in $Domicile[$b]) { $zList += (Get-Phase -PointIdx $sIdx -AnchorIdx $dom) }

  # H / h — equal-house from ASC (the operator on the ASC frame).
  # NB: PowerShell variable names are CASE-INSENSITIVE — $H and $h are the SAME variable, so the
  # house phase and its microphase must use distinct names ($Hh / $hm), not $H / $h.
  $off = ((($lon - $ascLon) % 360) + 360) % 360
  $Hh = [int][math]::Floor($off / 30.0) + 1
  $degInHouse = $off - ([math]::Floor($off / 30.0) * 30.0)
  $hm = Get-Micro $degInHouse

  # D — dispositor's sign-phase (recursion). Ruler of the planet's sign, then that ruler's Z from
  # its nearest domicile (dual rulers resolved by nearest home to the ruler's current sign).
  $ruler = $SignRuler[$sIdx - 1]
  $D = ""; $rulerSignTxt = ""
  if ($lonMap.Contains($ruler)) {
    $rLon = [double]$lonMap[$ruler]; $rSign = Get-SignIdx $rLon; $rulerSignTxt = $SignNames[$rSign-1]
    $best = $null
    foreach ($rdom in $Domicile[$ruler]) {
      $cand = Get-Phase -PointIdx $rSign -AnchorIdx $rdom
      # nearest home = smallest forward distance from domicile to ruler's sign
      $dist = (((($rSign - $rdom) % 12) + 12) % 12)
      if ($null -eq $best -or $dist -lt $best.dist) { $best = @{ phase = $cand; dist = $dist } }
    }
    $D = $best.phase
  }

  $Dname = ""; if ($D -ne "") { $Dname = $PhaseName[[int]$D-1] }
  # Zakharian dignity (authoritative for the phase model — NOT the engine's scheme).
  $dignity = Get-ZakharianDignity -Body $b -Sign $sIdx
  # Two rulers, DIRECT names (no hiding inside "dispositor"): by position (sign ruler = material) and
  # by phase (phase ruler = motivation). Phase ruler is dual for Mercury/Venus (one per Z).
  $rulerByPosition = $ruler
  $rulerByPhase = ($zList | ForEach-Object { $PhaseRuler[$_-1] }) -join "/"
  $rows += [pscustomobject]@{
    body                  = $b
    longitude             = [math]::Round($lon, 4)
    sign                  = $SignNames[$sIdx-1]
    deg_in_sign           = [math]::Round($degIn, 2)
    dignity_zakharian     = $dignity
    ruler_by_position     = $rulerByPosition       # управитель по положению (управитель знака) — материал
    ruler_by_phase        = $rulerByPhase          # управитель по фазе — мотивация
    Z                     = ($zList -join "/")      # dual shown as a/b for Mercury, Venus
    Z_phase_name          = ($zList | ForEach-Object { $PhaseName[$_-1] }) -join "/"
    z_micro               = $z
    z_micro_name          = $PhaseName[$z-1]
    H_house               = $Hh
    H_phase_name          = $PhaseName[$Hh-1]
    h_micro               = $hm
    h_micro_name          = $PhaseName[$hm-1]
    D_pos_ruler_sign      = $rulerSignTxt           # знак, где стоит управитель по положению
    D_pos_ruler_phase     = $D                      # его фаза (рекурсия диспозитора по положению)
    D_pos_ruler_phasename = $Dname
    vector                = "P<$($zList -join '/').$z : $Hh.$hm : $D>"
    tier                  = "Z,H,достоинство=grounded(book); z,h,D=anumita(operator+attested)"
  }
}

# --- write (provenance run-dir in results/ + join copy in chart outputs/) ---------------------
if ([string]::IsNullOrWhiteSpace($OutputBase)) { $OutputBase = Join-Path $PSScriptRoot "..\results" }
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("phase_vectors_" + $ChartId)
$runCsv = Join-Path $runDir "01_phase_vectors.csv"
$rows | Export-Csv -Path $runCsv -NoTypeInformation -Encoding UTF8

# join copy into the chart project so the coverage ledger can pick it up by body
if ([string]::IsNullOrWhiteSpace($OutputCsv)) { $OutputCsv = Join-Path $outputsDir "phase_vectors.csv" }
if (Test-Path $outputsDir) { Copy-Item $runCsv $OutputCsv -Force }

# Zakharian dignity layer — authoritative for the phase model. Emit standalone (run-dir + join copy)
# so the coverage ledger prefers it over the engine's generic dignity scheme.
$digRows = $rows | ForEach-Object { [pscustomobject]@{ body = $_.body; sign = $_.sign; dignity = $_.dignity_zakharian } }
$digRunCsv = Join-Path $runDir "02_zakharian_dignities.csv"
$digRows | Export-Csv -Path $digRunCsv -NoTypeInformation -Encoding UTF8
$digJoin = Join-Path $outputsDir "zakharian_dignities.csv"
if (Test-Path $outputsDir) { Copy-Item $digRunCsv $digJoin -Force }

# Divergence check vs the engine's dignities (audit, not silent): where Zakharian ≠ engine.
$engDig = @{}
$engPath = $null
foreach ($n in @("natal_dignities.csv","07_natal_dignities.csv")) { $p = Join-Path $outputsDir $n; if (Test-Path $p) { $engPath = $p; break } }
$divergences = @()
if ($engPath) {
  foreach ($r in (Import-Csv $engPath)) { $engDig[("$($r.body)").ToLower()] = "$($r.dignity)" }
  foreach ($d in $digRows) {
    $eng = $engDig[("$($d.body)").ToLower()]
    if ($eng -and ($eng -ne (& { switch ($d.dignity) { "домицил" {"domicile"} "изгнание" {"detriment"} "экзальтация" {"exaltation"} "падение" {"fall"} default {"peregrine"} } }))) {
      $divergences += "$($d.body) $($d.sign): Захарян=$($d.dignity) · движок=$eng"
    }
  }
}

$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId; script_version = $scriptVersion; chart_id = $ChartId
  asc_longitude = [math]::Round($ascLon, 6); body_count = $rows.Count
  rulership = "modern"; house_model = "equal-from-ASC"
}
$runFinishedAt = (Get-Date).ToUniversalTime()
$outputHash = Get-RunOutputHash -RunDir $runDir -ExcludeFiles @("00_summary.txt")
Write-RunSummary -Path (Join-Path $runDir "00_summary.txt") `
  -ScriptId $scriptId -ScriptVersion $scriptVersion `
  -RunStartedAtUtc $runStartedAt -RunFinishedAtUtc $runFinishedAt `
  -InputHash $inputHash -OutputHash $outputHash -Fields ([ordered]@{
    CHART_ID = $ChartId; METHOD = "PHASE_VECTORS_ZAKHARIAN"; SELF_TEST = "PASS_144_144"
    ASC_LONGITUDE = [math]::Round($ascLon, 4); BODY_COUNT = $rows.Count
    RULERSHIP = "modern"; HOUSE_MODEL = "equal-from-ASC"
    TIER = "Z,H=grounded(book Table 2.2); z,h,D=anumita(operator+attested,unverifiable)"
    DIGNITY_SOURCE = "Zakharian Table 1 (verified)"; DIGNITY_DIVERGENCE_VS_ENGINE = $divergences.Count
    OUTPUT_DIR = $runDir; JOIN_COPY = $OutputCsv
  })

Write-Host "ASC longitude: $([math]::Round($ascLon,2))°  ·  bodies: $($rows.Count)"
Write-Host "phase vectors → $runDir  (join copy → $OutputCsv)"
Write-Host "Zakharian dignities → $digJoin"
if ($divergences.Count -gt 0) {
  Write-Host "⚠ Достоинства: Захарян ≠ движок в $($divergences.Count) — реестр возьмёт ЗАХАРЯНА:"
  $divergences | ForEach-Object { Write-Host "    $_" }
} else { Write-Host "Достоинства: Захарян == движок на этой карте (0 расхождений)." }
$rows | Format-Table body, sign, dignity_zakharian, ruler_by_position, ruler_by_phase, Z, z_micro, H_house, vector -AutoSize | Out-String | Write-Host
