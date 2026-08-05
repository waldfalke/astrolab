"""Golden tests for the Python rising-sign clock.

GOLDEN REFERENCE: the PowerShell recipe `artifacts/mcp-recipes/run_rising_hands.ps1` in general mode.
These values are its witnessed output for a mundane (no-PII) input:
    date=2026-06-22, lat=45.04, lon=38.98, tz=+3, step=10min  (Krasnodar)
Source: 03_watches.csv of that run — 12 watches, first = 02:44 Близнецы.

The Python function must reproduce the PowerShell reference, not merely return a plausible shape.
"""
import pytest

from tests.conftest import require_engine_a

# The function under test does not exist yet — this import is the RED.
from astro.rising_hands import rising_hands  # noqa: E402

GOLDEN_INPUT = dict(date="2026-06-22", lat=45.04, lon=38.98, tz=3)
GOLDEN_FIRST_WATCH = {"start_local": "02:44", "asc_sign": "Близнецы"}
GOLDEN_WATCH_COUNT = 12  # 12 watches, not 13 (midnight edge sign wraps — merged)


def test_returns_twelve_watches():
    result = rising_hands(**GOLDEN_INPUT)
    assert len(result["watches"]) == GOLDEN_WATCH_COUNT


def test_first_watch_matches_powershell_golden():
    result = rising_hands(**GOLDEN_INPUT)
    first = result["watches"][0]
    assert first["start_local"] == GOLDEN_FIRST_WATCH["start_local"]
    assert first["asc_sign"] == GOLDEN_FIRST_WATCH["asc_sign"]


@pytest.mark.needs_swiss_mcp
def test_engine_agnostic_whole_clock_a_equals_b1():
    """The full 12-watch clock is identical on engine A and B1.

    Skips where pyswisseph (engine A) is absent, so the suite stays green without it.
    """
    import pytest

    require_engine_a()
    b1 = rising_hands(**GOLDEN_INPUT, engine="b1")
    a = rising_hands(**GOLDEN_INPUT, engine="a")
    assert a == b1
