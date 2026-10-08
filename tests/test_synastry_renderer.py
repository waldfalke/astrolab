"""Synthetic, private bundle contracts for two reciprocal synastry views."""
import csv
import hashlib
import importlib.util
import io
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECIPE_SCRIPT = ROOT / "artifacts/mcp-recipes/synastry_local.py"
SPEC = importlib.util.spec_from_file_location("synastry_local_for_visuals", RECIPE_SCRIPT)
recipe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recipe)
RENDER_SCRIPT = ROOT / "artifacts/renderer/render_synastry.py"
if RENDER_SCRIPT.exists():
    RENDER_SPEC = importlib.util.spec_from_file_location("render_synastry", RENDER_SCRIPT)
    visual = importlib.util.module_from_spec(RENDER_SPEC)
    RENDER_SPEC.loader.exec_module(visual)
else:
    visual = None
SVG = "{http://www.w3.org/2000/svg}"
BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")


def _natal(offset, moment, lat, lon):
    positions = {body: float((index * 34 + offset) % 360)
                 for index, body in enumerate(BODIES)}
    cusps = [float((350 + offset + index * 30) % 360) for index in range(12)]
    return {
        "positions": positions,
        "houses": {"cusps": cusps, "angles": {"asc": cusps[0], "ic": cusps[3],
                                                "dsc": cusps[6], "mc": cusps[9]}},
        "aspects": [], "moment_utc": moment, "location": {"lat": lat, "lon": lon},
    }


@pytest.fixture
def bundle(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps({"participants": {
        "A": {"id": "one", "datetime_utc": "2000-01-01T12:00:00Z",
              "latitude": 0, "longitude": 0},
        "B": {"id": "two", "datetime_utc": "2001-01-01T12:00:00Z",
              "latitude": 10, "longitude": 20},
    }}), encoding="utf-8")
    target = private / "calculation-final"
    one = _natal(0, "2000-01-01T12:00:00Z", 0, 0)
    two = _natal(7, "2001-01-01T12:00:00Z", 10, 20)
    one["positions"]["sun"] = 0.0
    two["positions"]["sun"] = 1.0
    recipe.write_bundle(source, target, {"one": one, "two": two},
                        {"one": {body: 0.1 for body in BODIES},
                         "two": {body: -0.1 for body in BODIES}},
                        provenance={"engine": "synthetic-test"}, private_root=private)
    return private, target


def test_two_mutual_wheels_grid_and_manifest_are_complete(bundle):
    assert visual is not None, "synastry renderer is missing"
    private, source = bundle
    output = private / "visuals"
    files = visual.render_synastry(source, output, "A & <one>", "B <two>",
                                   private_root=private)
    assert {p.name for p in files} == {"01_A_inner_B_outer.svg",
                                           "02_B_inner_A_outer.svg",
                                           "03_cross_aspect_grid.svg",
                                           "04_visual_manifest.json"}
    manifest = json.loads((output / "04_visual_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_manifest_sha256"] == hashlib.sha256(
        (source / "manifest.json").read_bytes()).hexdigest()
    for name in ("natals/A.json", "natals/B.json", "cross_aspects.csv"):
        assert manifest["inputs"][name] == hashlib.sha256((source / name).read_bytes()).hexdigest()
    assert manifest["renderer_sha256"]["render_chart.py"] == hashlib.sha256(
        (ROOT / "artifacts/renderer/render_chart.py").read_bytes()).hexdigest()
    for name in ("01_A_inner_B_outer.svg", "02_B_inner_A_outer.svg",
                 "03_cross_aspect_grid.svg"):
        assert manifest["outputs"][name] == hashlib.sha256((output / name).read_bytes()).hexdigest()
        ET.parse(output / name)
    assert str(private) not in json.dumps(manifest)

    with (source / "cross_aspects.csv").open(encoding="utf-8", newline="") as stream:
        contacts = list(csv.DictReader(stream))
    for name, owner in (("01_A_inner_B_outer.svg", "A & <one>"),
                        ("02_B_inner_A_outer.svg", "B <two>")):
        root = ET.parse(output / name).getroot()
        chords = [n for n in root.iter(SVG + "line")
                  if n.attrib.get("data-contact") == "cross-aspect"]
        assert len(chords) == len(contacts)
        assert owner in " ".join(n.text or "" for n in root.iter(SVG + "text"))
        inner_slot, outer_slot = ("A", "B") if name.startswith("01_") else ("B", "A")
        inner = json.loads((source / f"natals/{inner_slot}.json").read_text(encoding="utf-8"))
        outer = json.loads((source / f"natals/{outer_slot}.json").read_text(encoding="utf-8"))
        asc = inner["houses"]["angles"]["asc"]

        def xy(radius, longitude):
            angle = math.radians((180 + longitude - asc) % 360)
            return (750 + radius * math.cos(angle), 750 - radius * math.sin(angle))

        sun_chords = [n for n in chords if n.attrib.get("data-inner-body") == "sun" and
                      n.attrib.get("data-outer-body") == "sun" and
                      n.attrib.get("data-inner-kind") == "planet" and
                      n.attrib.get("data-outer-kind") == "planet"]
        assert len(sun_chords) == 1
        chord = sun_chords[0]
        assert (float(chord.attrib["x1"]), float(chord.attrib["y1"])) == pytest.approx(
            xy(450, outer["positions"]["sun"]), abs=.01)
        assert (float(chord.attrib["x2"]), float(chord.attrib["y2"])) == pytest.approx(
            xy(405, inner["positions"]["sun"]), abs=.01)
        children = list(root)
        badges = [(children[index - 1], node) for index, node in enumerate(children)
                  if node.tag == SVG + "text" and node.attrib.get("class") == "plabel" and
                  index > 0 and children[index - 1].attrib.get("class") == "txtbg"]
        for rect, node in badges:
            if node.attrib.get("data-label-ring"):
                x, y = float(rect.attrib["x"]), float(rect.attrib["y"])
                assert 0 <= x and x + float(rect.attrib["width"]) <= 1500
                assert 0 <= y and y + float(rect.attrib["height"]) <= 1500

        def overlaps(first, second):
            ax, ay = float(first.attrib["x"]), float(first.attrib["y"])
            bx, by = float(second.attrib["x"]), float(second.attrib["y"])
            return (ax < bx + float(second.attrib["width"]) and
                    bx < ax + float(first.attrib["width"]) and
                    ay < by + float(second.attrib["height"]) and
                    by < ay + float(first.attrib["height"]))

        houses = [rect for rect, node in badges if not node.attrib.get("data-label-ring")]
        outer_angles = [rect for rect, node in badges if node.attrib.get("data-label-ring") == "outer"
                        and node.attrib.get("data-label-kind") == "angle"]
        assert len(outer_angles) == 4
        for house in houses:
            for angle in outer_angles:
                assert not overlaps(house, angle), (inner_slot, house.attrib, angle.attrib)
    grid = ET.parse(output / "03_cross_aspect_grid.svg").getroot()
    cells = [n for n in grid.iter() if n.attrib.get("data-contact-key")]
    assert len(cells) == len(contacts)
    glyphs = {"conjunction": "☌", "sextile": "⚹", "square": "□",
              "trine": "△", "opposition": "☍"}
    assert [cell.text for cell in cells] == [glyphs[row["aspect"]] for row in contacts]
    assert [cell.attrib["data-aspect"] for cell in cells] == [row["aspect"] for row in contacts]
    names = list(BODIES) + ["asc", "mc", "ic", "dsc"]
    for cell, contact in zip(cells, contacts):
        a_point, b_point = ((contact["from_point"], contact["to_point"])
                            if contact["from_owner"] == "one" else
                            (contact["to_point"], contact["from_point"]))
        assert float(cell.attrib["x"]) == pytest.approx(225 + names.index(b_point) * 112 + 56)
        assert float(cell.attrib["y"]) == pytest.approx(215 + names.index(a_point) * 112 + 46)
    grid_svg = (output / "03_cross_aspect_grid.svg").read_text(encoding="utf-8")
    assert ".aspect-glyph{font-size:36px" in grid_svg
    assert ".orb{font-size:22px" in grid_svg
    assert ".axis-symbol{font-size:30px" in grid_svg
    assert ".legend{font-size:26px" in grid_svg
    assert "Segoe UI Symbol" in grid_svg
    text = " ".join(n.text or "" for n in grid.iter(SVG + "text"))
    assert "A & <one>" in text and "B <two>" in text
    assert "орб в градусах" in text
    for name in ("соединение", "секстиль", "квадрат", "трин", "оппозиция"):
        assert name in text


@pytest.mark.parametrize("damage", ["missing", "changed", "missing_contact",
                                    "missing_adapter", "bad_endpoint"])
def test_incomplete_or_mismatched_bundle_rejected_before_output(bundle, damage):
    assert visual is not None, "synastry renderer is missing"
    private, source = bundle
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if damage == "missing":
        (source / "natals/B.json").unlink()
    elif damage == "changed":
        path = source / "natals/A.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif damage == "missing_contact":
        manifest["files"].pop("cross_aspects.csv")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif damage == "missing_adapter":
        manifest["files"].pop("adapters/charts/B/outputs/chart_points.csv")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    else:
        path = source / "cross_aspects.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        rows[0]["from_point"] = "unknown"
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_text(buffer.getvalue(), encoding="utf-8")
        manifest["files"]["cross_aspects.csv"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = private / "visuals"
    with pytest.raises((ValueError, FileNotFoundError)):
        visual.render_synastry(source, output, "A", "B", private_root=private)
    assert not output.exists()


def test_output_must_be_new_and_inside_private_root(bundle, tmp_path):
    assert visual is not None, "synastry renderer is missing"
    private, source = bundle
    with pytest.raises(ValueError, match="private"):
        visual.render_synastry(source, tmp_path / "public", "A", "B", private_root=private)
    output = private / "visuals"
    output.mkdir()
    with pytest.raises(FileExistsError):
        visual.render_synastry(source, output, "A", "B", private_root=private)
