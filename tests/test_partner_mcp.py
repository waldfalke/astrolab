"""New MCP-only product surface over fixed nonpersonal inputs; no transport/image claim."""
import asyncio
import hashlib
import json
from pathlib import Path

from fastmcp import Client
import pytest

from astro import engine, server

ROOT = Path(__file__).resolve().parents[1]
MOMENT = "2000-01-01T12:00:00Z"
INPUT = {"datetime_utc": MOMENT, "lat": 0.0, "lon": 0.0, "partner": "women"}
DOCS = {
    "recipe": "docs/partner-portrait-reading-recipe.md",
    "sources": "docs/research/partner-portrait-method-sources.md",
    "twin": "artifacts/report-templates/partner-portrait-astrology.md",
    "html": "artifacts/report-templates/partner-portrait-reading.html",
    "boundary": "docs/report-system.md",
}
OLD_TOOLS = {"rising_hands", "natal", "phase_states", "profection", "solar_return", "transits"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def engine_a(monkeypatch):
    monkeypatch.setattr(engine, "DEFAULT_ENGINE", "a")


async def call(name, arguments):
    async with Client(server.mcp) as client:
        assert name in {tool.name for tool in await client.list_tools()}, "requested tool is not registered"
        return await client.call_tool(name, arguments, raise_on_error=False)


def test_discovery_identifies_product_and_preserves_old_six_contracts():
    async def discover():
        async with Client(server.mcp) as client:
            return client.initialize_result, await client.list_tools()
    initialized, tools = asyncio.run(discover())
    assert {tool.name for tool in tools} == OLD_TOOLS | {"body_states", "partner_portrait", "partner_portrait_kit", "horary", "horary_kit"}
    assert "partner_portrait_kit" in initialized.instructions
    assert "partner_portrait_kit" in next(t.description for t in tools if t.name == "partner_portrait")
    projection = []
    for tool in tools:
        if tool.name in OLD_TOOLS:
            row = tool.model_dump(by_alias=True, exclude_none=True)
            projection.append({key: row[key] for key in ("name", "description", "inputSchema", "outputSchema")})
    assert digest(projection) == "2a92f7899c2da6f165b925d0e8e20d662cdda98b73c51ecdb538271f1226e344"


def test_five_documents_are_full_exact_bytes_and_manifest_is_bound():
    async def read():
        async with Client(server.mcp) as client:
            manifest = (await client.call_tool("partner_portrait_kit", {})).data
            docs = {name: (await client.call_tool("partner_portrait_kit", {"document": name})).data for name in DOCS}
            return manifest, docs
    manifest, docs = asyncio.run(read())
    assert manifest["kit_id"] and manifest["kit_version"]
    assert manifest["manifest_sha256"] == digest({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    assert manifest["profile"]["id"] == "selected-classical-v1"
    entries = {entry["id"]: entry for entry in manifest["documents"]}
    assert len(manifest["documents"]) == 5 and set(entries) == set(DOCS)
    for name, source in DOCS.items():
        raw = (ROOT / source).read_bytes()
        document, entry = docs[name], entries[name]
        assert document["content"].encode("utf-8") == raw
        assert document["byte_length"] == len(raw)
        assert document["sha256"] == entry["sha256"] == hashlib.sha256(raw).hexdigest()
        assert document["source_path"] == entry["source_path"] == source
        assert document["mime_type"] == entry["mime_type"]
        assert document["id"] == name and entry["required"] is True and entry["role"]


@pytest.mark.parametrize("partner", ["women", "men"])
def test_partner_returns_fixed_profile_states_real_speeds_and_actual_kit(partner):
    async def consume():
        async with Client(server.mcp) as client:
            manifest = (await client.call_tool("partner_portrait_kit", {})).data
            physical = (await client.call_tool("body_states", {"datetime_utc": MOMENT})).data
            result = (await client.call_tool("partner_portrait", {**INPUT, "partner": partner})).data
            phases = (await client.call_tool("phase_states", {"positions": result["natal"]["positions"],
                "moment_utc": MOMENT, "cusps": result["natal"]["houses"]["cusps"]})).data
            return manifest, physical, result, phases
    manifest, physical, result, phases = asyncio.run(consume())
    assert result["kit"] == manifest
    assert result["body_states"] == physical
    assert set(result["natal"]["positions"]) == set(engine.DEFAULT_BODIES)
    assert result["settings"]["dignities"] == "traditional"
    assert result["settings"]["state_profile"] == "selected-classical-v1"
    assert result["natal"]["phases"] == result["phase_states"] == phases
    assert result["carrier_states"]["profile"] == "selected-classical-v1"
    assert result["carrier_states"]["input_sha256"] == {"natal": digest(result["natal"]), "body_states": digest(physical)}
    assert result["motion_input"]["values"] == {b: v["longitude_speed_deg_per_day"] for b, v in physical["bodies"].items()}
    assert result["contacts"] and all(row["motion"]["status"] != "unavailable" for row in result["contacts"])
    assert result["provenance"]["kit_manifest_sha256"] == manifest["manifest_sha256"]
    assert "astro/partner_portrait.py" in result["provenance"]["operator_sha256"]
    assert not {"prose", "interpretation", "reading", "report_html"} & result.keys()
    assert str(ROOT) not in json.dumps(result)


def test_standalone_body_states_preserves_fractions_partner_explicitly_refuses():
    moment = "2000-01-01T12:00:00.500000Z"
    physical = asyncio.run(call("body_states", {"datetime_utc": moment}))
    rejected = asyncio.run(call("partner_portrait", {**INPUT, "datetime_utc": moment}))
    assert not physical.is_error and physical.data["moment_utc"] == moment
    assert rejected.is_error and "whole seconds" in str(rejected.content)


@pytest.mark.parametrize("tool,arguments", [
    *( ("partner_portrait_kit", {"document": value}) for value in ("missing", "../recipe", ".private/test", "C:/test.txt") ),
    *( ("partner_portrait", {**INPUT, "datetime_utc": value}) for value in (None, "unknown", "2000-01-01", "2000-01-01T12:00:00+03:00", "2000-02-30T12:00:00Z") ),
    ("partner_portrait", {**INPUT, "lat": 91}), ("partner_portrait", {**INPUT, "lon": -181}),
    ("partner_portrait", {**INPUT, "lat": True}), ("partner_portrait", {**INPUT, "orb": True}),
    ("partner_portrait", {**INPUT, "orb": -1}), ("partner_portrait", {**INPUT, "orb": 16}),
    ("partner_portrait", {**INPUT, "orb": float("nan")}), ("partner_portrait", {**INPUT, "orb": float("inf")}),
    ("partner_portrait", {**INPUT, "lat": float("nan")}), ("partner_portrait", {**INPUT, "lon": float("inf")}),
    ("partner_portrait", {**INPUT, "partner": "unknown"}),
    ("body_states", {"datetime_utc": MOMENT, "bodies": ["unknown"]}),
    ("body_states", {"datetime_utc": MOMENT, "bodies": [True]}),
    ("body_states", {"datetime_utc": MOMENT, "bodies": []}),
    ("body_states", {"datetime_utc": MOMENT, "bodies": ["sun", "sun"]}),
    ("body_states", {"datetime_utc": MOMENT, "bodies": ["Sun"]}),
    ("body_states", {"datetime_utc": "2000-01-01T12:00:00.1234567Z"}),
])
def test_new_tools_reject_invalid_inputs_without_host_paths(tool, arguments):
    result = asyncio.run(call(tool, arguments))
    assert result.is_error
    assert str(ROOT) not in str(result.content)


@pytest.mark.parametrize("tool,arguments", [("body_states", {"datetime_utc": MOMENT}), ("partner_portrait", INPUT)])
def test_new_calculations_require_selected_engine_a(monkeypatch, tool, arguments):
    monkeypatch.setattr(engine, "DEFAULT_ENGINE", "b1")
    result = asyncio.run(call(tool, arguments))
    assert result.is_error and "Engine A" in str(result.content)


@pytest.mark.parametrize("tool,arguments,target", [
    ("body_states", {"datetime_utc": MOMENT}, "compute_body_states_series"),
    ("partner_portrait", INPUT, "compute_natal"),
])
def test_new_runtime_errors_do_not_reveal_host_paths(monkeypatch, tool, arguments, target):
    def broken(*args, **kwargs):
        raise RuntimeError(str(ROOT / ".private/synthetic-do-not-expose"))
    monkeypatch.setattr(server, target, broken)
    result = asyncio.run(call(tool, arguments))
    assert result.is_error and str(ROOT) not in str(result.content)
    assert "synthetic-do-not-expose" not in str(result.content)


def test_missing_required_document_is_an_error_without_a_host_path(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_KIT_ROOT", tmp_path)
    result = asyncio.run(call("partner_portrait_kit", {}))
    assert result.is_error and str(tmp_path) not in str(result.content)
