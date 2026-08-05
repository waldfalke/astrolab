"""Annual profection using whole-sign houses and traditional rulers.

Ported from the recipes' Get-AnnualProfection
(lib/mcp_helpers.ps1): the Ascendant advances one whole sign per completed year; Lord of Year =
TRADITIONAL ruler of the profected sign (Hellenistic technique — no modern outers). Whole-sign
frame: profected/lord house numbers are NOT Placidus houses (a reading must flag the divergence).

Age semantics follow the SR recipe: age_years = return_year - birth_year (at the solar return the
person turns exactly that age).
"""
from __future__ import annotations

from astro.dignities import SIGNS, sign_of

# Traditional rulerships only (Hellenistic technique).
_RULER_TRAD = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
}


def compute_profection(asc_longitude: float, age_years: int) -> dict:
    """Annual profection from the natal ASC: {age_years, profection_step, asc_sign,
    profected_house, profected_sign, lord_of_year}."""
    asc_idx = int((asc_longitude % 360.0) // 30.0)
    step = age_years % 12
    prof_sign = SIGNS[(asc_idx + step) % 12]
    return {
        "age_years": age_years,
        "profection_step": step,
        "asc_sign": SIGNS[asc_idx],
        "profected_house": step + 1,
        "profected_sign": prof_sign,
        "lord_of_year": _RULER_TRAD[prof_sign],
    }


def locate_wholesign(longitude: float, asc_longitude: float) -> dict:
    """A body's sign + whole-sign house counted from the natal ASC sign."""
    sign_idx = int((longitude % 360.0) // 30.0)
    asc_idx = int((asc_longitude % 360.0) // 30.0)
    return {"sign": sign_of(longitude), "wholesign_house": (sign_idx - asc_idx) % 12 + 1}


def compute_profection_for_year(
    natal_moment_utc, lat: float, lon: float, return_year: int, engine: str | None = None
) -> dict:
    """Mini-composite: profection of a solar year straight from birth data.

    Computes the natal ASC and the Lord of Year's natal position through the #115 seam, then
    applies the profection arithmetic. Age = return_year - birth year (SR recipe semantics).

    Returns the compute_profection dict + {"lord_natal": {sign, wholesign_house},
    "house_frame": "whole_sign"}.
    """
    from astro.engine import compute_houses_series, compute_positions_series

    asc = compute_houses_series([natal_moment_utc], lat, lon, engine=engine)[0]["angles"]["asc"]
    prof = compute_profection(asc, return_year - natal_moment_utc.year)
    lord_lon = compute_positions_series(
        [natal_moment_utc], lat, lon, bodies=[prof["lord_of_year"]], engine=engine
    )[0][prof["lord_of_year"]]
    prof["lord_natal"] = locate_wholesign(lord_lon, asc)
    prof["house_frame"] = "whole_sign"
    return prof
