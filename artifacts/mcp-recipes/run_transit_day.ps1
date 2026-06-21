param(
  # Natal (whose chart the day is read against)
  [Parameter(Mandatory = $true)][string]$BirthLocal,     # "1990-06-15 14:30:00"
  [Parameter(Mandatory = $true)][string]$Timezone,       # IANA, e.g. "Europe/Moscow"
  [Parameter(Mandatory = $true)][double]$NatalLatitude,
  [Parameter(Mandatory = $true)][double]$NatalLongitude,
  # The day + where the person OBSERVES it now (current residence — rising hands are cast here)
  [Parameter(Mandatory = $true)][string]$Day,            # "2026-06-22"
  [Parameter(Mandatory = $true)][double]$ObsLatitude,
  [Parameter(Mandatory = $true)][double]$ObsLongitude,
  [double]$ObsTzOffsetHours = 0,                         # +3 for Krasnodar (noon-local + hand timing)
  [string]$DisplayName = "",
  [int]$StepMin = 10,
  [double]$Orb = 3,
  # The emergent step (twin -> prose) behind a swappable adapter; empty = stop at the hand-off.
  [string]$ModelAdapter = "",
  [switch]$Assemble,                                     # second pass: gate twin+prose, then PDF
  [string]$PrivateRoot = ""
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# run_transit_day — the predictable protocol for the transit-day product (NKS astrolab #90).
#   data → TWIN (gate) → prose → PDF. Same shape as run_solar_gift: deterministic recipes compute,
#   the model reads behind an adapter, a GATE blocks the deliverable until the twin actually exists.
#   The twin is NOT optional: read-as-system → twin → prose. Skipping it = unverifiable prose
#   (the 2026-06-21 failure). This script makes the gate the harness, not the model's goodwill.
#
#   It does NOT recompute transit→natal aspects (run_transits_to_natal snapshot) nor the hands
#   (run_rising_hands) — it ORCHESTRATES them. No duplication.
# ─────────────────────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here "..\..")).Path
. "$here\lib\mcp_helpers.ps1" | Out-Null

if ([string]::IsNullOrWhiteSpace($PrivateRoot)) { $PrivateRoot = Join-Path $repo ".private\charts" }
$PrivateRoot = [System.IO.Path]::GetFullPath($PrivateRoot)
if ($PrivateRoot -notmatch "\\\.private\\") { throw "GUARD: PrivateRoot must be under .private — client data never goes to public charts/." }

function Stage($name) { Write-Host "`n=== [$name] ===" -ForegroundColor Cyan }
function Recipe($script, $argv) {
  & pwsh -NoProfile -File (Join-Path $here $script) @argv 2>&1 | Where-Object { $_ -notmatch 'Assertion failed' } | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "recipe failed: $script (exit $LASTEXITCODE)" }
}
function LatestRun($base, $prefix) {
  $d = Get-ChildItem -Path $base -Directory -Filter "$prefix*" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $d) { throw "no run dir '$prefix*' under $base" }
  return $d.FullName
}
# GATE TEETH — the PDF is BLOCKED unless the twin exists and is real (the 2026-06-21 lesson).
function Assert-TwinReady($pkgDir) {
  $twin = Join-Path $pkgDir "twin.md"
  if (-not (Test-Path $twin)) { throw "GATE FAILED: twin.md missing — read the day as a SYSTEM and write the twin BEFORE prose (no cutting it; #90)." }
  $t = Get-Content $twin -Raw
  if ($t.Length -lt 400) { throw "GATE FAILED: twin.md too thin ($($t.Length) chars) — a real twin names несущее/фон/углы/ось-узлы/тень, not a stub." }
  foreach ($sec in @("есущее", "он", "глы", "ось", "ень")) {  # carrying / background / angles / axis / shadow
    if ($t -notmatch $sec) { throw "GATE FAILED: twin.md missing a '$sec' section — the system-read is incomplete." }
  }
  $prose = Join-Path $pkgDir "prose.html"
  if (-not (Test-Path $prose)) { throw "GATE FAILED: prose.html missing — write prose AFTER the twin, checked against it." }
  Write-Host "  twin gate: PASS — twin.md present and substantive; prose.html present" -ForegroundColor Green
}

# ── derive UTCs ───────────────────────────────────────────────────────────────────────────────
Stage "tz -> UTC (natal birth + day-noon)"
$birthUtc = & python -c @"
from zoneinfo import ZoneInfo
from datetime import datetime
s = '$BirthLocal'.strip()
for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
    try: lt = datetime.strptime(s, fmt); break
    except ValueError: lt = None
if lt is None: raise SystemExit('birth datetime not YYYY-MM-DD HH:MM[:SS]: ' + s)
print(lt.replace(tzinfo=ZoneInfo('$Timezone')).astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ'))
"@
if ([string]::IsNullOrWhiteSpace($birthUtc)) { throw "tz resolution failed" }
$birthUtc = $birthUtc.Trim()
# noon at the OBSERVATION location, in UTC (snapshot for slow planets is legitimate at local noon)
$noonHourUtc = (12 - $ObsTzOffsetHours)
$dayNoonUtc = ("{0}T{1:00}:00:00Z" -f $Day, $noonHourUtc)

$chartId = "tday_" + ($Day -replace '-','') + "_" + [math]::Round($ObsLatitude,2)
$chartDir = Join-Path (Join-Path $PrivateRoot "_transit_days") $chartId
$runs = Join-Path $chartDir "_runs"
$pkg  = Join-Path $chartDir "_model_input"
New-Item -ItemType Directory -Force -Path $runs | Out-Null
New-Item -ItemType Directory -Force -Path $pkg  | Out-Null
Write-Host "  natal $BirthLocal $Timezone -> $birthUtc | day $Day noon(obs)->UTC $dayNoonUtc | id=$chartId"

# ── ASSEMBLE pass: gate the twin+prose, render PDF, stop ──────────────────────────────────────
if ($Assemble) {
  Stage "twin gate"
  Assert-TwinReady $pkg
  Stage "assemble PDF"
  $proseHtml = Join-Path $pkg "prose.html"
  $pdf = Join-Path $chartDir ("transit_day_" + ($Day -replace '-','') + ".pdf")
  $py = @"
from playwright.sync_api import sync_playwright
src=r'$proseHtml'.replace('\\','/'); dst=r'$pdf'.replace('\\','/')
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto('file:///'+src)
    pg.pdf(path=dst, format='A4', print_background=True, margin={'top':'14mm','bottom':'14mm','left':'12mm','right':'12mm'})
    b.close()
print('pdf -> '+dst)
"@
  $py | & python -
  Write-Host "  deliverable: $pdf" -ForegroundColor Green
  return
}

# ── BUILD pass: natal points + aspects + hands → work-package + BRIEF, then hand off ───────────
Stage "natal points (angles + classical bodies) for rising targets"
$nc = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = $birthUtc; latitude = $NatalLatitude; longitude = $NatalLongitude }
$np = @()
$angleMap = [ordered]@{ Ascendant="ASC(личность)"; Midheaven="MC(призвание)"; IC="IC(корни)"; Descendant="DSC(партнёр)" }
foreach ($k in $angleMap.Keys) { if ($nc.chart_points.PSObject.Properties.Name -contains $k) { $np += [pscustomobject]@{ name=$angleMap[$k]; longitude=[math]::Round([double]$nc.chart_points.$k.longitude,4) } } }
# CHART RULER is COMPUTED from the sign on the ASC (traditional rulers), never hardcoded — universal.
$signRulerTrad = @("mars","venus","mercury","moon","sun","mercury","venus","mars","jupiter","saturn","saturn","jupiter")
$ascLon = (($nc.chart_points.Ascendant.longitude % 360) + 360) % 360
$rulerKey = $signRulerTrad[[int][math]::Floor($ascLon / 30)]
$bodyRu = [ordered]@{ Sun="Солнце"; Moon="Луна"; Mercury="Меркурий"; Venus="Венера"; Mars="Марс"; Jupiter="Юпитер"; Saturn="Сатурн" }
foreach ($k in $bodyRu.Keys) {
  if ($nc.planets.PSObject.Properties.Name -contains $k) {
    $label = $bodyRu[$k]
    if ($k.ToLowerInvariant() -eq $rulerKey) { $label += "(упр)" }   # mark whichever body actually rules the ASC
    $np += [pscustomobject]@{ name=$label; longitude=[math]::Round([double]$nc.planets.$k.longitude,4) }
  }
}
$natalPointsCsv = Join-Path $pkg "natal_points.csv"
$np | Export-Csv $natalPointsCsv -NoTypeInformation -Encoding UTF8

Stage "aspects transit->natal (snapshot at obs-noon, WITH angles)"
Recipe "run_transits_to_natal.ps1" @("-CaseId",$chartId,"-Latitude",$NatalLatitude,"-Longitude",$NatalLongitude,"-BirthDateTimeUtc",$birthUtc,"-TransitDateTimeUtc",$dayNoonUtc,"-Orb",$Orb,"-OutputBase",$runs)
$aspRun = LatestRun $runs "transit_to_natal_$chartId"
Copy-Item (Join-Path $aspRun "03_transit_to_natal_aspects.csv") (Join-Path $pkg "aspects.csv") -Force

Stage "rising hands (floating, observation location) + coincidence detector"
Recipe "run_rising_hands.ps1" @("-Date",$Day,"-Latitude",$ObsLatitude,"-Longitude",$ObsLongitude,"-TzOffsetHours",$ObsTzOffsetHours,"-StepMin",$StepMin,"-NatalPointsCsv",$natalPointsCsv,"-OutputBase",$runs)
$handRun = LatestRun $runs "rising_hands_"
foreach ($f in @("03_watches.csv","04_rising_cross.csv","05_moon_timing.csv","06_coincidences.csv")) {
  Copy-Item (Join-Path $handRun $f) (Join-Path $pkg $f) -Force
}

Stage "work-package + BRIEF (twin-gated)"
$dn = if ($DisplayName) { $DisplayName } else { $chartId }

# Format template — the CANONICAL transit-day layout, shipped IN the package so it's self-contained
# (no reliance on "yesterday's file"). The model copies this and fills it; it does NOT reinvent format.
$template = @'
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>
@page { size: A4; margin: 16mm 14mm; }
body { font: 11.5pt/1.62 Georgia, "PT Serif", serif; color:#1a1a1a; max-width: 720px; }
h1 { font-size: 20pt; margin:0 0 2pt; letter-spacing:.2px; }
.sub { color:#666; font-size:10.5pt; margin-bottom:14pt; }
h2 { font-size:13.5pt; margin:20pt 0 6pt; border-bottom:1px solid #ddd; padding-bottom:3pt; }
h3 { font-size:11.5pt; margin:13pt 0 3pt; color:#333; }
p { margin:6pt 0; }
.tag { display:inline-block; font-size:9pt; color:#555; background:#f2f1ee; border-radius:4px; padding:1px 7px; margin-right:4px; }
table { border-collapse:collapse; font-size:10pt; margin:6pt 0; width:100%; }
td,th { border:1px solid #e3e1dd; padding:3px 8px; text-align:left; }
th { background:#f7f6f3; }
.note { color:#666; font-size:10pt; }
.lead { font-size:12pt; }
.cal { font-variant-numeric: tabular-nums; }
hr { border:0; border-top:1px solid #eee; margin:16pt 0; }
.dim { color:#888; }
</style></head><body>
<h1>Транзитный день</h1>
<div class="sub"><!-- дата · место · к наталу --></div>
<p class="lead"><!-- тон дня одним абзацем --></p>
<h2>Как читается «день», а не «точка»</h2>
<p><!-- три стрелки: фон / Луна / восходящий --></p>
<h2>Фон дня</h2>
<p><span class="tag">весь день</span><!-- перевал/медленные --></p>
<h2>Тон дня</h2>
<!-- быстрые касания, ● на несущих -->
<h2>Твои углы</h2>
<!-- что горит (ASC/MC/IC/DSC), что приутихло -->
<h2>Луна дня — «часовая стрелка»</h2>
<table class="cal"><tr><th>примерно</th><th>Луна</th><th>что</th></tr><!-- из 05_moon_timing --></table>
<h2>Восходящий день — тонкая стрелка</h2>
<table class="cal"><tr><th>восходит (ASC)</th><th>·</th><th>кульминирует (MC)</th></tr><!-- из 04_rising_cross --></table>
<h2>Сегодня по областям</h2>
<!-- краткий доменный срез: громко/средне/тихо -->
<h2>Итог дня</h2>
<p><!-- несущее · противовес · фон · осторожнее --></p>
<hr><p class="dim" style="font-size:9.5pt"><!-- источник: рецепты swiss, что снимок/что плавающее --></p>
</body></html>
'@
Set-Content -Path (Join-Path $pkg "template_prose.html") -Encoding UTF8 -Value $template
$brief = @"
# BRIEF — транзитный день $Day, $dn (наблюдение: $ObsLatitude/$ObsLongitude, к наталу $BirthLocal $Timezone)

Это РАБОЧИЙ пакет. Данные посчитаны рецептами (cold). Твоя работа — ПРОЧИТАТЬ день как СИСТЕМУ и подать.

## Протокол (НЕ срезать шаги — гейт проверит)
1. read-as-system → 2. **twin.md** (обязателен, гейт) → 3. **prose.html** (сверена против twin) → 4. PDF.
Без twin проза непроверяема. Гейт блокирует PDF, пока нет twin.md (с разделами несущее/фон/углы/ось/тень).

## Данные в пакете
- `aspects.csv` — транзит→натал на полдень (фон медленных · тон быстрых · УГЛИ ASC/MC/IC/DSC). Орбы в колонке.
- `03_watches.csv` — караулы (восходящий знак по часам) + управители.
- `04_rising_cross.csv` — тонкая стрелка: транзитный ASC/MC проходит твои натал-точки (восходит/кульминирует), время.
- `05_moon_timing.csv` — часовая стрелка: аспекты Луны к наталу за день, время.
- `06_coincidences.csv` — УЗЛЫ оси: где сходятся слои (караул + активация + Луна), по score. Сердце дня — топ-узел.

## twin.md — понимание дня как системы (НЕ клиентский текст)
Назови по разделам: НЕСУЩЕЕ (что ведёт день + орбы) · ПРОТИВОВЕС · ФОН (перевал/ресурс) · УГЛЫ (что горит,
что приутихло) · ОСЬ ДНЯ (узлы из 06_coincidences: сердце + контрасты) · В ТЕНЬ (что тихо) · ОСТОРОЖНО.
Заверши чеклистом сверки прозы. Образец — прошлый `_twin.md` (если есть рядом).

## prose.html — заполни ШАБЛОН из пакета, не переизобретай формат
Возьми `template_prose.html` (он в пакете — канонический CSS и структура: Georgia, .tag/.cal, таблицы Луны
и восходящего дня, разделы по порядку), скопируй и заполни плейсхолдеры из данных. Ставь ● на несущих
аспектах. НЕ меняй формат/визуал/структуру без явной санкции владельца — шаблон и есть формат.

## Принципы чтения
- Три стрелки (#90): фон (медленные, ровно весь день) · Луна (часовая) · восходящий ASC/MC (тонкая). Быстрые
  Солнце/Меркурий/Венера/Марс внутри дня почти-фон (их окно — дни). Углы первоклассны (#88), при точном времени ●.
- Сферы в дне — краткий доменный срез (громко/средне/тихо), не послойно (день мал — иначе Barnum).
- Подача событийности как качества, не приказа; осторожное — как ресурс, не приговор.

## Язык (realm clear-russsian — живой русский)
Живой глагол вместо отглагольного существительного («Солнце сошло», не «смещение»); явный деятель; конкретный
образ; русский эквивалент, не калька. Без канцелярита, без злоупотребления жирным, без лишних эмодзи-маркеров.

После twin.md + prose.html запусти второй проход: тот же вызов с `-Assemble` — гейт + PDF.
"@
Set-Content -Path (Join-Path $pkg "BRIEF.md") -Encoding UTF8 -Value $brief

Stage "hand-off"
Write-Host "  work-package: $pkg" -ForegroundColor Green
Write-Host "  next: build twin.md -> prose.html in the package, then re-run with -Assemble" -ForegroundColor Yellow
if ($ModelAdapter) {
  Stage "emergent step (adapter)"
  & pwsh -NoProfile -File (Join-Path $here $ModelAdapter) $pkg
  if ($LASTEXITCODE -ne 0) { throw "model adapter failed (exit $LASTEXITCODE)" }
  Assert-TwinReady $pkg
  Write-Host "  adapter done + twin gate passed; re-run with -Assemble for PDF" -ForegroundColor Green
}
