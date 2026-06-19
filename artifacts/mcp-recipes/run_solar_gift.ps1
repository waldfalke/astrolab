param(
  # Birth data
  [Parameter(Mandatory = $true)][string]$BirthLocal,     # e.g. "1990-06-15 14:30"
  [Parameter(Mandatory = $true)][string]$Timezone,       # IANA, e.g. "Europe/Moscow"
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [int]$ReturnYear = 0,                                   # 0 = current calendar year
  # Solar-return RELOCATION — where the person MEETS the birthday (current residence), not birthplace.
  # The SR is cast for this location; angles/houses of the year follow it. Omit = birth location.
  [double]$ReturnLatitude = [double]::NaN,
  [double]$ReturnLongitude = [double]::NaN,
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
# POST-MODEL GATE TEETH — the deliverable is BLOCKED unless the model actually filled the self-check
# registries (blind run left dispositions at 195 blank stubs + year-roles unresolved). No silent pass.
function Assert-DeliverableReady($packDir) {
  $disp = Join-Path $packDir "coverage_dispositions.csv"
  if (-not (Test-Path $disp)) { throw "GATE FAILED: coverage_dispositions.csv missing — model didn't do the completeness pass." }
  $rows = @(Import-Csv $disp)
  $holes = @($rows | Where-Object { [string]::IsNullOrWhiteSpace($_.salience) })
  if ($holes.Count -gt 0) {
    $sample = ($holes | Select-Object -First 8 | ForEach-Object { $_.factor_id }) -join ', '
    throw "GATE FAILED: $($holes.Count)/$($rows.Count) factors have NO salience (лысый соляр). Fill coverage_dispositions.csv. e.g.: $sample"
  }
  $rolePath = Join-Path $packDir "year_roles.csv"
  if (Test-Path $rolePath) {
    $rr = @(Import-Csv $rolePath)
    $unresolved = @($rr | Where-Object { [string]::IsNullOrWhiteSpace($_.role) })
    if ($unresolved.Count -gt 0) {
      $rs = ($unresolved | ForEach-Object { $_.planet }) -join ', '
      throw "GATE FAILED: year-role unresolved for: $rs. Resolve each ONCE in year_roles.csv (kept single across spheres)."
    }
  }
  Write-Host "  deliverable gate: PASS — dispositions ($($rows.Count)) + year-roles all resolved" -ForegroundColor Green
}

# ── 0. resolve UTC via IANA (deterministic; never assert tz from recall) ──────────────────────
Stage "tz -> UTC"
$utc = & python -c @"
from zoneinfo import ZoneInfo
from datetime import datetime
# Accept HH:MM:SS or HH:MM — never SILENTLY drop seconds (an unflagged data-loss class).
s = '$BirthLocal'.strip()
for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
    try:
        lt = datetime.strptime(s, fmt); break
    except ValueError:
        lt = None
if lt is None:
    raise SystemExit('birth datetime not in \"YYYY-MM-DD HH:MM[:SS]\": ' + s)
lt = lt.replace(tzinfo=ZoneInfo('$Timezone'))
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
$srArgs = @("-CaseId",$chartId,"-BirthLatitude",$Latitude,"-BirthLongitude",$Longitude,"-BirthDateTimeUtc",$utc,"-ReturnYear",$ReturnYear,"-OutputBase",$runs)
if (-not ([double]::IsNaN($ReturnLatitude) -or [double]::IsNaN($ReturnLongitude))) {
  $srArgs += @("-ReturnLatitude",$ReturnLatitude,"-ReturnLongitude",$ReturnLongitude)
  Write-Host ("  SR relocated to {0},{1} (residence ≠ birthplace)" -f $ReturnLatitude,$ReturnLongitude)
}
Recipe "run_solar_revolution.ps1" $srArgs
$srRun = LatestRun $runs "solar_return_$chartId"
# Anchor the WHOLE forecast to the SR-INSTANT of the chosen ReturnYear, NOT the calendar "now" — so any
# year reads correctly: a past year (2020), the current one, or a future one (2030). Transits cover ITS
# solar year; directions/progressions mature to THAT year's moment. "From now" silently dropped the
# already-elapsed half of an in-progress year and made past/future returns nonsense.
# (First-life-year SR — ReturnYear = birth year — is a degenerate case ≈ the natal moment; out of scope.)
$srSummary = Get-Content (Join-Path $srRun "00_summary.txt") -Raw
$srInstant = ([regex]::Match($srSummary, 'RETURN_INSTANT_UTC=([0-9T:\-Z]+)')).Groups[1].Value
if ([string]::IsNullOrWhiteSpace($srInstant)) { throw "could not read RETURN_INSTANT_UTC from SR summary" }
$srYearStart = [datetimeoffset]::Parse($srInstant).UtcDateTime

# ── 3. TRANSITS over the solar year (SR-instant → +15 mo: the 12-month year + 3 of overhang for zones #84) ──
Stage "transit windows"
$rangeStart = $srInstant
$rangeEnd   = $srYearStart.AddMonths(15).ToString("yyyy-MM-ddT00:00:00Z")
Recipe "run_transits_to_natal.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-BirthDateTimeUtc",$utc,"-RangeStartUtc",$rangeStart,"-RangeEndUtc",$rangeEnd,"-StepDays",7,"-Orb",1,"-OutputBase",$runs)
$trRun = LatestRun $runs "transit_timeline_$chartId"
$carrier = Join-Path $trRun "03_carrier_windows.csv"

# ── 3b. DEEPENING natal layers: solar-arc directions + secondary progressions, directed to the SOLAR
#     YEAR'S MOMENT (SR-instant), not the calendar present — a past/future year gets maturation to ITS
#     time. Folded into the chart project so coverage enumerates dir2n / prog2n factors.
$targetUtc = $srInstant
Stage "solar-arc directions (to solar-year moment)"
Recipe "run_solar_arc.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-BirthDateTimeUtc",$utc,"-TargetDateUtc",$targetUtc,"-Orb",1.0,"-OutputBase",$runs)
$saRun = LatestRun $runs "solar_arc_$chartId"
Stage "secondary progressions (to solar-year moment)"
Recipe "run_secondary_progressions.ps1" @("-CaseId",$chartId,"-Latitude",$Latitude,"-Longitude",$Longitude,"-BirthDateTimeUtc",$utc,"-TargetDateUtc",$targetUtc,"-Orb",1.0,"-OutputBase",$runs)
$spRun = LatestRun $runs "secondary_progressions_$chartId"

# ── 4. assemble chart project (forced into .private) — folds in directions + progressions ──────
Stage "chart project (.private)"
$dn = if ([string]::IsNullOrWhiteSpace($DisplayName)) { $chartId } else { $DisplayName }
Recipe "build_chart_project.ps1" @("-ChartId",$chartId,"-BirthDateTimeLocal",$BirthLocal,"-BirthDateTimeUtc",$utc,"-Latitude",$Latitude,"-Longitude",$Longitude,"-DisplayName",$dn,"-NatalFailoverRunDir",$natalRun,"-HouseRunDir",$houseRun,"-SolarArcRunDir",$saRun,"-SecondaryProgressionsRunDir",$spRun,"-ChartsRoot",$PrivateRoot)

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

# ── 5b. sphere ledger (the DOMAIN-axis projection — twin to carrier_windows' TIME axis) ───────
#     Routes every coverage factor to its life-sphere(s) by house/ruler/significator, and flags
#     which spheres are charged vs ТИХИЙ — so spheres are read whole-per-domain, not inverted out
#     of windows, and an empty sphere is visible instead of padded (NKS astrolab #80/#82).
Stage "sphere ledger (domain axis)"
Recipe "run_sphere_ledger.ps1" @("-ChartId",$chartId,"-ChartsRoot",$PrivateRoot,"-SolarReturnRunDir",$srRun)

# ── 6. VALIDATION GATE — must pass before any deliverable ─────────────────────────────────────
# Persist the gate output (the model's blind-run found it vanished to stdout — can't audit post-hoc).
Stage "validation gate (schema + provenance)"
$pkg = Join-Path $chartDir "_model_input"
New-Item -ItemType Directory -Force -Path $pkg | Out-Null
$valReport = Join-Path $pkg "validation_report.txt"
& python (Join-Path $repo ".agents\skills\schema-validator\scripts\validate_chart.py") "--chart-dir" $chartDir 2>&1 | Tee-Object -FilePath $valReport
if ($LASTEXITCODE -ne 0) { throw "GATE FAILED: schema validation. Not proceeding to deliverable. See $valReport" }
Recipe "check_chart_provenance.ps1" @("-ChartsRoot",$PrivateRoot,"-ChartId",$chartId) | Tee-Object -FilePath $valReport -Append
Write-Host "  schema + provenance: PASS (report -> $valReport)"

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

## Порядок работы — сначала чтение, потом сверка
Лучше всего читается так: сперва пойми карту КАК СИСТЕМУ (портрет → тема года → окна → сферы) и напиши
прозу из этого понимания — twin.md, потом prose.md. Реестр `coverage_dispositions.csv` (~200 строк)
заполняй ПОСЛЕ, как ретроактивную сверку против уже написанного: что из факторов я использовал, что
осознанно отбросил и почему. Это не «перечисли всё до прозы» (так чтение скатывается в чек-лист, а проза
— в методичку), а «убедись, что после живого чтения ничего не потеряно». Гейт всё равно проверит реестр
перед сборкой — но к тому моменту проза уже написана из понимания, а не из режима перечисления.

Две вещи про то, КАК думать (а не только в каком порядке):
- **Главное года кристаллизуется в КОНЦЕ рассуждения, не в начале.** «Ось года / самый важный фактор» —
  это ВЫВОД из чтения, а не посылка для него. Если поставить ось в начале twin, дальше легко начать
  подгонять факторы под неё (а не выводить её из них). В twin иди от факторов к оси: фактура по слоям →
  как складывается → и только потом, что выходит главным. В отчёте ось может стоять в начале (читателю
  так удобнее) — но к тому моменту она у тебя уже ВЫВЕДЕНА, не угадана наперёд.
- **Гипотезу главного проверь один раз серьёзно — и доверься.** Когда ось наметилась, спроси: держится
  ли она под честной попыткой её опровергнуть? Опора — СХОЖДЕНИЕ ПО СЛОЯМ: если в одну сторону тянут
  несколько независимых слоёв (транзит + дирекция + прогрессия + профекция) — выдержала, бери уверенно.
  Один слабый слой — пересмотри. Это ОДИН раунд проверки, не бесконечное сомнение: допроверка нужна,
  чтобы вывод был твёрдым, а не чтобы расплыться в «с одной стороны / с другой». Проверил — доверься.
- **Перепроход.** Когда сферы и окна собраны — пройди по ним ВТОРОЙ раз свежим взглядом: где-то вес
  сместится, тихая сфера окажется и правда тихой, а громкая — перегретой. Второй проход уточняет; на
  нём чтение и сходится.

## Три вещи, без которых не работает (это основа, не про стиль)
- Числа бери из посчитанных файлов; не выдумывай и не прикидывай на глаз. Чего нет в данных — лучше
  сказать «нет», чем дорисовать. ОСОБЕННО ДОМА: дом планеты бери из посчитанного (`phase_vectors`
  H_house / `sphere_routing` — Placidus), НИКОГДА на глаз по близости к углу. «Солнце под MC» ≠ «Солнце
  в 10-м»: 3° под MC — это 9-й дом, кульминирующий. Дом на глаз → ошибка в портрет + рассинхрон разделов.
- Соляр читается ОТНОСИТЕЛЬНО натала, не сам по себе: натал — фундамент, соляр кладётся поверх.
- Все данные клиента остаются в этой `.private`-папке.

## Как обычно читают (ориентир, не чек-лист — порядок и глубину выбираешь сам)
Натал как целое (секта, темперамент, управитель, диспозиторы/рецепции — двигатель, угловые и
аспектированные тела, достоинства) → соляр против натала (SR-ASC и его управитель, SR-планеты на
натальные точки, хозяин года из профекции — сходятся ли в одну сторону) → транзитные окна года.
SR-Солнце на своём же градусе — это определение возврата, не событие; пропусти.

## Совет на развилке (advisor) — ИСПОЛЬЗУЙ, ЕСЛИ есть такой инструмент
Если в твоей среде есть второй-мнение/advisor — сверяйся, особенно на весомых развилках (рамка чтения
ПЕРЕД прозой и реестром — пока не закостенело; тупик; смена подхода). Это улучшает результат — не
экономь на нём. Бери из ответа РАМКУ и фактические правки, не обязан следовать всему (может уйти в
сторону — твоё суждение решает). ⚠️ КАЖДОЕ обращение ЛОГИРУЙ в `advisor_log.md` (в этой же папке):
вопрос · ключевое из ответа · что ТЫ взял / что отверг и почему. Это не для клиента — это КОПИМ ПРАКТИКУ:
по этим логам мы потом чиним харнесс (повторяющийся совет = недостающее правило/баг). Инструмента нет
или недоступен → просто продолжай, не блокируйся; отметь в логе «advisor недоступен».

## Фазовый слой — фишка метода, ради неё многое
Это то, что делает отчёт не гороскопом. В пакете рядом — `phase_vectors.csv` (стадия каждого тела),
`zakharian_dignities.csv`, `12_monthly_phase_windows.csv` (год как 12 фаз-сегментов от ДР). Стадийный
слой: на какой стадии тело/год (импульс · ресурс · связь · база · творчество · служение · зеркало ·
трансформация · стратегия · результат · оптимизация · архив). Две вещи хорошо ложатся в прозу: стадия
ключевых тел простым словом («главный твой инструмент, ум, сейчас на стадии завершения-и-результата») и
привязка окон к фазе-сегменту года (сентябрьское окно — в сегменте «связь», зимний поворот — в
«трансформация»), чтобы тайминг рифмовался с ритмом года. Несёшь качество стадии простым языком — без
нотации `P⟨⟩` и имени автора. Калибровка: Z (знак) и H (дом) — ●; микрофазы z/h и диспозиторная D — ◐.
Фаза ПОЗИЦИИ (в т.ч. транзитной/прогрессивной/директной планеты — её градус в момент T) — это тот же
оператор, разрешена (●/◐). А вот фаза аспектного ЦИКЛА (формирование→перфекция→расхождение как 12-фаз)
у нас НЕ выверена по источнику — если строишь, то только `kalpita`, внутренней пометкой, НЕ в текст и
НИКОГДА как «метод Захаряна так говорит».
Фаза — это качество тела: она вплавляется в текст про это тело, его сферу, его окно («Меркурий,
управитель карты, в домициле — и сейчас на ноте результата»). НЕ выноси в отдельный раздел «Фазовая
картина» — это превращает глубину в оговорку и дисклеймер.

## Слой склонений (параллели/контрпараллели + OOB) — НЕ теряй
Кроме долготных аспектов есть аспекты по СКЛОНЕНИЮ: параллель (работает как соединение) и
контрпараллель (как оппозиция) — в run-каталогах и в coverage (`*.declasp.*`). И OOB: тело «вне границ»
(δ > 23°26′) действует за рамками нормы — отдельный фактор (`*.oob.*`). Слой устойчив по склонению, не
по времени → калибровка ●. Читай его и в натале, и в соляре, в соотношении с долготным.

## Углубление натала: дирекции и прогрессии (на «сейчас»)
В coverage есть `dir2n.*` (дирекции солнечной дуги к наталу) и `prog2n.*` / `prog.obj.*` (вторичные
прогрессии к наталу) — это НАТАЛЬНЫЙ таймлайн: дуга датирует событие, прогрессия показывает внутреннее
созревание на текущий момент жизни. Используй как фон-углубление портрета и подтверждение тем года
(если дирекция/прогрессия садится на тот же натальный фактор, что и соляр/транзит — тема звучит ещё
раз, это усиление). Прогрессия со сменой знака (`prog.obj.*` помечен «сменил знак») — это смена
КАЧЕСТВА планеты на этот период; особенно значимо, если это управитель года или управитель карты
(тогда это несущая тема, не фон — обязательно в чтение). Не перегружай прозу числами — это глубина для
тебя, в текст идёт смысл.
Реестр большой, тесные дирекции/прогрессии легко проскользнуть. Тесный (орб < 0.5°) `dir2n`/`prog2n`/
склонение глянь внимательнее — тесная дирекция на управителя карты или года (директный Плутон ☍
натал-Меркурий, орб 0.4°) обычно несущая. Кладёшь в фон — пусть будет короткая причина в `basis`.

## Лунные узлы (ось роста/освобождения) — НЕ немая точка
Узлы есть в натале (позиция + аспекты к ним, `natal.ptasp.*`), в дирекциях (`dir2n.*`), в соляре
(`sr.point.*` с домом соляра) и в транзитах как ОСЬ ГОДА (`carrier_windows`: транзитный Сев.Узел на
натальной точке = «узловой год», активация оси судьбы). Читается оси по соединению/оппозиции/квадрату
(квадрат = «на изгибе»): Сев.Узел — куда тянет рост, Юж.Узел — что отпускается/привычная колея. Только
СУ — носитель оси; ЮУ всегда напротив (отдельно не дублируй). Светило/управитель на оси — сильный сигнал.

## Что сдать (в эту же папку)
1. `twin.md` — твои рабочие заметки: фактура из данных + твоя логика, ФАКТЫ→ЛОГИКА→ВЫВОД по разделам
   работы (двойник: холодная фактура ПЕРЕД прозой, чтобы прозу можно было проследить к ней).
   ⚖️ ОБЕ оси года проходят через двойник СИММЕТРИЧНО: раздел на каждое окно (ось времени) И раздел на
   каждую ЗАРЯЖЕННУЮ сферу (ось области, `sphere_summary.csv`). Раздел сферы: ФАКТЫ = какие факторы сюда
   роутятся (`sphere_routing.csv` — выпиши их, не из головы) + роль ключевой планеты (`year_roles.csv`);
   ЛОГИКА = как складываются (натальная база → SR-заряд → сдвиг → узел); ВЫВОД = тон/вес сферы. Так
   сфера собрана ИЗ ФАКТОРОВ, а не Barnum. Тихую сферу — одной строкой «спокойный год по X».
   В КОНЦЕ — короткий список факторов, которые ты осознанно НЕ понёс в отчёт, по одной строке «почему»
   (фон/дубль темы/слабый орб). Это твоя само-проверка, что фактор отброшен сознательно, а не потерян молча.
2. `prose.md` — тёплая русская проза ПО РАЗДЕЛАМ готового отчёта (структура ниже), написанная из
   живого понимания карты: показывай, не заверяй; где вывод крепкий — увереннее, где зависит от
   точного времени — мягче (●/◐ по желанию); трудное называй честно и по-доброму.
3. `../packs/coverage_dispositions.csv` — заполни ПОСЛЕ прозы, как ретроактивную сверку: пройди ~200
   строк реестра и для каждой проставь `salience` (несущий / тихий / пропущено-осознанно) + короткий
   `basis` (почему; ссылка на factor_id-основания через `;`, прозу — в `note`). Смысл — «после живого
   чтения убедись, что ничего не потеряно молча», а не «перечисли всё до прозы». Гейт проверит реестр
   перед сборкой (пустой salience не пройдёт), но к этому моменту проза уже написана из понимания.
4. `../packs/year_roles.csv` — для ключевых планет года (хозяин года, управитель карты) впиши `role`:
   одну роль на планету, единую во всех её сферах (не «Венера за меня» в любви и «против» в деньгах).
   Заполняется тем же ретро-проходом; гейт ждёт её непустой.

## Структура отчёта (форма продукта — её задаёт харнес; ты её НЕ выдумываешь и НЕ копируешь у других)
Готовый отчёт — `grand-report` (пустой шаблон и стандарт лежат тут же в пакете: `grand-report.html`,
`report-standards.md`, `prose-style-ru.md`). Разделы: портрет · год (карта года + тема) · по одной
главе на каждое транзитное окно года · 7 сфер жизни · опоры на год · метод-нота.
Твоё дело — ПРОЗА каждого раздела. Числа в техблоках, колёса/бивилы и сборку HTML→PDF делает
оркестратор из посчитанных данных. НЕ строй техблоки руками, НЕ рисуй колёса, НЕ подсматривай чужие
готовые отчёты, НЕ собирай HTML. Нет данных на раздел — скажи, не выдумывай.

## Формат `prose.md` — СТРОГИЙ контракт (сборщик парсит по маркерам [[…]])
Пиши ТОЛЬКО прозу, каждый блок начинается строкой-маркером, тело — до следующего маркера:
```
[[TITLE]] / [[COVER_KICKER]] / [[BIRTH_LINE]] / [[FORECAST_LINE]]   — по одной строке
[[TLDR]] / [[HOW_TO_READ]]                                          — абзац(ы)
[[PORTRAIT_H]] (заголовок) / [[PORTRAIT_BODY]] (абзацы)
[[YEAR_H]] / [[YEAR_LEAD]] / [[YEAR_THEME]]
[[WINDOW open=ГГГГ-ММ-ДД title=Название окна]]   — ОДИН на КАЖДОЕ выбранное несущее окно;
        open = ровно window_open из carrier_windows (ключ для колеса+техблока). Тело — проза окна.
[[SPHERE key=work title=Дело kicker=призвание]]  — ОДИН на КАЖДУЮ ЗАРЯЖЕННУЮ сферу (sphere_summary);
        key = sphere из sphere_summary. Тело — проза сферы (от натала, см. ниже).
[[PHASE_NOTE]]    — НЕ «раздел о фазах» (фаза идёт ВНУТРЬ сфер/портрета/окон, не сюда).
                    Только если есть одна тезисная фраза про ритм года, не влезшая никуда.
                    Если фаза уже в тексте — пропусти блок; пустой [[PHASE_NOTE]] хуже чем его отсутствие.
[[SUPPORTS_BODY]] / [[NOTE_METHOD]]
```
Окна: ты ОТБИРАЕШЬ несущие (не все из carrier — только значимые); техблок и колесо строит оркестратор
по `open`. Сферу без `[[SPHERE]]` оркестратор пропустит — заряженной сфере проза ОБЯЗАТЕЛЬНА.

## Сферы жизни — ОТДЕЛЬНАЯ ось, и она ГЛУБОКАЯ (это сердце отчёта, не довесок)
Окна = ось ВРЕМЕНИ (хронология). Сферы = ось ОБЛАСТИ — ПОСЛОЙНЫЙ срез темы. Это РАЗНАЯ ось организации,
НЕ «с планетами / без планет»: сфера НАСЫЩЕНА планетами, домами, аспектами, датами — детально и плотно.
ОБЪЁМ СФЕРЫ СЛЕДУЕТ ЕЁ СОБЫТИЙНОСТИ, не числу слов: богатая событиями сфера (куда бьёт много слоёв —
как «Ум» у этого клиента) может быть РАЗМЕРОМ СО ВСЕ ОКНА ВМЕСТЕ (500+ слов — это норма, не предел);
тихая — коротко, честной строкой. НЕ надувай пустое ради объёма и НЕ режь богатое ради краткости —
объём по карте. Послойно: (1) как область устроена ОТ НАТАЛА (дома сферы + их управители + жильцы +
аспекты — С ИМЕНАМИ); (2) что соляр (SR-планеты в домах сферы, sr→натал, склонения); (3) сдвиг
(прогрессии/дирекции на управителей сферы, с датами перфекций); (4) итог года. Уровень детализации
(реф): «Меркурий — управитель карты, в домициле, в 9-м — уже сильная тема. Год добавляет: Уран бьёт
дважды (сентябрь и июнь 2027), Плутон трином начинает долгую работу мысли (с марта 2027)…» — и ГЛУБЖЕ.
Даты и планеты В СФЕРЕ ОБЯЗАТЕЛЬНЫ (не пересказ окна — окно по хронологии, сфера по теме послойно). НЕ
обезличивай в «ум/струну/ветер» — это вата. Прежнее «сферы без планет/дат, даты примечание» ОТМЕНЕНО.
`sphere_summary.csv` даёт СЫРЬЁ — сколько факторов роутится в сферу (флаг charged тут грубый: «есть
факторы / нет», не вердикт «заряжена»). Заряжена сфера или тихая по-настоящему — РЕШАЕШЬ ТЫ, глядя на
факторы и их орбы в `sphere_routing.csv`: дотянулся один слабый секстиль — это тихая сфера, не
заряженная; сошлись несколько тесных на управителя — живая. Тихую назови честно («спокойный год по X»),
не заливай водой; на тихой сфере горизонт спасает от пустоты («ядра нет, но вызревает X»). Один фактор
может быть в нескольких сферах (Венера → и любовь, и деньги) — норма; роль планеты на год держи единой
во всех сферах. Тон фактора, если он и в окне, и в сфере — один (валентность из диспозиции, не пересчитывай).

## Данные
chart.yaml, outputs/ (натал/дома/точки/аспекты), coverage_factors.csv (перечень факторов — чтобы
ничего не упустить из виду), sphere_summary.csv + sphere_routing.csv (разрез по сферам), run-каталоги
(соляр: SR→натал, профекция, активации; транзиты: окна), _renders/ (колёса).
"@
Set-Content -Path (Join-Path $pkg "BRIEF.md") -Encoding UTF8 -Value $brief
Copy-Item (Join-Path $chartDir "chart.yaml") $pkg -Force -ErrorAction SilentlyContinue
$packsFactors = Join-Path $chartDir "packs\coverage_factors.csv"
if (Test-Path $packsFactors) { Copy-Item $packsFactors $pkg -Force }
# Sphere ledger (domain-axis projection): which factors route to which life-sphere + charged/тихий flags.
foreach ($sf in @("sphere_summary.csv","sphere_routing.csv","year_roles.csv")) {
  $sp = Join-Path $chartDir "packs\$sf"; if (Test-Path $sp) { Copy-Item $sp $pkg -Force }
}
# Exact declination aspects (parallels/contraparallels) — they live deep in the SR run-dir and the
# blind run lost them. Surface the tight ones (orb < 0.5°) as ONE file so the model can't miss them.
$srDeclAsp = Join-Path $srRun "08_declination_aspects.csv"
if (Test-Path $srDeclAsp) {
  Import-Csv $srDeclAsp | Where-Object { [double]($_.orb -replace ',','.') -lt 0.5 } |
    Export-Csv (Join-Path $pkg "decl_aspects_exact.csv") -NoTypeInformation -Encoding UTF8
}
# METHOD LAYER (the signature) — surface it INTO the package, else it stays buried and never reaches
# prose (blind run: phases/stages never used). 12 monthly phase-windows live deep in the SR run;
# per-body phase-vectors + Zakharian stages live in outputs/. Copy all three next to the model.
$phaseWin = Join-Path $srRun "12_monthly_phase_windows.csv"
if (Test-Path $phaseWin) { Copy-Item $phaseWin $pkg -Force }
foreach ($mf in @("phase_vectors.csv","zakharian_dignities.csv")) {
  $mp = Join-Path $chartDir "outputs\$mf"; if (Test-Path $mp) { Copy-Item $mp $pkg -Force }
}
# manifest of where everything is
@{
  chart_id = $chartId; chart_dir = $chartDir; utc = $utc; return_year = $ReturnYear
  outputs = (Join-Path $chartDir "outputs"); natal_run = $natalRun; sr_run = $srRun
  transit_carrier = $carrier; renders = $renders; coverage = $packsFactors
  pending = @("twin.md","prose.md (the [[SECTION]] contract)","coverage_dispositions.csv","year_roles.csv")
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
  # TEETH: the model must have filled the self-check registries — else no deliverable.
  Stage "deliverable gate (dispositions + year-roles filled)"
  # Gate reads packs/ — the CANONICAL location ledger writes and BRIEF tells the model to fill
  # (../packs/). Checking _model_input/ was a latent break: a model following BRIEF hit GATE FAILED.
  Assert-DeliverableReady (Join-Path $chartDir "packs")
  # BACK HALF: deterministic assembly — real wheels + compute techblocks + template fill -> HTML -> PDF.
  Stage "assemble deliverable (wheels + techblocks + PDF)"
  $prosePath = Join-Path $pkg "prose.md"
  if (-not (Test-Path $prosePath)) { throw "GATE FAILED: prose.md missing — the model produced no prose to assemble." }
  Recipe "run_assemble_report.ps1" @("-ChartId",$chartId,"-ChartsRoot",$PrivateRoot,"-ProseMd",$prosePath,"-SolarReturnRunDir",$srRun,"-NatalRunDir",$natalRun,"-TransitTimelineCsv",$carrier)
  Write-Host "  adapter done — self-check passed, report assembled (HTML+PDF in packs/)." -ForegroundColor Green
}

Write-Host "`nrun_solar_gift complete for $chartId" -ForegroundColor Green
