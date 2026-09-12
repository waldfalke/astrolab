<img src="assets/astrolab-hero.png" alt="Astrolab — небесный путешественник с астролябией" width="100%">

# Astrolab

Астрология для работы с ИИ. Astrolab рассчитывает карту, соляр и транзиты —
ты с агентом разбираешь, что они могут значить для тебя.

[Создать STARS](docs/stars/README.md) · [Выбрать разбор](#разборы) ·
[Подключить расчёты](#run-with-docker) · [API](docs/mcp-api.md)

## STARS.md — ИИ, который лучше понимает тебя

<img src="assets/stars-dialogue.png" alt="Человек и собеседник вместе складывают созвездие — общий язык STARS" width="100%">

STARS.md помогает ИИ лучше понимать тебя и учитывать это в совместной работе:
какие вопросы задавать, что предлагать и как объяснять.

Всё, что ты разберёшь с агентом, сохраняется. К этому можно возвращаться, дополнять
и пересматривать — чтобы взаимопонимание развивалось по мере общения.

**[Сделать свой STARS →](docs/stars/README.md)** · [Посмотреть пример](docs/stars/EXAMPLE.md)

Начать можно без установки расчётного сервера.

## Разборы

Выбери тему и передай поручение своему агенту.

<p>
<a href="docs/recipes.md#natal"><img src="assets/natal-card.svg" alt="Натальная карта. Увидеть карту целиком: что связано между собой, где напряжение и на что можно опереться. Разобрать карту →" width="360"></a>
<a href="docs/recipes.md#solar"><img src="assets/solar-card.svg" alt="Соляр. Разобрать личный год: его основные темы и их связь с натальной картой. Посмотреть год →" width="360"></a>
</p>
<p>
<a href="docs/recipes.md#transits"><img src="assets/transits-card.svg" alt="Транзиты. Увидеть развитие периода: длительный фон, точные прохождения и возвращение одной темы. Разобрать период →" width="360"></a>
<a href="docs/recipes.md#day"><img src="assets/day-forecast-card.svg" alt="Прогноз дня. Проследить день в движении: общий фон, смену ритма и часы, когда сходятся несколько указаний. Как устроен разбор →" width="360"></a>
</p>

Знаешь астрологию глубже? Собирай свои разборы из [расчётов API](docs/mcp-api.md).
Astrolab возвращает структурированные данные и не ограничивает тебя этими рецептами.
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
