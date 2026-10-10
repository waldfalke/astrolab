"""The production ribbon builder composes the existing MCP collector and probe."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

import astro.engine as engine
from astro.server import mcp
from tests.conftest import require_engine_a


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "artifacts/mcp-recipes/build_day_ribbon.py"


def builder():
    assert SCRIPT.exists(), "production day-ribbon builder is not implemented"
    spec = importlib.util.spec_from_file_location("build_day_ribbon", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_wires_boundary_output_and_manifest_without_touching_core(tmp_path, monkeypatch):
    module = builder()
    calls = []

    async def fake_day(args):
        args.output.mkdir(parents=True)
        (args.output / "minute-frames.json").write_text("[]", encoding="utf-8")
        (args.output / "metadata.json").write_text("{}", encoding="utf-8")
        calls.append("day")

    def fake_probe(_frames, _metadata, output, **_kwargs):
        output.mkdir(parents=True)
        for name, raw in (("states.json", b"states"), ("events.json", b"events"),
                          ("events.csv", b"csv")):
            (output / name).write_bytes(raw)
        calls.append("ribbon")
        return {"counts": {"states": 1}, "input_paths": {}, "source_paths": {}}

    async def fake_boundary(args):
        args.output.mkdir(parents=True)
        context = {"schema_version": "city-day-boundary-context-v1", "edge_states": [{}, {}]}
        (args.output / "boundary-context.json").write_text(
            json.dumps(context) + "\n", encoding="utf-8",
        )
        (args.output / "mcp-exchanges.jsonl").write_text("{}\n", encoding="utf-8")
        calls.append("boundary")
        return context

    monkeypatch.setattr(module.collect_mcp_day_frames, "run", fake_day)
    monkeypatch.setattr(module.clock_event_state_probe, "run_probe", fake_probe)
    monkeypatch.setattr(module.collect_mcp_boundary_context, "run", fake_boundary)
    output = tmp_path / "run"

    asyncio.run(module.build(
        mcp_target=object(), mcp_label="test", engine=None, date="2026-10-05",
        lat=45.04, lon=38.98, tz=3, aspect_orb=6.0, output=output,
    ))

    assert calls == ["day", "ribbon", "boundary"]
    boundary_raw = (output / "ribbon/boundary-context.json").read_bytes()
    author = json.loads((output / "ribbon/author-manifest.json").read_text(encoding="utf-8"))
    assert author["boundary_context"] == {
        "schema_version": "city-day-boundary-context-v1",
        "sha256": hashlib.sha256(boundary_raw).hexdigest(),
    }


def test_build_composes_complete_mcp_day_and_ribbon(tmp_path, monkeypatch):
    require_engine_a()
    monkeypatch.setattr(engine, "DEFAULT_ENGINE", "a")
    output = tmp_path / "run"

    manifest = asyncio.run(builder().build(
        mcp_target=mcp,
        mcp_label="in-process:astro.server",
        engine="a",
        date="2026-10-05",
        lat=45.04,
        lon=38.98,
        tz=3,
        aspect_orb=6.0,
        output=output,
    ))

    source_meta = json.loads((output / "source/metadata.json").read_text(encoding="utf-8"))
    saved_manifest = json.loads((output / "ribbon/manifest.json").read_text(encoding="utf-8"))
    author_manifest = json.loads((output / "ribbon/author-manifest.json").read_text(encoding="utf-8"))
    boundary_raw = (output / "ribbon/boundary-context.json").read_bytes()
    boundary = json.loads(boundary_raw)
    assert source_meta["mcp"]["tool"] == "natal"
    assert source_meta["mcp"]["requests"] == 1441
    assert source_meta["mcp"]["transport"] == "in_process"
    assert source_meta["engine"] == "a"
    assert saved_manifest == manifest
    assert manifest["counts"]["states"] == 1441
    assert manifest["counts"]["intervals"] == 1440
    assert manifest["counts"]["events"] > 0
    assert manifest["input_sha256"]["frames"] == source_meta["raw_sha256"]
    assert "input_paths" not in author_manifest
    assert "source_paths" not in author_manifest
    assert author_manifest["input_sha256"] == manifest["input_sha256"]
    assert author_manifest["provenance"]["mcp"]["transport"] == "in_process"
    assert boundary["schema_version"] == "city-day-boundary-context-v1"
    assert [state["edge"] for state in boundary["edge_states"]] == ["start", "end"]
    assert author_manifest["boundary_context"] == {
        "schema_version": "city-day-boundary-context-v1",
        "sha256": hashlib.sha256(boundary_raw).hexdigest(),
    }
    assert (output / "boundary/mcp-exchanges.jsonl").exists()
    assert ".private" not in json.dumps(author_manifest)

    with pytest.raises(FileExistsError, match="output already exists"):
        asyncio.run(builder().build(
            mcp_target=mcp,
            mcp_label="in-process:astro.server",
            engine="a",
            date="2026-10-05",
            lat=45.04,
            lon=38.98,
            tz=3,
            aspect_orb=6.0,
            output=output,
        ))


def test_boundary_context_does_not_change_day_core(tmp_path, monkeypatch):
    require_engine_a()
    monkeypatch.setattr(engine, "DEFAULT_ENGINE", "a")
    with_context = tmp_path / "with-context"
    old_ribbon = tmp_path / "old-ribbon"
    common = {
        "mcp_target": mcp,
        "mcp_label": "in-process:astro.server",
        "engine": "a",
        "date": "2026-10-05",
        "lat": 45.04,
        "lon": 38.98,
        "tz": 3,
        "aspect_orb": 6.0,
    }

    asyncio.run(builder().build(**common, output=with_context))
    asyncio.run(builder().build(
        **common, output=old_ribbon, include_boundary_context=False,
    ))

    for name in ("states.json", "events.json", "events.csv"):
        assert (with_context / "ribbon" / name).read_bytes() == (old_ribbon / "ribbon" / name).read_bytes()
    assert not (old_ribbon / "ribbon/boundary-context.json").exists()
    old_manifest = json.loads((old_ribbon / "ribbon/author-manifest.json").read_text(encoding="utf-8"))
    assert "boundary_context" not in old_manifest

