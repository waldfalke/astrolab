# 08 Known Issues

This file exists to keep agents calm and deterministic around expected noise.

## KI-001: Swiss provider transient 504/400

Symptoms:

- log lines mention `swissremote appears offline` or HTTP 400/504
- recipe still exits with code 0 and writes full output

Interpretation:

- non-blocking transient upstream instability

Action:

1. Check `SWISS_RETRY_TOTAL` and `SWISS_RETRY_BY_TOOL` in summary.
2. If output exists and validation passes, continue.
3. Record in TaskLog.

## KI-002: Locale CSV decimal comma in legacy synastry outputs

Symptoms:

- numbers like `82,928095` in old `03_synastry_aspect_matrix.csv`

Interpretation:

- legacy formatting path before invariant CSV fix

Action:

1. Re-run recipe with current code.
2. Use regenerated file with dot-decimals.

## KI-003: Transit recipe naming confusion

Symptoms:

- old flows use `run_synastry_matrix.ps1` for transit tasks

Interpretation:

- historical workaround, not the preferred method

Action:

- use `run_transits_to_natal.ps1` for transit jobs

## KI-004: Birth timezone argument fragility in older invocations

Symptoms:

- old command examples fail on `-BirthTimezone` parsing edge cases

Interpretation:

- invocation formatting issue; script now supports derived timezone

Action:

1. Pass `BirthDateTimeLocal` + `BirthDateTimeUtc`.
2. Leave `BirthTimezone` empty if needed.

## KI-005: Private skill intentionally absent from canonical layer

Symptoms:

- `astro-engineering-scanner` not found in `.agents/skills`

Interpretation:

- expected by policy (private skill)

Action:

- do not treat as failure in public workflows

## KI-006: mcporter crashes on process teardown under Node 25 (Windows)

Symptoms:

- stderr shows `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file src\win\async.c`
- process exits with `0xC0000409` / `-1073740791` **after** printing a complete, valid JSON result
- only affects the local swiss StreamableHTTP endpoint (`http://localhost:8000/mcp`); `ephem`
  (https) exits 0 cleanly

Interpretation:

- libuv async-handle teardown crash specific to Node v25.x (non-LTS) + mcporter StreamableHTTP
  client. The MCP call itself succeeds; only the exit code is poisoned.

Action:

1. Non-blocking. `Invoke-McpToolJson` parses stdout first and trusts a valid payload over a
   teardown-only nonzero exit, so recipes still succeed.
2. Real fix: run on Node LTS (20/22). Do not waste time debugging the assertion per call.

## KI-007: swissremote primary is self-hosted on localhost

Symptoms:

- primary URL is `http://localhost:8000/mcp`, not the historical `https://www.theme-astral.me/mcp`

Interpretation:

- the public theme-astral.me demo was decommissioned (DNS NXDOMAIN, 2026-06). swissremote now
  runs as a local Docker container (`swiss-mcp`, image `swiss-mcp:local`) built from
  `dm0lz/swiss-ephemeris-mcp-server`. Same 4 tools, full Placidus houses.

Action:

1. Ensure the container is up: `docker start swiss-mcp` (it has `--restart unless-stopped`).
2. If relocated, override with `$env:SWISS_MCP_URL`.
3. Reproducible build is pinned in `infra/swiss-mcp/Dockerfile`
   (dm0lz `e164fced…`, swisseph `v2.10.03`); rebuild + verify per `infra/swiss-mcp/README.md`.
   Never run an unpinned `HEAD` build for chart-project work.
