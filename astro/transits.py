"""transits — the transits-to-natal composite: dated aspect EVENTS over a range + carrier windows.

Port of run_transits_to_natal.ps1 range-scan mode (golden-locked to a witnessed recipe run):
sample transit longitudes at step_days; per (transit body x natal target x major aspect) build the
orb series and detect each exact pass as a LOCAL MINIMUM within orb; refine the exact time by
parabolic interpolation and the orb-ingress/egress by linear interpolation (no extra engine
calls). Retrograde multi-passes surface as separate events; carrier windows then MERGE all passes
of one (slow body, target, aspect) into ONE theme — the cause of window-bloat is un-merged retro
passes (HARNESS_PITFALLS #13). Zone (tail/core/horizon) is a date PROPERTY vs the solar-year
anchor (#84/#85), never the theme's role.

Defaults follow the recipe: transit bodies = sun..pluto + north_node (NO Moon — hourly noise at
daily steps; the rising-clock family owns intra-day), natal targets = classical 10 + ASC/MC/IC/DSC
+ natal north node, orb 1.0, step 7d (use 2-3d for clean carrier windows).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from astro.engine import (
    DEFAULT_BODIES,
    compute_houses_series,
    compute_positions_series,
)

TRANSIT_BODIES_DEFAULT = (
    "sun", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto", "north_node",
)
SLOW_CARRIERS = ("jupiter", "saturn", "uranus", "neptune", "pluto", "north_node")

_ASPECTS = (
    ("conjunction", 0.0), ("sextile", 60.0), ("square", 90.0),
    ("trine", 120.0), ("opposition", 180.0),
)


def _min_sep(a: float, b: float) -> float:
    d = abs(a % 360.0 - b % 360.0)
    return 360.0 - d if d > 180.0 else d


def _natal_targets(
    natal_moment: datetime, lat: float, lon: float, engine: str | None
) -> dict[str, float]:
    """Classical 10 + natal angles (ASC/MC/IC/DSC) + natal north node — recipe target set."""
    pos = compute_positions_series(
        [natal_moment], lat, lon, bodies=list(DEFAULT_BODIES) + ["north_node"], engine=engine
    )[0]
    angles = compute_houses_series([natal_moment], lat, lon, engine=engine)[0]["angles"]
    targets = {b: pos[b] for b in DEFAULT_BODIES}
    targets.update({
        "ASC": angles["asc"], "MC": angles["mc"], "IC": angles["ic"], "DSC": angles["dsc"],
        "north_node": pos["north_node"],
    })
    return targets


def compute_transit_events(
    natal_moment_utc: datetime,
    lat: float,
    lon: float,
    range_start_utc: datetime,
    range_end_utc: datetime,
    step_days: float = 7.0,
    transit_bodies: list[str] | None = None,
    orb: float = 1.0,
    engine: str | None = None,
) -> list[dict]:
    """Dated exact-pass events of transiting bodies over natal targets in [start, end].

    One event per LOCAL MINIMUM of the orb series within `orb`: {"transit_body", "natal_target",
    "aspect", "exact_date" (yyyy-mm-dd), "min_orb_deg" (3 dp), "window_start", "window_end"}.
    Sorted like the recipe timeline (exact_date, body, target).
    """
    if step_days <= 0:
        raise ValueError("step_days must be greater than zero")
    if orb < 0:
        raise ValueError("orb must not be negative")
    if range_end_utc <= range_start_utc:
        raise ValueError("range_end_utc must be later than range_start_utc")
    bodies = list(transit_bodies) if transit_bodies is not None else list(TRANSIT_BODIES_DEFAULT)
    targets = _natal_targets(natal_moment_utc, lat, lon, engine)

    times: list[datetime] = []
    cursor = range_start_utc.astimezone(timezone.utc)
    end = range_end_utc.astimezone(timezone.utc)
    while cursor <= end:
        times.append(cursor)
        cursor = cursor + timedelta(days=step_days)
    series = compute_positions_series(times, lat, lon, bodies=bodies, engine=engine)
    n = len(times)

    events: list[dict] = []
    for b in bodies:
        lons = [s[b] for s in series]
        for target, nlon in targets.items():
            for asp_name, asp_angle in _ASPECTS:
                g = [abs(_min_sep(l, nlon) - asp_angle) for l in lons]
                for i in range(1, n - 1):
                    if not (g[i] <= orb and g[i - 1] >= g[i] and g[i] <= g[i + 1]):
                        continue
                    y0, y1, y2 = g[i - 1], g[i], g[i + 1]
                    denom = y0 - 2.0 * y1 + y2
                    delta = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-9 else 0.0
                    delta = max(-1.0, min(1.0, delta))
                    exact_t = times[i] + timedelta(days=delta * step_days)
                    min_orb = max(0.0, y1 - 0.25 * (y0 - y2) * delta)
                    L = i
                    while L - 1 >= 0 and g[L - 1] <= orb:
                        L -= 1
                    R = i
                    while R + 1 < n and g[R + 1] <= orb:
                        R += 1
                    open_t = times[L]
                    if L - 1 >= 0 and g[L - 1] > orb:
                        den = g[L - 1] - g[L]
                        f = (g[L - 1] - orb) / den if abs(den) > 1e-9 else 0.0
                        open_t = times[L - 1] + timedelta(days=max(0.0, min(1.0, f)) * step_days)
                    close_t = times[R]
                    if R + 1 < n and g[R + 1] > orb:
                        den = g[R + 1] - g[R]
                        f = (orb - g[R]) / den if abs(den) > 1e-9 else 0.0
                        close_t = times[R] + timedelta(days=max(0.0, min(1.0, f)) * step_days)
                    events.append({
                        "transit_body": b,
                        "natal_target": target,
                        "aspect": asp_name,
                        "exact_date": exact_t.strftime("%Y-%m-%d"),
                        "min_orb_deg": round(min_orb, 3),
                        "window_start": open_t.strftime("%Y-%m-%d"),
                        "window_end": close_t.strftime("%Y-%m-%d"),
                    })
    events.sort(key=lambda e: (e["exact_date"], e["transit_body"], e["natal_target"]))
    return events


def compute_carrier_windows(
    events: list[dict], solar_year_start_utc: datetime | None = None
) -> list[dict]:
    """Merge slow-carrier passes into one theme per (body, target, aspect) — pure function.

    Window = earliest open -> latest close across ALL passes (retro gaps included); peak = the
    TIGHTEST pass; zone (only with an anchor): drop if closed before the anchor, else
    tail (peak before anchor) / core (peak inside [anchor, +365.25d]) / horizon (peak past it).
    """
    groups: dict[tuple, list[dict]] = {}
    for e in events:
        if e["transit_body"] not in SLOW_CARRIERS:
            continue
        groups.setdefault((e["transit_body"], e["natal_target"], e["aspect"]), []).append(e)

    windows: list[dict] = []
    for (body, target, aspect), passes in groups.items():
        opens = sorted(p["window_start"] for p in passes)
        closes = sorted(p["window_end"] for p in passes)
        exacts = sorted(p["exact_date"] for p in passes)
        peak = min(passes, key=lambda p: p["min_orb_deg"])
        zone = ""
        if solar_year_start_utc is not None:
            sy = solar_year_start_utc.astimezone(timezone.utc)
            sy_end = sy + timedelta(days=365.25)
            close_d = datetime.strptime(closes[-1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            peak_d = datetime.strptime(peak["exact_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if close_d < sy:
                continue  # finished before the year opened — last year's theme
            zone = "tail" if peak_d < sy else ("core" if peak_d <= sy_end else "horizon")
        windows.append({
            "window_open": opens[0],
            "window_close": closes[-1],
            "transit_body": body,
            "aspect": aspect,
            "natal_target": target,
            "zone": zone,
            "passes": len(passes),
            "exact_dates": "; ".join(exacts),
            "tightest_orb_deg": round(peak["min_orb_deg"], 3),
        })
    windows.sort(key=lambda w: (w["window_open"], w["transit_body"], w["natal_target"]))
    return windows


def compute_transits_to_natal(
    natal_moment_utc: datetime,
    lat: float,
    lon: float,
    range_start_utc: datetime,
    range_end_utc: datetime,
    step_days: float = 7.0,
    transit_bodies: list[str] | None = None,
    orb: float = 1.0,
    solar_year_start_utc: datetime | None = None,
    engine: str | None = None,
) -> dict:
    """The composite: {"timeline": events, "carrier_windows": merged slow-carrier themes}."""
    events = compute_transit_events(
        natal_moment_utc, lat, lon, range_start_utc, range_end_utc,
        step_days=step_days, transit_bodies=transit_bodies, orb=orb, engine=engine,
    )
    return {
        "timeline": events,
        "carrier_windows": compute_carrier_windows(events, solar_year_start_utc),
    }
