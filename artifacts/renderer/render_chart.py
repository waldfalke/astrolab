#!/usr/bin/env python3
import argparse
import csv
import json
import math
import html
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

HOUSE_ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
}

FONT_STACK_TEXT = '"Noto Sans","Segoe UI","DejaVu Sans",Arial,sans-serif'
FONT_STACK_SYMBOL = '"Noto Sans Symbols 2","Noto Sans Symbols","Segoe UI Symbol","DejaVu Sans","Noto Sans","Segoe UI",sans-serif'


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


def distribute_label_positions(nodes, top, bottom, min_gap):
    if not nodes:
        return
    nodes.sort(key=lambda n: n["target_y"])
    y = top
    for n in nodes:
        half_h = n.get("half_h", 0.0)
        min_center = y + half_h
        n["y"] = max(n["target_y"], min_center)
        y = n["y"] + half_h + min_gap
    y = bottom
    for n in reversed(nodes):
        half_h = n.get("half_h", 0.0)
        max_center = y - half_h
        n["y"] = min(n["y"], max_center)
        y = n["y"] - half_h - min_gap


def distribute_label_positions_x(nodes, left, right, min_gap):
    if not nodes:
        return
    nodes.sort(key=lambda n: n["target_x"])
    x = left
    for n in nodes:
        n["x"] = max(n["target_x"], x)
        x = n["x"] + min_gap
    x = right
    for n in reversed(nodes):
        n["x"] = min(n["x"], x)
        x = n["x"] - min_gap


def distribute_label_positions_x_with_width(nodes, left, right, min_gap):
    if not nodes:
        return
    nodes.sort(key=lambda n: n["target_x"])
    cursor = left
    for n in nodes:
        half_w = n.get("half_w", 20.0)
        min_center = cursor + half_w
        n["x"] = max(n["target_x"], min_center)
        cursor = n["x"] + half_w + min_gap
    cursor = right
    for n in reversed(nodes):
        half_w = n.get("half_w", 20.0)
        max_center = cursor - half_w
        n["x"] = min(n["x"], max_center)
        cursor = n["x"] - half_w - min_gap
    # Final strict spacing pass: preserve at least min_gap between badge boxes.
    nodes.sort(key=lambda n: n["x"])
    for i in range(1, len(nodes)):
        prev = nodes[i - 1]
        cur = nodes[i]
        needed = prev["x"] + prev.get("half_w", 20.0) + min_gap + cur.get("half_w", 20.0)
        if cur["x"] < needed:
            cur["x"] = needed


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


def wheel_style():
    return (
        f'<style>'
        f'text{{font-family:{FONT_STACK_TEXT};fill:#1f2937;font-weight:500}} '
        f'.txtbg{{fill:#ffffff;opacity:0.98;stroke:#d1d5db;stroke-width:1}} '
        f'.small{{font-size:13px}} .mid{{font-size:22px;font-family:{FONT_STACK_SYMBOL};font-weight:500}} '
        f'.bold{{font-weight:600}} '
        f'.plabel{{font-size:13px;font-weight:600;font-family:{FONT_STACK_SYMBOL};paint-order:stroke;stroke:#ffffff;stroke-width:3;stroke-linejoin:round;}}'
        f'</style>'
    )


def grid_style():
    return (
        f'<style>'
        f'text{{font-family:{FONT_STACK_TEXT};fill:#111827;font-weight:500}} '
        f'.lbl{{font-size:14px;font-family:{FONT_STACK_SYMBOL};font-weight:500}} '
        f'.val{{font-size:13px;font-weight:600}}'
        f'</style>'
    )


def text_width_px(text, font_size):
    # Practical approximation for sans fonts in SVG.
    return max(font_size * 0.9, len(text) * font_size * 0.74)


def add_text_with_bg(lines, text, x, y, cls, anchor="middle", baseline="middle", font_size=13, pad=2, layer=None):
    target = layer if layer is not None else lines
    safe = html.escape(text)
    w = text_width_px(text, font_size)
    h = font_size * 1.28
    # Badge-like layout: text is always centered in the rounded rect.
    rx = x - w / 2 - pad
    ry = y - h / 2 - pad
    rw = w + pad * 2
    rh = h + pad * 2
    target.append(f'<rect class="txtbg" x="{rx:.2f}" y="{ry:.2f}" width="{rw:.2f}" height="{rh:.2f}" rx="8" ry="8"/>')
    target.append(f'<text class="{cls}" x="{x:.2f}" y="{y:.2f}" text-anchor="middle" dominant-baseline="middle">{safe}</text>')


def draw_wheel(planets, houses, points, aspects, out_path: Path):
    size = 1500
    c = size / 2
    outer = 520
    sign_ring = 470
    planet_r = 405
    aspect_r = 320

    lines = svg_header(size)
    lines.append(wheel_style())
    badge_layer = []

    asc_lon = 0.0
    for p in points:
        if str(p.get("point", "")).strip().lower() == "ascendant" and p.get("longitude"):
            asc_lon = float(p["longitude"])
            break

    lines.append(f'<circle cx="{c}" cy="{c}" r="{outer}" fill="none" stroke="#111827" stroke-width="3"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{sign_ring}" fill="none" stroke="#6b7280" stroke-width="1.5"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{planet_r-20}" fill="none" stroke="#d1d5db" stroke-width="1"/>')
    lines.append(f'<circle cx="{c}" cy="{c}" r="{aspect_r}" fill="none" stroke="#d1d5db" stroke-width="1"/>')

    # Keep zodiac signs on the classical sign ring band (between two outer circles).
    sign_label_r = (outer + sign_ring) / 2.0
    for i in range(12):
        lon = i * 30.0
        x1, y1 = lon_to_xy(c, sign_ring, lon, asc_lon=asc_lon)
        x2, y2 = lon_to_xy(c, outer, lon, asc_lon=asc_lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#9ca3af" stroke-width="1"/>')
        mid = lon + 15.0
        tx, ty = lon_to_xy(c, sign_label_r, mid, asc_lon=asc_lon)
        sign = list(SIGN_SYMBOLS.keys())[i]
        lines.append(f'<text class="mid" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">{SIGN_SYMBOLS[sign]}</text>')

    house_rows = sorted((h for h in houses if h.get("longitude")), key=lambda x: int(float(x.get("house", 0))))
    angle_house_labels = {1: "ASC", 4: "IC", 7: "DSC", 10: "MC"}
    sign_order = list(SIGN_SYMBOLS.keys())
    house_nodes_left = []
    house_nodes_right = []
    house_nodes_top = []
    house_nodes_bottom = []
    house_badge_font = 13
    house_badge_pad = 2
    house_half_h = (house_badge_font * 1.28 + house_badge_pad * 2) / 2.0
    house_side_x = outer + 34
    house_side_y = outer + 34
    for h in house_rows:
        house_num = int(float(h["house"]))
        lon = float(h["longitude"])
        x1, y1 = lon_to_xy(c, planet_r - 30, lon, asc_lon=asc_lon)
        x2, y2 = lon_to_xy(c, outer, lon, asc_lon=asc_lon)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#4b5563" stroke-width="1.2"/>')
        tx, ty = lon_to_xy(c, outer + 28, lon, asc_lon=asc_lon)
        sign_idx = int((lon % 360.0) // 30.0)
        sign_name = sign_order[sign_idx]
        sign_glyph = SIGN_SYMBOLS[sign_name]
        deg_label = format_deg_min(lon % 30.0)
        house_label = angle_house_labels.get(house_num, HOUSE_ROMAN.get(house_num, str(house_num)))
        label = f"{house_label} {sign_glyph} {deg_label}"
        angle_y_shift = {1: 26.0, 4: 14.0, 7: -26.0, 10: -14.0}
        node = {
            "label": label,
            "ax": x2,
            "ay": y2,
            "target_x": tx,
            "target_y": ty + angle_y_shift.get(house_num, 0.0),
            "x": tx,
            "y": ty + angle_y_shift.get(house_num, 0.0),
            "half_w": text_width_px(label, house_badge_font) / 2.0 + house_badge_pad,
            "half_h": house_half_h,
            "font_size": house_badge_font,
            "pad": house_badge_pad,
        }
        dx = tx - c
        dy = ty - c
        if abs(dx) >= abs(dy) and dx >= 0:
            node["x"] = c + house_side_x
            house_nodes_right.append(node)
        elif abs(dx) >= abs(dy) and dx < 0:
            node["x"] = c - house_side_x
            house_nodes_left.append(node)
        elif dy < 0:
            node["y"] = c - house_side_y
            house_nodes_top.append(node)
        else:
            node["y"] = c + house_side_y
            house_nodes_bottom.append(node)

    distribute_label_positions(house_nodes_left, 90, size - 90, 8)
    distribute_label_positions(house_nodes_right, 90, size - 90, 8)
    distribute_label_positions_x_with_width(house_nodes_top, 80, size - 80, 8)
    distribute_label_positions_x_with_width(house_nodes_bottom, 80, size - 80, 8)
    for node in house_nodes_left + house_nodes_right + house_nodes_top + house_nodes_bottom:
        lines.append(
            f'<line x1="{node["ax"]:.2f}" y1="{node["ay"]:.2f}" x2="{node["x"]:.2f}" y2="{node["y"]:.2f}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        add_text_with_bg(
            lines,
            node["label"],
            node["x"],
            node["y"],
            cls="small",
            anchor="middle",
            baseline="middle",
            font_size=node["font_size"],
            pad=node["pad"],
            layer=badge_layer,
        )

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

    # Infographic-style callouts on 4 sides of a frame (not just 2 columns).
    label_r = outer + 26
    margin_x = 80
    margin_y = 60
    side_x = outer + 90
    side_y = outer + 90
    min_gap = 4
    badge_font = 13
    badge_pad = 2
    badge_half_h = (badge_font * 1.28 + badge_pad * 2) / 2.0
    left_nodes = []
    right_nodes = []
    top_nodes = []
    bottom_nodes = []
    for row in planet_rows:
        body = row["body"]
        lon = row["lon"]
        mx, my = lon_to_xy(c, planet_r, lon, asc_lon=asc_lon)
        ex, ey = lon_to_xy(c, label_r, lon, asc_lon=asc_lon)

        symbol = PLANET_GLYPHS.get(body, body[:2].title())
        sign_glyph = SIGN_SYMBOLS.get(row["sign"], row["sign"][:2])
        deg_min = format_deg_min(row["degree"])
        retro = " R" if row["retro"] else ""
        label = f"{symbol} {sign_glyph} {deg_min}{retro}"

        dx = ex - c
        dy = ey - c
        node = {
            "mx": mx,
            "my": my,
            "ex": ex,
            "ey": ey,
            "lon": lon,
            "target_x": ex,
            "target_y": ey,
            "x": ex,
            "y": ey,
            "label": label,
            "half_w": text_width_px(label, 13) / 2.0 + badge_pad,
            "half_h": badge_half_h,
        }
        if abs(dx) >= abs(dy) and dx >= 0:
            node["side"] = "right"
            node["x"] = c + side_x
            right_nodes.append(node)
        elif abs(dx) >= abs(dy) and dx < 0:
            node["side"] = "left"
            node["x"] = c - side_x
            left_nodes.append(node)
        elif dy < 0:
            node["side"] = "top"
            node["y"] = c - side_y
            top_nodes.append(node)
        else:
            node["side"] = "bottom"
            node["y"] = c + side_y
            bottom_nodes.append(node)

    distribute_label_positions(left_nodes, margin_y, size - margin_y, min_gap)
    distribute_label_positions(right_nodes, margin_y, size - margin_y, min_gap)
    distribute_label_positions_x_with_width(top_nodes, margin_x, size - margin_x, min_gap)
    distribute_label_positions_x_with_width(bottom_nodes, margin_x, size - margin_x, min_gap)

    for node in left_nodes + right_nodes + top_nodes + bottom_nodes:
        mx, my = node["mx"], node["my"]
        ex, ey = node["ex"], node["ey"]
        lx, ly = node["x"], node["y"]
        ix, iy = lon_to_xy(c, aspect_r, node["lon"], asc_lon=asc_lon)

        # Dotted guide from planet marker to exact point on inner planet arc.
        lines.append(
            f'<line x1="{mx:.2f}" y1="{my:.2f}" x2="{ix:.2f}" y2="{iy:.2f}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        if node["side"] == "right":
            elbow_x = lx - 24
            elbow_y = ly
            anchor = "middle"
            tx = lx
            ty = ly
        elif node["side"] == "left":
            elbow_x = lx + 24
            elbow_y = ly
            anchor = "middle"
            tx = lx
            ty = ly
        elif node["side"] == "top":
            elbow_x = lx
            elbow_y = ly + 20
            anchor = "middle"
            tx = lx
            ty = ly
        else:
            elbow_x = lx
            elbow_y = ly - 20
            anchor = "middle"
            tx = lx
            ty = ly

        lines.append(f'<line x1="{mx:.2f}" y1="{my:.2f}" x2="{ex:.2f}" y2="{ey:.2f}" stroke="#9ca3af" stroke-width="1"/>')
        lines.append(
            f'<polyline points="{ex:.2f},{ey:.2f} {elbow_x:.2f},{elbow_y:.2f} {lx:.2f},{ly:.2f}" fill="none" stroke="#9ca3af" stroke-width="1"/>'
        )
        lines.append(f'<circle cx="{mx:.2f}" cy="{my:.2f}" r="7" fill="#111827"/>')
        add_text_with_bg(
            lines,
            node["label"],
            tx,
            ty,
            cls="plabel",
            anchor=anchor,
            baseline="middle",
            font_size=badge_font,
            pad=badge_pad,
            layer=badge_layer,
        )

    # Draw all badges last so lines never cut through badge text blocks.
    lines.extend(badge_layer)
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
    lines.append(grid_style())
    lines.append(f'<text x="30" y="40" font-size="22" fill="#111827">Aspect Grid</text>')

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
