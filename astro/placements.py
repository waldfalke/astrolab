"""placements — engine-free element: which house a longitude occupies, given the cusp frame.

House i spans the forward arc from cusp i to cusp i+1 (wrapping 12 -> 1). Membership is the
standard forward-arc test: lon is in house i iff (lon - cusp_i) mod 360 < (cusp_{i+1} - cusp_i)
mod 360 — cusp-exact longitudes belong to the house they open. Consumes the positions + houses
elements' output; no engine, no I/O.
"""
from __future__ import annotations


def house_of(longitude: float, cusps: list[float]) -> int:
    """House number (1..12) containing an ecliptic longitude, for a 12-cusp frame."""
    if len(cusps) != 12:
        raise ValueError("expected 12 cusps, got %d" % len(cusps))
    for i in range(12):
        start = cusps[i]
        span = (cusps[(i + 1) % 12] - start) % 360.0
        if (longitude - start) % 360.0 < span:
            return i + 1
    # Unreachable for a well-formed frame (the 12 arcs tile the circle).
    raise ValueError("longitude %r not covered by the cusp frame" % longitude)


def compute_placements(longitudes: dict[str, float], cusps: list[float]) -> dict[str, int]:
    """House placement of each body: {body -> house 1..12}."""
    return {body: house_of(lon, cusps) for body, lon in longitudes.items()}
