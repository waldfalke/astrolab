"""Collect one fixed-offset local day through Astrolab's existing MCP ``natal`` tool."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import re
from datetime import date as date_type, datetime, timedelta, timezone
from pathlib import Path

from fastmcp import Client


METHOD_VERSION = "mcp-natal-minute-frames-v1"
BODIES = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)


def _offset_minutes(tz: float) -> int:
    if isinstance(tz, bool) or not isinstance(tz, (int, float)) or not math.isfinite(tz):
        raise ValueError("tz must be a finite number")
    minutes = round(tz * 60)
    if not math.isclose(tz * 60, minutes, abs_tol=1e-9):
        raise ValueError("tz must use minute precision")
    if not -12 * 60 <= minutes <= 14 * 60:
        raise ValueError("tz must be between -12 and 14")
    return minutes


def utc_offset_label(tz: float) -> str:
    minutes = _offset_minutes(tz)
    sign = "+" if minutes >= 0 else "-"
    hours, remainder = divmod(abs(minutes), 60)
    return f"UTC{sign}{hours:02d}:{remainder:02d}"


def day_moments(date: str, tz: float) -> list[datetime]:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) is None:
        raise ValueError("date must use yyyy-MM-dd")
    try:
        local_date = date_type.fromisoformat(date)
    except ValueError as exc:
        raise ValueError("date must use yyyy-MM-dd") from exc
    local_midnight = datetime.combine(
        local_date, datetime.min.time(), timezone(timedelta(minutes=_offset_minutes(tz))),
    )
    start = local_midnight.astimezone(timezone.utc)
    return [start + timedelta(minutes=minute) for minute in range(1441)]


def frame_from_chart(
    index: int, moment: datetime, chart: dict, *, lat: float, lon: float,
) -> dict:
    expected = moment.astimezone(timezone.utc)
    try:
        returned = datetime.fromisoformat(chart["moment_utc"].replace("Z", "+00:00"))
        location = chart["location"]
        positions = chart["positions"]
        houses = chart["houses"]
        cusps = houses["cusps"]
        angles = houses["angles"]
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"incomplete natal response at minute {index}: {exc}") from exc
    if returned.utcoffset() != timedelta(0):
        raise ValueError(f"natal response moment requires an explicit UTC offset at minute {index}")
    if returned.astimezone(timezone.utc) != expected:
        raise ValueError(f"natal response moment differs at minute {index}")
    if location != {"lat": lat, "lon": lon}:
        raise ValueError(f"natal response location differs at minute {index}")
    missing = [body for body in BODIES if body not in positions]
    if missing:
        raise ValueError(f"natal response misses bodies at minute {index}: {', '.join(missing)}")
    try:
        house_frame = chart["phases"]["house_frame"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"natal response does not attest its house system at minute {index}") from exc
    if house_frame != "placidus":
        raise ValueError(f"natal response does not attest Placidus at minute {index}")
    if not isinstance(cusps, list) or len(cusps) != 12:
        raise ValueError(f"natal response requires 12 cusps at minute {index}")
    if not isinstance(angles, dict) or not {"asc", "mc"} <= set(angles):
        raise ValueError(f"natal response requires ASC and MC at minute {index}")
    values = [positions[body] for body in BODIES] + list(cusps) + list(angles.values())
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in values):
        raise ValueError(f"natal response contains a non-finite coordinate at minute {index}")
    return {
        "local_minute": index,
        "utc": expected.isoformat(),
        "positions": {body: positions[body] for body in BODIES},
        "cusps": cusps,
        "angles": angles,
    }


async def collect_frames(
    client: Client, *, date: str, lat: float, lon: float, tz: float,
    exchanges: list[dict] | None = None,
) -> list[dict]:
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in (lat, lon)):
        raise ValueError("lat and lon must be finite numbers")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("lat/lon are out of range")
    frames = []
    for index, moment in enumerate(day_moments(date, tz)):
        arguments = {
            "datetime_utc": moment.isoformat().replace("+00:00", "Z"),
            "lat": lat,
            "lon": lon,
        }
        chart = (await client.call_tool("natal", arguments)).data
        if exchanges is not None:
            exchanges.append({
                "request": {"tool": "natal", "arguments": arguments},
                "response": chart,
            })
        frames.append(frame_from_chart(index, moment, chart, lat=lat, lon=lon))
    return frames


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


async def run(args: argparse.Namespace) -> None:
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    exchanges: list[dict] = []
    target = getattr(args, "mcp_target", None) or args.mcp_url
    label = getattr(args, "mcp_label", None) or str(args.mcp_url)
    transport = getattr(args, "mcp_transport", None) or "http"
    async with Client(target) as client:
        frames = await collect_frames(
            client, date=args.date, lat=args.lat, lon=args.lon, tz=args.tz,
            exchanges=exchanges,
        )
    frames_raw = _json_bytes(frames)
    exchange_raw = b"".join(_json_bytes(item) + b"\n" for item in exchanges)
    moments = day_moments(args.date, args.tz)
    metadata = {
        "method_version": METHOD_VERSION,
        "date": args.date,
        "latitude": args.lat,
        "longitude": args.lon,
        "timezone": utc_offset_label(args.tz),
        "interval_utc": [moments[0].isoformat(), moments[-1].isoformat()],
        "samples": len(frames),
        "house_system": "placidus",
        "mcp": {"target": label, "transport": transport, "tool": "natal", "requests": len(exchanges)},
        "raw_sha256": hashlib.sha256(frames_raw).hexdigest(),
        "mcp_exchanges_sha256": hashlib.sha256(exchange_raw).hexdigest(),
    }
    engine = getattr(args, "engine", None)
    if engine is not None:
        metadata["engine"] = engine
    output.mkdir(parents=True)
    (output / "minute-frames.json").write_bytes(frames_raw)
    (output / "mcp-exchanges.jsonl").write_bytes(exchange_raw)
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp-url", default="http://127.0.0.1:8400/mcp")
    parser.add_argument("--date", required=True)
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--tz", required=True, type=float)
    parser.add_argument("--output", required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()

