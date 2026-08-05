"""Golden, cross-engine, and extraction tests for body positions.

The positions element is the FIRST element added to the seam after ASC. It is the true next
dependency of every composite above rising_hands (natal needs body longitudes). It establishes the
SHARED contract the rest of the element fleet (houses/aspects/dignities) builds on:

    compute_positions_series(moments_utc, lat, lon, bodies=None, engine=None) -> list[dict[str, float]]

one dict per moment, normalized lowercase body name -> ecliptic longitude (deg).

Fixture provenance: the Trump
fixture's `natal_longitudes.csv` is the BACKUP (ephem) provider — it drifts ~1 arcsec from swiss and
would make a B1 golden FALSELY red. The swiss-provenance golden is `planets_primary.csv`
(PROVIDER: swissremote), which is derived from the captured raw payload `01_primary_positions.json`.
Both are used here: the constants below are the swiss golden; the captured payload is the extraction
fixture.

Public-figure fixture only (Trump 1946-06-14T14:54:00Z, 40.7/-73.8164) — no PII.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.conftest import require_engine_a

from astro.engine import compute_positions_series, _select_positions  # RED: not defined yet.

# Natal moment of the public Trump fixture (the swiss golden was witnessed at this moment).
GOLDEN_MOMENT = datetime(1946, 6, 14, 14, 54, 0, tzinfo=timezone.utc)
GOLDEN_LAT = 40.7
GOLDEN_LON = -73.8164

# Swiss-provenance golden (planets_primary.csv, PROVIDER: swissremote == the engine B1 calls).
# 10 classical bodies, the default element set. Matches 01_primary_positions.json by construction.
GOLDEN_POSITIONS_B1 = {
    "sun": 82.9284020277778,
    "moon": 261.203814194444,
    "mercury": 98.8590341944444,
    "venus": 115.738145111111,
    "mars": 146.775944583333,
    "jupiter": 197.452071888889,
    "saturn": 113.815608305556,
    "uranus": 77.8930810277778,
    "neptune": 185.841946083333,
    "pluto": 130.04209025,
}

# Longitude agreement tolerance. The recipe CSV rounds to ~1e-12; B1 vs CSV is exact (same payload).
# A-vs-B1 is STRICT: engine A reads the SAME .se1 files the B1 container serves (infra/ephe,
# fetched by get-ephe.ps1 with SHA pins) — witnessed drift ~4e-5 arcsec across all 13 bodies.
# If this test suddenly needs loosening, the files are missing/wrong (Moshier fallback, KI-008).
TOL_DEG = 1e-6
TOL_DEG_A = 1e-4 / 3600.0  # same grade as the ASC element golden

# The captured raw swiss-mcp payload (the extraction fixture — real recorded engine output).
_PAYLOAD = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "trump" / "house_placidus" / "01_primary_positions.json"
)


def test_select_positions_extracts_swiss_golden_from_captured_payload():
    """Deterministic (no engine needed): the pure selector pulls the swiss golden out of a REAL
    captured swiss-mcp payload. Proves the extraction/naming contract against recorded source data.
    """
    # utf-8-sig: the PowerShell recipes persist raw JSON with a UTF-8 BOM (the live MCP wire has none).
    payload = json.loads(_PAYLOAD.read_text(encoding="utf-8-sig"))
    got = _select_positions(payload, list(GOLDEN_POSITIONS_B1.keys()))
    for body, lon in GOLDEN_POSITIONS_B1.items():
        assert abs(got[body] - lon) < TOL_DEG, body


def test_b1_positions_match_swiss_golden():
    """B1 (default engine) returns the swiss golden longitudes for the natal moment.

    Requires the swiss-mcp engine reachable (localhost:8000). RED while the engine is down — the
    same infra dependency as the ASC golden test; goes GREEN when the container is up.
    """
    series = compute_positions_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON)
    assert len(series) == 1
    got = series[0]
    for body, lon in GOLDEN_POSITIONS_B1.items():
        assert abs(got[body] - lon) < TOL_DEG, body


@pytest.mark.needs_swiss_mcp
def test_engine_a_positions_agree_with_b1():
    """Engine A agrees with B1 on body positions.
    the full natal body set — classical 10 + true node + mean-apogee Lilith + Chiron. The
    non-classical bodies prove the .se1 files are actually loaded: Moshier cannot serve Chiron at
    all, and its planet longitudes drift arcseconds (would blow TOL_DEG_A by orders)."""
    require_engine_a()
    bodies = list(GOLDEN_POSITIONS_B1) + ["north_node", "lilith", "chiron"]
    b1 = compute_positions_series(
        [GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, bodies=bodies, engine="b1"
    )
    a = compute_positions_series(
        [GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, bodies=bodies, engine="a"
    )
    for body in bodies:
        assert abs(a[0][body] - b1[0][body]) < TOL_DEG_A, body
