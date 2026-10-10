"""A clean MCP client can acquire the complete input for the day-state probe."""
import asyncio
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastmcp import Client

import astro.engine as engine
from astro.server import mcp
from tests.conftest import require_engine_a


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "artifacts/mcp-recipes/collect_mcp_day_frames.py"
EXPECTED_SHA256 = "44dba7f04d489e7da07721f08d235b099ae15cb56a6c299a96c20d4151a7afd7"


def collector():
    assert SCRIPT.exists(), "MCP day-frame collector is not implemented"
    spec = importlib.util.spec_from_file_location("mcp_day_frames", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_day_bounds_are_inclusive_and_utc():
    moments = collector().day_moments("2026-10-05", 3)
    assert len(moments) == 1441
    assert moments[0] == datetime(2026, 10, 4, 21, tzinfo=timezone.utc)
    assert moments[-1] == datetime(2026, 10, 5, 21, tzinfo=timezone.utc)


def test_fractional_fixed_offset_is_preserved():
    moments = collector().day_moments("2026-10-05", 5.5)
    assert moments[0] == datetime(2026, 10, 4, 18, 30, tzinfo=timezone.utc)
    assert moments[-1] == datetime(2026, 10, 5, 18, 30, tzinfo=timezone.utc)
    assert collector().utc_offset_label(5.5) == "UTC+05:30"


def test_local_day_rejects_non_contract_iso_forms():
    with pytest.raises(ValueError, match="yyyy-MM-dd"):
        collector().day_moments("20261005", 3)


def test_frame_rejects_an_incomplete_mcp_response():
    moment = datetime(2026, 10, 4, 21, tzinfo=timezone.utc)
    chart = {
        "moment_utc": "2026-10-04T21:00:00Z",
        "location": {"lat": 45.04, "lon": 38.98},
        "positions": {body: 0.0 for body in collector().BODIES if body != "moon"},
        "houses": {"cusps": [i * 30.0 for i in range(12)],
                   "angles": {"asc": 0.0, "mc": 270.0}},
    }
    with pytest.raises(ValueError, match="moon"):
        collector().frame_from_chart(0, moment, chart, lat=45.04, lon=38.98)


def test_frame_rejects_unattested_house_system_and_offsetless_utc():
    moment = datetime(2026, 10, 4, 21, tzinfo=timezone.utc)
    chart = {
        "moment_utc": "2026-10-04T21:00:00Z",
        "location": {"lat": 45.04, "lon": 38.98},
        "positions": {body: 0.0 for body in collector().BODIES},
        "houses": {"cusps": [i * 30.0 for i in range(12)],
                   "angles": {"asc": 0.0, "mc": 270.0}},
        "phases": {"house_frame": "equal_asc"},
    }
    with pytest.raises(ValueError, match="Placidus"):
        collector().frame_from_chart(0, moment, chart, lat=45.04, lon=38.98)
    chart["phases"]["house_frame"] = "placidus"
    chart["moment_utc"] = "2026-10-04T21:00:00"
    with pytest.raises(ValueError, match="explicit UTC"):
        collector().frame_from_chart(0, moment, chart, lat=45.04, lon=38.98)


def test_full_local_day_through_fastmcp_matches_accepted_input(monkeypatch):
    require_engine_a()
    monkeypatch.setattr(engine, "DEFAULT_ENGINE", "a")

    async def acquire():
        async with Client(mcp) as client:
            return await collector().collect_frames(
                client, date="2026-10-05", lat=45.04, lon=38.98, tz=3,
            )

    frames = asyncio.run(acquire())
    raw = json.dumps(frames, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(frames) == 1441
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256


