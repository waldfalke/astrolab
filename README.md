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

## Full Setup (from scratch)

Follow these steps in order. An AI agent (Claude Code) can execute all of them.

### 1. Prerequisites

| Tool | Required version | Check |
|------|-----------------|-------|
| Windows + PowerShell 7 | `pwsh` 7+ | `pwsh --version` |
| Python | 3.11+ | `python --version` |
| Node.js | **18–22 LTS** | `node --version` |
| Docker Desktop | any recent | `docker info` |

> **Node 25 is broken for this project.** The `npx mcporter` MCP client crashes on teardown
> under Node 25 (libuv assertion, KI-006). The crash is partially handled, but using Node LTS
> eliminates it entirely. Install [nvm-windows](https://github.com/coreybutler/nvm-windows) if
> you need to manage multiple Node versions: `nvm install 22 && nvm use 22`.

### 2. Clone and install packages

```powershell
git clone <repo-url>
cd CATMEastrolab
npm install                              # installs mcporter and other Node deps
python -m pip install pyyaml            # YAML parsing for validation
python -m pip install tzdata            # REQUIRED on Windows: zoneinfo has no tz data without this
```

> `tzdata` is mandatory on Windows. Without it, every recipe that converts a local birth time
> to UTC will fail with `ZoneInfoNotFoundError`. The recipes use Python `zoneinfo` — it works
> out of the box on Linux/macOS but needs `tzdata` explicitly on Windows.

### 3. Build the Swiss Ephemeris provider (swissremote)

The primary astrology provider runs as a self-hosted Docker container.
The public `theme-astral.me` endpoint was decommissioned in 2026-06.

**Build the image (one-time, ~3–5 min, downloads ephemeris data):**

```powershell
docker build -t swiss-mcp:local infra/swiss-mcp
```

**Start the container:**

```powershell
docker run -d --name swiss-mcp --restart unless-stopped -p 8000:8000 -e MCP_HTTP_MODE=true swiss-mcp:local
```

**Verify:**

```powershell
docker ps --filter "name=swiss-mcp"
# Expected: Up ... (healthy)   0.0.0.0:8000->8000/tcp

(Invoke-WebRequest http://localhost:8000/health).Content
# Expected JSON: {"status":"ok",...}
```

The container restarts automatically when Docker starts. If you need to start it manually:

```powershell
docker start swiss-mcp
```

Override the endpoint with `$env:SWISS_MCP_URL` if you run it on a different host or port.

### 4. Sync agent skills

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents -IncludeClaude
```

This mirrors `.agents/skills/` into `.claude/skills/` so Claude Code can discover them.
Re-run after pulling updates that touch `.agents/skills/`.

### 5. Smoke test

```powershell
# Natal (should hit swissremote as primary, exit 0)
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1 `
  -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
# Check: artifacts/results/natal_failover_verify_*/00_summary.txt
#   PROVIDER_USED=swissremote
#   RUN_STATUS=FULL

# House layer / Placidus (requires swissremote — ephem cannot do houses)
pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1 `
  -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
# Check: artifacts/results/house_placidus_verify_*/00_summary.txt
#   HOUSE_COUNT=12
#   HOUSE_SYSTEM=Placidus
```

If `PROVIDER_USED=ephem` appears in the natal summary, the swissremote container is not reachable —
go back to step 3.

### 6. Claude Code integration

`.mcp.json` is already in the repo root. Claude Code picks it up automatically when you open
the project folder — no extra configuration needed. The three MCP servers (swissremote, ephem,
vedastro) appear as native tools in the session.

The `.claude/` directory contains project-scoped settings and synced skills. It is committed
to the repo; do not hand-edit `.claude/skills/` (sync from `.agents/skills/` instead).

---

## MCP Providers

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

## Running a Solar Return Gift Report

After setup is complete (swissremote container running, skills synced):

```powershell
pwsh artifacts/mcp-recipes/run_solar_gift.ps1 `
  -BirthLocal "1990-06-15 14:30" `
  -Timezone "Europe/Moscow" `
  -Latitude 55.75 -Longitude 37.62
```

Outputs land in `.private/charts/gift_<id>/_model_input/` — the work-package for the model step.
Client data never touches the public `charts/` directory (PII guard enforced by the script).

To relocate the solar return (person lives somewhere other than their birthplace):

```powershell
pwsh artifacts/mcp-recipes/run_solar_gift.ps1 `
  -BirthLocal "1990-06-15 14:30" -Timezone "Europe/Moscow" `
  -Latitude 55.75 -Longitude 37.62 `
  -ReturnLatitude 59.95 -ReturnLongitude 30.32   # SR cast for St. Petersburg
```

Validate any chart project:

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
