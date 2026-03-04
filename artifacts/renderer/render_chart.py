#!/usr/bin/env python3
import argparse
import csv
import json
import math
from pathlib import Path

PLANET_ORDER = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

PLANET_GLYPHS = {
    "sun": "☉",
    "moon": "☽",
    "mercury": "☿",
    "venus": "♀",
    "mars": "♂",
    "jupiter": "♃",
    "saturn": "♄",
    "uranus": "♅",
    "neptune": "♆",
    "pluto": "♇",
}

SIGN_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋", "Leo": "♌", "Virgo": "♍",
    "Libra": "♎", "Scorpio": "♏", "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}


def format_deg_min(value):
    d = float(value)
    deg = int(math.floor(d))
    minutes = int(round((d - deg) * 60.0))
    if minutes == 60:
        deg += 1
        minutes = 0
    return f"{deg:02d}°{minutes:02d}'"


def is_retrograde(row):
    val = str(row.get("retrograde", "")).strip().lower()
    return val in {"true", "1", "yes", "r", "retrograde"}


def cluster_planets_by_longitude(rows, threshold_deg=7.0):
    if not rows:
        return []
    sorted_rows = sorted(rows, key=lambda x: x["lon"])
    clusters = [[sorted_rows[0]]]
    for row in sorted_rows[1:]:
        prev = clusters[-1][-1]
        diff = (row["lon"] - prev["lon"]) % 360.0
        if diff <= threshold_deg:
            clusters[-1].append(row)
        else:
            clusters.append([row])

    if len(clusters) > 1:
        first = clusters[0]
        last = clusters[-1]
        wrap_diff = ((first[0]["lon"] + 360.0) - last[-1]["lon"]) % 360.0
        if wrap_diff <= threshold_deg:
            merged = last + first
            clusters = [merged] + clusters[1:-1]
    return clusters


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


def lon_to_xy(center, radius, lon, asc_lon=0.0):
    # Angle-anchored orientation:
    # Ascendant is fixed to the left (9 o'clock); wheel rotates with chart angles.
    # Longitudes increase clockwise from Asc.
    ang = math.radians((180.0 + (lon - asc_lon)) % 360.0)
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
    lines.append('<style>text{font-family:"Segoe UI Symbol","Noto Sans Symbols 2","Noto Sans Symbols","DejaVu Sans",Consolas,Menlo,monospace;fill:#1f2937} .small{font-size:14px} .mid{font-size:18px} .bold{font-weight:700} .plabel{font-size:13px;font-weight:700;paint-order:stroke;stroke:#ffffff;stroke-width:3;stroke-linejoin:round;}</style>')

    asc_lon = 0.0
    for p in points:
        if str(p.get("point", "")).strip().lower() == "ascendant" and p.get("longitude"):
            asc_lon = float(p["longitude"])
            break

    lines.append(f'<circle cx="{c}" cy="{c}" r="{outer}" fill="none" stroke="#111827" stroke-width="3"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{sign_ring}" fill="none" stroke="#6b7280" stroke-width="1.5"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{planet_r-20}" fill="none" stroke="#d1d5db" stroke-width="1"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{aspect_r}" fill="none" stroke="#d1d5db" stroke-width="1"/>')

    for i in range(12):
        lon = i * 30.0
        x1, y1 = lon_to_xy(c, sign_ring, lon, asc_lon=asc_lon)
        x2, y2 = lon_to_xy(c, outer, lon, asc_lon=asc_lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#9ca3af" stroke-width="1"/>')
        mid = lon + 15.0
        tx, ty = lon_to_xy(c, (outer + sign_ring) / 2, mid, asc_lon=asc_lon)
        sign = list(SIGN_SYMBOLS.keys())[i]
        lines.append(f'<text class="mid" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">{SIGN_SYMBOLS[sign]}</text>')

    house_rows = sorted((h for h in houses if h.get("longitude")), key=lambda x: int(float(x.get("house", 0))))
    for h in house_rows:
        lon = float(h["longitude"])
        x1, y1 = lon_to_xy(c, planet_r - 30, lon, asc_lon=asc_lon)
        x2, y2 = lon_to_xy(c, outer, lon, asc_lon=asc_lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#4b5563" stroke-width="1.2"/>')
        tx, ty = lon_to_xy(c, outer + 18, lon, asc_lon=asc_lon)
        lines.append(f'<text class="small" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">H{int(float(h["house"]))}</text>')

    pmap = {}
    for p in planets:
        if not p.get("body") or not p.get("longitude"):
            continue
        body = p["body"].strip().lower()
        pmap[body] = float(p["longitude"])

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
        x1, y1 = lon_to_xy(c, aspect_r, pmap[b1], asc_lon=asc_lon)
        x2, y2 = lon_to_xy(c, aspect_r, pmap[b2], asc_lon=asc_lon)
        col = aspect_colors.get(str(a.get("aspect", "")).lower(), "#6b7280")
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="1.2" opacity="0.9"/>')

    planet_rows = []
    for p in planets:
        body = str(p.get("body", "")).strip().lower()
        if body not in PLANET_ORDER:
            continue
        if not p.get("longitude"):
            continue
        planet_rows.append(
            {
                "body": body,
                "lon": float(p["longitude"]),
                "sign": str(p.get("sign", "")).strip(),
                "degree": p.get("degree", 0.0),
                "retro": is_retrograde(p),
            }
        )

    clusters = cluster_planets_by_longitude(planet_rows, threshold_deg=7.0)
    for cluster in clusters:
        n = len(cluster)
        for i, row in enumerate(cluster):
            body = row["body"]
            lon = row["lon"]

            ring_offset = i * 18
            mark_r = planet_r + ring_offset
            label_r = mark_r + 28

            mx, my = lon_to_xy(c, mark_r, lon, asc_lon=asc_lon)
            lx, ly = lon_to_xy(c, label_r, lon, asc_lon=asc_lon)

            # Tangential spread for conjunction/stellium readability.
            tx = -(ly - c)
            ty = (lx - c)
            norm = math.hypot(tx, ty) or 1.0
            tx /= norm
            ty /= norm
            spread = (i - (n - 1) / 2.0) * 12.0
            lx += tx * spread
            ly += ty * spread

            symbol = PLANET_GLYPHS.get(body, body[:2].title())
            sign_glyph = SIGN_SYMBOLS.get(row["sign"], row["sign"][:2])
            deg_min = format_deg_min(row["degree"])
            retro = " R" if row["retro"] else ""
            label = f"{symbol} {sign_glyph} {deg_min}{retro}"

            lines.append(f'<line x1="{mx:.2f}" y1="{my:.2f}" x2="{lx:.2f}" y2="{ly:.2f}" stroke="#9ca3af" stroke-width="1"/>')
            lines.append(f'<circle cx="{mx:.2f}" cy="{my:.2f}" r="7" fill="#111827"/>')
            anchor = "start" if lx >= c else "end"
            xpad = 6 if anchor == "start" else -6
            lines.append(f'<text class="plabel" x="{(lx + xpad):.2f}" y="{ly:.2f}" text-anchor="{anchor}" dominant-baseline="middle" fill="#111827">{label}</text>')

    angle_map = {"ascendant": "ASC", "midheaven": "MC", "descendant": "DSC", "ic": "IC"}
    for p in points:
        name = str(p.get("point", "")).strip().lower()
        if name not in angle_map or not p.get("longitude"):
            continue
        lon = float(p["longitude"])
        x, y = lon_to_xy(c, outer + 40, lon, asc_lon=asc_lon)
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
    lines.append('<style>text{font-family:"Segoe UI Symbol","Noto Sans Symbols 2","Noto Sans Symbols","DejaVu Sans",Consolas,Menlo,monospace;fill:#111827} .lbl{font-size:14px} .val{font-size:13px;font-weight:700}</style>')
    lines.append(f'<text x="30" y="40" font-size="22" font-family="Segoe UI Symbol,Consolas,Menlo,monospace" fill="#111827">Aspect Grid</text>')

    for i, b in enumerate(order):
        x = margin + i * cell + cell / 2
        lines.append(f'<text class="lbl" x="{x:.2f}" y="85" text-anchor="middle">{PLANET_GLYPHS.get(b, b[:3].upper())}</text>')
        y = margin + i * cell + cell / 2
        lines.append(f'<text class="lbl" x="85" y="{y:.2f}" text-anchor="middle" dominant-baseline="middle">{PLANET_GLYPHS.get(b, b[:3].upper())}</text>')

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
