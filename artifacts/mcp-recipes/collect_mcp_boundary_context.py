"""Observe the two rising-sign states cut by a fixed-offset civil day."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp import Client


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import clock_event_state_probe
import collect_mcp_day_frames


SCHEMA_VERSION = "city-day-boundary-context-v1"
MAX_SCAN_MINUTES = 1440
SIGNS = clock_event_state_probe.SIGNS


def _utc(value: str) -> datetime:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.utcoffset() is None:
        raise ValueError("UTC instant requires an explicit offset")
    return moment.astimezone(timezone.utc)


def _utc_text(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _fixed_zone(label: str) -> timezone:
    match = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", label or "")
    if not match or int(match[2]) > 23 or int(match[3]) > 59:
        raise ValueError("metadata requires a fixed UTC offset")
    minutes = int(match[2]) * 60 + int(match[3])
    return timezone(timedelta(minutes=minutes if match[1] == "+" else -minutes))


def _local_text(moment: datetime, zone: timezone) -> str:
    return moment.astimezone(zone).isoformat(timespec="seconds")


def _sign_index(frame: dict) -> int:
    return int(frame["angles"]["asc"] // 30) % 12


async def _external_frame(client, moment: datetime, index: int, *, lat: float, lon: float,
                          exchanges: list[dict]) -> dict:
    arguments = {
        "datetime_utc": _utc_text(moment),
        "lat": lat,
        "lon": lon,
    }
    chart = (await client.call_tool("natal", arguments)).data
    exchanges.append({
        "request": {"tool": "natal", "arguments": arguments},
        "response": chart,
    })
    return collect_mcp_day_frames.frame_from_chart(index, moment, chart, lat=lat, lon=lon)


async def _scan_edge(client, *, boundary: datetime, direction: int, anchor: dict,
                     lat: float, lon: float, exchanges: list[dict], limit: int) -> list[dict]:
    side = "before" if direction < 0 else "after"
    frames = []
    anchor_sign = _sign_index(anchor)
    for distance in range(1, limit + 1):
        frame = await _external_frame(
            client,
            boundary + timedelta(minutes=direction * distance),
            anchor["local_minute"] + direction * distance,
            lat=lat,
            lon=lon,
            exchanges=exchanges,
        )
        frames.append(frame)
        if _sign_index(frame) != anchor_sign:
            return list(reversed(frames)) if direction < 0 else frames
    raise ValueError(f"ASC sign change was not observed within {limit} minutes {side} the day")


def _asc_ingresses(frames: list[dict]) -> list[dict]:
    events = []
    seen = set()
    for left, right in zip(frames, frames[1:]):
        if _sign_index(left) == _sign_index(right):
            continue
        hits = [hit for hit in clock_event_state_probe.contacts_in_step(
            left["angles"]["asc"], right["angles"]["asc"], 0, 0,
            targets=tuple(range(0, 360, 30)),
        ) if 0 <= hit["fraction"] <= 1]
        if len(hits) != 1:
            raise ValueError("ASC sign change does not have exactly one sampled boundary")
        hit = hits[0]
        left_time, right_time = _utc(left["utc"]), _utc(right["utc"])
        moment = left_time + (right_time - left_time) * hit["fraction"]
        boundary = int(hit["target_deg"] // 30)
        increasing = hit["direction"] == "increasing"
        event = {
            "linear_estimate_utc": _utc_text(moment),
            "bracket_utc": [_utc_text(left_time), _utc_text(right_time)],
            "sign_before": SIGNS[(boundary - 1 if increasing else boundary) % 12],
            "sign_after": SIGNS[(boundary if increasing else boundary - 1) % 12],
            "time_method": "linear_relative_longitude_in_sample_bracket",
        }
        key = (event["linear_estimate_utc"], event["sign_before"], event["sign_after"])
        if key not in seen:
            seen.add(key)
            events.append(event)
    return events


def _attribution(moment: datetime, start: datetime, end: datetime) -> str:
    if moment < start:
        return "context_before_day"
    if moment >= end:
        return "context_after_day"
    return "in_report_day"


def _edge_state(ingresses: list[dict], *, edge: str, probe: datetime,
                start: datetime, end: datetime, zone: timezone) -> dict:
    earlier = [event for event in ingresses if _utc(event["linear_estimate_utc"]) <= probe]
    later = [event for event in ingresses if _utc(event["linear_estimate_utc"]) > probe]
    if not earlier or not later:
        raise ValueError(f"{edge} edge requires an observed ingress on both sides")
    left, right = earlier[-1], later[0]
    full_start, full_end = _utc(left["linear_estimate_utc"]), _utc(right["linear_estimate_utc"])
    return {
        "edge": edge,
        "sign": left["sign_after"],
        "full_interval_local": [_local_text(full_start, zone), _local_text(full_end, zone)],
        "visible_interval_local": [
            _local_text(max(full_start, start), zone),
            _local_text(min(full_end, end), zone),
        ],
        "start_attribution": _attribution(full_start, start, end),
        "end_attribution": _attribution(full_end, start, end),
        "start_ingress": left,
        "end_ingress": right,
    }


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


async def collect_boundary_context(client, *, source: Path, output: Path,
                                   max_scan_minutes: int = MAX_SCAN_MINUTES) -> dict:
    """Write observed context for the first and last rising states of one day."""
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    if isinstance(max_scan_minutes, bool) or not isinstance(max_scan_minutes, int) \
            or not 1 <= max_scan_minutes <= MAX_SCAN_MINUTES:
        raise ValueError(f"max_scan_minutes must be an integer in [1, {MAX_SCAN_MINUTES}]")
    frames, metadata = clock_event_state_probe.load_inputs(
        source / "minute-frames.json", source / "metadata.json", house_system="placidus",
    )
    if metadata.get("engine") != "a":
        raise ValueError("boundary context requires source frames attested by Engine A")
    mcp = metadata.get("mcp")
    if not isinstance(mcp, dict) or mcp.get("tool") != "natal":
        raise ValueError("source metadata must attest the MCP natal tool")
    start, end = map(_utc, metadata["interval_utc"])
    lat, lon = metadata["latitude"], metadata["longitude"]
    zone = _fixed_zone(metadata["timezone"])
    exchanges: list[dict] = []

    before = await _scan_edge(
        client, boundary=start, direction=-1, anchor=frames[0], lat=lat, lon=lon,
        exchanges=exchanges, limit=max_scan_minutes,
    )
    before_count = len(before)
    after = await _scan_edge(
        client, boundary=end, direction=1, anchor=frames[-1], lat=lat, lon=lon,
        exchanges=exchanges, limit=max_scan_minutes,
    )
    combined = before + frames + after
    ingresses = _asc_ingresses(combined)
    edge_states = [
        _edge_state(ingresses, edge="start", probe=start, start=start, end=end, zone=zone),
        _edge_state(
            ingresses, edge="end", probe=end - timedelta(microseconds=1),
            start=start, end=end, zone=zone,
        ),
    ]
    exchange_raw = b"".join(_json_bytes(item) + b"\n" for item in exchanges)
    result = {
        "schema_version": SCHEMA_VERSION,
        "report_interval_local": [_local_text(start, zone), _local_text(end, zone)],
        "calculation_basis": {
            "latitude": lat,
            "longitude": lon,
            "timezone": metadata["timezone"],
            "house_system": metadata["house_system"],
            "engine": metadata["engine"],
        },
        "edge_states": edge_states,
        "counts": {
            "day_samples": len(frames),
            "external_requests": len(exchanges),
            "before_day_requests": before_count,
            "after_day_requests": len(after),
            "edge_states": len(edge_states),
        },
        "provenance": {
            "day_frames_sha256": metadata["raw_sha256"],
            "mcp": {**mcp, "requests": len(exchanges)},
            "mcp_exchanges_sha256": hashlib.sha256(exchange_raw).hexdigest(),
        },
    }
    output.mkdir(parents=True)
    (output / "mcp-exchanges.jsonl").write_bytes(exchange_raw)
    (output / "boundary-context.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


async def run(args: argparse.Namespace) -> dict:
    target = getattr(args, "mcp_target", None) or args.mcp_url
    async with Client(target) as client:
        return await collect_boundary_context(
            client,
            source=Path(args.source),
            output=Path(args.output),
            max_scan_minutes=getattr(args, "max_scan_minutes", MAX_SCAN_MINUTES),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-url", default="http://127.0.0.1:8400/mcp")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-scan-minutes", default=MAX_SCAN_MINUTES, type=int)
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args))
    except (FileExistsError, KeyError, OSError, TypeError, ValueError) as error:
        parser.exit(2, f"Boundary context rejected: {error}\n")
    print(json.dumps(result["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

