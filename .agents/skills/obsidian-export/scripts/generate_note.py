#!/usr/bin/env python3
"""
Generate Obsidian export bundle from chart project outputs.

Outputs:
- <chart_id>_natal.md
- <chart_id>_planets_table.md
- <chart_id>_canvas.json
- attachments/chart_wheel.svg (if exists)
- attachments/aspect_grid.svg (if exists)
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

import yaml


def split_local_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")
    text = str(value or "").strip()
    if not text:
        return "unknown", "unknown"
    parts = text.split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], "unknown"


def load_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def load_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_chart_data(chart_dir: Path):
    chart_yaml = chart_dir / "chart.yaml"
    if not chart_yaml.exists():
        raise FileNotFoundError(f"chart.yaml not found: {chart_yaml}")

    metadata = yaml.safe_load(chart_yaml.read_text(encoding="utf-8")) or {}
    outputs = chart_dir / "outputs"
    return {
        "metadata": metadata,
        "positions": load_csv(outputs / "planets_primary.csv"),
        "houses": load_csv(outputs / "houses_placidus.csv"),
        "points": load_csv(outputs / "chart_points.csv"),
        "aspects": load_json(outputs / "natal_aspects.json") or [],
        "outputs_dir": outputs,
    }


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def as_motion_label(row):
    state = str(row.get("motion_state", "")).strip().upper()
    retro = str(row.get("retrograde", "")).strip().lower() in {"true", "1", "yes", "r", "retrograde"}
    if state == "ST":
        return "ST"
    if state == "R" or retro:
        return "R"
    if state == "D":
        return "D"
    return ""


def normalize_aspects(aspects):
    if isinstance(aspects, dict):
        aspects = aspects.get("aspects", [])
    if not isinstance(aspects, list):
        return []
    out = []
    for a in aspects:
        if not isinstance(a, dict):
            continue
        out.append(
            {
                "body1": a.get("body1", a.get("planet1", "")),
                "body2": a.get("body2", a.get("planet2", "")),
                "aspect": a.get("aspect", a.get("type", "")),
                "angle": a.get("angle", ""),
                "orb": a.get("orb", ""),
                "applying": bool(a.get("applying", False)),
            }
        )
    return out


def planets_table_markdown(rows):
    lines = [
        "| Body | Longitude | Sign | Degree | Motion | Speed (deg/day) | Shadow |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lon = f'{to_float(r.get("longitude", 0.0)):.6f}'
        deg = f'{to_float(r.get("degree", 0.0)):.2f}'
        speed_raw = str(r.get("speed_deg_day", "")).strip()
        speed = f"{to_float(speed_raw):.6f}" if speed_raw else ""
        lines.append(
            f'| {r.get("body","")} | {lon}° | {r.get("sign","")} | {deg}° | {as_motion_label(r)} | {speed} | {r.get("shadow_state","none")} |'
        )
    return "\n".join(lines) + "\n"


def houses_table_markdown(rows):
    if not rows:
        return ""
    angle_names = {1: "ASC", 4: "IC", 7: "DSC", 10: "MC"}
    lines = ["| House | Longitude | Sign | Degree |", "|---|---|---|---|"]
    for r in rows:
        h = int(to_float(r.get("house", 0), 0))
        label = angle_names.get(h, str(h))
        lon = f'{to_float(r.get("longitude", 0.0)):.6f}'
        deg = f'{to_float(r.get("degree", 0.0)):.2f}'
        lines.append(f'| {label} | {lon}° | {r.get("sign","")} | {deg}° |')
    return "\n".join(lines) + "\n"


def aspects_table_markdown(rows):
    lines = ["| Body 1 | Body 2 | Aspect | Angle | Orb | Applying |", "|---|---|---|---|---|---|"]
    for a in rows:
        applying = "Yes" if a.get("applying") else "No"
        lines.append(
            f'| {a.get("body1","")} | {a.get("body2","")} | {a.get("aspect","")} | {a.get("angle","")}° | {a.get("orb","")}° | {applying} |'
        )
    return "\n".join(lines) + "\n"


def build_note(chart_id, data):
    metadata = data["metadata"]
    birth = metadata.get("birth", {})
    location = metadata.get("location", {})
    birth_date, birth_time = split_local_datetime(birth.get("local_datetime", ""))

    aspects = normalize_aspects(data.get("aspects", []))
    planets_table = planets_table_markdown(data.get("positions", []))
    houses_table = houses_table_markdown(data.get("houses", []))
    aspects_table = aspects_table_markdown(aspects)

    lines = [
        "---",
        "tags: [chart, natal, obsidian-export]",
        f"chart_id: {metadata.get('chart_id', chart_id)}",
        f"birth_date: {birth_date}",
        f"birth_time: {birth_time}",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        "---",
        "",
        f"# Natal Chart: {metadata.get('display_name', chart_id)}",
        "",
        "## Birth Data",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Date | {birth_date} |",
        f"| Time | {birth_time} ({birth.get('timezone', 'unknown')}) |",
        f"| UTC | {birth.get('utc_datetime', 'unknown')} |",
        f"| Location | {location.get('latitude', '')}, {location.get('longitude', '')} |",
        "",
        "## Planetary Positions",
        "",
        planets_table.strip(),
        "",
        "## House Cusps",
        "",
        houses_table.strip(),
        "",
        "## Major Aspects",
        "",
        aspects_table.strip(),
        "",
        "## Related",
        "",
        f"- [[{chart_id}_canvas.json]]",
        f"- [[{chart_id}_planets_table.md]]",
        "- [[attachments/chart_wheel.svg]]",
        "- [[attachments/aspect_grid.svg]]",
    ]
    return "\n".join(lines) + "\n", planets_table


def build_canvas(chart_id, metadata):
    display_name = metadata.get("display_name", chart_id)
    canvas = {
        "nodes": [
            {
                "id": "n_meta",
                "type": "text",
                "x": 40,
                "y": 40,
                "width": 420,
                "height": 180,
                "text": f"# {display_name}\nChart ID: {chart_id}\n\nUse linked file nodes to open wheel/grid.",
            },
            {
                "id": "n_wheel",
                "type": "file",
                "x": 520,
                "y": 40,
                "width": 700,
                "height": 700,
                "file": "attachments/chart_wheel.svg",
            },
            {
                "id": "n_grid",
                "type": "file",
                "x": 520,
                "y": 780,
                "width": 700,
                "height": 520,
                "file": "attachments/aspect_grid.svg",
            },
            {
                "id": "n_table",
                "type": "file",
                "x": 40,
                "y": 260,
                "width": 420,
                "height": 480,
                "file": f"{chart_id}_planets_table.md",
            },
        ],
        "edges": [],
    }
    return canvas


def copy_attachments(outputs_dir: Path, target_attachments: Path):
    target_attachments.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ("chart_wheel.svg", "aspect_grid.svg"):
        src = outputs_dir / name
        if src.exists():
            shutil.copy2(src, target_attachments / name)
            copied.append(name)
    return copied


def generate_bundle(chart_id: str, output_root: Path):
    chart_dir = Path("charts") / chart_id
    data = load_chart_data(chart_dir)

    output_root.mkdir(parents=True, exist_ok=True)
    out_dir = output_root / chart_id
    out_dir.mkdir(parents=True, exist_ok=True)

    note_md, table_md = build_note(chart_id, data)
    note_path = out_dir / f"{chart_id}_natal.md"
    table_path = out_dir / f"{chart_id}_planets_table.md"
    canvas_path = out_dir / f"{chart_id}_canvas.json"
    attachments_dir = out_dir / "attachments"

    note_path.write_text(note_md, encoding="utf-8")
    table_path.write_text(table_md, encoding="utf-8")
    canvas_path.write_text(json.dumps(build_canvas(chart_id, data["metadata"]), ensure_ascii=False, indent=2), encoding="utf-8")
    copied = copy_attachments(data["outputs_dir"], attachments_dir)

    print(f"Generated: {note_path}")
    print(f"Generated: {table_path}")
    print(f"Generated: {canvas_path}")
    print(f"Attachments: {', '.join(copied) if copied else 'none'}")
    return {
        "note": note_path,
        "table": table_path,
        "canvas": canvas_path,
        "attachments": copied,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Obsidian note/canvas/table from chart")
    parser.add_argument("--chart-id", required=True, help="Chart ID")
    parser.add_argument("--output", default="artifacts/skill-smoke/obsidian", help="Output root directory")
    args = parser.parse_args()

    generate_bundle(args.chart_id, Path(args.output))


if __name__ == "__main__":
    main()
