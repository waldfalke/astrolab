"""MCP-server golden tests through an in-memory FastMCP client.

This exercises the SAME golden as tests/test_rising_hands.py, but THROUGH the MCP boundary:
a FastMCP in-memory Client calls the registered tool and we assert on its result. It proves
The registered tool accepts typed input and returns data without writing files.
"""
import asyncio
import pytest

# The server module does not exist yet — this import is the RED.
from astro.server import mcp  # noqa: E402

from fastmcp import Client

GOLDEN_INPUT = dict(date="2026-06-22", lat=45.04, lon=38.98, tz=3)
GOLDEN_FIRST_WATCH = {"start_local": "02:44", "asc_sign": "Близнецы"}
GOLDEN_WATCH_COUNT = 12


async def _call_tool(name: str, args: dict):
    async with Client(mcp) as client:
        return await client.call_tool(name, args)


def test_tool_returns_golden_watches():
    # Drive the async in-memory MCP client from a sync test (no pytest-asyncio dependency).
    result = asyncio.run(_call_tool("rising_hands", GOLDEN_INPUT))
    watches = result.data["watches"]
    assert len(watches) == GOLDEN_WATCH_COUNT
    first = watches[0]
    assert first["start_local"] == GOLDEN_FIRST_WATCH["start_local"]
    assert first["asc_sign"] == GOLDEN_FIRST_WATCH["asc_sign"]


def test_natal_tool_returns_golden_structure():
    """The natal composite through the MCP boundary:
    spot-checks the same Trump-fixture goldens as tests/test_natal.py."""
    result = asyncio.run(_call_tool(
        "natal",
        dict(datetime_utc="1946-06-14T14:54:00Z", lat=40.7, lon=-73.8164),
    ))
    chart = result.data
    assert abs(chart["positions"]["sun"] - 82.9284020277778) < 1e-6
    assert abs(chart["houses"]["angles"]["asc"] - 149.958846361111) < 1e-6
    assert chart["dignities"]["saturn"] == {"sign": "Cancer", "dignity": "detriment"}
    assert any(
        {a["body1"], a["body2"]} == {"venus", "saturn"} and a["aspect"] == "conjunction"
        for a in chart["aspects"]
    )


def test_solar_return_tool_returns_witnessed_golden():
    """SR composite through the MCP boundary: recipe-witnessed instant + spot values."""
    result = asyncio.run(_call_tool(
        "solar_return",
        dict(natal_datetime_utc="1946-06-14T14:54:00Z", birth_lat=40.7, birth_lon=-73.8164,
             return_year=2025),
    ))
    sr = result.data
    assert sr["return_instant_utc"] == "2025-06-13T16:57:23Z"
    assert abs(sr["return"]["positions"]["jupiter"] - 90.87001844444444) < 1e-6
    assert sr["profection"]["lord_of_year"] == "jupiter"


def test_profection_tool_returns_witnessed_golden():
    """Profection through the MCP boundary: age 79 (return 2025) on the Trump fixture =
    step 7 -> 8th house Pisces, Lord of Year Jupiter, natally in Libra / whole-sign 3rd
    (recipe-function-witnessed values, see tests/test_profection.py)."""
    result = asyncio.run(_call_tool(
        "profection",
        dict(natal_datetime_utc="1946-06-14T14:54:00Z", lat=40.7, lon=-73.8164,
             return_year=2025),
    ))
    prof = result.data
    assert prof["age_years"] == 79
    assert prof["profected_house"] == 8
    assert prof["profected_sign"] == "Pisces"
    assert prof["lord_of_year"] == "jupiter"
    assert prof["lord_natal"] == {"sign": "Libra", "wholesign_house": 3}
    assert prof["house_frame"] == "whole_sign"


@pytest.mark.parametrize("step_days", [0, -1])
def test_transits_rejects_nonpositive_step(step_days):
    with pytest.raises(Exception, match="step_days must be greater than zero"):
        asyncio.run(_call_tool(
            "transits",
            dict(
                natal_datetime_utc="2000-01-01T12:00:00Z",
                lat=0.0,
                lon=0.0,
                range_start_utc="2026-01-01T00:00:00Z",
                range_end_utc="2026-01-02T00:00:00Z",
                step_days=step_days,
            ),
        ))


def test_solar_return_requires_complete_relocation_pair():
    with pytest.raises(Exception, match="sr_lat and sr_lon must be provided together"):
        asyncio.run(_call_tool(
            "solar_return",
            dict(
                natal_datetime_utc="2000-01-01T12:00:00Z",
                birth_lat=0.0,
                birth_lon=0.0,
                return_year=2026,
                sr_lat=45.0,
            ),
        ))


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        (
            "natal",
            dict(datetime_utc="2000-01-01T12:00:00", lat=0.0, lon=0.0),
            "datetime_utc must include an explicit UTC offset",
        ),
        (
            "natal",
            dict(datetime_utc="2000-01-01T12:00:00Z", lat=91.0, lon=0.0),
            "lat must be between -90 and 90",
        ),
        (
            "transits",
            dict(
                natal_datetime_utc="2000-01-01T12:00:00Z",
                lat=0.0,
                lon=0.0,
                range_start_utc="2026-01-02T00:00:00Z",
                range_end_utc="2026-01-01T00:00:00Z",
            ),
            "range_end_utc must be later than range_start_utc",
        ),
    ],
)
def test_tools_reject_invalid_public_inputs(tool, arguments, message):
    with pytest.raises(Exception, match=message):
        asyncio.run(_call_tool(tool, arguments))
