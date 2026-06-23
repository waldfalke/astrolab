"""Headless MCP server exposing rising_hands as a typed MCP tool (NKS astrolab G2/G3).

This is the THIN wrapper: it does not recompute anything. The single tool delegates to
astro.rising_hands.rising_hands (which is the B1 swiss-mcp client). FastMCP derives the typed
inputSchema (G2) from the annotated signature, and the dict return travels back as structured
content (G3 — stateless, no files written).

The sync tool runs in a worker thread (FastMCP default run_in_thread=True), so rising_hands'
internal asyncio.run() has a fresh event loop and does not collide with the server's loop.
"""
from fastmcp import FastMCP

from astro.rising_hands import rising_hands

mcp = FastMCP("catme-astrolab")


@mcp.tool(name="rising_hands")
def rising_hands_tool(date: str, lat: float, lon: float, tz: int) -> dict:
    """Compute the day's rising-sign watches (the floating rising-sign clock, minute hand).

    Args:
        date: day to scan, "yyyy-MM-dd".
        lat: observation latitude (degrees).
        lon: observation longitude (degrees).
        tz: local-time DISPLAY offset in whole hours (e.g. 3 for Krasnodar).

    Returns:
        {"watches": [{"start_local": "HH:MM", "asc_sign": "<Russian sign>"}, ...]} — 12 watches.
    """
    return rising_hands(date=date, lat=lat, lon=lon, tz=tz)


if __name__ == "__main__":
    mcp.run()
