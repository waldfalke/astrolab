param(
  # Birth data
  [Parameter(Mandatory = $true)][string]$BirthLocal,     # e.g. "1990-06-15 14:30"
  [Parameter(Mandatory = $true)][string]$Timezone,       # IANA, e.g. "Europe/Moscow"
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [int]$ReturnYear = 0,                                   # 0 = current calendar year
  [string]$DisplayName = "",
  # The emergent step (twin -> prose) goes behind a SWAPPABLE adapter. A script/command that takes
  # the work-package dir as $args[0] and writes twin.md + prose into it. Empty = stop at the hand-off
  # (model undecided: Claude / Codex / GLM are just three adapters behind this one boundary).
  [string]$ModelAdapter = "",
  [string]$PrivateRoot = ""                               # default: <repo>/.private/charts
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# run_solar_gift — the model-AGNOSTIC orchestrator for the SR-gift product.
#
# Forces the frame a fresh, context-less model won't self-enforce (the general-agent failure):
#   • NATAL FIRST — a solar return is read against the natal, never in isolation (computed before SR);
#   • COMPUTE ONLY VIA RECIPES — no hand-authored chart data is even reachable from here;
#   • PII → .private ONLY — client data never touches the public, tracked charts/;
#   • VALIDATION GATE — schema + provenance must pass before the deliverable step;
#   • the EMERGENT read (twin -> prose) is the ONLY LLM step, bounded, behind a swappable adapter,
#     fed an engineered work-package (cold data + BRIEF) so the model needs no docs it could skip.
#
# Deterministic substrate = this script + the recipes. Emergent organ = the model behind the adapter.
# ─────────────────────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"   # validator/tz print unicode; cp1251 console would crash them
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here "..\..")).Path

if ([string]::IsNullOrWhiteSpace($PrivateRoot)) { $PrivateRoot = Join-Path $repo ".private\charts" }
$PrivateRoot = [System.IO.Path]::GetFullPath($PrivateRoot)
if ($PrivateRoot -notmatch "\\\.private\\") { throw "GUARD: PrivateRoot must be under .private (got '$PrivateRoot') — client data never goes to public charts/." }

function Stage($name) { Write-Host "`n=== [$name] ===" -ForegroundColor Cyan }
function Recipe($script, $argv) {
  & pwsh -NoProfile -File (Join-Path $here $script) @argv 2>&1 | ForEach-Object { $_ } | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "recipe failed: $script (exit $LASTEXITCODE)" }
}
function LatestRun($base, $prefix) {
  $d = Get-ChildItem -Path $base -Directory -Filter "$prefix*" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $d) { throw "no run dir '$prefix*' under $base" }
  return $d.FullName
}

# ── 0. resolve UTC via IANA (deterministic; never assert tz from recall) ──────────────────────
Stage "tz -> UTC"
$utc = & python -c @"
from zoneinfo import ZoneInfo
from datetime import datetime
lt = datetime.strptime('$BirthLocal', '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('$Timezone'))
print(lt.astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ'))
"@
if ([string]::IsNullOrWhiteSpace($utc)) { throw "tz resolution failed" }
$utc = $utc.Trim()
if ($ReturnYear -le 0) { $ReturnYear = (Get-Date).Year }
$compact = ($BirthLocal -replace '[-: ]','')
$chartId = "gift_$compact"
$chartDir = Join-Path $PrivateRoot $chartId
$runs = Join-Path $chartDir "_runs"
New-Item -ItemType Directory -Force -Path $runs | Out-Null
Write-Host "  local $BirthLocal $Timezone -> UTC $utc | id=$chartId | returnYear=$ReturnYear"

# ── 1. NATAL FIRST (the gate that the general agent skipped) ──────────────────────────────────
Stage "natal + houses (natal first — SR is read against it)"
Recipe "run_natal_with_failover.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-DateTimeUtc",$utc,"-Orb",6,"-OutputBase",$runs)
Recipe "run_house_layer_placidus.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-DateTimeUtc",$utc,"-OutputBase",$runs)
$natalRun = LatestRun $runs "natal_failover_$chartId" ; $houseRun = LatestRun $runs "house_placidus_$chartId"

# ── 2. SOLAR RETURN (only now, with natal in hand) ────────────────────────────────────────────
Stage "solar return $ReturnYear"
Recipe "run_solar_revolution.ps1" @("-CaseId",$chartId,"-BirthLatitude",$Latitude,"-BirthLongitude",$Longitude,"-BirthDateTimeUtc",$utc,"-ReturnYear",$ReturnYear,"-OutputBase",$runs)
$srRun = LatestRun $runs "solar_return_$chartId"

# ── 3. TRANSITS over the solar year ───────────────────────────────────────────────────────────
Stage "transit windows"
$rangeStart = (Get-Date).ToString("yyyy-MM-ddT00:00:00Z")
$rangeEnd   = (Get-Date).AddMonths(15).ToString("yyyy-MM-ddT00:00:00Z")
Recipe "run_transits_to_natal.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-BirthDateTimeUtc",$utc,"-RangeStartUtc",$rangeStart,"-RangeEndUtc",$rangeEnd,"-StepDays",7,"-Orb",1,"-OutputBase",$runs)
$trRun = LatestRun $runs "transit_timeline_$chartId"
$carrier = Join-Path $trRun "03_carrier_windows.csv"

# ── 4. assemble chart project (forced into .private) ──────────────────────────────────────────
Stage "chart project (.private)"
$dn = if ([string]::IsNullOrWhiteSpace($DisplayName)) { $chartId } else { $DisplayName }
Recipe "build_chart_project.ps1" @("-ChartId",$chartId,"-BirthDateTimeLocal",$BirthLocal,"-BirthDateTimeUtc",$utc,"-Latitude",$Latitude,"-Longitude",$Longitude,"-DisplayName",$dn,"-NatalFailoverRunDir",$natalRun,"-HouseRunDir",$houseRun,"-ChartsRoot",$PrivateRoot)

# ── 4b. PHASE VECTORS (Zakharian — the project's signature layer). Project mode reads outputs/
#     natal_longitudes.csv + houses_placidus.csv, writes phase_vectors.csv + zakharian_dignities.csv
#     into outputs/. -ChartsRoot $PrivateRoot is MANDATORY: the recipe otherwise writes to public
#     charts/ (a PII leak). Modern rulership (declared; differs from the traditional dispositors/
#     profection — pinned per layer). Deliverable presents PLAIN-LANGUAGE stage-quality only: Z/H
#     grounded (●, Z verifies vs book Table 2.2), z/h/D anumita (◐); never the P⟨⟩ notation or author name.
Stage "phase vectors (Zakharian — natal layer)"
Recipe "run_phase_vectors.ps1" @("-ChartId",$chartId,"-ChartsRoot",$PrivateRoot,"-OutputBase",$runs)

# ── 5. coverage ledger (the eye-checklist: every factor enumerated) ───────────────────────────
Stage "coverage ledger"
Recipe "build_coverage_ledger.ps1" @("-ChartId",$chartId,"-ChartsRoot",$PrivateRoot,"-SolarReturnRunDir",$srRun,"-TransitTimelineCsv",$carrier)

# ── 6. VALIDATION GATE — must pass before any deliverable ─────────────────────────────────────
Stage "validation gate (schema + provenance)"
& python (Join-Path $repo ".agents\skills\schema-validator\scripts\validate_chart.py") "--chart-dir" $chartDir 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "GATE FAILED: schema validation. Not proceeding to deliverable." }
Recipe "check_chart_provenance.ps1" @("-ChartsRoot",$PrivateRoot,"-ChartId",$chartId)
Write-Host "  schema + provenance: PASS"

# ── 7. render natal wheel + SR biwheel ────────────────────────────────────────────────────────
Stage "render wheels"
$renders = Join-Path $chartDir "_renders"
Recipe "run_renderer.ps1" @("-ChartId",$chartId,"-ChartsRoot",$PrivateRoot,"-OutputBase",$renders)

# ── 8. assemble the MODEL WORK-PACKAGE (engineered context for the swappable emergent step) ──
Stage "model work-package"
$pkg = Join-Path $chartDir "_model_input"
New-Item -ItemType Directory -Force -Path $pkg | Out-Null
$brief = @"
# Соляр-отчёт в подарок — твой шаг (чтение)

Карта уже посчитана. Твоя работа — прочитать её как живой астролог и написать тёплый отчёт-подарок
человеку на день рождения. Это ТВОЁ чтение: данные дают материал, а не сценарий. Читай карту целиком
и в соотношении, не по кусочкам.

## Три вещи, без которых не работает (это основа, не про стиль)
- Числа бери из посчитанных файлов; не выдумывай и не прикидывай на глаз. Чего нет в данных — лучше
  сказать «нет», чем дорисовать.
- Соляр читается ОТНОСИТЕЛЬНО натала, не сам по себе: натал — фундамент, соляр кладётся поверх.
- Все данные клиента остаются в этой `.private`-папке.

## Как обычно читают (ориентир, не чек-лист — порядок и глубину выбираешь сам)
Натал как целое (секта, темперамент, управитель, диспозиторы/рецепции — двигатель, угловые и
аспектированные тела, достоинства) → соляр против натала (SR-ASC и его управитель, SR-планеты на
натальные точки, хозяин года из профекции — сходятся ли в одну сторону) → транзитные окна года.
SR-Солнце на своём же градусе — это определение возврата, не событие; пропусти.

## Фазовый слой (фишка метода — используй, но честно)
В `outputs/` есть `phase_vectors.csv` (фаза каждого тела) и `zakharian_dignities.csv` — второй,
СТАДИЙНЫЙ слой поверх традиционного чтения: на какой стадии стоит тело/год (импульс · ресурс · связь ·
база · творчество · служение · зеркало · трансформация · стратегия · результат · оптимизация · архив).
Год как 12 фаз-сегментов от ДР — в `12_monthly_phase_windows.csv`. В прозу неси КАЧЕСТВО стадии простым
языком — НЕ нотацию `P⟨⟩` и НЕ имя автора. Калибровка: фаза по знаку (Z) и дому (H) — надёжно ●;
микрофазы (z/h) и диспозиторная (D) — выведенные, помечай ◐.

## Что сдать (в эту же папку)
1. `twin.md` — твои рабочие заметки: фактура из данных + твоя логика, чтобы держаться карты.
   Структурируй как удобно тебе.
2. `prose.md` — тёплая русская проза ПО РАЗДЕЛАМ готового отчёта (структура ниже): показывай, не
   заверяй; где вывод крепкий — увереннее, где зависит от точного времени — мягче (●/◐ по желанию);
   трудное называй честно и по-доброму.

## Структура отчёта (форма продукта — её задаёт харнес; ты её НЕ выдумываешь и НЕ копируешь у других)
Готовый отчёт — `grand-report` (пустой шаблон и стандарт лежат тут же в пакете: `grand-report.html`,
`report-standards.md`, `prose-style-ru.md`). Разделы: портрет · год (карта года + тема) · по одной
главе на каждое транзитное окно года · 7 сфер жизни · опоры на год · метод-нота.
Твоё дело — ПРОЗА каждого раздела. Числа в техблоках, колёса/бивилы и сборку HTML→PDF делает
оркестратор из посчитанных данных. НЕ строй техблоки руками, НЕ рисуй колёса, НЕ подсматривай чужие
готовые отчёты. Нет данных на раздел — скажи, не выдумывай.

## Данные
chart.yaml, outputs/ (натал/дома/точки/аспекты), coverage_factors.csv (перечень факторов — чтобы
ничего не упустить из виду), run-каталоги (соляр: SR→натал, профекция, активации; транзиты: окна),
_renders/ (колёса).
"@
Set-Content -Path (Join-Path $pkg "BRIEF.md") -Encoding UTF8 -Value $brief
Copy-Item (Join-Path $chartDir "chart.yaml") $pkg -Force -ErrorAction SilentlyContinue
$packsFactors = Join-Path $chartDir "packs\coverage_factors.csv"
if (Test-Path $packsFactors) { Copy-Item $packsFactors $pkg -Force }
# manifest of where everything is
@{
  chart_id = $chartId; chart_dir = $chartDir; utc = $utc; return_year = $ReturnYear
  outputs = (Join-Path $chartDir "outputs"); natal_run = $natalRun; sr_run = $srRun
  transit_carrier = $carrier; renders = $renders; coverage = $packsFactors
  pending = @("twin.md","prose.md","grand-report fill","PDF")
} | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $pkg "manifest.json") -Encoding UTF8
# structure + standard + voice travel WITH the package — the model fills THIS empty form,
# it must never hunt or copy another client's filled report.
foreach ($f in @("artifacts\report-templates\grand-report.html","docs\report-standards.md","docs\prose-style-ru.md")) {
  $src = Join-Path $repo $f
  if (Test-Path $src) { Copy-Item $src $pkg -Force }
}

# ── 9. HAND-OFF to the swappable model adapter (or stop, cleanly) ──────────────────────────────
Stage "emergent step (swappable adapter)"
if ([string]::IsNullOrWhiteSpace($ModelAdapter)) {
  Write-Host "  READY FOR MODEL STEP — deterministic spine complete, validated." -ForegroundColor Green
  Write-Host "  Work-package: $pkg"
  Write-Host "  Set -ModelAdapter <cmd> to run the emergent step (twin->prose) with Claude/Codex/GLM."
} else {
  Write-Host "  invoking adapter: $ModelAdapter"
  & $ModelAdapter $pkg
  if ($LASTEXITCODE -ne 0) { throw "model adapter failed (exit $LASTEXITCODE)" }
  Write-Host "  adapter done — twin/prose produced. (template fill + PDF: next stage, TODO)"
}

Write-Host "`nrun_solar_gift complete for $chartId" -ForegroundColor Green
