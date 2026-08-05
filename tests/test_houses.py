"""Golden, cross-engine, and extraction tests for houses and angles.

The houses element is the THIRD element on the seam (ASC, positions, houses). A natal composite
needs the full house frame, not just ASC: 12 Placidus cusps + the angle set. Contract:

    compute_houses_series(moments_utc, lat, lon, engine=None) -> list[dict]

one dict per moment: {"cusps": [12 floats, cusps[0] = house 1], "angles": {asc, mc, dsc, ic,
vertex, armc -> deg}}. Normalized lowercase angle names; cusp order matches the recipe CSV.

Fixture provenance: `02_houses_placidus.csv` +
`03_chart_points.csv` of the public Trump fixture (PROVIDER: swissremote — the engine B1 calls),
both derived from the captured raw payload `01_primary_positions.json` used as the extraction
fixture. Public-figure fixture only — no PII.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.conftest import require_engine_a

from astro.engine import compute_houses_series, _select_houses

GOLDEN_MOMENT = datetime(1946, 6, 14, 14, 54, 0, tzinfo=timezone.utc)
GOLDEN_LAT = 40.7
GOLDEN_LON = -73.8164

# 02_houses_placidus.csv, houses 1..12 (PROVIDER: swissremote == engine B1).
GOLDEN_CUSPS_B1 = [
    149.958846361111, 173.004190666667, 201.199416194444, 234.35059875,
    269.341986166667, 301.743358972222, 329.958846361111, 353.004190666667,
    21.1994161944444, 54.35059875, 89.3419861666667, 121.743358972222,
]

# 03_chart_points.csv, normalized lowercase names.
GOLDEN_ANGLES_B1 = {
    "asc": 149.958846361111,
    "mc": 54.35059875,
    "ic": 234.35059875,
    "dsc": 329.958846361111,
    "vertex": 292.900744666667,
    "armc": 51.9822345277778,
}

TOL_DEG = 1e-6
# Houses are pure geometry of time+place; A-vs-B1 drift is nutation/obliquity model noise only —
# same tight tolerance as the ASC element (1e-4 arcsec).
TOL_DEG_A = 1e-4 / 3600.0

_PAYLOAD = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "trump" / "house_placidus" / "01_primary_positions.json"
)


def _assert_frame_matches_golden(frame: dict, tol: float) -> None:
    assert len(frame["cusps"]) == 12
    for i, lon in enumerate(GOLDEN_CUSPS_B1):
        assert abs(frame["cusps"][i] - lon) < tol, "cusp %d" % (i + 1)
    for name, lon in GOLDEN_ANGLES_B1.items():
        assert abs(frame["angles"][name] - lon) < tol, name


def test_select_houses_extracts_swiss_golden_from_captured_payload():
    """Deterministic (no engine needed): the pure selector pulls cusps+angles out of a REAL
    captured swiss-mcp payload. Proves the extraction/naming contract against recorded source data.
    """
    payload = json.loads(_PAYLOAD.read_text(encoding="utf-8-sig"))
    frame = _select_houses(payload)
    _assert_frame_matches_golden(frame, TOL_DEG)


def test_b1_houses_match_swiss_golden():
    """B1 (default engine) returns the swiss golden cusps+angles for the natal moment.

    Requires the swiss-mcp engine reachable (localhost:8000) — same infra dependency as the other
    B1 goldens.
    """
    series = compute_houses_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON)
    assert len(series) == 1
    _assert_frame_matches_golden(series[0], TOL_DEG)


@pytest.mark.needs_swiss_mcp
def test_engine_a_houses_agree_with_b1():
    """Engine A agrees with B1 on houses and angles to sub-arcsecond tolerance.
    house geometry does not depend on the ephemeris files that cause planet drift."""
    require_engine_a()
    b1 = compute_houses_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, engine="b1")
    a = compute_houses_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, engine="a")
    for i in range(12):
        assert abs(a[0]["cusps"][i] - b1[0]["cusps"][i]) < TOL_DEG_A, "cusp %d" % (i + 1)
    for name in GOLDEN_ANGLES_B1:
        assert abs(a[0]["angles"][name] - b1[0]["angles"][name]) < TOL_DEG_A, name
