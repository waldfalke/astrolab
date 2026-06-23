param(
  # The day + the PLACE it is read for (rising hands are cast here — no personal chart involved)
  [Parameter(Mandatory = $true)][string]$Day,            # "2026-06-23"
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [double]$TzOffsetHours = 0,                             # +3 for Krasnodar (local times of the hands)
  [string]$PlaceName = "",                                # e.g. "Краснодар" — shown in the deliverable
  [int]$StepMin = 10,
  # The emergent step (twin -> prose) behind a swappable adapter; empty = stop at the hand-off.
  [string]$ModelAdapter = "",
  [switch]$Assemble,                                     # second pass: gate twin+prose, then PDF
  [string]$PrivateRoot = ""
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# run_mundane_day — the predictable protocol for the natal-FREE "rising-sign clock" mundane forecast
#   ("космограмма качества времени дня"). Younger sibling of run_transit_day (NKS astrolab #90/#91/#93):
#   data → TWIN (gate) → prose → PDF. Same shape, MINUS the natal layer — no transit→natal aspects,
#   no караул×натал coincidence nodes. Pure quality-of-the-day for a PLACE.
#
#   It does NOT recompute the hands — it ORCHESTRATES run_rising_hands in GENERAL mode (no natal points)
#   and hands off the canonical template (artifacts/report-templates/rising-clock-mundane.html) so the
#   model fills the STANDARD, never reinvents the format. The twin is NOT optional: read-as-system →
#   twin → prose. Skipping it = unverifiable prose. This script makes the gate the harness.
# ─────────────────────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here "..\..")).Path
. "$here\lib\mcp_helpers.ps1" | Out-Null

if ([string]::IsNullOrWhiteSpace($PrivateRoot)) { $PrivateRoot = Join-Path $repo ".private\charts" }
$PrivateRoot = [System.IO.Path]::GetFullPath($PrivateRoot)
if ($PrivateRoot -notmatch "\\\.private\\") { throw "GUARD: PrivateRoot must be under .private — day forecasts never go to public charts/." }

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
# GATE TEETH — the PDF is BLOCKED unless the mundane twin exists and is real (the corner-cutting lesson).
function Assert-TwinReady($pkgDir) {
  $twin = Join-Path $pkgDir "twin.md"
  if (-not (Test-Path $twin)) { throw "GATE FAILED: twin.md missing — read the day as a SYSTEM and write the twin BEFORE prose (no cutting it; #90)." }
  $t = Get-Content $twin -Raw
  if ($t.Length -lt 400) { throw "GATE FAILED: twin.md too thin ($($t.Length) chars) — a real twin names 12 караулов/начкары, восходящие объекты, лунную стрелку, фон-ретро, осторожно." }
  # mundane sections (case-insensitive substring roots): watches / rising objects / Moon / climate / caution
  foreach ($sec in @("араул", "осходящ", "уна", "фон", "сторожно")) {
    if ($t -notmatch $sec) { throw "GATE FAILED: twin.md missing a '$sec' section — the system-read is incomplete (need караулы · восходящие · луна · фон · осторожно)." }
  }
  $prose = Join-Path $pkgDir "prose.html"
  if (-not (Test-Path $prose)) { throw "GATE FAILED: prose.html missing — write prose AFTER the twin, checked against it." }
  Write-Host "  twin gate: PASS — twin.md present and substantive; prose.html present" -ForegroundColor Green
}

$placeSlug = if ($PlaceName) { ($PlaceName -replace '[^\p{L}\p{Nd}]+','_').ToLowerInvariant() } else { "{0}_{1}" -f [math]::Round($Latitude,2), [math]::Round($Longitude,2) }
$chartId  = "mday_" + ($Day -replace '-','') + "_" + $placeSlug
$chartDir = Join-Path (Join-Path $PrivateRoot "_transit_days") $chartId
$runs = Join-Path $chartDir "_runs"
$pkg  = Join-Path $chartDir "_model_input"
New-Item -ItemType Directory -Force -Path $runs | Out-Null
New-Item -ItemType Directory -Force -Path $pkg  | Out-Null

# ── ASSEMBLE pass: gate the twin+prose, render PDF, stop ──────────────────────────────────────
if ($Assemble) {
  Stage "twin gate"
  Assert-TwinReady $pkg
  Stage "assemble PDF"
  $proseHtml = Join-Path $pkg "prose.html"
  $pdf = Join-Path $chartDir ("mundane_day_" + ($Day -replace '-','') + ".pdf")
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

# ── BUILD pass: rising hands (general, no natal) → work-package + template + BRIEF, then hand off ─
$dn = if ($PlaceName) { $PlaceName } else { "{0}/{1}" -f $Latitude, $Longitude }
Write-Host "  mundane day $Day @ $dn (lat $Latitude / lon $Longitude, tz +$TzOffsetHours) | id=$chartId"

Stage "rising hands (floating, GENERAL mode — no natal points)"
Recipe "run_rising_hands.ps1" @("-Date",$Day,"-Latitude",$Latitude,"-Longitude",$Longitude,"-TzOffsetHours",$TzOffsetHours,"-StepMin",$StepMin,"-OutputBase",$runs)
$handRun = LatestRun $runs "rising_hands_"
foreach ($f in @("03_watches.csv","07_moon_to_planets.csv","08_sphere_quality.csv","09_void_of_course.csv","10_rising_objects.csv","00_summary.txt")) {
  $srcF = Join-Path $handRun $f
  if (Test-Path $srcF) { Copy-Item $srcF (Join-Path $pkg $f) -Force }
}

Stage "work-package + template + BRIEF (twin-gated)"
# Single source of truth: copy the CANONICAL git template into the package as template_prose.html.
$tpl = Join-Path $repo "artifacts\report-templates\rising-clock-mundane.html"
if (-not (Test-Path $tpl)) { throw "canonical template missing: $tpl" }
Copy-Item $tpl (Join-Path $pkg "template_prose.html") -Force

$brief = @"
# BRIEF — мунданный день $Day, $dn (космограмма качества времени дня, БЕЗ натала)

Это РАБОЧИЙ пакет. Данные посчитаны рецептом run_rising_hands в GENERAL-режиме (cold). Твоя работа —
ПРОЧИТАТЬ день как СИСТЕМУ и подать по канону. Личной карты нет: это качество времени для МЕСТА.

## Протокол (НЕ срезать шаги — гейт проверит)
1. read-as-system → 2. **twin.md** (обязателен, гейт) → 3. **prose.html** (сверена против twin) → 4. PDF.
Без twin проза непроверяема. Гейт блокирует PDF, пока нет twin.md с разделами: караулы · восходящие
объекты · лунная стрелка · фон · осторожно.

## Данные в пакете
- `03_watches.csv` — 12 караулов (восходящий знак ~2ч) + начкар (управитель): знак, достоинство, фаза.
- `10_rising_objects.csv` — объекты на восходящем ГРАДУСЕ: транзитный ASC/MC проходит планету (восходит/кульминирует).
- `07_moon_to_planets.csv` — лунная часовая стрелка: аспекты Луны к транзитным планетам, время.
- `08_sphere_quality.csv` — к какой сфере жизни клонит каждый караул (#97).
- `09_void_of_course.csv` — Луна без курса (уходит из знака без мажорного аспекта), если есть.
- `00_summary.txt` — сводка: ретро-климат, VoC.

## twin.md — понимание дня как системы (НЕ клиентский текст)
Назови по разделам: 12 КАРАУЛОВ + начкары (положение + ДОСТОИНСТВО + фаза-архетип) · ВОСХОДЯЩИЕ ОБЪЕКТЫ
(на восходящем градусе) · ЛУННАЯ стрелка (падежи: НА квадрате / В оппозиции) · СФЕРЫ (куда клонит) ·
ФОН (только ретро — высшие НЕ как ровный фон) · ОСТОРОЖНО. Заверши чеклистом сверки прозы.

## prose.html — заполни ШАБЛОН из пакета, не переизобретай формат
Возьми `template_prose.html` (он в пакете — это КАНОН: artifacts/report-templates/rising-clock-mundane.html),
скопируй и заполни плейсхолдеры из данных. Все правила формата — в ведущем HTML-комментарии шаблона.
НЕ меняй формат/визуал/структуру без явной санкции владельца — шаблон и есть формат.

## Правила подачи (краткая выжимка — полностью в шапке шаблона)
- Два слоя по порядку: I. Астрологический (точно) → II. По-человечески.
- 12 караулов (не 13) абзацами: заголовок (время · знак) болдом, БЕЗ точки, тем же шрифтом; текст ниже.
- ДОСТОИНСТВО ≠ ФАЗА: достоинство = сила (домицил/экзальтация/падение/перегрин); фаза = архетип-СЛОВО,
  формулу P⟨…⟩ НЕ печатать (working layer).
- «Объекты на восходящем ГРАДУСЕ», не «горизонт»; строками, не таблицей.
- Падежи аспектов: НА квадрате / НА трине / НА секстиле / В оппозиции / В соединении.
- Высшие НЕ как ровный фон; единственный климат — РЕТРО; отметь VoC.

## Язык (realm clear-russsian — живой русский)
Живой глагол вместо отглагольного существительного; явный деятель; конкретный образ; русский эквивалент,
не калька. Без канцелярита, без злоупотребления жирным, без «заметок себе» в клиентском тексте.

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
