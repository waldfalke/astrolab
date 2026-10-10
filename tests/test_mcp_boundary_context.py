"""Focused boundary context extends only the two rising states cut by midnight."""
import asyncio
import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "artifacts/mcp-recipes/collect_mcp_boundary_context.py"
BODIES = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)
START = datetime(2026, 10, 4, 21, tzinfo=timezone.utc)


def collector():
    assert SCRIPT.exists(), "production boundary-context collector is not implemented"
    spec = importlib.util.spec_from_file_location("mcp_boundary_context", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(index: int, asc: float) -> dict:
    cusps = [(asc + house * 30) % 360 for house in range(12)]
    return {
        "local_minute": index,
        "utc": (START + timedelta(minutes=index)).isoformat(),
        "positions": {body: 10.0 + offset for offset, body in enumerate(BODIES)},
        "cusps": cusps,
        "angles": {"asc": asc, "mc": cusps[9]},
    }


def source_package(tmp_path: Path, *, exact_end_ingress: bool = False) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    frames = []
    for index in range(1441):
        if index < 720:
            asc = 45.0
        elif exact_end_ingress and index < 1440:
            asc = 75.0
        elif exact_end_ingress:
            asc = 90.0
        else:
            asc = 75.0
        frames.append(frame(index, asc))
    raw = json.dumps(frames, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    metadata = {
        "method_version": "mcp-natal-minute-frames-v1",
        "date": "2026-10-05",
        "latitude": 45.04,
        "longitude": 38.98,
        "timezone": "UTC+03:00",
        "interval_utc": [START.isoformat(), (START + timedelta(days=1)).isoformat()],
        "samples": 1441,
        "house_system": "placidus",
        "engine": "a",
        "mcp": {"target": "in-process:astro.server", "transport": "in_process", "tool": "natal"},
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }
    (source / "minute-frames.json").write_bytes(raw)
    (source / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return source


def chart(moment: datetime, asc: float, *, lat: float = 45.04) -> dict:
    cusps = [(asc + house * 30) % 360 for house in range(12)]
    return {
        "moment_utc": moment.isoformat().replace("+00:00", "Z"),
        "location": {"lat": lat, "lon": 38.98},
        "positions": {body: 10.0 + offset for offset, body in enumerate(BODIES)},
        "houses": {"cusps": cusps, "angles": {"asc": asc, "mc": cusps[9]}},
        "phases": {"house_frame": "placidus"},
    }


class FakeClient:
    def __init__(self, *, exact_end_ingress: bool = False, bad_location: bool = False,
                 never_changes: bool = False):
        self.exact_end_ingress = exact_end_ingress
        self.bad_location = bad_location
        self.never_changes = never_changes
        self.moments = []

    async def call_tool(self, name, arguments):
        assert name == "natal"
        moment = datetime.fromisoformat(arguments["datetime_utc"].replace("Z", "+00:00"))
        self.moments.append(moment)
        minute = int((moment - START).total_seconds() // 60)
        if self.never_changes:
            asc = 45.0
        elif minute < 0:
            asc = 44.0 if minute == -1 else 29.0
        elif self.exact_end_ingress:
            asc = 95.0 if minute == 1441 else 121.0
        else:
            asc = 80.0 if minute == 1441 else 91.0
        return SimpleNamespace(data=chart(moment, asc, lat=0.0 if self.bad_location else 45.04))


def test_collects_only_until_both_external_ingresses_and_records_them(tmp_path):
    source = source_package(tmp_path)
    output = tmp_path / "boundary"
    client = FakeClient()

    result = asyncio.run(collector().collect_boundary_context(
        client, source=source, output=output,
    ))

    assert client.moments == [
        START - timedelta(minutes=1), START - timedelta(minutes=2),
        START + timedelta(minutes=1441), START + timedelta(minutes=1442),
    ]
    assert result["schema_version"] == "city-day-boundary-context-v1"
    assert [state["edge"] for state in result["edge_states"]] == ["start", "end"]
    assert [state["sign"] for state in result["edge_states"]] == ["Taurus", "Gemini"]
    assert result["edge_states"][0]["start_attribution"] == "context_before_day"
    assert result["edge_states"][1]["end_attribution"] == "context_after_day"
    assert result["counts"] == {
        "day_samples": 1441,
        "external_requests": 4,
        "before_day_requests": 2,
        "after_day_requests": 2,
        "edge_states": 2,
    }
    assert result["provenance"]["mcp"]["requests"] == 4
    exchange_raw = (output / "mcp-exchanges.jsonl").read_bytes()
    assert len(exchange_raw.splitlines()) == 4
    assert result["provenance"]["mcp_exchanges_sha256"] == hashlib.sha256(exchange_raw).hexdigest()
    assert json.loads((output / "boundary-context.json").read_text(encoding="utf-8")) == result


def test_right_boundary_uses_last_instant_of_half_open_day(tmp_path):
    source = source_package(tmp_path, exact_end_ingress=True)
    result = asyncio.run(collector().collect_boundary_context(
        FakeClient(exact_end_ingress=True), source=source, output=tmp_path / "boundary",
    ))

    end_state = result["edge_states"][1]
    assert end_state["sign"] == "Gemini"
    assert end_state["full_interval_local"][1] == "2026-10-06T00:00:00+03:00"
    assert end_state["visible_interval_local"][1] == "2026-10-06T00:00:00+03:00"
    assert end_state["end_ingress"]["sign_after"] == "Cancer"


def test_rejects_incompatible_external_response(tmp_path):
    with pytest.raises(ValueError, match="location differs"):
        asyncio.run(collector().collect_boundary_context(
            FakeClient(bad_location=True), source=source_package(tmp_path),
            output=tmp_path / "boundary",
        ))
    assert not (tmp_path / "boundary").exists()


def test_rejects_scan_without_sign_change(tmp_path):
    client = FakeClient(never_changes=True)
    with pytest.raises(ValueError, match="within 2 minutes before the day"):
        asyncio.run(collector().collect_boundary_context(
            client, source=source_package(tmp_path), output=tmp_path / "boundary",
            max_scan_minutes=2,
        ))
    assert len(client.moments) == 2
    assert not (tmp_path / "boundary").exists()

