"""Assemble calculation elements into a natal structure.

A composite assembles rather than recalculates: positions and houses/angles come through the engine boundary,
aspects/dignities are engine-free element math over the positions slice. The output is one
normalized stateless dictionary.

B1 note: positions and houses currently cost one wire call each (the same swiss-mcp payload
fetched twice). Deliberate v1 simplicity — the composite stays on the PUBLIC seam contract instead
of reaching into engine internals; collapse to one fetch only if a real consumer feels it.
"""
from __future__ import annotations

from datetime import datetime

from astro.aspects import compute_aspects
from astro.dignities import compute_dignities
from astro.engine import (
    DEFAULT_BODIES,
    _iso_utc,
    compute_houses_series,
    compute_positions_series,
)
from astro.placements import compute_placements
from astro.sect import compute_part_of_fortune, compute_sect

# The natal body set (feature map: 10 classical + nodes + Lilith + Chiron). PoF is derived, not
# fetched — a later element.
NATAL_BODIES = DEFAULT_BODIES + ("north_node", "lilith", "chiron")


def compute_natal(
    moment_utc: datetime,
    lat: float,
    lon: float,
    bodies: list[str] | None = None,
    orb: float = 6.0,
    scheme: str = "modern",
    engine: str | None = None,
) -> dict:
    """Assemble the natal chart structure for one UTC moment.

    Args:
        moment_utc: tz-aware UTC birth instant.
        lat, lon: birth location.
        bodies: normalized lowercase body names; None -> NATAL_BODIES.
        orb: major-aspect orb in degrees (recipe default 6).
        scheme: dignity scheme, "modern" or "traditional".
        engine: seam engine override ("b1"/"a"); None -> env/default.

    Returns:
        {"moment_utc", "location": {lat, lon}, "positions", "houses": {cusps, angles},
         "aspects", "dignities", "sect", "points": {"part_of_fortune"},
         "placements"} — the normalized natal structure (#118).
    """
    bods = list(bodies) if bodies is not None else list(NATAL_BODIES)
    positions = compute_positions_series([moment_utc], lat, lon, bodies=bods, engine=engine)[0]
    houses = compute_houses_series([moment_utc], lat, lon, engine=engine)[0]
    asc = houses["angles"]["asc"]
    sect = compute_sect(positions, asc)
    points = {}
    if "sun" in positions and "moon" in positions:
        points["part_of_fortune"] = compute_part_of_fortune(
            asc, positions["sun"], positions["moon"], sect["chart_sect"]
        )
    return {
        "moment_utc": _iso_utc(moment_utc),
        "location": {"lat": lat, "lon": lon},
        "positions": positions,
        "houses": houses,
        "aspects": compute_aspects(positions, orb=orb),
        "dignities": compute_dignities(positions, scheme=scheme),
        "sect": sect,
        "points": points,
        "placements": compute_placements({**positions, **points}, houses["cusps"]),
    }
