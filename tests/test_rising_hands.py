"""Golden tests for the Python rising_hands MCP function (NKS astrolab #109, first MCPization target).

GOLDEN REFERENCE: the PowerShell recipe `artifacts/mcp-recipes/run_rising_hands.ps1` in general mode.
These values are its witnessed output for a mundane (no-PII) input:
    date=2026-06-22, lat=45.04, lon=38.98, tz=+3, step=10min  (Krasnodar)
Source: 03_watches.csv of that run — 12 watches, first = 02:44 Близнецы.

DOMAIN GATE (verstakify): the Python function must reproduce the PowerShell reference, not merely
"return something". RED now (function does not exist); GREEN waits on pyswisseph (not yet installed).
"""
import pytest

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
