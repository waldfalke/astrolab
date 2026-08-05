"""Hellenistic sect and the Part of Fortune.

Ported from the recipes' Get-Sect (lib/mcp_helpers.ps1):
  * Day chart = Sun above the horizon, tested on the ASC->DSC arc: (lon - ASC) mod 360 in
    [0, 180) is the below-horizon half (houses 1-6), [180, 360) the above-horizon half (7-12).
  * Diurnal team: Sun, Jupiter, Saturn. Nocturnal: Moon, Venus, Mars. Mercury takes sect by
    ORIENTALITY from the signed Sun->Mercury angle (negative = rises before the Sun = oriental =
    diurnal) — not a raw longitude compare, which breaks near 0 Aries.
  * Outers carry no classical sect (team "none", role "outer").

Part of Fortune: day = ASC + Moon - Sun; night = ASC + Sun - Moon (classical flip).
Consumes the positions element's output; no engine, no I/O.
"""
from __future__ import annotations

from astro.dignities import sign_of

_DIURNAL = ("sun", "jupiter", "saturn")
_NOCTURNAL = ("moon", "venus", "mars")

_ROLES = {
    "day": {
        "sun": "sect_light", "jupiter": "benefic_of_sect", "venus": "benefic_contrary",
        "saturn": "malefic_of_sect", "mars": "malefic_contrary", "moon": "luminary_out_of_sect",
    },
    "night": {
        "moon": "sect_light", "venus": "benefic_of_sect", "jupiter": "benefic_contrary",
        "mars": "malefic_of_sect", "saturn": "malefic_contrary", "sun": "luminary_out_of_sect",
    },
}


def signed_delta_deg(from_lon: float, to_lon: float) -> float:
    """Signed shortest arc from one longitude to another, degrees in (-180, 180]."""
    d = to_lon % 360.0 - from_lon % 360.0
    if d > 180.0:
        d -= 360.0
    if d <= -180.0:
        d += 360.0
    return d


def _above_horizon(lon: float, asc: float) -> bool:
    return (lon - asc) % 360.0 >= 180.0


def compute_sect(longitudes: dict[str, float], asc: float) -> dict:
    """Chart sect + per-body sect membership and role.

    Returns {"chart_sect": "day"|"night", "sun_above_horizon", "mercury_team",
    "bodies": {body -> {"sign", "planet_team", "above_horizon", "placement", "role"}}}.
    """
    if "sun" not in longitudes:
        raise ValueError("compute_sect requires the Sun longitude")
    sun_above = _above_horizon(longitudes["sun"], asc)
    chart_sect = "day" if sun_above else "night"
    chart_team = "diurnal" if sun_above else "nocturnal"

    mercury_team = "none"
    if "mercury" in longitudes:
        d = signed_delta_deg(longitudes["sun"], longitudes["mercury"])
        mercury_team = "diurnal" if d < 0 else "nocturnal"

    roles = _ROLES[chart_sect]
    bodies: dict[str, dict] = {}
    for body, lon in longitudes.items():
        if body in _DIURNAL:
            team = "diurnal"
        elif body in _NOCTURNAL:
            team = "nocturnal"
        elif body == "mercury":
            team = mercury_team
        else:
            team = "none"
        placement = "n/a" if team == "none" else (
            "in_sect" if team == chart_team else "out_of_sect"
        )
        role = "outer" if team == "none" else roles.get(body, "neutral")
        bodies[body] = {
            "sign": sign_of(lon),
            "planet_team": team,
            "above_horizon": _above_horizon(lon, asc),
            "placement": placement,
            "role": role,
        }
    return {
        "chart_sect": chart_sect,
        "sun_above_horizon": sun_above,
        "mercury_team": mercury_team,
        "bodies": bodies,
    }


def compute_part_of_fortune(asc: float, sun: float, moon: float, chart_sect: str) -> float:
    """Part of Fortune longitude: day = ASC + Moon - Sun; night = ASC + Sun - Moon."""
    if chart_sect == "day":
        return (asc + moon - sun) % 360.0
    if chart_sect == "night":
        return (asc + sun - moon) % 360.0
    raise ValueError("unknown chart_sect %r (expected 'day' or 'night')" % chart_sect)
