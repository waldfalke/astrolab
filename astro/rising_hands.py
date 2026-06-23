"""rising_hands — the FLOATING intraday rising-sign clock, minute hand only (NKS astrolab #109).

First MCPization target. This is the Python port of the *watch core* of the PowerShell recipe
`artifacts/mcp-recipes/run_rising_hands.ps1` (general mode): it scans the Ascendant across a day,
finds when the rising SIGN changes (the "караул" units), and returns those watches.

Engine-agnostic (NKS #115): rising_hands does NOT call any engine directly. It asks the THIN seam
`astro.engine.compute_asc_series` for the day's ASC longitudes and stays engine-blind. The default
engine is B1 (swiss-mcp client, swisseph v2.10.03 — the SAME engine the PowerShell recipe calls, so
the numbers match the golden BY CONSTRUCTION); engine="a" (or env SWISS_ENGINE=a) runs the whole
clock on in-process pyswisseph where it is installed. The seam is the ONLY place the engine differs.

SCOPE (minimal, golden-test driven): ONLY the watches (start_local + asc_sign). The recipe's other
hands — natal crossings, Moon timing, phases, dignities, spheres, void-of-course, coincidences — are
deliberately NOT ported here. They are out of scope for the rising_hands watch contract.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from astro.engine import compute_asc_series

# Russian sign names, index 0..11 = Aries..Pisces (same order as the recipe's $Signs).
SIGNS = (
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
)


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


def _scan_asc(date: str, lat: float, lon: float, step_min: int, engine: str | None) -> list[float]:
    """Floating scan: ASC longitude at every grid step across the day, via the engine seam.

    Builds pure-UTC moments from date + utcMin (no tz shift — tz is display-only) and hands them
    to compute_asc_series. rising_hands stays engine-blind; only `engine` is threaded through.
    """
    n_steps = int(1440 / step_min)
    base = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    moments = [base + timedelta(minutes=k * step_min) for k in range(n_steps)]
    return compute_asc_series(moments, lat, lon, engine=engine)


def rising_hands(
    date: str, lat: float, lon: float, tz: float, step_min: int = 10, engine: str | None = None
) -> dict:
    """Compute the day's rising-sign watches (minute hand of the rising-sign clock).

    Args:
        date: day to scan, "yyyy-MM-dd".
        lat, lon: observation location.
        tz: local-time DISPLAY offset in hours (e.g. +3 for Krasnodar). Does NOT move the
            moments sent to the engine.
        step_min: floating-scan grid step in minutes. Default 10 — this matches the golden
            reference run; a different step brackets the 30deg crossings differently and can
            shift an interpolated boundary by a minute.
        engine: which compute engine to use ("b1" default / "a" pyswisseph). None -> env
            SWISS_ENGINE, else "b1". Forwarded to the seam; rising_hands itself stays engine-blind.

    Returns:
        {"watches": [{"start_local": "HH:MM", "asc_sign": "<Russian sign>"}, ...]} — exactly 12
        watches over a full day (the midnight-edge sign, which opens AND closes the scan, is merged).
    """
    asc = _scan_asc(date, lat, lon, step_min, engine)

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
