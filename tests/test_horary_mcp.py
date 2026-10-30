"""Horary MCP handoff, physical boundaries and append-only CLI on synthetic data."""
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from fastmcp import Client
import pytest

from astro import engine, horary, server
from artifacts.renderer.render_chart import draw_wheel

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "artifacts/mcp-recipes/examples/horary-input.example.json"
DOCS = {
    "recipe": "docs/horary-reading-recipe.md",
    "sources": "docs/research/horary-method-sources.md",
    "twin": "artifacts/report-templates/horary-astrology.md",
    "html": "artifacts/report-templates/horary-reading.html",
    "boundary": "docs/report-system.md",
}
OLD_NINE = {"rising_hands", "natal", "phase_states", "profection", "solar_return", "transits",
            "body_states", "partner_portrait", "partner_portrait_kit"}


def example():
    return dict(json.loads(EXAMPLE.read_text(encoding="utf-8")), scan_days=3)


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


def test_horary_discovery_preserves_all_nine_existing_tools():
    async def discover():
        async with Client(server.mcp) as client:
            return client.initialize_result, await client.list_tools()
    initialized, tools = asyncio.run(discover())
    assert {tool.name for tool in tools} == OLD_NINE | {"horary", "horary_kit"}
    assert "horary_kit" in initialized.instructions
    assert "horary_kit" in next(t.description for t in tools if t.name == "horary")
    projection = []
    for tool in tools:
        if tool.name in OLD_NINE:
            wire = tool.model_dump(by_alias=True, exclude_none=True)
            projection.append({k: wire[k] for k in ("name", "description", "inputSchema", "outputSchema")})
    assert digest(projection) == "0c8bba95b907c42ead93f04773692f536e79d19a289775f6bdd651d621defd91"


def test_horary_kit_delivers_exact_five_documents_and_bound_manifest():
    async def read():
        async with Client(server.mcp) as client:
            manifest = (await client.call_tool("horary_kit", {})).data
            documents = {key: (await client.call_tool("horary_kit", {"document": key})).data for key in DOCS}
            return manifest, documents
    manifest, documents = asyncio.run(read())
    assert manifest["kit_id"] == "horary" and manifest["kit_version"]
    assert manifest["manifest_sha256"] == digest({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    assert manifest["profile"]["house_system"] == "Regiomontanus"
    assert manifest["profile"]["rulership"] == "traditional"
    assert manifest["profile"]["id"] == "selected-classical-v1"
    assert "Regiomontanus H/h" in manifest["unavailable_layers"]
    entries = {entry["id"]: entry for entry in manifest["documents"]}
    assert len(manifest["documents"]) == 5 and set(entries) == set(DOCS)
    for key, path in DOCS.items():
        raw = (ROOT / path).read_bytes()
        doc, entry = documents[key], entries[key]
        assert doc["content"].encode("utf-8") == raw
        assert doc["byte_length"] == entry["byte_length"] == len(raw)
        assert doc["sha256"] == entry["sha256"] == hashlib.sha256(raw).hexdigest()
        assert doc["source_path"] == entry["source_path"] == path
        assert doc["required"] is True and doc["role"] and doc["mime_type"]


@pytest.mark.parametrize("document", ["../recipe", ".private/test", "C:/test.txt", "missing"])
def test_horary_kit_rejects_paths_and_unknown_ids(document):
    result = asyncio.run(call("horary_kit", {"document": document}))
    assert result.is_error and str(ROOT) not in str(result.content)


@pytest.mark.parametrize("missing", [True, False])
def test_horary_kit_missing_or_empty_document_is_bounded_error(monkeypatch, tmp_path, missing):
    for path in DOCS.values():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("synthetic document", encoding="utf-8")
    target = tmp_path / DOCS["sources"]
    target.unlink() if missing else target.write_bytes(b"")
    monkeypatch.setattr(server, "_KIT_ROOT", tmp_path)
    result = asyncio.run(call("horary_kit", {}))
    assert result.is_error and str(tmp_path) not in str(result.content)


def test_horary_mcp_returns_core_facts_svg_and_actual_kit():
    cfg = example()
    result = asyncio.run(call("horary", {"input": cfg}))
    assert not result.is_error
    payload = result.data
    direct = horary.compute_facts(cfg)
    assert payload["facts"] == json.loads(json.dumps(direct))
    assert payload["wheel_svg"] == horary.render_wheel(direct)
    assert ET.fromstring(payload["wheel_svg"]).tag == "{http://www.w3.org/2000/svg}svg"
    manifest = asyncio.run(call("horary_kit", {})).data
    assert payload["kit"] == manifest
    assert payload["provenance"]["kit_manifest_sha256"] == manifest["manifest_sha256"]
    assert payload["provenance"]["input_sha256"] == digest(cfg)
    assert payload["provenance"]["facts_sha256"] == digest(payload["facts"])
    for path, expected in payload["provenance"]["operator_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert "artifacts/renderer/render_chart.py" in payload["provenance"]["operator_sha256"]
    assert not {"prose", "interpretation", "report_html"} & payload.keys()
    assert payload["facts"]["radicality_verdict"] is None
    assert str(ROOT) not in json.dumps(payload)


@pytest.mark.parametrize("failure", ["intake", "date", "polar", "engine", "runtime"])
def test_horary_errors_never_return_facts_or_svg(monkeypatch, failure):
    cfg = copy.deepcopy(example())
    if failure == "intake":
        cfg["intake"]["status"] = "needs_clarification"
    elif failure == "date":
        del cfg["moment"]["local"]
    elif failure == "polar":
        cfg["moment"].update(local="2026-01-15T12:00:00+01:00", timezone="Europe/Oslo",
                             latitude=69.6492, longitude=18.9553)
    elif failure == "engine":
        monkeypatch.setattr(engine, "DEFAULT_ENGINE", "b1")
    else:
        def broken(*a, **k):
            raise RuntimeError(str(ROOT / ".private/synthetic-do-not-expose"))
        monkeypatch.setattr(server, "compute_horary_facts", broken, raising=False)
    result = asyncio.run(call("horary", {"input": cfg}))
    assert result.is_error and result.data is None
    assert str(ROOT) not in str(result.content) and "synthetic-do-not-expose" not in str(result.content)


def test_renderer_returns_the_same_svg_it_writes(tmp_path):
    path = tmp_path / "wheel.svg"
    planets = [{"body": "sun", "longitude": 5.0, "sign": "Aries", "degree": 5.0}]
    returned = draw_wheel(planets, [], [{"point": "asc", "longitude": 30.0}], [], path)
    assert isinstance(returned, str)
    assert returned.encode("utf-8") == path.read_bytes()
    assert draw_wheel(planets, [], [{"point": "asc", "longitude": 30.0}], []) == returned
    assert ET.fromstring(returned).tag == "{http://www.w3.org/2000/svg}svg"


def test_cli_creates_exact_artifacts_preserves_existing_bytes_and_leaves_no_false_manifest(tmp_path):
    cfg = example()
    source = tmp_path / "input.json"
    source.write_text(json.dumps(cfg), encoding="utf-8")
    output = tmp_path / ".private/synthetic-result"
    command = [sys.executable, "-B", str(ROOT / "artifacts/mcp-recipes/horary_facts.py"),
               "--input", str(source), "--out", str(output)]
    run = lambda: subprocess.run(command, cwd=tmp_path, env=dict(os.environ, SWISS_ENGINE="a"),
                                 capture_output=True, encoding="utf-8")
    first = run()
    assert first.returncode == 0, first.stdout + first.stderr
    assert {p.name for p in output.iterdir()} == {"facts.json", "wheel.svg", "manifest.json"}
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    manifest = json.loads(before["manifest.json"])
    assert manifest["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["artifacts"] == {name: hashlib.sha256(before[name]).hexdigest()
                                     for name in ("facts.json", "wheel.svg")}
    assert run().returncode != 0
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    cfg["intake"]["status"] = "needs_clarification"
    source.write_text(json.dumps(cfg), encoding="utf-8")
    failed_output = tmp_path / ".private/rejected-result"
    command[-1] = str(failed_output)
    assert run().returncode != 0
    assert not (failed_output / "manifest.json").exists()
