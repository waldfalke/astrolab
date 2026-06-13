# AGENTS.md — l402-proof-of-vision

Local constraints for agents working in this subproject.

## Context

This subproject proves aA2A commerce: an AI agent autonomously pays for an API call via Lightning Network using the L402 protocol.

## Read order (local)

1. `BACKLOG.md` — task graph with phases and DAG
2. `docs/architecture.md` — target architecture and component map
3. `docs/docker-gotchas.md` — known Docker/LND/bitcoind issues
4. `tasks/` — individual task specs and logs

## Phase 2 components

| Component | Image / Source | Role |
|---|---|---|
| bitcoind | `lncm/bitcoind:v25.0` | Regtest blockchain |
| lnd (server) | `lightninglabs/lnd:v0.17.0-beta` | Invoice generation for Aperture |
| lnd-client | `lightninglabs/lnd:v0.17.0-beta` | Payment wallet for client-agent |
| Aperture | `lightninglabs/aperture:v0.3-beta` | L402 reverse proxy (gate) |
| mock-api | `./mock-api` (Node.js) | Pure astro backend (no L402 logic) |
| client-agent | `./client-agent` (Node.js) | Pays via lnd-client, gets resource |

## Hard rules

1. Do NOT write L402 logic in mock-api — Aperture handles it.
2. Do NOT use Polar or NWC — we run headless Docker only.
3. All LND services MUST have `--tlsextradomain=<service_name>` and healthchecks.
4. bitcoind MUST have `-rpcbind=0.0.0.0`.
5. After fresh volume creation, always `createwallet` + mine 101+ blocks.
6. When changing TLS params on LND, delete the volume first.

## Quick commands

```bash
# Start infra
docker compose up -d bitcoind lnd lnd-client

# Fund regtest (after both LNDs healthy)
./scripts/setup-channel.sh

# Start Aperture + backend
docker compose up -d aperture mock-api

# Run client-agent E2E
docker compose run --build client-agent
```
