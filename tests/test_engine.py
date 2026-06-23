"""Golden + agnosticism tests for the thin engine seam (NKS astrolab #115).

PRINCIPLE #115 — engine-agnosticism: the computational engine hides behind a THIN interface
(`astro.engine.compute_asc_series`); a golden test is the arbiter that the NUMBERS agree across
engines. Default engine is B1 (swiss-mcp client, works without pyswisseph). Engine A (in-process
pyswisseph) is optional and, where available, must agree with B1 by construction.

GOLDEN MOMENT (mundane, no-PII): 2026-06-22T00:00:00Z, lat=45.04, lon=38.98 (Krasnodar).
The B1 reference ASC below was witnessed from the SAME swiss-ephemeris MCP (v2.10.03) the
PowerShell recipe `run_rising_hands.ps1` calls — so B1 == recipe engine by construction.
The non-tautological arbiter of #115 is the A==B1 cross-check, not this constant's provenance.
"""
from datetime import datetime, timezone

import pytest

from astro.engine import compute_asc_series  # RED: module does not exist yet.

GOLDEN_MOMENT = datetime(2026, 6, 22, 0, 0, 0, tzinfo=timezone.utc)
GOLDEN_LAT = 45.04
GOLDEN_LON = 38.98
GOLDEN_ASC_B1 = 63.64472375  # witnessed from swiss-mcp (recipe engine), v2.10.03

# ASC agreement tolerance: 1e-4 arcsec = ~2.8e-8 deg. Measured A-vs-B1 drift was 4.5e-5 arcsec.
TOL_DEG = 1e-4 / 3600.0


def test_b1_compute_asc_series_matches_golden():
    """B1 (default engine) returns the recipe-engine ASC for the golden moment."""
    series = compute_asc_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON)
    assert len(series) == 1
    assert abs(series[0] - GOLDEN_ASC_B1) < TOL_DEG


def test_engine_a_agrees_with_b1():
    """#115 arbiter: engine A (in-process pyswisseph) agrees with B1 on the same number.

    Skips cleanly where pyswisseph is not installed, so the suite stays green without engine A.
    Where A IS available, this PASSES and *demonstrates* agnosticism (not merely asserts it).
    """
    pytest.importorskip("swisseph")
    b1 = compute_asc_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, engine="b1")
    a = compute_asc_series([GOLDEN_MOMENT], GOLDEN_LAT, GOLDEN_LON, engine="a")
    assert abs(a[0] - b1[0]) < TOL_DEG
