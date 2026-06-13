# 14 L402 / Lightning Payment Stack

## Overview

The project implements aA2A (Automated Agent-to-Agent) commerce via the L402 protocol.
An agent discovers a paid API, receives HTTP 402 with a Lightning invoice, pays it, and gains access.

## Architecture

```
client-agent ──→ Aperture (:8081) ──→ astro-api (:3000)
  (L402 client)    (L402 gate)         (pure backend)
       ↕                 ↕
    lnd-client         lnd (server)
       ↕                 ↕
           bitcoind (regtest)
```

## Components

### Server-side: Aperture
- **What:** L402 reverse proxy by Lightning Labs. Sits in front of any API.
- **Docker:** `lightninglabs/aperture:v0.3-beta`
- **Config:** `aperture.yaml` — services with price in sats, rate limits, macaroon capabilities.
- **Connects to:** LND via gRPC (tls.cert + macaroon).
- **Regtest:** `authenticator.network: "regtest"`
- **Repo:** https://github.com/lightninglabs/aperture

### Client-side: refined-element/lightning-enable-mcp
- **What:** MCP server giving AI agents a Lightning wallet + L402 auto-pay.
- **Key tool:** `access_l402_resource` — full L402 cycle (402 → parse → pay → retry with preimage).
- **Connects to:** LND REST + macaroon (also supports Strike, NWC).
- **Regtest:** YES (parses `lnbcrt` prefix).
- **Repo:** https://github.com/refined-element/lightning-enable-mcp

### Fallback client: ehallmark/btc-lightning-mcp-server
- **What:** Direct LND gRPC wrapper (Python). 5 MCP tools.
- **Repo:** https://github.com/ehallmark/btc-lightning-client

## Docker gotchas (known issues)

1. bitcoind needs `-rpcbind=0.0.0.0` — otherwise RPC listens on 127.0.0.1 only.
2. LND needs `--tlsextradomain=<docker_service_name>` — otherwise TLS cert won't match.
3. When changing LND TLS params, delete the `lnd_data` volume — cert won't regenerate otherwise.
4. LND proto file is `lightning.proto`, not `rpc.proto`.
5. After starting bitcoind+LND, create wallet (`createwallet`) and mine 101+ blocks for maturity.

## Working directory

All L402 artifacts live in `l402-proof-of-vision/`.

- `docker-compose.yml` — full stack definition
- `mock-api/` — backend service (Node.js/Express)
- `client-agent/` — agent script (Node.js)
- `tasks/` — task specs + logs
- `BACKLOG.md` — task tracking with Phase 1 (done) and Phase 2 (Aperture)

## Detailed research

See `l402-proof-of-vision/tasks/research_log_lightning_mcp_ecosystem_20260306.md`
