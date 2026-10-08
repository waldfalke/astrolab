#!/usr/bin/env python3
"""Assemble a reviewed two-person reading with sealed calculation and visual packets."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import importlib.metadata
import json
import math
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from markdown_it import MarkdownIt

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "artifacts/mcp-recipes") not in sys.path:
    sys.path.insert(0, str(REPO / "artifacts/mcp-recipes"))

from artifacts.renderer.render_chart import PLANET_GLYPHS, SIGN_SYMBOLS
from artifacts.renderer.render_synastry import OUTPUT_NAMES, _read_bundle
from synastry_local import directed_overlays

PRIVATE_ROOT = REPO / ".private"
TEMPLATE = REPO / "artifacts/report-templates/synastry-reading.html"
SVG_NS = "{http://www.w3.org/2000/svg}"
SAFE_SVG_TAGS = {"svg", "style", "circle", "line", "polyline", "rect", "text", "path", "g"}
BODY_NAMES = {"sun": "Солнце", "moon": "Луна", "mercury": "Меркурий",
              "venus": "Венера", "mars": "Марс", "jupiter": "Юпитер",
              "saturn": "Сатурн", "uranus": "Уран", "neptune": "Нептун",
              "pluto": "Плутон"}
ANGLE_NAMES = {"asc": "ASC", "mc": "MC", "ic": "IC", "dsc": "DSC"}
ASPECT_NAMES = {"conjunction": "☌ соединение", "sextile": "⚹ секстиль",
                "square": "□ квадрат", "trine": "△ трин", "opposition": "☍ оппозиция"}
MOTION_NAMES = {"direct": "Прямое", "retrograde": "Попятное",
                "not_computed": "Не вычислено"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _paths(bundle: Path, visuals: Path, reading: Path, twin: Path, art: Path,
           output: Path, private_root: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    root = private_root.resolve()
    sources = tuple(path.resolve() for path in (bundle, visuals, reading, twin, art))
    target = output.resolve()
    if not all(path.is_relative_to(root) for path in sources[:4]):
        raise ValueError("bundle, visuals, reading and twin must be beneath the private root")
    if not sources[0].is_dir() or not sources[1].is_dir() or not all(
            path.is_file() for path in sources[2:]):
        raise ValueError("bundle, visuals, reading, twin and local art must exist")
    if (not target.is_relative_to(root) or target == root or
            any(target.is_relative_to(source) for source in sources[:2])):
        raise ValueError("output must be a new directory beneath the private root, outside inputs")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output already exists: {output}")
    return (*sources, target)


def _svg_data(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|@import|url\s*\(|https?://|javascript:",
                 source, re.IGNORECASE):
        # The SVG namespace itself contains http://; exclude it from this test.
        without_namespace = source.replace('http://www.w3.org/2000/svg', '')
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|@import|url\s*\(|https?://|javascript:",
                     without_namespace, re.IGNORECASE):
            raise ValueError(f"SVG contains an external or active resource: {path.name}")
    root = ET.fromstring(source)
    if root.tag != SVG_NS + "svg":
        raise ValueError(f"invalid SVG root: {path.name}")
    for element in root.iter():
        if not element.tag.startswith(SVG_NS) or element.tag[len(SVG_NS):] not in SAFE_SVG_TAGS:
            raise ValueError(f"unsupported SVG element: {path.name}")
        for key in element.attrib:
            plain = key.split("}")[-1].lower()
            if plain.startswith("on") or plain in {"href", "src", "style"}:
                raise ValueError(f"unsafe SVG attribute: {path.name}")
    # Only the presentation copy changes. The sealed visual and its digest stay intact.
    source = re.sub(r"(\.plabel\{)([^}]*)(\})",
                    lambda match: match[1] + re.sub(
                        r"(?:paint-order:stroke|stroke:#ffffff|stroke-width:3|stroke-linejoin:round);?",
                        "", match[2]) + match[3], source)
    return "data:image/svg+xml;base64," + base64.b64encode(source.encode("utf-8")).decode("ascii")


def _art_data(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ValueError("art must be a local PNG, JPEG or WebP file")
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def _validate_visuals(bundle: Path, visuals: Path, bundle_manifest: dict,
                      owners: dict, labels: dict, contact_count: int) -> dict:
    path = visuals / "04_visual_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("renderer") != "catme-synastry-svg" or
            manifest.get("source_manifest_sha256") != _sha(bundle / "manifest.json") or
            manifest.get("participants") != owners or manifest.get("labels") != labels or
            manifest.get("coordinate_system") != "tropical" or
            manifest.get("contact_count") != contact_count or
            manifest.get("inputs") != bundle_manifest["files"] or
            manifest.get("house_owner") != {
                "01_A_inner_B_outer.svg": "A", "02_B_inner_A_outer.svg": "B"}):
        raise ValueError("visual manifest disagrees with calculation, labels or chart owners")
    for name in ("render_chart.py", "render_synastry.py"):
        if manifest.get("renderer_sha256", {}).get(name) != _sha(REPO / "artifacts/renderer" / name):
            raise ValueError(f"visuals were made by another renderer version: {name}")
    if set(manifest.get("outputs", {})) != set(OUTPUT_NAMES):
        raise ValueError("visual manifest requires exactly two wheels and a grid")
    for name in OUTPUT_NAMES:
        if _sha(visuals / name) != manifest["outputs"][name]:
            raise ValueError(f"visual SHA256 mismatch: {name}")
    return manifest


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _table(headers: list[tuple[str, str]], rows: list[dict], row_class: str,
           table_class: str = "") -> str:
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in headers)
    body = "".join('<tr class="' + row_class + '">' + "".join(
        f"<td>{html.escape(str(row[key]), quote=True)}</td>" for key, _ in headers) +
        "</tr>" for row in rows)
    css = f' class="{table_class}"' if table_class else ""
    return f"<table{css}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _point(kind: str, name: str) -> str:
    if kind == "planet" and name in BODY_NAMES:
        return f"{PLANET_GLYPHS[name]} {BODY_NAMES[name]}"
    if kind == "angle" and name in ANGLE_NAMES:
        return ANGLE_NAMES[name]
    raise ValueError(f"unknown chart point: {kind}:{name}")


def _position(longitude: str | float) -> str:
    rounded = round(float(longitude), 2) % 360
    if not math.isfinite(rounded):
        raise ValueError("invalid position longitude")
    signs = list(SIGN_SYMBOLS.values())
    return f"{signs[int(rounded // 30)]} {rounded % 30:.2f}°"


def _tables(bundle: Path, owners: dict, labels: dict, contacts: list[dict]) -> tuple[str, str, str]:
    contact_rows = []
    for row in sorted(contacts, key=lambda item: (float(item["orb"]), item["key"])):
        a_end, b_end = (("from", "to") if row["from_owner"] == owners["A"]
                        else ("to", "from"))
        contact_rows.append({
            "a_point": _point(row[f"{a_end}_kind"], row[f"{a_end}_point"]),
            "aspect": ASPECT_NAMES[row["aspect"]],
            "b_point": _point(row[f"{b_end}_kind"], row[f"{b_end}_point"]),
            "orb": f'{float(row["orb"]):.2f}°',
        })
    contacts_html = _table([
        ("a_point", f'{labels["A"]}: точка'), ("aspect", "Аспект"),
        ("b_point", f'{labels["B"]}: точка'), ("orb", "Орб")],
        contact_rows, "contact-row", "contact-table")
    positions = []
    for slot in ("A", "B"):
        base = bundle / f"adapters/charts/{slot}/outputs"
        planet_rows = [{"body": _point("planet", row["body"]),
                        "position": _position(row["longitude"]),
                        "house": row["house"],
                        "motion": MOTION_NAMES[row["motion"]]}
                       for row in _csv(base / "planets_primary.csv")]
        if len(planet_rows) != 10:
            raise ValueError(f"natal {slot} must contain ten planet rows")
        positions.append(f"<h3>{html.escape(labels[slot])}: планеты</h3>" + _table([
            ("body", "Планета"), ("position", "Положение"),
            ("house", "Дом"), ("motion", "Движение")], planet_rows, "position-row"))
        house_rows = [{"house": row["house"], "position": _position(row["longitude"])}
                      for row in _csv(base / "houses_placidus.csv")]
        positions.append(f"<h3>{html.escape(labels[slot])}: куспиды домов</h3>" + _table([
            ("house", "Дом"), ("position", "Положение")], house_rows, "house-row"))
        angle_rows = [{"point": _point("angle", row["point"]),
                       "position": _position(row["longitude"])}
                      for row in _csv(base / "chart_points.csv")]
        positions.append(f"<h3>{html.escape(labels[slot])}: углы</h3>" + _table([
            ("point", "Угол"), ("position", "Положение")], angle_rows, "angle-row"))
    overlays = _csv(bundle / "overlays.csv")
    if len(overlays) != 20 or not all(set(row) == {
            "from_owner", "body", "to_owner", "house", "longitude"} for row in overlays):
        raise ValueError("two directed overlays require twenty complete rows")
    natals = {owners[slot]: json.loads((bundle / f"natals/{slot}.json").read_text(encoding="utf-8"))
              for slot in ("A", "B")}
    expected = directed_overlays(natals)
    for actual, reference in zip(overlays, expected, strict=True):
        if (actual["from_owner"] != reference["from_owner"] or
                actual["body"] != reference["body"] or
                actual["to_owner"] != reference["to_owner"] or
                int(actual["house"]) != reference["house"] or
                not math.isclose(float(actual["longitude"]), reference["longitude"], abs_tol=1e-7)):
            raise ValueError("overlay disagrees with natal positions or receiving houses")
    overlay_html = []
    for slot in ("A", "B"):
        other = "B" if slot == "A" else "A"
        rows = [{"body": _point("planet", row["body"]), "house": row["house"],
                 "position": _position(row["longitude"])}
                for row in overlays if row["from_owner"] == owners[slot]]
        overlay_html.append(f"<h3>{html.escape(labels[slot])} → {html.escape(labels[other])}</h3>" +
                            _table([("body", "Планета"), ("house", "Дом партнёра"),
                                    ("position", "Положение")], rows, "overlay-row"))
    return contacts_html, "".join(positions), "".join(overlay_html)


def _markdown(source: str) -> str:
    parser = MarkdownIt("js-default").enable("table")
    tokens = parser.parse(source)

    def inert(items):
        for token in items:
            if token.type == "image":
                token.type, token.tag, token.content, token.children = "text", "", token.content, None
                token.attrs = {}
            elif token.type == "link_open":
                token.type, token.tag, token.attrs = "span_open", "span", {}
            elif token.type == "link_close":
                token.type, token.tag = "span_close", "span"
            if token.children:
                inert(token.children)

    inert(tokens)
    return parser.renderer.render(tokens, parser.options, {})


def _print_pdf(html_path: Path, pdf_path: Path, browser_executable: Path | None) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF requires the optional synastry group: uv sync --group synastry") from exc
    try:
        with sync_playwright() as playwright:
            kwargs = {"executable_path": str(browser_executable)} if browser_executable else {}
            browser = playwright.chromium.launch(**kwargs)
            try:
                page = browser.new_page()
                page.goto(html_path.as_uri(), wait_until="load")
                page.evaluate("""async () => {
                    await document.fonts.ready;
                    await Promise.all(Array.from(document.images, image => image.decode()));
                }""")
                page.pdf(path=str(pdf_path), print_background=True,
                         prefer_css_page_size=True, display_header_footer=False)
                version = browser.version
            finally:
                browser.close()
    except Exception as exc:
        raise RuntimeError("Chromium PDF rendering failed; install Chromium with "
                           "`python -m playwright install chromium` or pass "
                           "--browser-executable") from exc
    if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError("Chromium did not produce a valid PDF")
    return {"playwright": importlib.metadata.version("playwright"), "chromium": version}


def assemble_synastry(*, bundle: str | Path, visuals: str | Path, reading: str | Path,
                      twin: str | Path, art: str | Path, output_dir: str | Path,
                      title: str, label_a: str, label_b: str, pdf: bool = False,
                      browser_executable: str | Path | None = None, include_basis: bool = True,
                      private_root: Path = PRIVATE_ROOT) -> list[Path]:
    """Write a new private report directory only after every input and output succeeds."""
    bundle, visuals, reading, twin, art, output = _paths(
        *(Path(value) for value in (bundle, visuals, reading, twin, art, output_dir)), private_root)
    for label in (title, label_a, label_b):
        if not isinstance(label, str) or not label.strip():
            raise ValueError("title and both labels must be non-empty text")
    labels = {"A": label_a, "B": label_b}
    bundle_manifest, _, _, contacts = _read_bundle(bundle)
    owners = bundle_manifest["participants"]
    visual_manifest = _validate_visuals(bundle, visuals, bundle_manifest, owners, labels,
                                        len(contacts))
    contact_html, position_html, overlay_html = _tables(bundle, owners, labels, contacts)
    template = TEMPLATE.read_text(encoding="utf-8")
    reading_html = _markdown(reading.read_text(encoding="utf-8"))
    basis_html = _markdown(twin.read_text(encoding="utf-8")) if include_basis else ""
    if not include_basis:
        template = re.sub(r'<details id="basis".*?</details>', '', template, flags=re.DOTALL)
        template = re.sub(r'<a href="#basis">.*?</a>', '', template, flags=re.DOTALL)
        template = template.replace(
            "Astrolab · Синастрия. Аналитическое основание с альтернативами и ограничениями доступно в HTML-версии отчёта.",
            "Astrolab · Синастрия.")
    replacements = {
        "TITLE": html.escape(title, quote=True),
        "LABEL_A": html.escape(label_a, quote=True),
        "LABEL_B": html.escape(label_b, quote=True),
        "READING_HTML": reading_html,
        "BASIS_HTML": basis_html,
        "CONTACT_TABLE": contact_html,
        "POSITIONS_HTML": position_html,
        "OVERLAYS_HTML": overlay_html,
        "ART_URI": _art_data(art),
        "WHEEL_A_URI": _svg_data(visuals / OUTPUT_NAMES[0]),
        "WHEEL_B_URI": _svg_data(visuals / OUTPUT_NAMES[1]),
        "GRID_URI": _svg_data(visuals / OUTPUT_NAMES[2]),
    }
    required_tokens = set(re.findall(r"\{\{([A-Z_]+)\}\}", template))
    if required_tokens != set(replacements) - ({"BASIS_HTML"} if not include_basis else set()):
        raise ValueError("presentation template tokens changed or are incomplete")
    report = re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: replacements[match[1]], template)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".synastry-report-", dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / "report.html").write_text(report, encoding="utf-8", newline="\n")
        shutil.copyfile(reading, stage / "reading.md")
        shutil.copyfile(twin, stage / "twin.md")
        browser = {"status": "not_requested"}
        if pdf:
            browser = _print_pdf(stage / "report.html", stage / "report.pdf",
                                 Path(browser_executable) if browser_executable else None)
        outputs = {path.name: _sha(path) for path in stage.iterdir() if path.is_file()}
        manifest = {
            "assembler": "catme-synastry-presentation", "version": "0.1.0",
            "participants": owners, "labels": labels, "title": title,
            "house_owner": visual_manifest["house_owner"],
            "contact_count": len(contacts), "basis_in_html": include_basis,
            "inputs": {
                "bundle_manifest": _sha(bundle / "manifest.json"),
                "bundle_files": bundle_manifest["files"],
                "visual_manifest": _sha(visuals / "04_visual_manifest.json"),
                "visuals": visual_manifest["outputs"],
                "reading": _sha(reading), "twin": _sha(twin), "art": _sha(art),
                "template": _sha(TEMPLATE), "assembler": _sha(Path(__file__)),
            },
            "versions": {"markdown_it_py": importlib.metadata.version("markdown-it-py"),
                         "renderer_sha256": visual_manifest["renderer_sha256"],
                         "browser": browser},
            "outputs": outputs,
        }
        (stage / "manifest.json").write_bytes(_json_bytes(manifest))
        stage.rename(output)
    return [output / name for name in (*outputs, "manifest.json")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "visuals", "reading", "twin", "art", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("title", "label-a", "label-b"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--pdf", action="store_true", help="print with Chromium")
    parser.add_argument("--browser-executable", type=Path, help="explicit Chromium executable")
    parser.add_argument("--omit-basis", action="store_true", help="keep twin.md without HTML basis")
    args = parser.parse_args(argv)
    files = assemble_synastry(bundle=args.bundle, visuals=args.visuals,
                              reading=args.reading, twin=args.twin, art=args.art,
                              output_dir=args.output_dir, title=args.title,
                              label_a=args.label_a, label_b=args.label_b,
                              pdf=args.pdf, browser_executable=args.browser_executable,
                              include_basis=not args.omit_basis)
    print(json.dumps({"files": [path.name for path in files]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
