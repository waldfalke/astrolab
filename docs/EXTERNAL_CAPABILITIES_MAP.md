# External Capabilities Map

> ⚠️ **STALE (as of 2026-06-17) — refresh pending.** This snapshot is from March and no longer matches
> reality. Key drift: **`swissremote` at `https://www.theme-astral.me/mcp` is DEAD** — the engine moved
> to a **self-hosted Docker container** `swiss-mcp` on `http://localhost:8000` (start: Docker Desktop →
> `docker start swiss-mcp`; a Node-25 libuv teardown crash is non-fatal). Treat the provider table below
> as historical until a fresh `run_mcp_provider_probe.ps1` regenerates it. Tracked in `REGISTRIES.md`.

Snapshot date: 2026-03-04
Source snapshot run: `artifacts/results/provider_probe_20260304_110257`

## 1) External Providers (MCP HTTP)

| Provider | URL | Family | Health (snapshot) | Tool count | Key tools we use | Current role |
|---|---|---|---|---:|---|---|
| swissremote | https://www.theme-astral.me/mcp | western | healthy | 4 | `calculate_planetary_positions`, `calculate_transits`, `calculate_solar_revolution`, `calculate_synastry` | Primary provider (houses/placidus-oriented workflows) |
| ephem | https://ephemeris.fyi/mcp | western | healthy | 11 | `get_ephemeris_data`, `calculate_aspects`, `get_moon_phase`, `get_daily_events`, `compare_positions` | Backup + continuity + broad raw tooling |
| vedastro | https://mcp.vedastro.org/api/mcp | vedic | healthy | 6 | `get_horoscope_predictions`, `get_astrology_raw_data`, `get_ashtakvarga_data` | Probe-only today (not in production recipes) |

Notes:

- Production profile is defined in `artifacts/mcp-recipes/provider_profile.yaml`.
- Active failover path in recipes is primary `swissremote` -> backup `ephem`.

## 2) MCP Transport/Client Layer

| External component | How used in repo | Key capabilities | Where configured |
|---|---|---|---|
| MCPorter | `npx -y mcporter call` and `list` | Uniform MCP call envelope for HTTP/stdio servers; JSON output mode | `artifacts/mcp-recipes/lib/mcp_helpers.ps1` |
| npm/npx | Runtime delivery for MCPorter | No global install required | `package.json` (`mcporter` dependency) |
| Obsidian MCP (stdio, optional) | Probed via MCPorter stdio mode | Note/canvas/vault operations (server-dependent) | `artifacts/mcp-recipes/run_obsidian_mcp_probe.ps1` |

Operational behavior already implemented:

- Timeout propagation via `MCPORTER_CALL_TIMEOUT`.
- Retry loop for Swiss primary calls (`MaxAttempts=3`).
- Retry telemetry fields in summaries:
  - `SWISS_RETRY_TOTAL`
  - `SWISS_RETRY_BY_TOOL`

## 3) Lightning / L402 Payment Layer

Snapshot date: 2026-03-06
Source: `l402-proof-of-vision/tasks/research_log_lightning_mcp_ecosystem_20260306.md`

### Server-side (L402 gate in front of our API)

| Component | Role | Docker image | Connects to | Regtest | Status |
|---|---|---|---|---|---|
| **Aperture** (Lightning Labs) | L402 reverse proxy — 402 + macaroon + invoice + verify | `lightninglabs/aperture:v0.3-beta` | LND gRPC (tls.cert + macaroon) | YES (`authenticator.network: "regtest"`) | Selected for Phase 2 |

Config: YAML (`aperture.yaml`). Define `services[]` with hostregexp, pathregexp, address, price (sats).
Repo: https://github.com/lightninglabs/aperture

### Client-side (agent pays for L402-protected API)

| Component | Role | MCP tools | Connects to | Regtest | Status |
|---|---|---|---|---|---|
| **refined-element/lightning-enable-mcp** | L402 client for AI agents | 15 (`access_l402_resource`, `pay_invoice`, `create_invoice`, `discover_api`...) | LND REST + macaroon; also Strike, NWC | YES (parses `lnbcrt`) | Selected for Phase 2 |
| ehallmark/btc-lightning-mcp-server | Direct LND gRPC wrapper | 5 (`pay_invoice`, `create_invoice`, `check_invoice_is_settled`...) | LND gRPC (tls.cert + macaroon) | YES | Fallback |

### Infrastructure (test network)

| Component | Role | Docker image | Notes |
|---|---|---|---|
| bitcoind | Regtest blockchain | `lncm/bitcoind:v25.0` | Needs `-rpcbind=0.0.0.0` for cross-container |
| LND (server) | Invoice generation for Aperture | `lightninglabs/lnd:v0.17.0-beta` | Needs `--tlsextradomain=<service_name>` |
| LND (client) | Payment wallet for client-agent | `lightninglabs/lnd:v0.17.0-beta` | Separate volume, funded via bitcoind |

### Evaluated but not selected

| Component | Why not |
|---|---|
| polar-mcp (jamaljsr) | Requires Polar GUI (Electron). No headless/Docker/CI. Dev-only. |
| getAlby/mcp | NWC-only (no direct LND gRPC). No regtest support. |
| PayGated | Credit system + Stripe. Not L402/Lightning. |
| SatGate MCP Proxy | Client-side budget proxy only. No invoice creation. |
| lightningfaucet/lightning-wallet-mcp | SaaS only. No self-host, no regtest. |

### Decision guidance

- Need to gate an API with L402 → use **Aperture** as reverse proxy.
- Need an agent to pay L402 APIs → use **refined-element** MCP.
- Need low-level LND control from Python → use **ehallmark** client.
- Need local dev testing with GUI → install Polar + polar-mcp (optional).

## 4) Runtime Platforms/Libraries

| External component | Purpose | Used by |
|---|---|---|
| PowerShell 7 (`pwsh`) | Main orchestration/runtime for recipes | `artifacts/mcp-recipes/*.ps1` |
| Python 3.11+ | Skill scripts (validation/export) | `.codex/skills/*/scripts/*.py` |
| `pyyaml` | YAML read/write in Python skills | schema-validator, obsidian-export |
| Node.js | host for `npx mcporter` | all MCP recipe calls |

## 4) Current Capability Coverage

Covered now:

1. Planetary/luminary positions
2. Major aspects and deltas
3. Moon phase and daily events
4. House cusps (Placidus) + chart points
5. Secondary progressions
6. Solar arc directions
7. Transit-to-natal matrix
8. Provider failover and cross-provider QC
9. Chart project provenance/schema validation

Known gaps:

1. Declination + parallel/contraparallel
2. Native chart wheel image rendering from external providers (handled internally by renderer roadmap)
3. Unified production profile for Obsidian MCP provider selection (currently optional, user-chosen server)

## 5) How To Refresh This Map

1. Run provider probe:

```powershell
pwsh artifacts/mcp-recipes/run_mcp_provider_probe.ps1
```

2. Take latest run from:

- `artifacts/results/provider_probe_<timestamp>/`

3. Update this document with:

- health status
- tool counts and key tool names
- role changes (primary/backup/probe-only)
- Obsidian MCP probe outcome (if enabled)

## 6) Decision Guidance

- Need robust production continuity -> use `swissremote` primary + `ephem` backup.
- Need broad raw ephemeris utilities -> use `ephem`.
- Need vedic-specific experimentation -> evaluate `vedastro` in isolated recipe before production adoption.
