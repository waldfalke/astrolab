"""rising_hands — the FLOATING intraday rising-sign clock, minute hand only (NKS astrolab #109).

First MCPization target. This is the Python port of the *watch core* of the PowerShell recipe
`artifacts/mcp-recipes/run_rising_hands.ps1` (general mode): it scans the Ascendant across a day,
finds when the rising SIGN changes (the "караул" units), and returns those watches.

Engine = B1 (NKS #113 spike): Python is a CLIENT of the already-running self-hosted swiss-ephemeris
MCP (StreamableHTTP at http://localhost:8000/mcp, swisseph v2.10.03 pinned). Because it is the SAME
engine the PowerShell recipe calls, the numbers match the golden BY CONSTRUCTION — no second build,
no pyswisseph (that is a different #113 spike).

SCOPE (minimal, golden-test driven): ONLY the watches (start_local + asc_sign). The recipe's other
hands — natal crossings, Moon timing, phases, dignities, spheres, void-of-course, coincidences — are
deliberately NOT ported here. They are out of scope for the rising_hands watch contract.
"""
from __future__ import annotations

import asyncio
import json
import math
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# Russian sign names, index 0..11 = Aries..Pisces (same order as the recipe's $Signs).
SIGNS = (
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
)

SWISS_MCP_URL = os.environ.get("SWISS_MCP_URL", "http://localhost:8000/mcp")


def _sign_idx(lon: float) -> int:
    """Sign index 0..11 of an ecliptic longitude. Port of the recipe's SignIdx."""
    return int(math.floor(((lon % 360) + 360) % 360 / 30.0))


def _local_str(utc_min: float, tz_offset_hours: float) -> str:
    """UTC-minutes-of-day -> local HH:MM display string. Port of the recipe's LocalStr.

    tz is DISPLAY-ONLY: it shifts the shown clock, never the moment sent to swiss.
    floor BOTH fields (the recipe note: int() rounds half-to-even and would yield 'HH:60').
    """
    loc = ((utc_min + tz_offset_hours * 60) % 1440 + 1440) % 1440
    return "{:02d}:{:02d}".format(int(math.floor(loc / 60)), int(math.floor(loc % 60)))


def _cross(a: float, b: float, target: float) -> float:
    """Does the forward arc a->b pass through target? Return fraction 0..1 within the step, else -1.

    Port of the recipe's Cross (guards against backward / retro big jumps).
    """
    da = ((target - a) % 360 + 360) % 360
    db = ((b - a) % 360 + 360) % 360
    if db <= 0 or db > 180:
        return -1.0
    if 0 <= da <= db:
        return da / db
    return -1.0


async def _scan_asc(date: str, lat: float, lon: float, step_min: int) -> list[float]:
    """Floating scan: ASC longitude at every grid step across the day, via ONE swiss-mcp session.

    Returns a list of ASC longitudes, one per step (utcMin = k * step_min). The datetime sent to
    swiss is pure UTC built from date + utcMin (no tz shift) — tz is applied only at display time.
    """
    n_steps = int(1440 / step_min)
    asc = []
    async with streamable_http_client(SWISS_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for k in range(n_steps):
                utc_min = k * step_min
                iso = "{}T{:02d}:{:02d}:00Z".format(
                    date, int(math.floor(utc_min / 60)), int(utc_min % 60)
                )
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
                asc.append(float(payload["chart_points"]["Ascendant"]["longitude"]))
    return asc


def rising_hands(date: str, lat: float, lon: float, tz: float, step_min: int = 10) -> dict:
    """Compute the day's rising-sign watches (minute hand of the rising-sign clock).

    Args:
        date: day to scan, "yyyy-MM-dd".
        lat, lon: observation location.
        tz: local-time DISPLAY offset in hours (e.g. +3 for Krasnodar). Does NOT move the
            moments sent to the engine.
        step_min: floating-scan grid step in minutes. Default 10 — this matches the golden
            reference run; a different step brackets the 30deg crossings differently and can
            shift an interpolated boundary by a minute.

    Returns:
        {"watches": [{"start_local": "HH:MM", "asc_sign": "<Russian sign>"}, ...]} — exactly 12
        watches over a full day (the midnight-edge sign, which opens AND closes the scan, is merged).
    """
    asc = asyncio.run(_scan_asc(date, lat, lon, step_min))

    # MINUTE HAND: a watch boundary = the rising SIGN changes. Interpolate the 30deg crossing
    # time within the step (ASC ~linear over a step). Port of the recipe's watch loop.
    watches = []
    cur_sign = _sign_idx(asc[0])
    watch_start_min = 0.0
    for i in range(len(asc) - 1):
        s2 = _sign_idx(asc[i + 1])
        if s2 != cur_sign:
            utc_min_i = i * step_min
            b_deg = (math.floor(asc[i] / 30.0) + 1) * 30.0
            f = _cross(asc[i], asc[i + 1], b_deg % 360)
            b_min = utc_min_i + f * step_min if f >= 0 else (i + 1) * step_min
            watches.append(
                {"start_local": _local_str(watch_start_min, tz), "asc_sign": SIGNS[cur_sign]}
            )
            cur_sign = s2
            watch_start_min = b_min
    # final open watch to end of day
    watches.append({"start_local": _local_str(watch_start_min, tz), "asc_sign": SIGNS[cur_sign]})

    # 12 watches, NOT 13: a full 24h turns the ASC through all 12 signs; the same sign opens AND
    # closes the scan (wraps through midnight). Merge that edge pair into one watch so круг = 12:
    #   (a) the watch actually began before midnight -> take the last watch's start time;
    #   (b) drop the duplicated trailing watch.
    if len(watches) >= 2 and watches[0]["asc_sign"] == watches[-1]["asc_sign"]:
        watches[0]["start_local"] = watches[-1]["start_local"]
        watches = watches[:-1]

    return {"watches": watches}
