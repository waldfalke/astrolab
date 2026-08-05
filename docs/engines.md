# Calculation engines

Astrolab has one computation interface with two implementations.

## Engine A

The public Docker image uses in-process `pyswisseph` with four pinned `.se1` files. The image verifies
their hashes during the build. A source checkout obtains the same files with:

```powershell
pwsh infra/ephe/get-ephe.ps1 -Source web
```

Set `SWISS_ENGINE=a` and point `SWISS_EPHE_PATH` at `infra/ephe/files`.

## Engine B1

Engine B1 calls a `swiss-mcp` StreamableHTTP endpoint. It exists for maintainer comparisons and failover and
is selected with `SWISS_ENGINE=b1`. Override its address with `SWISS_MCP_URL`.

The public Docker image does not require Engine B1. The public release gate is:

```powershell
$env:SWISS_ENGINE = "a"
$env:SWISS_EPHE_PATH = (Resolve-Path "infra/ephe/files").Path
$env:REQUIRE_ENGINE_A = "1"
uv run pytest -m "not needs_swiss_mcp" -q
```

Tests marked `needs_swiss_mcp` are maintainer comparisons. Their result is reported only together
with the sidecar version or image digest; they are not part of the fresh-checkout claim.
