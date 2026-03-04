#!/usr/bin/env python3
"""
Validate chart project files against JSON schemas.

Usage:
    python validate_chart.py --chart-id tuapse_19820613_133910
    python validate_chart.py --chart-dir charts/tuapse_19820613_133910
"""

import json
import yaml
import os
import sys
from pathlib import Path

# Schema paths
SCHEMA_ROOT = "artifacts/schemas/chart-project"
CHART_SCHEMA = os.path.join(SCHEMA_ROOT, "chart.schema.v1.json")
INDEX_SCHEMA = os.path.join(SCHEMA_ROOT, "index.schema.v1.json")


def load_yaml(path):
    """Load YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_schema(path):
    """Load JSON schema."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_chart_yaml(data, schema):
    """Validate chart.yaml against schema."""
    errors = []
    
    # Check required top-level keys
    required = schema.get('required_top_level_keys', [])
    for key in required:
        if key not in data:
            errors.append({
                'path': key,
                'message': f'Missing required key: {key}',
                'severity': 'ERROR'
            })
    
    # Check nested keys
    nested_required = schema.get('required_nested_keys', {})
    for section, keys in nested_required.items():
        if section in data and isinstance(data[section], dict):
            for key in keys:
                if key not in data[section]:
                    errors.append({
                        'path': f'{section}.{key}',
                        'message': f'Missing required key: {key}',
                        'severity': 'ERROR'
                    })
    
    # Validate timezone format
    if 'birth' in data and 'timezone' in data['birth']:
        tz = data['birth']['timezone']
        import re
        if not re.match(r'^[+-]\d{2}:\d{2}$', tz):
            errors.append({
                'path': 'birth.timezone',
                'message': f'Invalid timezone format: {tz}. Use +04:00 not +4',
                'severity': 'ERROR'
            })
    
    # Validate lat/lon
    if 'location' in data:
        lat = data['location'].get('latitude', 0)
        lon = data['location'].get('longitude', 0)
        if not (-90 <= lat <= 90):
            errors.append({
                'path': 'location.latitude',
                'message': f'Latitude {lat} out of range (-90 to 90)',
                'severity': 'ERROR'
            })
        if not (-180 <= lon <= 180):
            errors.append({
                'path': 'location.longitude',
                'message': f'Longitude {lon} out of range (-180 to 180)',
                'severity': 'ERROR'
            })
    
    return errors


def check_provenance(chart_dir, index_data):
    """Check that all canonical_source paths exist."""
    errors = []
    
    # Check methods
    for method in index_data.get('raw_methods', []):
        method_path = os.path.join(chart_dir, method.get('canonical_run_dir', ''))
        if not os.path.isdir(method_path):
            errors.append({
                'path': method.get('canonical_run_dir'),
                'message': f'Method directory not found: {method_path}',
                'severity': 'ERROR'
            })
    
    # Check outputs
    for output in index_data.get('outputs', []):
        output_path = os.path.join(chart_dir, output.get('canonical_source', ''))
        if not os.path.isfile(output_path):
            errors.append({
                'path': output.get('canonical_source'),
                'message': f'Output file not found: {output_path}',
                'severity': 'ERROR'
            })
    
    return errors


def validate_chart_project(chart_id=None, chart_dir=None):
    """Main validation function."""
    
    # Resolve chart directory
    if chart_dir:
        chart_dir = Path(chart_dir).resolve()
    elif chart_id:
        chart_dir = Path(f"charts/{chart_id}").resolve()
    else:
        print("ERROR: Provide --chart-id or --chart-dir")
        return {'valid': False, 'errors': [{'message': 'No chart specified'}]}
    
    if not chart_dir.exists():
        return {'valid': False, 'errors': [{'message': f'Chart directory not found: {chart_dir}'}]}
    
    # Load files
    chart_yaml_path = chart_dir / "chart.yaml"
    index_yaml_path = chart_dir / "INDEX.yaml"
    
    if not chart_yaml_path.exists():
        return {'valid': False, 'errors': [{'message': 'chart.yaml not found'}]}
    
    if not index_yaml_path.exists():
        return {'valid': False, 'errors': [{'message': 'INDEX.yaml not found'}]}
    
    # Load schemas
    chart_schema = load_schema(CHART_SCHEMA)
    
    # Validate chart.yaml
    chart_data = load_yaml(chart_yaml_path)
    chart_errors = validate_chart_yaml(chart_data, chart_schema)
    
    # Validate INDEX.yaml
    index_data = load_yaml(index_yaml_path)
    index_errors = []  # Add INDEX validation if needed
    
    # Check provenance
    provenance_errors = check_provenance(str(chart_dir), index_data)
    
    # Combine results
    all_errors = chart_errors + index_errors + provenance_errors
    
    return {
        'valid': len(all_errors) == 0,
        'errors': all_errors,
        'chart_id': chart_data.get('chart_id', chart_id),
        'chart_yaml_valid': len(chart_errors) == 0,
        'provenance_valid': len(provenance_errors) == 0
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate chart project')
    parser.add_argument('--chart-id', help='Chart ID')
    parser.add_argument('--chart-dir', help='Chart directory path')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    
    args = parser.parse_args()
    
    result = validate_chart_project(chart_id=args.chart_id, chart_dir=args.chart_dir)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['valid']:
            print(f"✓ VALID: {result['chart_id']}")
        else:
            print(f"✗ INVALID: {result['chart_id']}")
            for err in result['errors']:
                print(f"  - {err['path']}: {err['message']}")
    
    sys.exit(0 if result['valid'] else 1)
