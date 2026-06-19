# CATMEastrolab

Proprietary engineering platform for astrology computation — API-first, artifact-first, agent-native.

Recipes produce reproducible, provenance-tracked outputs from Swiss Ephemeris.
Designed for AI agent consumption (aA2A): the computation substrate is deterministic;
the emergent read layer is a swappable model adapter.

## What The Platform Does

1. Reproducible calculations — no black-box UI, every number traces to a raw JSON source.
2. Provider failover — primary `swissremote` (self-hosted Swiss Ephemeris) → backup `ephem`.
3. Chart-as-project — outputs live in `charts/<chart_id>/` with schema + provenance validation.
4. Agent-native workflows — `.agents/` playbook drives AI assistants without manual steps.

## Built-In Techniques

- Natal snapshot (planets, houses Placidus, chart points, sect, motion state)
- House layer (Placidus + additional points + sect)
- Secondary progressions
- Solar arc directions
- Transit-to-natal aspect windows (carrier model with theme merging)
- Phase vectors — Zakharian stage layer
- Sphere ledger — life-domain routing
- Cross-provider QC
- Chart project build + schema/provenance validation
- Solar return gift report orchestrator (`run_solar_gift.ps1`)

## Requirements

| Tool | Version | Purpose |
|------|---------|---------|
| Windows + PowerShell 7 | `pwsh` 7+ | recipe execution |
| Python | 3.11+ | timezone resolution, validation |
| Node.js | 18–22 LTS | `npx mcporter` (MCP client); **avoid Node 25** — libuv crash on teardown (KI-006) |
| Docker | any recent | self-hosted Swiss Ephemeris MCP server |

Python package:

```powershell
python -m pip install pyyaml
```

Node packages:

```powershell
npm install
```

## Setup: Swiss Ephemeris Provider (swissremote)

The primary astrology provider runs as a local Docker container.
The public `theme-astral.me` instance was decommissioned in 2026-06 — you must build it yourself.

**Build and start (one-time):**

```powershell
docker build -t swiss-mcp:local infra/swiss-mcp
docker run -d --name swiss-mcp --restart unless-stopped -p 8000:8000 -e MCP_HTTP_MODE=true swiss-mcp:local
```

**Verify it is running:**

```powershell
docker ps --filter "name=swiss-mcp"
# Expected: Up ... (healthy)   0.0.0.0:8000->8000/tcp
```

**Health check:**

```powershell
(Invoke-WebRequest http://localhost:8000/health).Content
# Expected: {"status":"ok",...}
```

**If the container stopped (e.g. after reboot):**

```powershell
docker start swiss-mcp
```

The container has `--restart unless-stopped`, so it starts automatically after Docker itself starts.

The endpoint `http://localhost:8000/mcp` is already wired in `.mcp.json` and in the recipe helpers.
Override with `$env:SWISS_MCP_URL` if you moved it.

## MCP Providers

`.mcp.json` registers three providers for Claude Code native MCP:

| Server | URL | Role |
|--------|-----|------|
| `swissremote` | `http://localhost:8000/mcp` | primary (self-hosted, full Placidus) |
| `ephem` | `https://ephemeris.fyi/mcp` | backup (no houses) |
| `vedastro` | `https://mcp.vedastro.org/api/mcp` | probe/exploration only |

**In recipes** (production work): always go through `artifacts/mcp-recipes/lib/mcp_helpers.ps1` —
it enforces swiss→ephem failover, retry/backoff, and raw-JSON persistence.
Native MCP tools are for exploration only.

## Quick Start

1. Build the Swiss Ephemeris container (see **Setup** above).

2. Sync agent skills:

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeClaude
```

3. Smoke test — natal + house layer:

```powershell
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1 `
  -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
# -> 00_summary.txt: PROVIDER_USED=swissremote, RUN_STATUS=FULL

pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1 `
  -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
# -> 00_summary.txt: HOUSE_COUNT=12, HOUSE_SYSTEM=Placidus
```

4. Run a solar return gift report:

```powershell
pwsh artifacts/mcp-recipes/run_solar_gift.ps1 `
  -BirthLocal "1990-06-15 14:30" -Timezone "Europe/Moscow" `
  -Latitude 55.75 -Longitude 37.62
# -> .private/charts/gift_199006151430/_model_input/  (work-package for the model)
```

5. Validate a chart project:

```powershell
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId <chart_id> -ChartsRoot .private/charts
```

## Architecture

```
artifacts/mcp-recipes/     operational PowerShell recipes (main execution layer)
  lib/mcp_helpers.ps1      provider calls, failover, CSV helpers
  run_solar_gift.ps1       orchestrator: natal → SR → transits → directions → report
artifacts/schemas/         chart project JSON schema contracts
charts/<chart_id>/         public chart outputs (no PII)
.private/charts/           client chart outputs (PII — gitignored)
.agents/                   canonical machine playbook and skill layer
infra/swiss-mcp/           reproducible Docker build of swissremote
docs/                      public documentation
```

## Known Issues

See `.agents/docs/08-known-issues.md`. Key one for setup:

- **KI-006** — Node 25 + mcporter teardown crash (non-blocking, already handled in helpers).
  Use Node LTS 20 or 22 to eliminate it entirely.

## Agent-First Documentation

Main machine entrypoint: `.agents/AGENTS.md`

Full read order and operational guides: `.agents/docs/00` … `14`

Includes: smoke tests, fail-fast rules, known issues, PowerShell style, MCPorter usage, anti-patterns.

## License

Proprietary — commercial use requires a license agreement.
See [LICENSE](LICENSE) for terms.
Contact: stribojich@gmail.com
