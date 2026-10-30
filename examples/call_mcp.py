"""Run valid and invalid calls against an Astrolab MCP server."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

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
_ROOT = Path(__file__).resolve().parents[1]
_KIT_PATHS = {
    "partner_portrait": {
        "recipe": "docs/partner-portrait-reading-recipe.md",
        "sources": "docs/research/partner-portrait-method-sources.md",
        "twin": "artifacts/report-templates/partner-portrait-astrology.md",
        "html": "artifacts/report-templates/partner-portrait-reading.html",
        "boundary": "docs/report-system.md",
    },
    "horary": {
        "recipe": "docs/horary-reading-recipe.md",
        "sources": "docs/research/horary-method-sources.md",
        "twin": "artifacts/report-templates/horary-astrology.md",
        "html": "artifacts/report-templates/horary-reading.html",
        "boundary": "docs/report-system.md",
    },
}


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


async def _read_product_kit(client: Client, product: str) -> dict:
    tool, paths = product + "_kit", _KIT_PATHS[product]
    manifest = (await client.call_tool(tool, {})).data
    if manifest["manifest_sha256"] != _digest({k: v for k, v in manifest.items() if k != "manifest_sha256"}):
        raise RuntimeError(f"{product}: manifest hash differs")
    entries = manifest["documents"]
    if len(entries) != len(paths) or {e["id"] for e in entries} != set(paths):
        raise RuntimeError(f"{product}: expected exactly five known documents")
    for entry in entries:
        identity = entry["id"]
        document = (await client.call_tool(tool, {"document": identity})).data
        raw = document["content"].encode("utf-8")
        if (document["source_path"] != paths[identity] or entry["source_path"] != paths[identity]
                or document["id"] != identity or entry["required"] is not True
                or raw != (_ROOT / paths[identity]).read_bytes()
                or len(raw) != document["byte_length"] or len(raw) != entry["byte_length"]
                or hashlib.sha256(raw).hexdigest() != document["sha256"]
                or document["sha256"] != entry["sha256"]):
            raise RuntimeError(f"{product}: delivered {identity} differs from the allowed source bytes")
    return manifest


async def _products_workflow(url: str) -> dict:
    moment = "2000-01-01T12:00:00Z"
    cfg = json.loads((_ROOT / "artifacts/mcp-recipes/examples/horary-input.example.json").read_text(encoding="utf-8"))
    async with Client(url) as client:
        physical = (await client.call_tool("body_states", {"datetime_utc": moment})).data
        kits = {product: await _read_product_kit(client, product) for product in _KIT_PATHS}
        partner = (await client.call_tool("partner_portrait", {
            "datetime_utc": moment, "lat": 0.0, "lon": 0.0, "partner": "women",
        })).data
        horary = (await client.call_tool("horary", {"input": cfg})).data
        bad = copy.deepcopy(cfg)
        bad["intake"]["status"] = "needs_clarification"
        rejected = await client.call_tool("horary", {"input": bad}, raise_on_error=False)
    if physical["moment_utc"] != moment or partner["body_states"] != physical:
        raise RuntimeError("partner physical states differ from the independent body-state call")
    for product, result in (("partner_portrait", partner), ("horary", horary)):
        if result["kit"] != kits[product] or result["provenance"]["kit_manifest_sha256"] != kits[product]["manifest_sha256"]:
            raise RuntimeError(f"{product}: result is not bound to the delivered kit")
    facts, provenance = horary["facts"], horary["provenance"]
    if (facts["input"] != cfg or facts["radicality_verdict"] is not None
            or provenance["input_sha256"] != _digest(cfg) or provenance["facts_sha256"] != _digest(facts)
            or ET.fromstring(horary["wheel_svg"]).tag != "{http://www.w3.org/2000/svg}svg"):
        raise RuntimeError("horary input, facts provenance or SVG differs")
    if not rejected.is_error or rejected.data is not None:
        raise RuntimeError("unaccepted horary input was not rejected as an MCP error")
    return {
        "body_state_count": len(physical["bodies"]),
        "kit_document_counts": {product: len(kit["documents"]) for product, kit in kits.items()},
        "kit_manifest_sha256": {product: kit["manifest_sha256"] for product, kit in kits.items()},
        "partner": partner["partner"],
        "horary_method": facts["method"], "horary_moment_utc": facts["moment_utc"],
        "horary_event_count": len(facts["events"]),
        "wheel_svg_bytes": len(horary["wheel_svg"].encode("utf-8")),
        "invalid_horary_rejected": rejected.is_error,
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
        solar_events = [
            event
            for event in transits["timeline"]
            if event["transit_body"] == "sun"
            and event["natal_target"] == "sun"
            and event["aspect"] == "conjunction"
        ]
        if len(solar_events) != 1:
            raise RuntimeError(f"expected one Sun-to-Sun conjunction, got {len(solar_events)}")

        transit_instant = solar_events[0]["estimated_exact_instant_utc"]
        transit_chart = (
            await client.call_tool(
                "natal",
                {
                    "datetime_utc": transit_instant,
                    "lat": natal_args["lat"],
                    "lon": natal_args["lon"],
                },
            )
        ).data
        transit_phases = (
            await client.call_tool(
                "phase_states",
                {
                    "positions": transit_chart["positions"],
                    "moment_utc": transit_instant,
                },
            )
        ).data

    natal_sun = natal["positions"]["sun"]
    if abs(solar["natal"]["positions"]["sun"] - natal_sun) > 1e-8:
        raise RuntimeError("solar-return natal Sun differs from the natal tool")
    if abs(solar["return"]["positions"]["sun"] - natal_sun) > 1e-5:
        raise RuntimeError("return Sun does not reproduce the natal Sun")
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
        "solar_conjunction_estimated_instant_utc": transit_instant,
        "transit_sun_phase": transit_phases["states"]["sun"],
        "transit_phase_frame": transit_phases["house_frame"],
        "transit_event_count": len(transits["timeline"]),
    }


async def call(url: str, example: str) -> None:
    if example == "products_workflow":
        print(json.dumps(await _products_workflow(url), ensure_ascii=False, indent=2))
        return
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
        "example", choices=(*_CALLS, "chart_workflow", "products_workflow"), nargs="?", default="rising_hands"
    )
    parser.add_argument("--url", default="http://127.0.0.1:8400/mcp")
    args = parser.parse_args()
    asyncio.run(call(args.url, args.example))


if __name__ == "__main__":
    main()
