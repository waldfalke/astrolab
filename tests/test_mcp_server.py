"""MCP-server golden test (NKS astrolab G2/G3): rising_hands wrapped as a FastMCP tool.

This exercises the SAME golden as tests/test_rising_hands.py, but THROUGH the MCP boundary:
a FastMCP in-memory Client calls the registered tool and we assert on its result. It proves
G2 (typed inputSchema — the tool accepts date/lat/lon/tz) and G3 (stateless return — watches
come back as data, no files). RED now: astro.server does not exist yet.
"""
import asyncio

# The server module does not exist yet — this import is the RED.
from astro.server import mcp  # noqa: E402

from fastmcp import Client

GOLDEN_INPUT = dict(date="2026-06-22", lat=45.04, lon=38.98, tz=3)
GOLDEN_FIRST_WATCH = {"start_local": "02:44", "asc_sign": "Близнецы"}
GOLDEN_WATCH_COUNT = 12


async def _call_tool():
    async with Client(mcp) as client:
        return await client.call_tool("rising_hands", GOLDEN_INPUT)


def test_tool_returns_golden_watches():
    # Drive the async in-memory MCP client from a sync test (no pytest-asyncio dependency).
    result = asyncio.run(_call_tool())
    watches = result.data["watches"]
    assert len(watches) == GOLDEN_WATCH_COUNT
    first = watches[0]
    assert first["start_local"] == GOLDEN_FIRST_WATCH["start_local"]
    assert first["asc_sign"] == GOLDEN_FIRST_WATCH["asc_sign"]
