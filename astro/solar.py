"""solar — the solar-return composite (#119-family): true return instant + relocated SR chart.

The provider's own calculate_solar_revolution is naive (birth time-of-day on the birthday, ~9h
error, meaningless houses) — like the PS recipe, this SOLVES the exact instant the transiting Sun
returns to its natal longitude by bisection, then assembles the SR chart AT that instant FOR the
return location (relocation; defaults to birth location).

Bisection semantics match run_solar_revolution.ps1 for golden fidelity: bracket = birthday-in-year
±2 days, signed-delta zero-crossing, early exit at |delta| < 5e-5 deg (~4 s of Sun motion), max 40
halvings, instant truncated to whole seconds before casting. Feb-29 births share the recipe's
known limitation (naive month/day transplant).

Cross-aspects (return -> natal) follow the recipe: classical 10 bodies, orb 2.0, directed —
endpoints are never sorted (return:saturn->natal:moon is not natal:saturn->return:moon).
NOT in v1 (deliberate): declination layer (ephem-only source), the timing layer (monthly phase
windows, Sun-activation dates) — recipe steps 4-5 remain PS-only for now.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from astro.aspects import compute_cross_aspects
from astro.dignities import compute_dignities
from astro.engine import (
    DEFAULT_BODIES,
    _iso_utc,
    compute_houses_series,
    compute_positions_series,
)
from astro.natal import NATAL_BODIES
from astro.placements import compute_placements
from astro.profection import compute_profection, locate_wholesign
from astro.sect import compute_sect, signed_delta_deg

_BISECT_TOL_DEG = 5e-5
_BISECT_MAX_ITER = 40


def _sun_lon(moment: datetime, lat: float, lon: float, engine: str | None) -> float:
    return compute_positions_series([moment], lat, lon, bodies=["sun"], engine=engine)[0]["sun"]


def find_solar_return_instant(
    natal_moment_utc: datetime,
    birth_lat: float,
    birth_lon: float,
    return_year: int,
    sr_lat: float | None = None,
    sr_lon: float | None = None,
    engine: str | None = None,
) -> datetime:
    """The UTC instant in `return_year` when the transiting Sun reaches its natal longitude.

    Whole-second precision (truncated, recipe-compatible). Raises if the return is not
    bracketed within birthday-in-year ±2 days.
    """
    eff_lat = sr_lat if sr_lat is not None else birth_lat
    eff_lon = sr_lon if sr_lon is not None else birth_lon
    natal = natal_moment_utc.astimezone(timezone.utc)
    natal_sun = _sun_lon(natal, birth_lat, birth_lon, engine)

    approx = datetime(
        return_year, natal.month, natal.day, natal.hour, natal.minute, natal.second,
        tzinfo=timezone.utc,
    )
    lo, hi = approx - timedelta(days=2), approx + timedelta(days=2)
    f_lo = signed_delta_deg(natal_sun, _sun_lon(lo, eff_lat, eff_lon, engine))
    f_hi = signed_delta_deg(natal_sun, _sun_lon(hi, eff_lat, eff_lon, engine))
    if (f_lo < 0) == (f_hi < 0):
        raise ValueError(
            "solar return not bracketed in [%s, %s] (f_lo=%.6f f_hi=%.6f)"
            % (lo.isoformat(), hi.isoformat(), f_lo, f_hi)
        )
    for _ in range(_BISECT_MAX_ITER):
        mid = lo + (hi - lo) / 2
        f_mid = signed_delta_deg(natal_sun, _sun_lon(mid, eff_lat, eff_lon, engine))
        if abs(f_mid) < _BISECT_TOL_DEG:
            lo = hi = mid
            break
        if (f_lo < 0) == (f_mid < 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    instant = lo + (hi - lo) / 2
    return instant.replace(microsecond=0)


def compute_solar_return(
    natal_moment_utc: datetime,
    birth_lat: float,
    birth_lon: float,
    return_year: int,
    sr_lat: float | None = None,
    sr_lon: float | None = None,
    orb: float = 2.0,
    scheme: str = "modern",
    engine: str | None = None,
) -> dict:
    """Assemble the solar-return structure for one solar year.

    Returns {"return_instant_utc", "location": {lat, lon, relocated}, "natal": {positions},
    "return": {positions, houses, dignities, sect, placements}, "sr_to_natal_aspects"
    (classical 10, directed, orb 2), "profection"} — stateless dict, seam elements only.
    """
    eff_lat = sr_lat if sr_lat is not None else birth_lat
    eff_lon = sr_lon if sr_lon is not None else birth_lon
    instant = find_solar_return_instant(
        natal_moment_utc, birth_lat, birth_lon, return_year, sr_lat, sr_lon, engine
    )

    natal_pos = compute_positions_series(
        [natal_moment_utc], birth_lat, birth_lon, bodies=list(NATAL_BODIES), engine=engine
    )[0]
    sr_pos = compute_positions_series(
        [instant], eff_lat, eff_lon, bodies=list(NATAL_BODIES), engine=engine
    )[0]
    sr_houses = compute_houses_series([instant], eff_lat, eff_lon, engine=engine)[0]
    natal_houses = compute_houses_series(
        [natal_moment_utc], birth_lat, birth_lon, engine=engine
    )[0]

    classical = list(DEFAULT_BODIES)
    aspects = compute_cross_aspects(
        {b: sr_pos[b] for b in classical}, {b: natal_pos[b] for b in classical}, orb=orb
    )

    natal_asc = natal_houses["angles"]["asc"]
    prof = compute_profection(natal_asc, return_year - natal_moment_utc.year)
    prof["lord_natal"] = locate_wholesign(natal_pos[prof["lord_of_year"]], natal_asc)
    prof["house_frame"] = "whole_sign"

    sect = compute_sect(sr_pos, sr_houses["angles"]["asc"])
    return {
        "return_instant_utc": _iso_utc(instant),
        "location": {"lat": eff_lat, "lon": eff_lon, "relocated": sr_lat is not None},
        "natal": {"positions": natal_pos},
        "return": {
            "positions": sr_pos,
            "houses": sr_houses,
            "dignities": compute_dignities(sr_pos, scheme=scheme),
            "sect": sect,
            "placements": compute_placements(sr_pos, sr_houses["cusps"]),
        },
        "sr_to_natal_aspects": aspects,
        "profection": prof,
    }
