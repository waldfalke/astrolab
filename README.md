<img src="assets/astrolab-hero.png" alt="Astrolab — небесный путешественник с астролябией" width="100%">

# Astrolab

Астрология для работы с ИИ. Astrolab рассчитывает карту, соляр и транзиты —
вы с агентом разбираете, что они могут значить для вас.

[Создать STARS](docs/stars/README.md) · [Выбрать разбор](#разборы) ·
[Подключить расчёты](#run-with-docker) · [API](docs/mcp-api.md)

## STARS.md — ИИ, который лучше понимает вас

STARS.md помогает ИИ лучше понимать вас и учитывать это в совместной работе:
какие вопросы задавать, что предлагать и как объяснять.

Всё, что вы разберёте вместе, сохраняется. К этому можно возвращаться, дополнять
и пересматривать — чтобы ваше взаимопонимание развивалось по мере общения.

**[Сделать свой STARS →](docs/stars/README.md)** · [Посмотреть пример](docs/stars/EXAMPLE.md)

Начать можно без установки расчётного сервера.

## Разборы

Выберите тему и передайте поручение своему агенту.

<table>
<tr>
<td width="50%" valign="top">
<a href="docs/recipes.md#natal"><img src="assets/natal.png" alt="Картограф с кругом натальной карты" width="220"></a>
<h3>Натальная карта</h3>
<p>Увидеть карту целиком: что связано между собой, где напряжение и на что можно опереться.</p>
<p><a href="docs/recipes.md#natal">Разобрать карту →</a></p>
</td>
<td width="50%" valign="top">
<a href="docs/recipes.md#solar"><img src="assets/solar.png" alt="Путешественница в солнечном круге" width="220"></a>
<h3>Соляр</h3>
<p>Разобрать личный год: его основные темы и их связь с натальной картой.</p>
<p><a href="docs/recipes.md#solar">Посмотреть год →</a></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="docs/recipes.md#transits"><img src="assets/transits.png" alt="Путешественник среди планетных орбит" width="220"></a>
<h3>Транзиты</h3>
<p>Увидеть развитие периода: длительный фон, точные прохождения и возвращение одной темы.</p>
<p><a href="docs/recipes.md#transits">Разобрать период →</a></p>
</td>
<td width="50%" valign="top">
<a href="docs/recipes.md#day"><img src="assets/day-forecast.png" alt="Хранитель времени с часами Солнца и Луны" width="220"></a>
<h3>Прогноз дня</h3>
<p>Проследить день в движении: общий фон, смену ритма и часы, когда сходятся несколько указаний.</p>
<p><a href="docs/recipes.md#day">Как устроен разбор →</a><br><sub>Пока не входит в публичный пакет.</sub></p>
</td>
</tr>
</table>

Знаете астрологию глубже? Собирайте свои разборы из [расчётов API](docs/mcp-api.md).
Astrolab возвращает структурированные данные и не ограничивает вас этими рецептами.
Астрологические толкования — не установленные факты и не гарантии событий.

## Available tools

- `rising_hands` - the twelve rising-sign intervals for a date and place;
- `natal` - positions, houses, angles, aspects, dignities, sect, placements, and Part of Fortune;
- `profection` - annual profection and lord of the year;
- `solar_return` - solar-return instant and return-to-natal structure;
- `transits` - exact transit events and merged carrier windows.

All datetimes crossing the API are UTC ISO 8601 unless a tool explicitly asks for a display offset.
Longitudes are ecliptic degrees in `[0, 360)`.

## Run with Docker

Docker is the shortest supported path. The image downloads the pinned Swiss Ephemeris files during
the build and verifies their SHA-256 hashes.

```powershell
docker build -t astrolab .
docker run --rm --name astrolab -p 127.0.0.1:8400:8400 astrolab
```

The MCP endpoint is `http://127.0.0.1:8400/mcp`. In another terminal:

```powershell
uv sync --frozen
uv run python examples/call_mcp.py --url http://127.0.0.1:8400/mcp
```

The example supports `rising_hands`, `natal`, `chart_workflow`, and `invalid_input`;
see the MCP documentation below.

This command exposes Astrolab only on the local machine. The server does not provide authentication
or TLS; do not publish its port on a LAN or the internet. Remote deployment requires a separate
authenticated TLS ingress with access controls.

## Run from source

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), and PowerShell 7.

```powershell
uv sync --frozen --group engine-a
pwsh infra/ephe/get-ephe.ps1 -Source web

$env:SWISS_ENGINE = "a"
$env:SWISS_EPHE_PATH = (Resolve-Path "infra/ephe/files").Path
$env:ASTRO_MCP_TRANSPORT = "http"
$env:ASTRO_MCP_HOST = "127.0.0.1"
uv run python -m astro.server
```

The server refuses to use Engine A when the required ephemeris files are absent or incomplete.

## Verify a checkout

```powershell
python tools/check_public_surface.py
uv sync --frozen --group engine-a
pwsh infra/ephe/get-ephe.ps1 -Source web

$env:SWISS_ENGINE = "a"
$env:SWISS_EPHE_PATH = (Resolve-Path "infra/ephe/files").Path
$env:REQUIRE_ENGINE_A = "1"
uv run pytest -m "not needs_swiss_mcp" -q
```

The four `needs_swiss_mcp` comparison tests additionally require the reference sidecar at
`http://localhost:8000/mcp`. They are not needed to run the public Docker image.

## Documentation

- [MCP tools](docs/mcp-api.md)
- [Calculation engines](docs/engines.md)
- [Output contract](docs/output-contract.md)

## License

Private non-commercial evaluation is permitted for 30 days. Production and commercial use require a
written license agreement. See [LICENSE](LICENSE).
