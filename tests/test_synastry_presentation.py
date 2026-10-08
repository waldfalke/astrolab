"""Presentation accepts only a sealed, owned synastry calculation and visual pair."""
import base64
import csv
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recipe = _load("synastry_recipe_for_presentation", "artifacts/mcp-recipes/synastry_local.py")
visual = _load("synastry_visual_for_presentation", "artifacts/renderer/render_synastry.py")
SCRIPT = ROOT / "artifacts/renderer/assemble_synastry.py"
presentation = _load("synastry_presentation", "artifacts/renderer/assemble_synastry.py") if SCRIPT.exists() else None
BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")


def _natal(offset, instant, lat, lon):
    positions = {body: float((index * 34 + offset) % 360)
                 for index, body in enumerate(BODIES)}
    cusps = [float((350 + offset + index * 30) % 360) for index in range(12)]
    return {"positions": positions,
            "houses": {"cusps": cusps, "angles": {"asc": cusps[0], "ic": cusps[3],
                                              "dsc": cusps[6], "mc": cusps[9]}},
            "aspects": [], "moment_utc": instant, "location": {"lat": lat, "lon": lon}}


@pytest.fixture
def packet(tmp_path):
    private = tmp_path / ".private"
    private.mkdir()
    source = private / "input.json"
    source.write_text(json.dumps({"participants": {
        "A": {"id": "one", "datetime_utc": "2000-01-01T12:00:00Z",
              "latitude": 0, "longitude": 0},
        "B": {"id": "two", "datetime_utc": "2001-01-01T12:00:00Z",
              "latitude": 10, "longitude": 20}}}), encoding="utf-8")
    bundle = private / "bundle"
    natals = {"one": _natal(0, "2000-01-01T12:00:00Z", 0, 0),
              "two": _natal(7, "2001-01-01T12:00:00Z", 10, 20)}
    recipe.write_bundle(source, bundle, natals,
                        {owner: {body: 0.1 for body in BODIES} for owner in natals},
                        {"engine": "synthetic-test"}, private_root=private)
    visuals = private / "visuals"
    visual.render_synastry(bundle, visuals, "A & <one>", "B <two>", private_root=private)
    reading = private / "reading-source.md"
    reading.write_text("# Совместная работа\n\nПервый абзац.\n\nВторой абзац <script>alert(1)</script>.\n"
                       "\n| Ось | Наблюдение |\n|---|---|\n| A → B | Проверка |\n",
                       encoding="utf-8")
    twin = private / "twin-source.md"
    twin.write_text("# Основание\n\nАльтернатива и пределы вывода.\n", encoding="utf-8")
    art = private / "art.png"
    art.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg=="))
    return private, bundle, visuals, reading, twin, art


def _assemble(packet, **changes):
    assert presentation is not None, "presentation assembler is missing"
    private, bundle, visuals, reading, twin, art = packet
    arguments = dict(bundle=bundle, visuals=visuals, reading=reading, twin=twin,
                     art=art, output_dir=private / "report", title="Двое <вместе>",
                     label_a="A & <one>", label_b="B <two>", private_root=private)
    arguments.update(changes)
    return presentation.assemble_synastry(**arguments)


def test_complete_owned_html_and_sources_with_hashed_manifest(packet):
    _assemble(packet)
    private, bundle, visuals, reading, twin, art = packet
    output = private / "report"
    html = (output / "report.html").read_text(encoding="utf-8")
    assert b"\r\n" not in (output / "report.html").read_bytes()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert "{{" not in html
    assert "Двое &lt;вместе&gt;" in html
    assert "A &amp; &lt;one&gt;" in html and "B &lt;two&gt;" in html
    assert "Первый абзац" in html and "Второй абзац" in html
    assert "Альтернатива и пределы вывода" in html
    assert "<table" in html and "Проверка" in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert (output / "reading.md").read_bytes() == reading.read_bytes()
    assert (output / "twin.md").read_bytes() == twin.read_bytes()
    for name in ("report.html", "reading.md", "twin.md"):
        assert manifest["outputs"][name] == hashlib.sha256((output / name).read_bytes()).hexdigest()
    assert manifest["inputs"]["bundle_manifest"] == hashlib.sha256(
        (bundle / "manifest.json").read_bytes()).hexdigest()
    assert manifest["inputs"]["visual_manifest"] == hashlib.sha256(
        (visuals / "04_visual_manifest.json").read_bytes()).hexdigest()
    assert manifest["participants"] == {"A": "one", "B": "two"}
    assert manifest["house_owner"] == {"01_A_inner_B_outer.svg": "A",
                                       "02_B_inner_A_outer.svg": "B"}
    with (bundle / "cross_aspects.csv").open(encoding="utf-8", newline="") as stream:
        contacts = list(csv.DictReader(stream))
    assert html.count('class="contact-row"') == len(contacts)
    assert html.count('class="position-row"') == 20
    assert html.count('class="overlay-row"') == 20
    contact_row = re.search(r'<tr class="contact-row">(.*?)</tr>', html)
    position_row = re.search(r'<tr class="position-row">(.*?)</tr>', html)
    assert contact_row and contact_row[1].count("<td>") == 4
    assert position_row and position_row[1].count("<td>") == 4
    assert "Солнце" in html and "☉" in html
    assert "соединение" in html and "☌" in html
    assert "<th>Ключ</th>" not in html
    assert "<th>Расстояние, °</th>" not in html
    assert "A &amp; &lt;one&gt; → B &lt;two&gt;" in html
    assert "B &lt;two&gt; → A &amp; &lt;one&gt;" in html
    assert "data:image/svg+xml;base64," in html and "data:image/png;base64," in html
    embedded_wheel = re.search(r'data:image/svg\+xml;base64,([^" ]+)', html)
    assert embedded_wheel
    assert "paint-order:stroke" not in base64.b64decode(embedded_wheel[1]).decode("utf-8")
    assert "paint-order:stroke" in (visuals / "01_A_inner_B_outer.svg").read_text(encoding="utf-8")


@pytest.mark.parametrize("damage", ["bundle_file", "adapter_value", "visual_file", "visual_owner", "visual_label",
                                    "script_svg", "remote_svg"])
def test_rejects_damaged_calculation_or_visual_before_output(packet, damage):
    private, bundle, visuals, *_ = packet
    if damage == "bundle_file":
        with (bundle / "cross_aspects.csv").open("ab") as stream:
            stream.write(b"\n")
    elif damage == "adapter_value":
        relative = "adapters/charts/A/outputs/planets_primary.csv"
        csv_path = bundle / relative
        with csv_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        rows[0]["longitude"] = "123.0"
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        csv_path.write_text(buffer.getvalue(), encoding="utf-8")
        bundle_manifest_path = bundle / "manifest.json"
        bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        bundle_manifest["files"][relative] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        bundle_manifest_path.write_text(json.dumps(bundle_manifest), encoding="utf-8")
        visual_manifest_path = visuals / "04_visual_manifest.json"
        visual_manifest = json.loads(visual_manifest_path.read_text(encoding="utf-8"))
        visual_manifest["inputs"] = bundle_manifest["files"]
        visual_manifest["source_manifest_sha256"] = hashlib.sha256(
            bundle_manifest_path.read_bytes()).hexdigest()
        visual_manifest_path.write_text(json.dumps(visual_manifest), encoding="utf-8")
    elif damage == "visual_file":
        with (visuals / "01_A_inner_B_outer.svg").open("ab") as stream:
            stream.write(b"\n")
    else:
        path = visuals / "04_visual_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if damage == "visual_owner":
            manifest["house_owner"]["01_A_inner_B_outer.svg"] = "B"
        elif damage == "visual_label":
            manifest["labels"]["A"] = "other"
        else:
            svg = visuals / "01_A_inner_B_outer.svg"
            content = svg.read_text(encoding="utf-8")
            added = ('<script xmlns="http://www.w3.org/2000/svg">alert(1)</script>'
                     if damage == "script_svg" else
                     '<image xmlns="http://www.w3.org/2000/svg" href="https://example.org/x.png"/>')
            svg.write_text(content.replace("</svg>", added + "</svg>"), encoding="utf-8")
            manifest["outputs"][svg.name] = hashlib.sha256(svg.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        _assemble(packet)
    assert not (private / "report").exists()


def test_markdown_cannot_load_remote_resources_or_execute_html(packet):
    private, _, _, reading, twin, _ = packet
    reading.write_text("![tracking](https://example.org/track.png)\n\n"
                       "[remote](https://example.org/)\n\n"
                       "<img src='https://example.org/x'>\n", encoding="utf-8")
    _assemble(packet)
    html = (private / "report/report.html").read_text(encoding="utf-8")
    assert not re.search(r'<(?:img|a)\b[^>]*(?:src|href)=["\']https://example\.org', html)
    assert "<img src='https://example.org/x'>" not in html
    assert twin.read_text(encoding="utf-8") in (private / "report/twin.md").read_text(encoding="utf-8")


def test_refuses_existing_output_and_outside_private(packet, tmp_path):
    private = packet[0]
    (private / "report").mkdir()
    with pytest.raises(FileExistsError):
        _assemble(packet)
    with pytest.raises(ValueError, match="private"):
        _assemble(packet, output_dir=tmp_path / "public")


def test_pdf_unavailable_does_not_publish_html_or_false_manifest(packet, monkeypatch):
    private = packet[0]
    assert presentation is not None, "presentation assembler is missing"

    def unavailable(*args, **kwargs):
        raise RuntimeError("Chromium unavailable")

    monkeypatch.setattr(presentation, "_print_pdf", unavailable)
    with pytest.raises(RuntimeError, match="Chromium unavailable"):
        _assemble(packet, pdf=True)
    assert not (private / "report").exists()


def test_omitted_basis_keeps_original_twin_but_not_its_html(packet):
    private = packet[0]
    _assemble(packet, include_basis=False)
    html = (private / "report/report.html").read_text(encoding="utf-8")
    assert "Альтернатива и пределы вывода" not in html
    assert "Альтернатива и пределы вывода" in (private / "report/twin.md").read_text(encoding="utf-8")
    assert 'href="#basis"' not in html
    assert "Основание с альтернативами" not in html
    assert not re.search(r"{{[A-Z_]+}}", html)
