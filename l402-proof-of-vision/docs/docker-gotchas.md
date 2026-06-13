# Docker Gotchas — L402 Stack

Known issues discovered during development. Check here FIRST when debugging.

## bitcoind

| Problem | Symptom | Fix |
|---|---|---|
| RPC not reachable from other containers | `connection refused` on :18443 | Add `-rpcbind=0.0.0.0` to command |
| No wallet on fresh start | `No wallet is loaded` | Run `bitcoin-cli -regtest createwallet "default"` |
| LND stuck on "Waiting for chain backend to finish sync" | LND logs: `start_height=0` | Mine blocks: `generatetoaddress 101 <address>` |

## LND

| Problem | Symptom | Fix |
|---|---|---|
| TLS cert doesn't match Docker hostname | `ERR_TLS_CERT_ALTNAME_INVALID: Host: lnd.` | Add `--tlsextradomain=<service_name>` to LND command |
| TLS cert not regenerated after config change | Old altnames in cert | Delete the `lnd_data` volume, restart |
| LND starts before bitcoind is ready | `connection refused` to bitcoind RPC | Use `depends_on: bitcoind: condition: service_healthy` |
| healthcheck fails during startup | `RPC server is in the process of starting up` | Increase `retries` in healthcheck (30+) |

## Aperture

| Problem | Symptom | Fix |
|---|---|---|
| Can't connect to LND | gRPC connection error | Verify `tlsextradomain` includes Aperture's view of LND hostname; check macaroon path |
| Self-signed TLS warning | Clients reject Aperture cert | Use `insecure: true` in aperture.yaml for regtest |

## Proto files

| Problem | Symptom | Fix |
|---|---|---|
| Wrong proto filename | `ENOENT rpc.proto` | Use `lightning.proto` (not `rpc.proto`) |

## General

- After `docker compose down` + volume removal, ALL state is lost (wallets, channels, certs).
- `docker compose` on Windows/Git Bash: paths starting with `/root` get rewritten to `C:/Program Files/Git/root`. Use `//root` double-slash prefix in exec commands.
- `version: '3.7'` in docker-compose.yml is obsolete — remove to avoid warnings.
