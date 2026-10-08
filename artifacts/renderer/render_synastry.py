#!/usr/bin/env python3
"""Render two reciprocal wheels and a cross-aspect grid from one sealed private bundle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
for directory in (REPO, REPO / "artifacts/mcp-recipes"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from synastry_local import cross_contacts, validate_natal
from astro.dignities import sign_of
from astro.placements import house_of
from artifacts.renderer.render_chart import (PLANET_GLYPHS, PLANET_ORDER, SIGN_SYMBOLS,
                                             draw_wheel, lon_to_sign_deg)

PRIVATE_ROOT = REPO / ".private"
ANGLES = ("asc", "mc", "ic", "dsc")
ASPECTS = {"conjunction", "sextile", "square", "trine", "opposition"}
ASPECT_GLYPHS = {"conjunction": "☌", "sextile": "⚹", "square": "□",
                 "trine": "△", "opposition": "☍"}
REQUIRED_FILES = {"cross_aspects.csv", "overlays.csv"}
for slot in ("A", "B"):
    REQUIRED_FILES.update({
        f"natals/{slot}.json", f"natals/{slot}_aspects.csv",
        *(f"adapters/charts/{slot}/outputs/{name}.csv"
          for name in ("natal_longitudes", "houses_placidus", "chart_points",
                       "planets_primary")),
    })
OUTPUT_NAMES = ("01_A_inner_B_outer.svg", "02_B_inner_A_outer.svg",
                "03_cross_aspect_grid.svg")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _private_paths(bundle: Path, output: Path, private_root: Path) -> tuple[Path, Path]:
    root = private_root.resolve()
    source, target = bundle.resolve(), output.resolve()
    if not source.is_relative_to(root) or not source.is_dir():
        raise ValueError("bundle must be an existing directory beneath the private root")
    if not target.is_relative_to(root) or target == root or target.is_relative_to(source):
        raise ValueError("output must be a new directory beneath the private root, outside bundle")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output already exists: {output}")
    return source, target


def _adapter_rows(path: Path, fields: tuple[str, ...], key: str) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"adapter columns disagree with the natal bundle: {path.name}")
        rows = list(reader)
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"adapter contains duplicate {key}: {path.name}")
    return indexed


def _same_number(raw: str, expected: float) -> bool:
    try:
        actual = float(raw)
    except (TypeError, ValueError):
        return False
    return math.isfinite(actual) and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-7)


def _validate_adapters(bundle: Path, slot: str, natal: dict) -> None:
    """Keep every tabular view numerically identical to its sealed natal JSON."""
    base = bundle / f"adapters/charts/{slot}/outputs"
    positions = natal["positions"]
    longitudes = _adapter_rows(base / "natal_longitudes.csv",
                               ("body", "longitude"), "body")
    if set(longitudes) != set(PLANET_ORDER) or any(
            not _same_number(longitudes[body]["longitude"], positions[body])
            for body in PLANET_ORDER):
        raise ValueError(f"natal_longitudes adapter disagrees with natal {slot}")

    houses = _adapter_rows(base / "houses_placidus.csv",
                           ("house", "longitude"), "house")
    if set(houses) != {str(index) for index in range(1, 13)} or any(
            not _same_number(houses[str(index)]["longitude"], longitude)
            for index, longitude in enumerate(natal["houses"]["cusps"], 1)):
        raise ValueError(f"houses_placidus adapter disagrees with natal {slot}")

    points = _adapter_rows(base / "chart_points.csv",
                           ("point", "longitude"), "point")
    if set(points) != set(ANGLES) or any(
            not _same_number(points[point]["longitude"], natal["houses"]["angles"][point])
            for point in ANGLES):
        raise ValueError(f"chart_points adapter disagrees with natal {slot}")

    primary_fields = ("body", "longitude", "sign", "house", "dignity", "sect_role",
                      "speed_longitude_deg_day", "motion")
    primary = _adapter_rows(base / "planets_primary.csv", primary_fields, "body")
    speeds = natal["motion"]["speed_longitude_deg_day"]
    for body in PLANET_ORDER:
        if body not in primary:
            raise ValueError(f"planets_primary adapter omits {body} from natal {slot}")
        row = primary[body]
        expected_speed = "" if speeds is None else speeds[body]
        expected = {
            "sign": sign_of(positions[body]),
            "house": str(natal.get("placements", {}).get(
                body, house_of(positions[body], natal["houses"]["cusps"]))),
            "dignity": str(natal.get("dignities", {}).get(body, {}).get(
                "dignity", "not_computed")),
            "sect_role": str(natal.get("sect", {}).get("bodies", {}).get(
                body, {}).get("role", "not_computed")),
            "motion": "not_computed" if speeds is None else (
                "retrograde" if speeds[body] < 0 else "direct"),
        }
        if (not _same_number(row["longitude"], positions[body]) or
                (expected_speed == "" and row["speed_longitude_deg_day"] != "") or
                (expected_speed != "" and not _same_number(
                    row["speed_longitude_deg_day"], expected_speed)) or
                any(row[field] != value for field, value in expected.items())):
            raise ValueError(f"planets_primary adapter disagrees with natal {slot}: {body}")


def _read_bundle(bundle: Path) -> tuple[dict, dict, dict, list[dict]]:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("recipe") != "synastry_local" or
            manifest.get("scope") != "private_exact_time_pilot" or
            manifest.get("settings", {}).get("zodiac") != "tropical" or
            manifest.get("settings", {}).get("houses") != "Placidus"):
        raise ValueError("unsupported or incomplete exact-time synastry manifest")
    owners = manifest.get("participants")
    if not isinstance(owners, dict) or set(owners) != {"A", "B"} or (
            not all(isinstance(v, str) and v for v in owners.values()) or
            owners["A"] == owners["B"]):
        raise ValueError("manifest requires two distinct owners")
    files = manifest.get("files")
    if not isinstance(files, dict) or not REQUIRED_FILES.issubset(files):
        raise ValueError("manifest is missing required natal or cross-aspect files")
    for relative, digest in files.items():
        path_name = PurePosixPath(relative)
        if (not isinstance(relative, str) or path_name.is_absolute() or
                ".." in path_name.parts or str(path_name) != relative or
                not re.fullmatch(r"[0-9a-f]{64}", str(digest))):
            raise ValueError(f"unsafe or invalid manifest file entry: {relative}")
        path = (bundle / relative).resolve()
        if not path.is_relative_to(bundle) or not path.is_file() or _sha(path) != digest:
            raise ValueError(f"manifest file missing or SHA256 mismatch: {relative}")

    natals = {}
    for slot in ("A", "B"):
        natal = json.loads((bundle / f"natals/{slot}.json").read_text(encoding="utf-8"))
        if natal.get("owner") != owners[slot] or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", str(natal.get("moment_utc", ""))):
            raise ValueError(f"natal {slot} owner or exact UTC moment disagrees with manifest")
        validate_natal(natal)
        motion = natal.get("motion", {})
        if motion.get("status") not in {"computed", "not_computed"}:
            raise ValueError(f"natal {slot} has incomplete motion state")
        speeds = motion.get("speed_longitude_deg_day")
        if motion["status"] == "computed":
            if not isinstance(speeds, dict) or set(speeds) != set(PLANET_ORDER) or not all(
                    isinstance(value, (int, float)) and not isinstance(value, bool) and
                    math.isfinite(value) for value in speeds.values()):
                raise ValueError(f"natal {slot} has invalid motion speeds")
        elif speeds is not None:
            raise ValueError(f"natal {slot} has contradictory motion state")
        _validate_adapters(bundle, slot, natal)
        natals[slot] = natal

    with (bundle / "cross_aspects.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"key", "from_owner", "from_kind", "from_point", "to_owner",
                    "to_kind", "to_point", "aspect", "separation", "orb", "orb_limit"}
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError("cross-aspect columns are incomplete")
        contacts = list(reader)
    expected = {row["key"]: row for row in cross_contacts(
        {owners[slot]: natals[slot] for slot in ("A", "B")})}
    actual = {}
    for row in contacts:
        key = row["key"]
        if key in actual or key not in expected or row["aspect"] not in ASPECTS:
            raise ValueError(f"unexpected or duplicate cross-aspect: {key}")
        reference = expected[key]
        for field in ("from_owner", "from_kind", "from_point", "to_owner",
                      "to_kind", "to_point", "aspect"):
            if row[field] != reference[field]:
                raise ValueError(f"cross-aspect {key} endpoint or kind mismatch")
        for field in ("separation", "orb", "orb_limit"):
            try:
                number = float(row[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"cross-aspect {key} has invalid {field}") from exc
            if not math.isfinite(number) or not math.isclose(
                    number, reference[field], rel_tol=0, abs_tol=1e-7):
                raise ValueError(f"cross-aspect {key} {field} mismatch")
        actual[key] = row
    if set(actual) != set(expected):
        raise ValueError("cross-aspect packet omits calculated contacts")
    return manifest, natals["A"], natals["B"], contacts


def _rows(natal: dict) -> tuple[list[dict], list[dict], list[dict]]:
    speeds = natal["motion"]["speed_longitude_deg_day"]
    planets = []
    for body in PLANET_ORDER:
        longitude = natal["positions"][body]
        sign, degree = lon_to_sign_deg(longitude)
        planets.append({"body": body, "longitude": longitude, "sign": sign,
                        "degree": degree, "motion": "retrograde" if speeds is not None and
                        speeds[body] < 0 else "direct" if speeds is not None else "not_computed"})
    houses = [{"house": index, "longitude": longitude}
              for index, longitude in enumerate(natal["houses"]["cusps"], start=1)]
    points = [{"point": name, "longitude": natal["houses"]["angles"][name]}
              for name in ANGLES]
    return planets, houses, points


def _orient_contacts(contacts: list[dict], inner_owner: str) -> list[dict]:
    oriented = []
    for row in contacts:
        inner_is_from = row["from_owner"] == inner_owner
        inner, outer = ("from", "to") if inner_is_from else ("to", "from")
        oriented.append({"inner_body": row[f"{inner}_point"],
                         "inner_kind": row[f"{inner}_kind"],
                         "outer_body": row[f"{outer}_point"],
                         "outer_kind": row[f"{outer}_kind"],
                         "aspect": row["aspect"], "orb": float(row["orb"]),
                         "key": row["key"]})
    return oriented


def draw_cross_aspect_grid(label_a: str, label_b: str, contacts: list[dict],
                           out_path: Path) -> None:
    """Draw all owned contacts; rows belong to A and columns belong to B."""
    names = list(PLANET_ORDER) + list(ANGLES)
    size, left, top, cell = 1850, 225, 215, 112
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
             f'viewBox="0 0 {size} {size}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<style>text{font-family:"Noto Sans","Segoe UI",Arial,sans-serif;fill:#17212b}'
             '.head{font-size:34px;font-weight:600}.axis{font-size:25px;font-weight:600}'
             '.axis-symbol{font-size:30px;font-family:"Segoe UI Symbol","Noto Sans Symbols 2",'
             '"Noto Sans Symbols","DejaVu Sans",sans-serif;font-weight:600}'
             '.aspect-glyph{font-size:36px;font-family:"Segoe UI Symbol","Noto Sans Symbols 2",'
             '"Noto Sans Symbols","DejaVu Sans",sans-serif;font-weight:600}'
             '.orb{font-size:22px;fill:#465362}.legend{font-size:26px}</style>',
             '<text class="head" x="52" y="64">Межкартные аспекты</text>',
             f'<text class="axis" x="{left}" y="98">Строки: {html.escape(label_a)} (A)</text>',
             f'<text class="axis" x="{left}" y="128">Столбцы: {html.escape(label_b)} (B)</text>',
             f'<text class="legend" x="{left}" y="163">'
             '☌ соединение · ⚹ секстиль · □ квадрат · △ трин · ☍ оппозиция · орб в градусах'
             '</text>']
    label = {**PLANET_GLYPHS, "asc": "ASC", "mc": "MC", "ic": "IC", "dsc": "DSC"}
    for index, name in enumerate(names):
        x = left + index * cell + cell / 2
        y = top + index * cell + cell / 2
        lines.append(f'<text class="axis-symbol" x="{x:.1f}" y="{top - 18}" text-anchor="middle">{label[name]}</text>')
        lines.append(f'<text class="axis-symbol" x="{left - 18}" y="{y:.1f}" text-anchor="end" dominant-baseline="middle">{label[name]}</text>')
    for row_index in range(len(names)):
        for column_index in range(len(names)):
            x, y = left + column_index * cell, top + row_index * cell
            lines.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                         f'fill="{"#f8fafc" if (row_index + column_index) % 2 else "#ffffff"}" '
                         f'stroke="#d8dee5"/>')
    index = {name: position for position, name in enumerate(names)}
    for row in contacts:
        if row["from_owner"] == "A":
            a_name, b_name = row["from_point"], row["to_point"]
        else:
            a_name, b_name = row["to_point"], row["from_point"]
        if a_name not in index or b_name not in index:
            raise ValueError("unresolved cross-aspect grid endpoint")
        x = left + index[b_name] * cell + cell / 2
        y = top + index[a_name] * cell + cell / 2
        aspect = html.escape(row["aspect"], quote=True)
        key = html.escape(row["key"], quote=True)
        lines.append(f'<text data-contact-key="{key}" data-aspect="{aspect}" '
                     f'class="aspect-glyph" x="{x:.1f}" y="{y - 10:.1f}" '
                     f'text-anchor="middle" dominant-baseline="middle">{ASPECT_GLYPHS[row["aspect"]]}</text>')
        lines.append(f'<text class="orb" x="{x:.1f}" y="{y + 31:.1f}" '
                     f'text-anchor="middle">{float(row["orb"]):.2f}°</text>')
    lines.append('</svg>')
    out_path.write_text("\n".join(lines), encoding="utf-8")


def render_synastry(bundle: str | Path, output_dir: str | Path, label_a: str, label_b: str,
                    *, private_root: Path = PRIVATE_ROOT) -> list[Path]:
    bundle, output_dir = _private_paths(Path(bundle), Path(output_dir), private_root)
    manifest, natal_a, natal_b, contacts = _read_bundle(bundle)
    if not isinstance(label_a, str) or not label_a.strip() or not isinstance(label_b, str) or not label_b.strip():
        raise ValueError("both owner labels are required")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".synastry-", dir=output_dir.parent) as stage_name:
        stage = Path(stage_name)
        views = (("A", natal_a, natal_b, label_a, label_b),
                 ("B", natal_b, natal_a, label_b, label_a))
        for file_name, (slot, inner, outer, inner_label, outer_label) in zip(OUTPUT_NAMES[:2], views):
            inner_planets, inner_houses, inner_points = _rows(inner)
            outer_planets, _, outer_points = _rows(outer)
            draw_wheel(inner_planets, inner_houses, inner_points, [], stage / file_name,
                       outer_planets=outer_planets, outer_points=outer_points,
                       outer_aspects=_orient_contacts(contacts, manifest["participants"][slot]),
                       inner_label=inner_label, outer_label=outer_label, cross_only=True)
        grid_contacts = [{**row, "from_owner": "A" if row["from_owner"] == manifest["participants"]["A"] else "B"}
                         for row in contacts]
        draw_cross_aspect_grid(label_a, label_b, grid_contacts, stage / OUTPUT_NAMES[2])
        result_manifest = {
            "renderer": "catme-synastry-svg", "source_manifest_sha256": _sha(bundle / "manifest.json"),
            "participants": manifest["participants"], "labels": {"A": label_a, "B": label_b},
            "coordinate_system": manifest["settings"]["zodiac"],
            "house_owner": {"01_A_inner_B_outer.svg": "A", "02_B_inner_A_outer.svg": "B"},
            "contact_count": len(contacts), "inputs": manifest["files"],
            "renderer_sha256": {"render_chart.py": _sha(REPO / "artifacts/renderer/render_chart.py"),
                                "render_synastry.py": _sha(Path(__file__))},
            "outputs": {name: _sha(stage / name) for name in OUTPUT_NAMES},
        }
        (stage / "04_visual_manifest.json").write_text(
            json.dumps(result_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        stage.rename(output_dir)
    return [output_dir / name for name in (*OUTPUT_NAMES, "04_visual_manifest.json")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render sealed private synastry visuals")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label-a", required=True)
    parser.add_argument("--label-b", required=True)
    args = parser.parse_args(argv)
    files = render_synastry(args.bundle, args.output_dir, args.label_a, args.label_b)
    print(json.dumps({"files": [path.name for path in files]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
