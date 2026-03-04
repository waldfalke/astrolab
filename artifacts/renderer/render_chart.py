#!/usr/bin/env python3
import argparse
import csv
import json
import math
from pathlib import Path

PLANET_ORDER = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

SIGN_SYMBOLS = {
    "Aries": "Ar", "Taurus": "Ta", "Gemini": "Ge", "Cancer": "Ca", "Leo": "Le", "Virgo": "Vi",
    "Libra": "Li", "Scorpio": "Sc", "Sagittarius": "Sg", "Capricorn": "Cp", "Aquarius": "Aq", "Pisces": "Pi",
}


def load_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_aspects(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict) and "aspects" in data:
        return data["aspects"]
    if isinstance(data, list):
        return data
    return []


def lon_to_xy(center, radius, lon):
    ang = math.radians((90.0 - lon) % 360.0)
    return center + radius * math.cos(ang), center - radius * math.sin(ang)


def svg_header(size):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]


def draw_wheel(planets, houses, points, aspects, out_path: Path):
    size = 1200
    c = size / 2
    outer = 520
    sign_ring = 470
    planet_r = 405
    aspect_r = 320

    lines = svg_header(size)
    lines.append('<style>text{font-family:Consolas,Menlo,monospace;fill:#1f2937} .small{font-size:14px} .mid{font-size:18px} .bold{font-weight:700}</style>')

    lines.append(f'<circle cx="{c}" cy="{c}" r="{outer}" fill="none" stroke="#111827" stroke-width="3"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{sign_ring}" fill="none" stroke="#6b7280" stroke-width="1.5"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{planet_r-20}" fill="none" stroke="#d1d5db" stroke-width="1"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{aspect_r}" fill="none" stroke="#d1d5db" stroke-width="1"/>')

    for i in range(12):
        lon = i * 30.0
        x1, y1 = lon_to_xy(c, sign_ring, lon)
        x2, y2 = lon_to_xy(c, outer, lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#9ca3af" stroke-width="1"/>')
        mid = lon + 15.0
        tx, ty = lon_to_xy(c, (outer + sign_ring) / 2, mid)
        sign = list(SIGN_SYMBOLS.keys())[i]
        lines.append(f'<text class="small" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">{SIGN_SYMBOLS[sign]}</text>')

    house_rows = sorted((h for h in houses if h.get("longitude")), key=lambda x: int(float(x.get("house", 0))))
    for h in house_rows:
        lon = float(h["longitude"])
        x1, y1 = lon_to_xy(c, planet_r - 30, lon)
        x2, y2 = lon_to_xy(c, outer, lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#4b5563" stroke-width="1.2"/>')
        tx, ty = lon_to_xy(c, outer + 18, lon)
        lines.append(f'<text class="small" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">H{int(float(h["house"]))}</text>')

    pmap = {}
    for p in planets:
        if not p.get("body") or not p.get("longitude"):
            continue
        body = p["body"].strip().lower()
        lon = float(p["longitude"])
        pmap[body] = lon

    aspect_colors = {
        "conjunction": "#111827",
        "sextile": "#2563eb",
        "square": "#dc2626",
        "trine": "#16a34a",
        "opposition": "#7c3aed",
    }
    for a in aspects:
        b1 = str(a.get("body1", "")).lower()
        b2 = str(a.get("body2", "")).lower()
        if b1 not in pmap or b2 not in pmap:
            continue
        x1, y1 = lon_to_xy(c, aspect_r, pmap[b1])
        x2, y2 = lon_to_xy(c, aspect_r, pmap[b2])
        col = aspect_colors.get(str(a.get("aspect", "")).lower(), "#6b7280")
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="1.2" opacity="0.9"/>')

    for idx, body in enumerate(PLANET_ORDER):
        if body not in pmap:
            continue
        lon = pmap[body]
        r = planet_r + (idx % 3) * 10
        x, y = lon_to_xy(c, r, lon)
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#111827"/>')
        lines.append(f'<text class="small bold" x="{x:.2f}" y="{y+0.5:.2f}" text-anchor="middle" dominant-baseline="middle" fill="#ffffff">{body[:2].upper()}</text>')

    angle_map = {"ascendant": "ASC", "midheaven": "MC", "descendant": "DSC", "ic": "IC"}
    for p in points:
        name = str(p.get("point", "")).strip().lower()
        if name not in angle_map or not p.get("longitude"):
            continue
        lon = float(p["longitude"])
        x, y = lon_to_xy(c, outer + 40, lon)
        lines.append(f'<text class="mid bold" x="{x:.2f}" y="{y:.2f}" text-anchor="middle" dominant-baseline="middle">{angle_map[name]}</text>')

    lines.append('<text class="mid bold" x="40" y="42">CATMEastrolab Renderer MVP</text>')
    lines.append('</svg>')
    out_path.write_text("\n".join(lines), encoding="utf-8")


def draw_aspect_grid(planets, aspects, out_path: Path):
    names = [p.get("body", "").lower() for p in planets if p.get("body")]
    order = [n for n in PLANET_ORDER if n in names]
    size = 900
    margin = 120
    n = max(1, len(order))
    cell = (size - margin - 40) / n

    aspect_lookup = {}
    for a in aspects:
        b1 = str(a.get("body1", "")).lower()
        b2 = str(a.get("body2", "")).lower()
        asp = str(a.get("aspect", "")).lower()
        if b1 and b2 and asp:
            aspect_lookup[(b1, b2)] = asp
            aspect_lookup[(b2, b1)] = asp

    symbol = {"conjunction": "0", "sextile": "60", "square": "90", "trine": "120", "opposition": "180"}
    color = {"conjunction": "#111827", "sextile": "#2563eb", "square": "#dc2626", "trine": "#16a34a", "opposition": "#7c3aed"}

    lines = svg_header(size)
    lines.append('<style>text{font-family:Consolas,Menlo,monospace;fill:#111827} .lbl{font-size:14px} .val{font-size:13px;font-weight:700}</style>')
    lines.append(f'<text x="30" y="40" font-size="22" font-family="Consolas,Menlo,monospace" fill="#111827">Aspect Grid</text>')

    for i, b in enumerate(order):
        x = margin + i * cell + cell / 2
        lines.append(f'<text class="lbl" x="{x:.2f}" y="85" text-anchor="middle">{b[:3].upper()}</text>')
        y = margin + i * cell + cell / 2
        lines.append(f'<text class="lbl" x="85" y="{y:.2f}" text-anchor="middle" dominant-baseline="middle">{b[:3].upper()}</text>')

    for i, bi in enumerate(order):
        for j, bj in enumerate(order):
            x = margin + j * cell
            y = margin + i * cell
            fill = "#f9fafb" if i == j else "#ffffff"
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" fill="{fill}" stroke="#d1d5db"/>')
            if i >= j:
                continue
            asp = aspect_lookup.get((bi, bj))
            if not asp:
                continue
            tx = x + cell / 2
            ty = y + cell / 2
            col = color.get(asp, "#374151")
            text = symbol.get(asp, asp[:3].upper())
            lines.append(f'<text class="val" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle" fill="{col}">{text}</text>')

    lines.append('</svg>')
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Render chart wheel and aspect grid from chart outputs")
    parser.add_argument("--chart-dir", required=True, help="Path to charts/<chart_id>")
    parser.add_argument("--output-dir", required=True, help="Renderer run output dir")
    args = parser.parse_args()

    chart_dir = Path(args.chart_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out = chart_dir / "outputs"
    planets = load_csv(out / "planets_primary.csv")
    houses = load_csv(out / "houses_placidus.csv")
    points = load_csv(out / "chart_points.csv")
    aspects = load_aspects(out / "natal_aspects.json")

    wheel_path = output_dir / "01_chart_wheel.svg"
    grid_path = output_dir / "02_aspect_grid.svg"
    manifest_path = output_dir / "03_render_manifest.json"

    draw_wheel(planets, houses, points, aspects, wheel_path)
    draw_aspect_grid(planets, aspects, grid_path)

    manifest = {
        "renderer": "catme-svg-mvp",
        "chart_dir": str(chart_dir),
        "inputs": {
            "planets": str(out / "planets_primary.csv"),
            "houses": str(out / "houses_placidus.csv"),
            "points": str(out / "chart_points.csv"),
            "aspects": str(out / "natal_aspects.json"),
        },
        "outputs": {
            "chart_wheel_svg": "01_chart_wheel.svg",
            "aspect_grid_svg": "02_aspect_grid.svg",
        },
        "counts": {
            "planets": len(planets),
            "houses": len(houses),
            "points": len(points),
            "aspects": len(aspects),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
