"""Analytic trajectories test geometry; these are not simulated Swiss output."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "artifacts/mcp-recipes/clock_event_state_probe.py"
BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")


def probe():
    assert SCRIPT.exists(), "event-state transformer is not implemented"
    spec = importlib.util.spec_from_file_location("clock_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("ends, fraction, direction", [
    ((0, 10, 5, 7), 0.625, "increasing"),
    ((359, 1, 0, 0), 0.5, "increasing"),
    ((1, 359, 0, 0), 0.5, "decreasing"),
    ((10, 20, 70, 75), 0, "increasing"),
])
def test_relative_contact_uses_both_moving_endpoints(ends, fraction, direction):
    target = -60 if ends[2] == 70 else 0
    contacts = probe().contacts_in_step(*ends, targets=[target])
    assert len(contacts) == 1
    assert contacts[0]["fraction"] == pytest.approx(fraction)
    assert contacts[0]["direction"] == direction


def test_identical_coincidence_has_no_isolated_contact():
    assert probe().contacts_in_step(0, 1, 0, 1, targets=[0]) == []


def frame(minute, asc=350, **positions):
    cusps = [(asc+x) % 360 for x in (0, 20, 50, 80, 110, 140, 170, 200, 230, 260, 290, 320)]
    moment = datetime(2026, 10, 4, 21, tzinfo=timezone.utc)+timedelta(minutes=minute)
    return {"local_minute": minute, "utc": moment.isoformat(),
            "positions": {**dict(zip(BODIES, (2, 12, 150, 180, 29, 83, 113, 143, 203, 263))), **positions},
            "cusps": cusps, "angles": {"asc": asc, "mc": cusps[9], "vertex": 254}}


def test_states_keep_real_house_arcs_full_phases_and_separate_dignity():
    rows = probe().build_states([frame(0), frame(1, sun=1)], aspect_orb=6)
    row = rows[0]
    assert row["raw_frame"] == frame(0)
    assert row["houses"][0] == {"house": 1, "start_deg": 350, "end_deg": 10, "width_deg": 20}
    assert row["houses"][1]["width_deg"] == 30
    assert row["bodies"]["sun"]["house_fraction"] == pytest.approx(0.6)
    assert row["bodies"]["sun"]["H_house"] == 1
    assert row["phase_states"]["states"]["mercury"]["Z"] == "4/1"
    assert row["phase_states"]["states"]["venus"]["Z"] == "6/1"
    assert row["bodies"]["sun"]["traditional_dignity"]["dignity"] == "exaltation"
    assert row["bodies"]["uranus"]["traditional_dignity"] == {"availability": "unavailable", "reason": "outside_seven_classical_bodies"}
    speed = row["bodies"]["sun"]["secant_motion"]
    assert speed["deg_per_day"] == pytest.approx(-1440)
    assert speed["direction"] == "retrograde"
    assert speed["interval_utc"] == [rows[0]["utc"], rows[1]["utc"]]
    assert row["bodies"]["moon"]["secant_motion"]["direction"] == "station_or_inconclusive"
    assert all(hit["orb_limit_deg"] == 6 for hit in row["interplanetary_aspects"] + row["asc_aspects"])


def test_event_boundary_dedup_terminal_exclusion_and_state_links():
    frames = [frame(0, 359, sun=0), frame(1, 0, sun=0), frame(2, 1, sun=0)]
    events = probe().build_events(frames)
    contacts = [e for e in events if e["kind"] == "asc_body_aspect" and e["participant2"] == "sun" and e["aspect"] == "conjunction"]
    assert len(contacts) == 1
    hit = contacts[0]
    assert hit["linear_estimate_utc"] == "2026-10-04T21:01:00Z"
    assert hit["bracket_utc"] == ["2026-10-04T21:00:00Z", "2026-10-04T21:01:00Z"]
    assert (hit["state_before_index"], hit["state_after_index"]) == (0, 1)
    assert not any(e["linear_estimate_utc"] == "2026-10-04T21:02:00Z" for e in events)
    assert any(e["kind"] == "asc_sign_ingress" and e["sign_before"] == "Pisces" and e["sign_after"] == "Aries" for e in events)
    assert any(e["kind"] == "body_cusp_crossing" and e["participant2"] == "cusp_1" for e in events)
    assert not any(e["participant1"] == "ASC" and e["participant2"] == "cusp_1" for e in events)


def test_interplanetary_relative_contact_and_mc_are_in_event_coverage():
    frames = [frame(0, sun=0, moon=5), frame(1, sun=10, moon=7)]
    events = probe().build_events(frames)
    hit = next(e for e in events if e["kind"] == "interplanetary_aspect" and set((e["participant1"], e["participant2"])) == {"sun", "moon"} and e["aspect"] == "conjunction")
    assert hit["fraction"] == pytest.approx(.625)
    assert hit["side_before_deg"] * hit["side_after_deg"] < 0
    mcframes = [frame(0, 100, sun=1), frame(1, 102, sun=1)]
    assert any(e["kind"] == "mc_body_conjunction" and e["participant2"] == "sun" for e in probe().build_events(mcframes))


def test_event_sort_compares_instants_not_variable_precision_iso_strings():
    events = probe().build_events([frame(0, 0, sun=0, moon=0.005),
                                  frame(1, 0.6, sun=0, moon=0.005)])
    moments = [datetime.fromisoformat(e["linear_estimate_utc"].replace("Z", "+00:00")) for e in events]
    assert moments == sorted(moments)
    first = next(e for e in events if e["kind"] == "asc_body_aspect" and e["participant2"] == "sun")
    assert first["state_before_relation"] == "at_estimate"
    assert first["bracket_start_index"] == 0
    assert first["side_before_deg"] == 0


def write_day(tmp_path, mutation=None):
    frames = [frame(i) for i in range(1441)]
    if mutation:
        mutation(frames)
    raw = json.dumps(frames).encode("utf-8")
    path = tmp_path / "frames.json"
    path.write_bytes(raw)
    metadata = {"date": "2026-10-05", "latitude": 45.04, "longitude": 38.98,
                "timezone": "UTC+03:00", "samples": len(frames),
                "interval_utc": ["2026-10-04T21:00:00+00:00", "2026-10-05T21:00:00+00:00"],
                "raw_sha256": hashlib.sha256(raw).hexdigest()}
    meta = tmp_path / "metadata.json"
    meta.write_text(json.dumps(metadata), encoding="utf-8")
    return path, meta


@pytest.mark.parametrize("mutation, message", [
    (lambda f: f[1]["cusps"].__setitem__(1, f[1]["cusps"][0]), "cusps"),
    (lambda f: f[1].__setitem__("utc", "2026-10-04T21:01:00"), "UTC"),
    (lambda f: f[1].__setitem__("utc", f[2]["utc"]), "step"),
    (lambda f: f[1]["positions"].__setitem__("sun", float("nan")), "finite"),
    (lambda f: f[1]["positions"].pop("moon"), "ten bodies"),
])
def test_invalid_day_fails_before_output_creation(tmp_path, mutation, message):
    paths = write_day(tmp_path, mutation)
    out = tmp_path / "output"
    with pytest.raises(ValueError, match=message):
        probe().run_probe(*paths, out, aspect_orb=6, house_system="placidus")
    assert not out.exists()


def test_broken_hash_and_nonplacidus_fail_before_output(tmp_path):
    paths = write_day(tmp_path)
    paths[0].write_bytes(paths[0].read_bytes()+b" ")
    out = tmp_path / "output"
    with pytest.raises(ValueError, match="SHA-256"):
        probe().run_probe(*paths, out, aspect_orb=6, house_system="placidus")
    assert not out.exists()
    with pytest.raises(ValueError, match="Placidus"):
        probe().run_probe(*paths, out, aspect_orb=6, house_system="whole_sign")


def test_existing_output_is_never_overwritten(tmp_path):
    paths = write_day(tmp_path)
    out = tmp_path / "output"
    out.mkdir()
    sentinel = out / "unchanged"
    sentinel.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        probe().run_probe(*paths, out, aspect_orb=6, house_system="placidus")
    assert sentinel.read_bytes() == b"original"


def test_cli_from_another_cwd_writes_reproducible_package(tmp_path):
    paths = write_day(tmp_path)
    outputs = [tmp_path / "first", tmp_path / "second"]
    for out in outputs:
        result = subprocess.run([sys.executable, str(SCRIPT), "--frames", str(paths[0]),
                                 "--metadata", str(paths[1]), "--output", str(out),
                                 "--aspect-orb", "6", "--house-system", "placidus"],
                                cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stdout + result.stderr
    for name in ("states.json", "events.json", "events.csv", "manifest.json", "BRIEF.md"):
        assert (outputs[0]/name).read_bytes() == (outputs[1]/name).read_bytes()
    manifest = json.loads((outputs[0]/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["method_version"] == "clock-event-state-v2-draft1"
    assert manifest["status"] == "experimental"
    assert manifest["counts"]["states"] == 1441
    assert manifest["counts"]["intervals"] == 1440
    assert set(manifest["source_sha256"]) >= {"transformer", "phases", "dignities", "aspects"}
    brief = (outputs[0]/"BRIEF.md").read_text(encoding="utf-8")
    assert "phase-analysis-reference.md" in brief
    assert "semantic-base.md" in brief
    assert "ceil" in brief and "floor" in brief
    assert "faster-to-slower" in brief


@pytest.mark.parametrize("mutation, message", [
    (lambda f: f[-1].__setitem__("utc", "2026-10-05T20:59:00Z"), "step"),
    (lambda f: f[1]["cusps"].__setitem__(2, f[1]["cusps"][3]+1), "ordered"),
    (lambda f: f[1]["angles"].pop("asc"), "ASC"),
])
def test_more_invalid_geometry_and_terminal_interval_inputs(tmp_path, mutation, message):
    paths = write_day(tmp_path, mutation)
    with pytest.raises(ValueError, match=message):
        probe().run_probe(*paths, tmp_path/"output", aspect_orb=6, house_system="placidus")
    assert not (tmp_path/"output").exists()

