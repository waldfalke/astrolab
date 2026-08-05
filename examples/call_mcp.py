"""Run valid and invalid calls against an Astrolab MCP server."""

from __future__ import annotations

import argparse
import asyncio
import json

from fastmcp import Client
from fastmcp.exceptions import ToolError


_CALLS = {
    "rising_hands": (
        "rising_hands",
        {"date": "2026-06-22", "lat": 45.04, "lon": 38.98, "tz": 3},
    ),
    "natal": (
        "natal",
        {
            "datetime_utc": "1946-06-14T14:54:00Z",
            "lat": 40.7,
            "lon": -73.8164,
        },
    ),
    "invalid_input": (
        "profection",
        {
            "natal_datetime_utc": "1946-06-14T14:54:00Z",
            "lat": 40.7,
            "lon": -73.8164,
            "return_year": 2025,
            "scheme": "modern",
        },
    ),
}


async def _chart_workflow(url: str) -> dict:
    natal_args = {
        "datetime_utc": "1946-06-14T14:54:00Z",
        "lat": 40.7,
        "lon": -73.8164,
    }
    async with Client(url) as client:
        natal = (await client.call_tool("natal", natal_args)).data
        solar = (
            await client.call_tool(
                "solar_return",
                {
                    "natal_datetime_utc": natal_args["datetime_utc"],
                    "birth_lat": natal_args["lat"],
                    "birth_lon": natal_args["lon"],
                    "return_year": 2025,
                },
            )
        ).data
        transits = (
            await client.call_tool(
                "transits",
                {
                    "natal_datetime_utc": natal_args["datetime_utc"],
                    "lat": natal_args["lat"],
                    "lon": natal_args["lon"],
                    "range_start_utc": "2025-06-01T00:00:00Z",
                    "range_end_utc": "2025-06-25T00:00:00Z",
                    "step_days": 1.0,
                    "orb": 1.0,
                    "solar_year_start_utc": solar["return_instant_utc"],
                },
            )
        ).data

    natal_sun = natal["positions"]["sun"]
    if abs(solar["natal"]["positions"]["sun"] - natal_sun) > 1e-8:
        raise RuntimeError("solar-return natal Sun differs from the natal tool")
    if abs(solar["return"]["positions"]["sun"] - natal_sun) > 1e-5:
        raise RuntimeError("return Sun does not reproduce the natal Sun")
    solar_events = [
        event
        for event in transits["timeline"]
        if event["transit_body"] == "sun"
        and event["natal_target"] == "sun"
        and event["aspect"] == "conjunction"
    ]
    if len(solar_events) != 1:
        raise RuntimeError(f"expected one Sun-to-Sun conjunction, got {len(solar_events)}")

    return {
        "natal_moment_utc": natal["moment_utc"],
        "natal_sun_deg": natal_sun,
        "solar_return_instant_utc": solar["return_instant_utc"],
        "return_sun_deg": solar["return"]["positions"]["sun"],
        "profection": {
            "age": solar["profection"]["age_years"],
            "lord_of_year": solar["profection"]["lord_of_year"],
        },
        "solar_conjunction_exact_date": solar_events[0]["exact_date"],
        "transit_event_count": len(transits["timeline"]),
    }


async def call(url: str, example: str) -> None:
    if example == "chart_workflow":
        print(json.dumps(await _chart_workflow(url), ensure_ascii=False, indent=2))
        return
    tool_name, arguments = _CALLS[example]
    async with Client(url) as client:
        if example == "invalid_input":
            try:
                await client.call_tool(tool_name, arguments)
            except ToolError as exc:
                print(f"Rejected as expected: {exc}")
                return
            raise RuntimeError("invalid input was unexpectedly accepted")

        result = await client.call_tool(tool_name, arguments)
    print(json.dumps(result.data, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "example", choices=(*_CALLS, "chart_workflow"), nargs="?", default="rising_hands"
    )
    parser.add_argument("--url", default="http://127.0.0.1:8400/mcp")
    args = parser.parse_args()
    asyncio.run(call(args.url, args.example))


if __name__ == "__main__":
    main()
