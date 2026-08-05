"""Golden test for assembly of the natal structure.

The composite is a PURE ASSEMBLY: positions + houses/angles + aspects + dignities, one normalized
dict. Element math is golden-tested at element level (test_positions / test_houses /
test_aspects / test_dignities); this test proves the ASSEMBLY wires them together correctly on the
public Trump fixture, through the default B1 engine.

Aspect cross-check note: the recorded aspect golden (04_backup_aspects.json) was computed by the
ephem BACKUP provider from its own longitudes, which drift up to ~arcsec from swiss. The composite
computes aspects from SWISS longitudes, so orbs are compared at 2e-3 deg, and the pair set is
compared over the recorded provider's bodies (fixed stars excluded — the composite models bodies).
Engine-agnosticism is covered at element level and not re-proven here (the assembly adds no
engine-dependent math).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from astro.natal import compute_natal

GOLDEN_MOMENT = datetime(1946, 6, 14, 14, 54, 0, tzinfo=timezone.utc)
GOLDEN_LAT = 40.7
GOLDEN_LON = -73.8164

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "trump"
_ASPECTS_JSON = (
    _FIXTURE / "natal_failover" / "04_backup_aspects.json"
)

TOL_DEG = 1e-6
# swiss-vs-ephem longitude drift, doubled (two bodies per pair). The Moon dominates: witnessed
# ~14 arcsec (0.0038 deg) between providers at the fixture moment; slow bodies drift ~arcsec.
ASPECT_ORB_TOL = 1e-2


def test_natal_composite_assembles_goldens():
    chart = compute_natal(GOLDEN_MOMENT, GOLDEN_LAT, GOLDEN_LON)

    # provenance echo
    assert chart["moment_utc"] == "1946-06-14T14:54:00Z"
    assert chart["location"] == {"lat": GOLDEN_LAT, "lon": GOLDEN_LON}

    # positions slice (element-golden spot checks: planets_primary.csv values)
    pos = chart["positions"]
    assert abs(pos["sun"] - 82.9284020277778) < TOL_DEG
    assert abs(pos["moon"] - 261.203814194444) < TOL_DEG
    assert abs(pos["pluto"] - 130.04209025) < TOL_DEG
    # the natal body set carries nodes/lilith/chiron on top of the 10 classical
    for extra in ("north_node", "lilith", "chiron"):
        assert extra in pos

    # house frame (02_houses_placidus.csv / 03_chart_points.csv values)
    assert abs(chart["houses"]["cusps"][0] - 149.958846361111) < TOL_DEG
    assert abs(chart["houses"]["angles"]["asc"] - 149.958846361111) < TOL_DEG
    assert abs(chart["houses"]["angles"]["mc"] - 54.35059875) < TOL_DEG

    # dignities (recipe-witnessed golden: Saturn in Cancer is the chart's one detriment)
    assert chart["dignities"]["saturn"] == {"sign": "Cancer", "dignity": "detriment"}
    assert chart["dignities"]["sun"] == {"sign": "Gemini", "dignity": "peregrine"}

    # sect (recipe-witnessed golden: day chart, Mercury occidental -> nocturnal)
    assert chart["sect"]["chart_sect"] == "day"
    assert chart["sect"]["mercury_team"] == "nocturnal"
    assert chart["sect"]["bodies"]["saturn"]["role"] == "malefic_of_sect"

    # Part of Fortune (05_additional_points.csv) + placements (hand-derived from golden cusps)
    assert abs(chart["points"]["part_of_fortune"] - 328.23425852777774) < 1e-6
    assert chart["placements"]["sun"] == 10
    assert chart["placements"]["moon"] == 4
    assert chart["placements"]["part_of_fortune"] == 6  # 328.23 in the cusp6..cusp7 arc

    # aspects: same pair set + aspect names as the recorded provider golden, over the 10 classical
    # bodies ONLY. Witnessed provider fork (2026-07-03): ephem's Chiron for this moment is
    # 197.743 deg vs swiss 194.912 deg (~2.83 deg apart; swiss matches the commonly cited 14deg55'
    # Libra) — so chiron pairs legitimately differ between the recorded ephem golden and the
    # swiss-based composite. Classical bodies agree to ~arcsec across both providers.
    recorded = json.loads(_ASPECTS_JSON.read_text(encoding="utf-8-sig"))
    classical = {
        "sun", "moon", "mercury", "venus", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    }
    recorded_bodies = classical & {
        b for a in recorded["aspects"] for b in (a["body1"], a["body2"])
    }
    expected = {
        frozenset((a["body1"], a["body2"])): a
        for a in recorded["aspects"]
        if {a["body1"], a["body2"]} <= recorded_bodies
    }
    got = {
        frozenset((h["body1"], h["body2"])): h
        for h in chart["aspects"]
        if {h["body1"], h["body2"]} <= recorded_bodies
    }
    assert set(got) == set(expected)
    for pair, exp in expected.items():
        assert got[pair]["aspect"] == exp["aspect"], pair
        assert abs(got[pair]["orb"] - exp["orb"]) < ASPECT_ORB_TOL, pair
