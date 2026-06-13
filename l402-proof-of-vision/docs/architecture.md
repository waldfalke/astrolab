# Architecture — L402 Proof of Vision (Phase 2)

## Target topology

```
                 ┌─────────────────────────────────────────┐
                 │            Docker Compose (regtest)      │
                 │                                          │
  HTTP :8081     │  ┌──────────┐        ┌──────────────┐   │
 ────────────────┼─►│ Aperture │───────►│  mock-api    │   │
                 │  │ (L402    │  :3000 │  (pure       │   │
                 │  │  proxy)  │        │   backend)   │   │
                 │  └────┬─────┘        └──────────────┘   │
                 │       │ gRPC :10009                      │
                 │  ┌────▼─────┐                            │
                 │  │   lnd    │◄──── ZMQ ────┐            │
                 │  │ (server) │              │            │
                 │  └──────────┘        ┌─────┴──────┐     │
                 │                      │  bitcoind   │     │
                 │  ┌──────────┐        │  (regtest)  │     │
                 │  │   lnd-   │◄──── ZMQ ────┘            │
                 │  │  client  │              │            │
                 │  └────▲─────┘        └────────────┘     │
                 │       │ gRPC :10009                      │
                 │  ┌────┴─────────┐                        │
                 │  │ client-agent │                        │
                 │  │ (pays L402)  │                        │
                 │  └──────────────┘                        │
                 └─────────────────────────────────────────┘
```

## L402 flow (step by step)

```
1. client-agent ──GET /sun_sign──► Aperture
2. Aperture: no L402 token → creates invoice via lnd (server)
3. Aperture ──402 + WWW-Authenticate: L402 macaroon="...", invoice="lnbcrt..."──► client-agent
4. client-agent: parses invoice, pays via lnd-client (sendPaymentSync)
5. client-agent: gets preimage from payment response
6. client-agent ──GET /sun_sign + Authorization: L402 macaroon:preimage──► Aperture
7. Aperture: validates preimage against invoice hash → proxies to mock-api:3000
8. mock-api ──{sign: "Leo", paid_resource: true}──► Aperture ──► client-agent
```

## Component responsibilities

| Component | Owns | Does NOT own |
|---|---|---|
| **Aperture** | L402 challenge, invoice creation, macaroon minting, preimage verification, rate limiting | Business logic |
| **mock-api** | Astro computation, JSON response | Authentication, payments |
| **client-agent** | Parse 402, pay invoice via own LND, retry with proof | Invoice creation |
| **lnd (server)** | Invoices for Aperture, receives payments | Client wallet |
| **lnd-client** | Client wallet, sends payments | Server invoices |
| **bitcoind** | Block production, on-chain | Lightning |

## Config files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Full stack definition |
| `aperture.yaml` | Aperture L402 proxy config (services, pricing, LND connection) |
| `scripts/setup-channel.sh` | Fund lnd-client, open channel, mine blocks |
