# swiss-mcp — self-hosted `swissremote` primary

Reproducible Docker build of the Swiss Ephemeris MCP server that backs the **primary**
astrology provider (`swissremote`). It exposes the same 4 tools the recipes expect
(`calculate_planetary_positions`, `calculate_transits`, `calculate_solar_revolution`,
`calculate_synastry`) plus full **Placidus** house cusps.

## Why this exists

The public demo `https://www.theme-astral.me/mcp` was decommissioned (DNS NXDOMAIN, 2026-06).
It was only the author's hosted instance of the open-source
[`dm0lz/swiss-ephemeris-mcp-server`](https://github.com/dm0lz/swiss-ephemeris-mcp-server),
a thin wrapper over the official `swetest` (Swiss Ephemeris). We self-host the same engine so
the provider chain no longer depends on anyone else's deployment.

## Pinning (reproducibility)

Both sources are pinned in the `Dockerfile` via build args, so a rebuild is deterministic:

| Source | Ref | What it is |
|---|---|---|
| `dm0lz/swiss-ephemeris-mcp-server` | `e164fced7699f0c574836895660f8f6f9b9c4bb8` | MCP server code + vendored ephemeris data (`vendor/swisseph`) |
| `aloistr/swisseph` | `v2.10.03` | Swiss Ephemeris engine compiled to `swetest` |

To move to a newer engine, bump `SWISSEPH_REF` / `DM0LZ_REF` deliberately and re-verify (below).
Never rely on an unpinned `HEAD` build for chart-project reproducibility.

## Build & run

```powershell
docker build -t swiss-mcp:swe2.10.03 infra/swiss-mcp
docker tag swiss-mcp:swe2.10.03 swiss-mcp:local
docker run -d --name swiss-mcp --restart unless-stopped -p 8000:8000 -e MCP_HTTP_MODE=true swiss-mcp:swe2.10.03
# health: curl http://localhost:8000/health  ->  {"status":"ok",...}
```

Endpoint: `http://localhost:8000/mcp` (StreamableHTTP). Consumed as primary by `.mcp.json`
(native MCP) and `artifacts/mcp-recipes/lib/mcp_helpers.ps1` (recipes; override with
`$env:SWISS_MCP_URL`).

## Verification after a (re)build

A pinned rebuild must reproduce known-good output:

```powershell
# 1. cross-check longitudes against the independent ephem provider (expect agreement < 0.01 deg)
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1 -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
#    -> 00_summary.txt: PROVIDER_USED=swissremote, RUN_STATUS=FULL

# 2. confirm the Placidus house layer (ephem cannot do houses)
pwsh artifacts/mcp-recipes/run_house_layer_placidus.ps1 -CaseId verify -Latitude 40.7 -Longitude -73.8164 -DateTimeUtc 1946-06-14T14:54:00Z
#    -> 00_summary.txt: HOUSE_COUNT=12, HOUSE_SYSTEM=Placidus
```

## Known issue

On Windows + Node 25 the `npx mcporter` StreamableHTTP client crashes on process teardown
(libuv `UV_HANDLE_CLOSING`, exit `0xC0000409`) **after** emitting valid JSON. The recipe helper
parses stdout before judging success, so this is non-blocking. See `.agents/docs/08-known-issues.md`
KI-006.
