"""engine — the THIN seam where the computational engine is swappable (NKS astrolab #115).

Principle #115 (engine-agnosticism): the engine is a replaceable PART, not a commitment. It hides
behind ONE function. A golden test is the arbiter that the numbers agree across engines.

    compute_asc_series(moments_utc, lat, lon, engine=None) -> list[float]

is the SINGLE point where the engine differs. `moments_utc` are tz-aware UTC datetimes (the
engine-neutral currency); the return is the rising (Ascendant) ecliptic longitude in degrees at
each moment. The batch granularity matches the unit the caller needs (a day-scan of ASC), so B1
can keep ONE swiss-mcp session instead of one handshake per moment — and nothing engine-specific
crosses the seam.

Engines:
  * "b1" (DEFAULT) — client of the self-hosted swiss-ephemeris MCP (StreamableHTTP, v2.10.03).
    Same engine the PowerShell recipe calls, so numbers match the golden BY CONSTRUCTION. Works
    everywhere, needs no compiled wheel.
  * "a" — in-process pyswisseph (`swe.houses_ex`). ~1000x faster, but OPTIONAL: importing this
    backend is deferred, so a missing pyswisseph never breaks `import astro.engine`. Preferred
    where available (#115: owner's preference, all else equal), but NOT the default — B1 runs
    without a C build.

This is NOT a plugin framework — it is one seeded function with a two-branch dispatch. YAGNI.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
from datetime import datetime, timezone

DEFAULT_ENGINE = os.environ.get("SWISS_ENGINE", "b1").lower()

SWISS_MCP_URL = os.environ.get("SWISS_MCP_URL", "http://localhost:8000/mcp")


def compute_asc_series(
    moments_utc: list[datetime], lat: float, lon: float, engine: str | None = None
) -> list[float]:
    """Rising (Ascendant) ecliptic longitude (deg) at each UTC moment, via the chosen engine.

    Args:
        moments_utc: tz-aware UTC datetimes. The engine-neutral currency crossing the seam.
        lat, lon: observation location.
        engine: "b1" (default, swiss-mcp client) or "a" (in-process pyswisseph). None -> env
            SWISS_ENGINE, else "b1".
    """
    eng = (engine or DEFAULT_ENGINE).lower()
    if eng == "b1":
        return _asc_series_b1(moments_utc, lat, lon)
    if eng == "a":
        return _asc_series_a(moments_utc, lat, lon)
    raise ValueError("unknown engine %r (expected 'b1' or 'a')" % eng)


def _iso_utc(m: datetime) -> str:
    """A UTC datetime -> 'yyyy-MM-ddTHH:MM:SSZ'. Engine-neutral moment -> swiss-mcp wire format."""
    m = m.astimezone(timezone.utc)
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
        m.year, m.month, m.day, m.hour, m.minute, m.second
    )


# --- Engine B1: swiss-mcp client (default) -----------------------------------------------------

async def _scan_asc_b1(moments_utc: list[datetime], lat: float, lon: float) -> list[float]:
    """ASC at each moment via ONE swiss-mcp session (the session never crosses the seam)."""
    # Deferred import: keep the optional MCP client off the import path of pure-A callers.
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    out: list[float] = []
    async with streamable_http_client(SWISS_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for m in moments_utc:
                iso = _iso_utc(m)
                res = await session.call_tool(
                    "calculate_planetary_positions",
                    {"datetime": iso, "latitude": lat, "longitude": lon},
                )
                payload = None
                for c in res.content:
                    if getattr(c, "type", None) == "text":
                        payload = json.loads(c.text)
                        break
                if payload is None:
                    raise RuntimeError("swiss-mcp returned no text payload for %s" % iso)
                out.append(float(payload["chart_points"]["Ascendant"]["longitude"]))
    return out


def _asc_series_b1(moments_utc: list[datetime], lat: float, lon: float) -> list[float]:
    return asyncio.run(_scan_asc_b1(moments_utc, lat, lon))


# --- Engine A: in-process pyswisseph (optional) ------------------------------------------------

def _asc_series_a(moments_utc: list[datetime], lat: float, lon: float) -> list[float]:
    """ASC at each moment via in-process pyswisseph. Imports swisseph lazily, so a missing
    pyswisseph only breaks engine="a" (not the module import / engine="b1")."""
    import swisseph as swe  # optional dependency, imported only when engine A is requested

    out: list[float] = []
    for m in moments_utc:
        m = m.astimezone(timezone.utc)
        ut_hours = m.hour + m.minute / 60.0 + m.second / 3600.0
        jd = swe.julday(m.year, m.month, m.day, ut_hours)
        # houses_ex -> (cusps, ascmc); ascmc[0] = Ascendant. House system is irrelevant to ASC;
        # 'P' (Placidus) matches the swiss-mcp default that produced the golden.
        _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
        out.append(float(ascmc[0]) % 360.0)
    return out
