"""Synthetic contracts for the private, exact-time local synastry recipe."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "artifacts/mcp-recipes/synastry_local.py"
SPEC = importlib.util.spec_from_file_location("synastry_local", SCRIPT)
recipe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recipe)

BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")


def synthetic_natal(offset=0):
    positions = {body: float((i * 34 + offset) % 360) for i, body in enumerate(BODIES)}
    cusps = [float((350 + offset + i * 30) % 360) for i in range(12)]
    angles = {"asc": cusps[0], "mc": cusps[9], "dsc": cusps[6], "ic": cusps[3]}
    return {"positions": positions, "houses": {"cusps": cusps, "angles": angles}}


def example_input():
    return {"participants": {
        "A": {"id": "one", "datetime_utc": "2000-01-01T12:00:00Z",
              "latitude": 0, "longitude": 0},
        "B": {"id": "two", "datetime_utc": "2001-01-01T12:00:00Z",
              "latitude": 10, "longitude": 20},
    }}


def test_swap_preserves_contact_keys_and_reverses_overlay_directions():
    one, two = synthetic_natal(), synthetic_natal(7)
    ab = recipe.cross_contacts({"one": one, "two": two})
    ba = recipe.cross_contacts({"two": two, "one": one})
    assert {r["key"] for r in ab} == {r["key"] for r in ba}
    assert len(ab) == len({r["key"] for r in ab})
    overlays = recipe.directed_overlays({"one": one, "two": two})
    swapped = recipe.directed_overlays({"two": two, "one": one})
    assert overlays == swapped
    assert {r["from_owner"] for r in overlays} == {"one", "two"}
    assert len(overlays) == 20


def test_cross_aspect_wrap_and_inclusive_orb_boundary():
    one, two = synthetic_natal(), synthetic_natal()
    one["positions"]["sun"] = 359.0
    two["positions"]["sun"] = 1.0
    hits = recipe.cross_contacts({"one": one, "two": two})
    sun = next(r for r in hits if r["from_owner"] == "one" and
               r["from_point"] == "sun" and r["to_owner"] == "two" and
               r["to_point"] == "sun")
    assert sun["aspect"] == "conjunction"
    assert sun["separation"] == pytest.approx(2)
    assert sun["orb"] == pytest.approx(2)
    two["positions"]["sun"] = 5.0  # 359 -> 5 = exactly 6 degrees
    assert any(r["from_point"] == r["to_point"] == "sun" and
               r["from_kind"] == r["to_kind"] == "planet"
               for r in recipe.cross_contacts({"one": one, "two": two}))
    two["positions"]["sun"] = 5.0001
    assert not any(r["from_point"] == r["to_point"] == "sun" and
                   r["from_kind"] == r["to_kind"] == "planet"
                   for r in recipe.cross_contacts({"one": one, "two": two}))


def test_angle_contacts_use_three_degree_orb():
    one, two = synthetic_natal(), synthetic_natal()
    one["positions"]["sun"] = 10.0
    two["houses"]["angles"]["asc"] = 13.0
    two["houses"]["angles"]["dsc"] = 193.0
    hits = recipe.cross_contacts({"one": one, "two": two})
    assert any(r["from_point"] == "sun" and r["to_point"] == "asc" and
               r["orb"] == pytest.approx(3) for r in hits)
    two["houses"]["angles"]["asc"] = 13.0001
    assert not any(r["from_point"] == "sun" and r["to_point"] == "asc"
                   for r in recipe.cross_contacts({"one": one, "two": two}))


def test_house_wrap_and_directed_overlays():
    one, two = synthetic_natal(), synthetic_natal(20)
    one["positions"]["sun"] = 5.0
    two["positions"]["sun"] = 355.0
    rows = recipe.directed_overlays({"one": one, "two": two})
    assert next(r["house"] for r in rows if r["from_owner"] == "one" and
                r["body"] == "sun") == 12  # other ASC is 10, preceding house wraps
    assert next(r["house"] for r in rows if r["from_owner"] == "two" and
                r["body"] == "sun") == 1   # own direction uses other ASC 350


@pytest.mark.parametrize("damage", ["missing", "nan", "infinite", "extra_angle_nan",
                                    "duplicate_cusp", "short_cusps"])
def test_natal_incomplete_positions_or_house_frame_rejected(damage):
    natal = synthetic_natal()
    if damage == "missing":
        del natal["positions"]["pluto"]
    elif damage == "nan":
        natal["positions"]["sun"] = math.nan
    elif damage == "infinite":
        natal["houses"]["angles"]["asc"] = math.inf
    elif damage == "extra_angle_nan":
        natal["houses"]["angles"]["vertex"] = math.nan
    elif damage == "duplicate_cusp":
        natal["houses"]["cusps"][3] = natal["houses"]["cusps"][2]
    else:
        natal["houses"]["cusps"].pop()
    with pytest.raises(ValueError):
        recipe.validate_natal(natal)


@pytest.mark.parametrize("damage", ["naive", "offset", "missing_id", "duplicate_id", "unsafe_id",
                                    "latitude", "longitude", "unknown_time", "nan"])
def test_input_requires_two_distinct_exact_utc_participants(damage):
    data = example_input()
    a, b = data["participants"]["A"], data["participants"]["B"]
    if damage == "naive":
        a["datetime_utc"] = "2000-01-01T12:00:00"
    elif damage == "offset":
        a["datetime_utc"] = "2000-01-01T12:00:00+03:00"
    elif damage == "missing_id":
        del a["id"]
    elif damage == "duplicate_id":
        b["id"] = a["id"]
    elif damage == "unsafe_id":
        a["id"] = "one|two"
    elif damage == "latitude":
        a["latitude"] = 91
    elif damage == "longitude":
        a["longitude"] = -181
    elif damage == "unknown_time":
        a["datetime_utc"] = "2000-01-01"
    else:
        a["latitude"] = math.nan
    with pytest.raises(ValueError):
        recipe.validate_input(data)


def test_private_path_guard_and_output_reuse(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps(example_input()), encoding="utf-8")
    output = private / "bundle"
    recipe.validate_paths(source, output, private_root=private)
    with pytest.raises(ValueError):
        recipe.validate_paths(tmp_path / "public.json", output, private_root=private)
    with pytest.raises(ValueError):
        recipe.validate_paths(source, tmp_path / "public-output", private_root=private)
    output.mkdir()
    with pytest.raises(FileExistsError):
        recipe.validate_paths(source, output, private_root=private)


def test_bundle_written_with_hashes_and_phase_adapter_from_synthetic_natals(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps(example_input()), encoding="utf-8")
    target = private / "bundle"
    natal_a, natal_b = synthetic_natal(), synthetic_natal(7)
    natal_a.update({"aspects": [], "dignities": {}, "sect": {}, "placements": {},
                    "moment_utc": "2000-01-01T12:00:00Z", "location": {"lat": 0, "lon": 0}})
    natal_b.update({"aspects": [], "dignities": {}, "sect": {}, "placements": {},
                    "moment_utc": "2001-01-01T12:00:00Z", "location": {"lat": 10, "lon": 20}})
    natal_a["phases"] = {"states": {"sun": {"Z": "stale"}}}
    recipe.write_bundle(source, target, {"one": natal_a, "two": natal_b},
                        {"one": {body: 0.1 for body in BODIES},
                         "two": {body: -0.1 for body in BODIES}},
                        provenance={"engine": "synthetic-test"}, private_root=private)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["files"]["natals/A.json"] == hashlib.sha256(
        (target / "natals/A.json").read_bytes()).hexdigest()
    natal_snapshot = json.loads((target / "natals/A.json").read_text(encoding="utf-8"))
    assert natal_snapshot["motion"]["status"] == "computed"
    assert natal_snapshot["motion"]["speed_longitude_deg_day"]["sun"] == pytest.approx(0.1)
    assert natal_snapshot["phases"]["states"]["sun"]["Z"] == "9"
    assert natal_snapshot["phases"]["moment_utc"] == "2000-01-01T12:00:00Z"
    natal_b_snapshot = json.loads((target / "natals/B.json").read_text(encoding="utf-8"))
    assert natal_b_snapshot["phases"]["states"]["sun"]["Z"] == "9"
    assert natal_b_snapshot["phases"]["input_sha256"] != natal_snapshot["phases"]["input_sha256"]
    with (target / "adapters/charts/A/outputs/natal_longitudes.csv").open(
            encoding="utf-8", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 10
    with (target / "adapters/charts/B/outputs/houses_placidus.csv").open(
            encoding="utf-8", newline="") as stream:
        assert [int(r["house"]) for r in csv.DictReader(stream)] == list(range(1, 13))
    assert manifest["files"]["cross_aspects.csv"]
    assert manifest["files"]["overlays.csv"]


def test_bundle_rejects_snapshot_mismatched_to_input_before_creating_output(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps(example_input()), encoding="utf-8")
    wrong = synthetic_natal()
    wrong["moment_utc"] = "2005-01-01T12:00:00Z"
    other = synthetic_natal(7)
    other["moment_utc"] = "2001-01-01T12:00:00Z"
    target = private / "bundle"
    with pytest.raises(ValueError):
        recipe.write_bundle(source, target, {"one": wrong, "two": other}, None,
                            provenance={}, private_root=private)
    assert not target.exists()


def test_bundle_rejects_partial_motion_before_creating_output(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps(example_input()), encoding="utf-8")
    one, two = synthetic_natal(), synthetic_natal(7)
    one.update({"moment_utc": "2000-01-01T12:00:00Z", "location": {"lat": 0, "lon": 0}})
    two.update({"moment_utc": "2001-01-01T12:00:00Z", "location": {"lat": 10, "lon": 20}})
    target = private / "bundle"
    with pytest.raises(ValueError):
        recipe.write_bundle(source, target, {"one": one, "two": two},
                            {"one": {body: 0.1 for body in BODIES}},
                            provenance={}, private_root=private)
    assert not target.exists()


def test_main_uses_local_engine_and_hashes_actual_ephemeris_files(tmp_path, monkeypatch):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps(example_input()), encoding="utf-8")
    target = private / "bundle"
    monkeypatch.setattr(recipe, "PRIVATE_ROOT", private)
    assert recipe.main(["--input", str(source), "--output", str(target)]) == 0
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["motion_status"] == "computed"
    assert manifest["provenance"]["pyswisseph_package"]
    ephemeris = manifest["provenance"]["ephemeris_files_sha256"]
    assert len(ephemeris) == 4
    assert all(Path(path).is_file() and hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
               for path, digest in ephemeris.items())
    assert manifest["files"]["natals/A.json"]
    assert manifest["files"]["natals/B.json"]
    assert manifest["provenance"]["code_sha256"]["astro/phases.py"]
