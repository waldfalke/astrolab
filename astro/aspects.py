"""Major-aspect detection over body longitudes.

The implementation is locked to recorded provider output on the public Trump fixture. It consumes
the positions output and performs no I/O.

With orb <= 15 deg a separation can match at most one major aspect (adjacent exact angles are
30/60 deg apart), so "closest major within orb" and "any major within orb" coincide — same
detection rule as the recipes' Get-ClosestMajorAspect and the ephem provider's calculate_aspects.
"""
from __future__ import annotations

MAJOR_ASPECTS = (
    ("conjunction", 0.0),
    ("sextile", 60.0),
    ("square", 90.0),
    ("trine", 120.0),
    ("opposition", 180.0),
)


def min_separation_deg(a: float, b: float) -> float:
    """Minimal angular separation of two ecliptic longitudes, degrees in [0, 180]."""
    d = abs(a % 360.0 - b % 360.0)
    return 360.0 - d if d > 180.0 else d


def compute_cross_aspects(
    from_longitudes: dict[str, float],
    to_longitudes: dict[str, float],
    orb: float = 2.0,
) -> list[dict]:
    """Major aspects BETWEEN two charts (directed: from -> to), e.g. return->natal.

    Direction is meaning-bearing (factor-id discipline: return:saturn->natal:moon is NOT
    natal:saturn->return:moon) — endpoints are never sorted. Same closest-major detection as
    compute_aspects; recipe default orb for cross-chart work is 2.0.

    Returns one dict per hit: {"from_body", "to_body", "aspect", "angle", "orb"},
    sorted by orb ascending then pair for determinism.
    """
    hits: list[dict] = []
    for fb in sorted(from_longitudes):
        for tb in sorted(to_longitudes):
            sep = min_separation_deg(from_longitudes[fb], to_longitudes[tb])
            name, exact = min(MAJOR_ASPECTS, key=lambda d: abs(sep - d[1]))
            delta = abs(sep - exact)
            if delta <= orb:
                hits.append(
                    {"from_body": fb, "to_body": tb, "aspect": name, "angle": sep, "orb": delta}
                )
    hits.sort(key=lambda h: (h["orb"], h["from_body"], h["to_body"]))
    return hits


def compute_aspects(
    longitudes: dict[str, float], orb: float = 6.0
) -> list[dict]:
    """Major aspects among `longitudes` (body -> ecliptic longitude, deg).

    Returns one dict per detected aspect: {"body1", "body2", "aspect", "angle", "orb"} —
    body1 < body2 alphabetically, angle = actual separation (0..180), orb = |angle - exact|.
    Hits sorted by orb ascending (tightest first), then by pair for determinism.
    """
    hits: list[dict] = []
    bodies = sorted(longitudes)
    for i, b1 in enumerate(bodies):
        for b2 in bodies[i + 1:]:
            sep = min_separation_deg(longitudes[b1], longitudes[b2])
            name, exact = min(MAJOR_ASPECTS, key=lambda d: abs(sep - d[1]))
            delta = abs(sep - exact)
            if delta <= orb:
                hits.append(
                    {"body1": b1, "body2": b2, "aspect": name, "angle": sep, "orb": delta}
                )
    hits.sort(key=lambda h: (h["orb"], h["body1"], h["body2"]))
    return hits
