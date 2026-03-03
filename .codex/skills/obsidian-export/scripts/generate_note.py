#!/usr/bin/env python3
"""
Generate Obsidian note from chart data.

Usage:
    python generate_note.py --chart-id tuapse_19820613_133910 --output obsidian/
"""

import yaml
import csv
import json
import os
from pathlib import Path
from datetime import datetime


def split_local_datetime(value):
    """Return (date, time) from YAML datetime/string value."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d'), value.strftime('%H:%M:%S')

    text = str(value or '').strip()
    if not text:
        return 'unknown', 'unknown'
    parts = text.split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], 'unknown'


def load_chart_data(chart_dir):
    """Load all chart data."""
    data = {}
    
    # Load chart.yaml
    chart_yaml = chart_dir / "chart.yaml"
    if chart_yaml.exists():
        with open(chart_yaml, 'r', encoding='utf-8') as f:
            data['metadata'] = yaml.safe_load(f)
    
    # Load positions
    positions_file = chart_dir / "outputs" / "planets_primary.csv"
    if positions_file.exists():
        data['positions'] = []
        with open(positions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data['positions'].append(dict(row))
    
    # Load houses
    houses_file = chart_dir / "outputs" / "houses_placidus.csv"
    if houses_file.exists():
        data['houses'] = []
        with open(houses_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data['houses'].append(dict(row))
    
    # Load aspects
    aspects_file = chart_dir / "outputs" / "natal_aspects.json"
    if aspects_file.exists():
        # Some generated JSON files include UTF-8 BOM; utf-8-sig handles both forms.
        with open(aspects_file, 'r', encoding='utf-8-sig') as f:
            data['aspects'] = json.load(f)
    
    return data


def generate_frontmatter(metadata):
    """Generate Obsidian frontmatter."""
    birth = metadata.get('birth', {})
    location = metadata.get('location', {})
    birth_date, birth_time = split_local_datetime(birth.get('local_datetime', ''))
    
    return f"""---
tags: [chart, natal]
chart_id: {metadata.get('chart_id', 'unknown')}
birth_date: {birth_date}
birth_time: {birth_time}
birth_place: {metadata.get('display_name', 'Unknown')}
created: {datetime.now().strftime('%Y-%m-%d')}
---
"""


def generate_positions_table(positions):
    """Generate planetary positions markdown table."""
    if not positions:
        return ""
    
    lines = ["| Planet | Longitude | Sign | Degree | House | Retrograde |",
             "|---|---|---|---|---|---|"]
    
    for p in positions:
        retro = "R" if p.get('retrograde', 'false').lower() == 'true' else ""
        lines.append(f"| {p.get('name', '')} | {p.get('longitude', '')}° | {p.get('sign', '')} | {p.get('sign_degree', '')}° | {p.get('house', '')} | {retro} |")
    
    return "\n".join(lines) + "\n"


def generate_houses_table(houses):
    """Generate house cusps markdown table."""
    if not houses:
        return ""
    
    angle_names = {1: 'ASC', 4: 'IC', 7: 'DSC', 10: 'MC'}
    
    lines = ["| House | Cusp | Sign | Degree |",
             "|---|---|---|---|"]
    
    for h in houses:
        num = int(h.get('number', 0))
        angle = angle_names.get(num, '')
        angle_str = f" ({angle})" if angle else ""
        lines.append(f"| {num}{angle_str} | {h.get('cusp', '')}° | {h.get('sign', '')} | {h.get('cusp_degree', '')}° |")
    
    return "\n".join(lines) + "\n"


def generate_aspects_table(aspects):
    """Generate aspects markdown table."""
    if not aspects:
        return ""

    if isinstance(aspects, dict):
        aspects = aspects.get('aspects', [])
    
    lines = ["| Planet 1 | Planet 2 | Aspect | Angle | Orb | Applying |",
             "|---|---|---|---|---|---|"]
    
    for a in aspects:
        if not isinstance(a, dict):
            continue
        applying = "Yes" if a.get('applying', False) else "No"
        p1 = a.get('planet1', a.get('body1', ''))
        p2 = a.get('planet2', a.get('body2', ''))
        aspect_type = a.get('type', a.get('aspect', ''))
        lines.append(f"| {p1} | {p2} | {aspect_type} | {a.get('angle', '')}° | {a.get('orb', '')}° | {applying} |")
    
    return "\n".join(lines) + "\n"


def generate_note(chart_id, output_dir):
    """Generate complete Obsidian note."""
    
    chart_dir = Path(f"charts/{chart_id}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    data = load_chart_data(chart_dir)
    
    if not data.get('metadata'):
        print(f"ERROR: chart.yaml not found for {chart_id}")
        return None
    
    metadata = data['metadata']
    
    # Generate note content
    content = generate_frontmatter(metadata)
    content += f"\n# Natal Chart: {metadata.get('display_name', chart_id)}\n\n"
    
    # Birth data
    birth = metadata.get('birth', {})
    location = metadata.get('location', {})
    birth_date, birth_time = split_local_datetime(birth.get('local_datetime', ''))
    content += "## Birth Data\n\n"
    content += f"| Field | Value |\n|---|---|\n"
    content += f"| Date | {birth_date} |\n"
    content += f"| Time | {birth_time} ({birth.get('timezone', 'unknown')}) |\n"
    content += f"| UTC | {birth.get('utc_datetime', 'unknown')} |\n"
    content += f"| Location | {location.get('latitude', '')}, {location.get('longitude', '')} |\n\n"
    
    # Planetary positions
    content += "## Planetary Positions\n\n"
    content += generate_positions_table(data.get('positions', []))
    content += "\n"
    
    # House cusps
    content += "## House Cusps (Placidus)\n\n"
    content += generate_houses_table(data.get('houses', []))
    content += "\n"
    
    # Aspects
    content += "## Major Aspects\n\n"
    content += generate_aspects_table(data.get('aspects', []))
    content += "\n"
    
    # Analysis notes section
    content += "## Analysis Notes\n\n<!-- Add interpretation notes here -->\n\n"
    
    # Related files
    content += "## Related Files\n\n"
    content += f"- [[{chart_id}_canvas.json]]\n"
    content += "- [[chart_wheel.svg]]\n"
    content += "- [[aspect_grid.svg]]\n"
    content += "- [[PACK_MANIFEST.yaml]]\n"
    
    # Write file
    output_file = output_dir / f"{chart_id}_natal.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated: {output_file}")
    return output_file


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Obsidian note from chart')
    parser.add_argument('--chart-id', required=True, help='Chart ID')
    parser.add_argument('--output', default='obsidian', help='Output directory')
    
    args = parser.parse_args()
    
    generate_note(args.chart_id, args.output)
