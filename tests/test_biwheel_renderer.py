"""Synthetic geometry and ownership contracts for the shared wheel renderer."""
import importlib.util
import csv
import hashlib
import json
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "artifacts/renderer/render_chart.py"
SPEC = importlib.util.spec_from_file_location("render_chart", SCRIPT)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)
SVG = "{http://www.w3.org/2000/svg}"


def _wheel(tmp_path, *, inner_lon=0.0, outer_lon=1.0, asc=37.0, contacts=(),
           outer_points=(), inner_label="A & <one>", outer_label="B <two>"):
    path = tmp_path / "wheel.svg"
    renderer.draw_wheel(
        [{"body": "sun", "longitude": inner_lon, "sign": "Aries", "degree": 0,
          "motion": "retrograde"}],
        [{"house": i, "longitude": (asc + (i - 1) * 30) % 360} for i in range(1, 13)],
        [{"point": "asc", "longitude": asc}, {"point": "mc", "longitude": (asc + 270) % 360}],
        [], path,
        outer_planets=[{"body": "sun", "longitude": outer_lon, "sign": "Aries",
                        "degree": outer_lon, "motion": "retrograde"}],
        outer_points=list(outer_points), outer_aspects=list(contacts),
        inner_label=inner_label, outer_label=outer_label, cross_only=True,
    )
    return ET.parse(path).getroot()


def _markers(root, ring, body):
    return [element for element in root.iter()
            if element.attrib.get("data-ring") == ring and element.attrib.get("data-body") == body]


def test_zero_longitude_exact_markers_and_rotated_asc(tmp_path):
    root = _wheel(tmp_path)
    inner, outer = _markers(root, "inner", "sun"), _markers(root, "outer", "sun")
    assert len(inner) == len(outer) == 1
    assert (float(inner[0].attrib["cx"]), float(inner[0].attrib["cy"])) == pytest.approx(
        renderer.lon_to_xy(750, 405, 0, asc_lon=37), abs=0.01)
    assert (float(outer[0].attrib["cx"]), float(outer[0].attrib["cy"])) == pytest.approx(
        renderer.lon_to_xy(750, 450, 1, asc_lon=37), abs=0.01)
    text = " ".join(element.text or "" for element in root.iter(SVG + "text"))
    assert "A & <one>" in text and "B <two>" in text
    assert " R" in text


def test_same_named_bodies_and_angular_endpoints_keep_owner_and_every_chord(tmp_path):
    contacts = [
        {"inner_body": "sun", "inner_kind": "planet", "outer_body": "sun",
         "outer_kind": "planet", "aspect": "conjunction", "orb": 1},
        {"inner_body": "asc", "inner_kind": "angle", "outer_body": "sun",
         "outer_kind": "planet", "aspect": "square", "orb": 0.5},
        {"inner_body": "sun", "inner_kind": "planet", "outer_body": "mc",
         "outer_kind": "angle", "aspect": "trine", "orb": 0.2},
        {"inner_body": "asc", "inner_kind": "angle", "outer_body": "mc",
         "outer_kind": "angle", "aspect": "opposition", "orb": 0.1},
    ]
    root = _wheel(tmp_path, contacts=contacts,
                  outer_points=[{"point": "mc", "longitude": 181.0}])
    chords = [node for node in root.iter(SVG + "line")
              if node.attrib.get("data-contact") == "cross-aspect"]
    assert len(chords) == len(contacts)
    assert {(n.attrib["data-inner-kind"], n.attrib["data-outer-kind"])
            for n in chords} == {("planet", "planet"), ("angle", "planet"),
                                ("planet", "angle"), ("angle", "angle")}
    assert len(_markers(root, "outer", "mc")) == 1
    assert len(_markers(root, "inner", "asc")) == 1


def test_wrap_cluster_preserves_true_longitudes_and_separates_labels(tmp_path):
    path = tmp_path / "crowded.svg"
    outer = [{"body": body, "longitude": lon, "sign": "Pisces", "degree": lon % 30}
             for body, lon in (("sun", 359), ("moon", 0), ("mercury", 1))]
    renderer.draw_wheel([], [], [{"point": "asc", "longitude": 70}], [], path,
                        outer_planets=outer, inner_label="A", outer_label="B")
    root = ET.parse(path).getroot()
    markers = [node for node in root.iter(SVG + "circle")
               if node.attrib.get("data-ring") == "outer"]
    assert len(markers) == 3
    assert all(float(node.attrib["r"]) <= 3.5 for node in markers)
    for node in markers:
        assert math.hypot(float(node.attrib["cx"]) - 750,
                          float(node.attrib["cy"]) - 750) == pytest.approx(450, abs=.01)
    badges = [node for node in root.iter(SVG + "text")
              if node.attrib.get("data-label-ring") == "outer"]
    assert len(badges) == 3
    assert len({(n.attrib["x"], n.attrib["y"]) for n in badges}) == 3


def test_unresolved_cross_endpoint_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="endpoint"):
        _wheel(tmp_path, contacts=[{"inner_body": "unknown", "outer_body": "sun",
                                    "aspect": "square", "orb": 1}])


@pytest.mark.parametrize("contact", [
    {"inner_body": "sun", "outer_body": "sun", "inner_kind": "wrong",
     "aspect": "square", "orb": 1},
    {"inner_body": "sun", "outer_body": "sun", "aspect": "unknown", "orb": 1},
    {"inner_body": "sun", "outer_body": "sun", "aspect": "square", "orb": "bad"},
])
def test_invalid_cross_contact_fails_closed(tmp_path, contact):
    with pytest.raises(ValueError):
        _wheel(tmp_path, contacts=[contact])


@pytest.mark.parametrize("count", [7, 10])
def test_dense_top_badges_stay_inside_canvas_for_both_owners(tmp_path, count):
    path = tmp_path / "dense.svg"
    bodies = renderer.PLANET_ORDER[:count]
    inner = [{"body": body, "longitude": float(index), "sign": "Aries"}
             for index, body in enumerate(bodies)]
    outer = [{"body": body, "longitude": float(index), "sign": "Aries"}
             for index, body in enumerate(bodies)]
    renderer.draw_wheel(inner, [], [{"point": "asc", "longitude": 90}], [], path,
                        outer_planets=outer, inner_label="A", outer_label="B")
    root = ET.parse(path).getroot()
    elements = list(root)
    badges = [(elements[index - 1], element) for index, element in enumerate(elements)
              if element.attrib.get("data-label-ring") in {"inner", "outer"}]
    assert len(badges) == count * 2
    for rect, label in badges:
        assert rect.attrib.get("class") == "txtbg"
        x, y = float(rect.attrib["x"]), float(rect.attrib["y"])
        w, h = float(rect.attrib["width"]), float(rect.attrib["height"])
        assert 0 <= x and x + w <= 1500
        assert 0 <= y and y + h <= 1500
        assert label.text.startswith("В:" if label.attrib["data-label-ring"] == "inner" else "Н:")
    text = " ".join(element.text or "" for element in root.iter(SVG + "text"))
    assert "В: внутри — A" in text and "Н: снаружи — B" in text


def test_outer_angles_have_owned_names_longitudes_and_exact_markers(tmp_path):
    outer_points = [{"point": name, "longitude": lon} for name, lon in
                    (("asc", 0), ("mc", 90), ("ic", 270), ("dsc", 180))]
    root = _wheel(tmp_path, outer_points=outer_points)
    for name, longitude in (("asc", 0), ("mc", 90), ("ic", 270), ("dsc", 180)):
        markers = _markers(root, "outer", name)
        assert len(markers) == 1
        assert (float(markers[0].attrib["cx"]), float(markers[0].attrib["cy"])) == pytest.approx(
            renderer.lon_to_xy(750, 450, longitude, asc_lon=37), abs=0.01)
        labels = [element for element in root.iter(SVG + "text")
                  if element.attrib.get("data-label-ring") == "outer" and
                  element.attrib.get("data-label-body") == name]
        assert len(labels) == 1
        assert labels[0].text.startswith(f"Н: {name.upper()}")
        assert "00°00'" in labels[0].text


def test_legacy_cli_manifest_records_outer_inputs_and_hashes(tmp_path):
    chart = tmp_path / "chart" / "outputs"
    chart.mkdir(parents=True)

    def write_csv(path, fields, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    write_csv(chart / "planets_primary.csv", ("body", "longitude", "sign"),
              [{"body": "sun", "longitude": 0, "sign": "Aries"}])
    write_csv(chart / "houses_placidus.csv", ("house", "longitude"),
              [{"house": i, "longitude": (i - 1) * 30} for i in range(1, 13)])
    write_csv(chart / "chart_points.csv", ("point", "longitude"),
              [{"point": "asc", "longitude": 0}])
    (chart / "natal_aspects.json").write_text("[]", encoding="utf-8")
    outer_planets = tmp_path / "outer_planets.csv"
    outer_aspects = tmp_path / "outer_aspects.csv"
    write_csv(outer_planets, ("body", "longitude", "sign"),
              [{"body": "moon", "longitude": 1, "sign": "Aries"}])
    write_csv(outer_aspects, ("transit_body", "natal_body", "aspect", "orb"),
              [{"transit_body": "moon", "natal_body": "sun", "aspect": "conjunction", "orb": 1}])
    output = tmp_path / "render"
    subprocess.run([sys.executable, str(SCRIPT), "--chart-dir", str(chart.parent),
                    "--output-dir", str(output), "--outer-planets", str(outer_planets),
                    "--outer-aspects", str(outer_aspects), "--outer-label", "outer"],
                   check=True)
    manifest = json.loads((output / "03_render_manifest.json").read_text(encoding="utf-8"))
    for key, path in (("outer_planets", outer_planets), ("outer_aspects", outer_aspects)):
        assert manifest["inputs"][key] == str(path)
        assert manifest["input_sha256"][key] == hashlib.sha256(path.read_bytes()).hexdigest()
