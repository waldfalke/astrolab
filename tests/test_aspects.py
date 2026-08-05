"""Golden and unit tests for major-aspect detection.

Aspects are ENGINE-FREE math: they consume the positions element's output (body -> longitude) and
detect major aspects by minimal angular separation. Contract:

    compute_aspects(longitudes, orb=6.0) -> list[dict]

each hit: {"body1", "body2", "aspect", "angle", "orb"} — angle = actual separation (0..180 deg),
orb = |angle - exact|. Pairs are normalized (body1 < body2 alphabetically), hits sorted by orb.
No "exact" flag in the contract — exactness is a consumer threshold, not element data.

Fixture provenance: the recorded ephem-provider output
`04_backup_aspects.json` of the public Trump fixture, RE-DERIVED from the same provider's own
recorded longitudes `06_backup_longitudes.csv` (same call instant, same provider). The recorded
JSON includes fixed-star pairs (sirius) the element does not model — the comparison is over pairs
whose both bodies are in the longitudes CSV. Public-figure fixture only — no PII.
"""
import csv
import json
from pathlib import Path

from astro.aspects import compute_aspects

_RUN = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "trump" / "natal_failover"
)

ORB_TOL = 1e-9


def _fixture_longitudes() -> dict[str, float]:
    with (_RUN / "06_backup_longitudes.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["body"]: float(row["longitude"]) for row in csv.DictReader(f)}


def test_simple_known_aspects():
    """Pure-math sanity: hand-checkable separations, including the 0/360 wrap."""
    hits = compute_aspects({"a": 10.0, "b": 190.0, "c": 358.0, "d": 3.0}, orb=6.0)
    by_pair = {(h["body1"], h["body2"]): h for h in hits}
    assert by_pair[("a", "b")]["aspect"] == "opposition"
    assert abs(by_pair[("a", "b")]["orb"]) < 1e-12
    # wrap: 358 vs 3 -> separation 5 -> conjunction, orb 5
    assert by_pair[("c", "d")]["aspect"] == "conjunction"
    assert abs(by_pair[("c", "d")]["orb"] - 5.0) < 1e-12
    # 10 vs 358 -> separation 12 -> nearest major is conjunction at orb 12 -> NO hit at orb 6
    assert ("a", "c") not in by_pair
    # hits come sorted by orb
    assert [h["orb"] for h in hits] == sorted(h["orb"] for h in hits)


def test_matches_recorded_ephem_aspects_on_fixture():
    """The port reproduces the recorded provider aspects (orb_used=6) from the provider's own
    recorded longitudes: same pair set, same aspect names, orbs equal to 1e-9."""
    longitudes = _fixture_longitudes()
    recorded = json.loads((_RUN / "04_backup_aspects.json").read_text(encoding="utf-8-sig"))
    assert recorded["orb_used"] == 6

    expected = {
        frozenset((a["body1"], a["body2"])): a
        for a in recorded["aspects"]
        if a["body1"] in longitudes and a["body2"] in longitudes
    }
    # the fixture drops only fixed-star pairs (sirius) — the element models bodies, not stars
    dropped = [a for a in recorded["aspects"] if frozenset((a["body1"], a["body2"])) not in expected]
    assert all("sirius" in (a["body1"], a["body2"]) for a in dropped)

    got = {frozenset((h["body1"], h["body2"])): h for h in compute_aspects(longitudes, orb=6.0)}
    assert set(got) == set(expected)
    for pair, exp in expected.items():
        assert got[pair]["aspect"] == exp["aspect"], pair
        assert abs(got[pair]["orb"] - exp["orb"]) < ORB_TOL, pair
        assert abs(got[pair]["angle"] - exp["angle"]) < ORB_TOL, pair
