"""Replaceable calculation-engine boundary.

The engine hides behind a small public interface. Cross-engine tests verify that supported engines
produce the same values within declared tolerances.

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
    where available, but NOT the default — B1 runs
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

# Normalized lowercase body name -> swiss-mcp payload["planets"] key. The boundary's
# contract is the lowercase name (matches the recipe CSVs); B1 maps it to swiss's Capitalized key.
# Covers the full payload set so future elements (nodes/chiron/asteroids) extend without a schema
# change; the DEFAULT set is the 10 classical bodies (what planets_primary.csv / the golden carry).
_PLANET_KEY_B1 = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus", "mars": "Mars",
    "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus", "neptune": "Neptune",
    "pluto": "Pluto", "north_node": "North Node", "lilith": "Lilith", "chiron": "Chiron",
    "ceres": "Ceres", "pallas": "Pallas", "juno": "Juno", "vesta": "Vesta",
}
DEFAULT_BODIES = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)


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


def compute_positions_series(
    moments_utc: list[datetime],
    lat: float,
    lon: float,
    bodies: list[str] | None = None,
    engine: str | None = None,
) -> list[dict[str, float]]:
    """Ecliptic longitudes (deg) of `bodies` at each UTC moment, via the chosen engine.

    The positions element of the seam (#115) — the shared contract every composite above
    rising_hands consumes. One swiss-mcp call already returns planets+houses+angles together, so on
    B1 a moment is fetched ONCE and this just selects the planet slice.

    Args:
        moments_utc: tz-aware UTC datetimes (the engine-neutral currency).
        lat, lon: observation location.
        bodies: normalized lowercase body names (see _PLANET_KEY_B1). None -> the 10 classical
            (DEFAULT_BODIES).
        engine: "b1" (default, swiss-mcp client) or "a" (in-process pyswisseph). None -> env
            SWISS_ENGINE, else "b1".

    Returns:
        one dict per moment: {body -> ecliptic longitude in degrees}.
    """
    eng = (engine or DEFAULT_ENGINE).lower()
    bods = list(bodies) if bodies is not None else list(DEFAULT_BODIES)
    if eng == "b1":
        return _positions_series_b1(moments_utc, lat, lon, bods)
    if eng == "a":
        return _positions_series_a(moments_utc, lat, lon, bods)
    raise ValueError("unknown engine %r (expected 'b1' or 'a')" % eng)


def compute_houses_series(
    moments_utc: list[datetime],
    lat: float,
    lon: float,
    engine: str | None = None,
) -> list[dict]:
    """Placidus house frame (12 cusps + angles) at each UTC moment, via the chosen engine.

    The houses element of the seam (#115). A natal composite needs the full frame, not just ASC.

    Args:
        moments_utc: tz-aware UTC datetimes (the engine-neutral currency).
        lat, lon: observation location.
        engine: "b1" (default, swiss-mcp client) or "a" (in-process pyswisseph). None -> env
            SWISS_ENGINE, else "b1".

    Returns:
        one dict per moment: {"cusps": [12 floats, cusps[0] = house 1],
        "angles": {"asc","mc","dsc","ic","vertex","armc" -> deg}}.
    """
    eng = (engine or DEFAULT_ENGINE).lower()
    if eng == "b1":
        payloads = asyncio.run(_scan_payloads_b1(moments_utc, lat, lon))
        return [_select_houses(p) for p in payloads]
    if eng == "a":
        return _houses_series_a(moments_utc, lat, lon)
    raise ValueError("unknown engine %r (expected 'b1' or 'a')" % eng)


# Normalized lowercase angle name -> swiss-mcp payload["chart_points"] key.
_ANGLE_KEY_B1 = {
    "asc": "Ascendant", "mc": "Midheaven", "dsc": "Descendant",
    "ic": "IC", "vertex": "Vertex", "armc": "ARMC",
}


def _select_houses(payload: dict) -> dict:
    """Pure selector: pull the house frame out of a swiss-mcp positions payload.

    Tested deterministically against a REAL captured payload (no engine needed). Reads
    payload["houses"]["1".."12"]["longitude"] and payload["chart_points"] via _ANGLE_KEY_B1.
    """
    houses = payload["houses"]
    cusps = [float(houses[str(i)]["longitude"]) for i in range(1, 13)]
    points = payload["chart_points"]
    angles = {name: float(points[key]["longitude"]) for name, key in _ANGLE_KEY_B1.items()}
    return {"cusps": cusps, "angles": angles}


def _select_positions(payload: dict, bodies: list[str]) -> dict[str, float]:
    """Pure selector: pull `bodies` longitudes out of a swiss-mcp positions payload.

    The engine-neutral extraction contract, tested deterministically against a REAL captured
    payload (no engine needed). Maps each normalized lowercase name to its swiss key and reads
    payload["planets"][key]["longitude"].
    """
    planets = payload["planets"]
    out: dict[str, float] = {}
    for b in bodies:
        key = _PLANET_KEY_B1.get(b)
        if key is None:
            raise KeyError("unknown body %r (not in _PLANET_KEY_B1)" % b)
        if key not in planets:
            raise KeyError("body %r (%s) absent from payload['planets']" % (b, key))
        out[b] = float(planets[key]["longitude"])
    return out


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


async def _scan_payloads_b1(moments_utc: list[datetime], lat: float, lon: float) -> list[dict]:
    """Full positions payload at each moment via ONE swiss-mcp session (planets+houses+angles).

    The richer sibling of _scan_asc_b1: returns the raw payload so callers select their slice
    (positions read ["planets"], a houses element would read ["houses"]). One call per moment, one
    session for the batch — the session never crosses the seam.
    """
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    out: list[dict] = []
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
                out.append(payload)
    return out


def _positions_series_b1(
    moments_utc: list[datetime], lat: float, lon: float, bodies: list[str]
) -> list[dict[str, float]]:
    payloads = asyncio.run(_scan_payloads_b1(moments_utc, lat, lon))
    return [_select_positions(p, bodies) for p in payloads]


# --- Engine A: in-process pyswisseph (optional) ------------------------------------------------

_SWE_EPHE_PATH: str | None = None
_SWE_RUNTIME_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1", "se00433s.se1")


def _init_swe():
    """Import pyswisseph and point it at the Swiss Ephemeris data files — PER THREAD.

    Path resolution (once per process): env SWISS_EPHE_PATH, else the repo-local infra/ephe/files.
    The runtime file set is checked before use so pyswisseph cannot silently fall back to Moshier.

    Per-thread, not per-process: pyswisseph ships a thread-local Swiss Ephemeris build, so a path
    set in the main thread is INVISIBLE to worker threads. Thread IDs can be reused after a worker
    exits, so set_ephe_path runs on every entry instead of caching IDs.
    """
    global _SWE_EPHE_PATH
    import swisseph as swe  # optional dependency, imported only when engine A is requested

    if _SWE_EPHE_PATH is None:
        from pathlib import Path

        configured_path = os.environ.get("SWISS_EPHE_PATH")
        ephe_path = (
            Path(configured_path).expanduser()
            if configured_path
            else Path(__file__).resolve().parents[1] / "infra" / "ephe" / "files"
        )
        if not ephe_path.is_dir():
            detail = "ephemeris directory does not exist: %s" % ephe_path
        else:
            missing = [name for name in _SWE_RUNTIME_FILES if not (ephe_path / name).is_file()]
            detail = "missing runtime files: %s" % ", ".join(missing) if missing else ""
        if detail:
            raise RuntimeError(
                "Engine A requires Swiss Ephemeris runtime files; %s. "
                "In a source checkout run `pwsh infra/ephe/get-ephe.ps1 -Source web`, "
                "or set SWISS_EPHE_PATH to a directory containing: %s."
                % (detail, ", ".join(_SWE_RUNTIME_FILES))
            )
        _SWE_EPHE_PATH = str(ephe_path)

    swe.set_ephe_path(_SWE_EPHE_PATH)
    return swe


def _asc_series_a(moments_utc: list[datetime], lat: float, lon: float) -> list[float]:
    """ASC at each moment via in-process pyswisseph. Imports swisseph lazily, so a missing
    pyswisseph only breaks engine="a" (not the module import / engine="b1")."""
    swe = _init_swe()

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


def _houses_series_a(moments_utc: list[datetime], lat: float, lon: float) -> list[dict]:
    """House frame at each moment via in-process pyswisseph (houses_ex, Placidus). DSC/IC are
    derived (+180 deg) — pyswisseph exposes only ASC/MC/ARMC/Vertex in ascmc."""
    swe = _init_swe()

    out: list[dict] = []
    for m in moments_utc:
        m = m.astimezone(timezone.utc)
        ut_hours = m.hour + m.minute / 60.0 + m.second / 3600.0
        jd = swe.julday(m.year, m.month, m.day, ut_hours)
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
        asc = float(ascmc[0]) % 360.0
        mc = float(ascmc[1]) % 360.0
        out.append({
            "cusps": [float(c) % 360.0 for c in cusps[:12]],
            "angles": {
                "asc": asc, "mc": mc,
                "dsc": (asc + 180.0) % 360.0, "ic": (mc + 180.0) % 360.0,
                "vertex": float(ascmc[3]) % 360.0, "armc": float(ascmc[2]) % 360.0,
            },
        })
    return out


# Normalized lowercase name -> pyswisseph body constant.
def _swe_body_consts():
    swe = _init_swe()
    return {
        "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
        "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN, "uranus": swe.URANUS,
        "neptune": swe.NEPTUNE, "pluto": swe.PLUTO, "north_node": swe.TRUE_NODE,
        "lilith": swe.MEAN_APOG, "chiron": swe.CHIRON,
    }


def _positions_series_a(
    moments_utc: list[datetime], lat: float, lon: float, bodies: list[str]
) -> list[dict[str, float]]:
    """Positions at each moment via in-process pyswisseph (calc_ut per body). Imports swisseph
    lazily, so a missing pyswisseph only breaks engine="a". _init_swe points it at the SAME
    Swiss Ephemeris (.se1) files B1 serves (infra/ephe) — without them calc_ut silently falls
    back to Moshier (KI-008); the strict A-vs-B1 golden is what notices."""
    swe = _init_swe()

    consts = _swe_body_consts()
    for b in bodies:
        if b not in consts:
            raise KeyError("engine A has no constant for body %r" % b)
    out: list[dict[str, float]] = []
    for m in moments_utc:
        m = m.astimezone(timezone.utc)
        ut_hours = m.hour + m.minute / 60.0 + m.second / 3600.0
        jd = swe.julday(m.year, m.month, m.day, ut_hours)
        snap: dict[str, float] = {}
        for b in bodies:
            xx, _retflag = swe.calc_ut(jd, consts[b], swe.FLG_SWIEPH)
            snap[b] = float(xx[0]) % 360.0
        out.append(snap)
    return out
