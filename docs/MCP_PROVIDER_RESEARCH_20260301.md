# MCP Provider Research (2026-03-01)

## Goal

Find practical MCP providers for professional astrology workflows (western-first, with house-layer support).

## Selected Runtime Providers

1. Swiss Ephemeris MCP (remote)
   - URL: `https://www.theme-astral.me/mcp`
   - Source: `https://github.com/dm0lz/swiss-ephemeris-mcp-server`
   - Why selected: houses (Placidus), chart points, transits, synastry, solar revolution.
2. Ephemeris backup MCP
   - URL: `https://ephemeris.fyi/mcp`
   - Why selected: stable base for positions/aspects/moon phase/events and continuity fallback.

## Additional Probed Provider

1. Vedastro MCP (non-western family, optional)
   - URL: `https://mcp.vedastro.org/api/mcp`
   - Source: `https://www.mcpservers.org/servers/VedAstro/VedAstroMCP`
   - Status: reachable and tool-discoverable.

## Candidate Sources for Extended Capability (future)

1. AstroMCP directory listing
   - `https://mcp.so/server/astromcp-mcp/ismaelvacco`
2. AstroMCP docs landing
   - `https://docs.astromcp.io/`
3. AstroMCP website
   - `https://www.astromcp.io/`

## Verification Artifact

Probe output (health + tool matrix):

- `artifacts/results/provider_probe_20260301_164009/provider_probe.csv`
