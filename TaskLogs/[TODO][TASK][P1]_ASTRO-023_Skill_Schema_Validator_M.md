# Task Log: ASTRO-023 - Skill: schema-validator

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Clear

## Objective

Create the `schema-validator` skill that validates chart-project files against JSON schemas. This skill enforces chart.yaml and INDEX.yaml contracts, checks provenance integrity, and reports conformance violations.

## Skill Location

```
.qwen/skills/schema-validator/
├── SKILL.md
├── scripts/
│   └── validate_json_schema.py
└── references/
    ├── chart-schema-v1.md
    └── index-schema-v1.md
```

## SKILL.md Frontmatter

```yaml
---
name: schema-validator
description: Validates chart.yaml and INDEX.yaml against JSON schemas. Checks file structure, required fields, data types, provenance integrity. Use when user requests "validate chart", "check schema", or before building delivery packs.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  schemas: artifacts/schemas/chart-project/
---
```

## Implementation Steps

### Step 1: Load JSON Schemas

Read schema files:

```python
import json

def load_schema(name):
    with open(f'artifacts/schemas/chart-project/{name}.schema.v1.json', 'r') as f:
        return json.load(f)

chart_schema = load_schema('chart')
index_schema = load_schema('index')
```

### Step 2: Validate chart.yaml

Check against `chart.schema.v1.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["chart_id", "birth", "location", "structure"],
  "properties": {
    "chart_id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$"
    },
    "display_name": {
      "type": "string"
    },
    "birth": {
      "type": "object",
      "required": ["local_datetime", "timezone", "utc_datetime"],
      "properties": {
        "local_datetime": {
          "type": "string",
          "format": "date-time"
        },
        "timezone": {
          "type": "string",
          "pattern": "^[+-]\\d{2}:\\d{2}$|^[A-Z]{3,4}$"
        },
        "utc_datetime": {
          "type": "string",
          "format": "date-time"
        }
      }
    },
    "location": {
      "type": "object",
      "required": ["latitude", "longitude"],
      "properties": {
        "latitude": {
          "type": "number",
          "minimum": -90,
          "maximum": 90
        },
        "longitude": {
          "type": "number",
          "minimum": -180,
          "maximum": 180
        }
      }
    },
    "structure": {
      "type": "object",
      "required": ["methods_dir", "outputs_dir"],
      "properties": {
        "methods_dir": {"type": "string"},
        "outputs_dir": {"type": "string"},
        "packs_dir": {"type": "string"}
      }
    }
  }
}
```

### Step 3: Validate INDEX.yaml

Check against `index.schema.v1.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["chart_id", "generated_at", "raw_methods", "outputs"],
  "properties": {
    "chart_id": {"type": "string"},
    "generated_at": {
      "type": "string",
      "format": "date-time"
    },
    "chart_file": {"type": "string"},
    "provenance_model": {"type": "string"},
    "raw_methods": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["method", "run_name", "project_run_dir", "canonical_run_dir"],
        "properties": {
          "method": {"type": "string"},
          "run_name": {"type": "string"},
          "project_run_dir": {"type": "string"},
          "canonical_run_dir": {"type": "string"},
          "source_run_dir": {"type": "string"},
          "external_source_run_dir": {"type": "string"},
          "external_source_run_exists": {"type": "boolean"},
          "summary": {"type": "object"}
        }
      }
    },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["label", "file", "source", "canonical_source"],
        "properties": {
          "label": {"type": "string"},
          "file": {"type": "string"},
          "source": {"type": "string"},
          "canonical_source": {"type": "string"},
          "external_source": {"type": "string"},
          "external_source_exists": {"type": "boolean"}
        }
      }
    }
  }
}
```

### Step 4: Run Validation

Use jsonschema library:

```python
from jsonschema import validate, ValidationError, Draft7Validator

def validate_file(file_path, schema):
    import yaml
    
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    errors = []
    validator = Draft7Validator(schema)
    
    for error in validator.iter_errors(data):
        errors.append({
            'path': '.'.join(str(p) for p in error.path),
            'message': error.message,
            'validator': error.validator
        })
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'file': file_path
    }
```

### Step 5: Check Provenance Integrity

Verify file paths exist:

```python
import os

def check_provenance_integrity(chart_dir, index_data):
    """Verify all canonical_source paths exist."""
    results = {
        'valid': True,
        'missing_files': [],
        'broken_links': []
    }
    
    # Check methods directories
    for method in index_data.get('raw_methods', []):
        method_path = os.path.join(chart_dir, method['canonical_run_dir'])
        if not os.path.isdir(method_path):
            results['valid'] = False
            results['missing_files'].append(method_path)
    
    # Check output files
    for output in index_data.get('outputs', []):
        output_path = os.path.join(chart_dir, output['canonical_source'])
        if not os.path.isfile(output_path):
            results['valid'] = False
            results['missing_files'].append(output_path)
        
        # Check external source if present
        if output.get('external_source'):
            if not os.path.isfile(output['external_source']):
                if output.get('external_source_exists', True):
                    results['broken_links'].append({
                        'file': output['file'],
                        'external_source': output['external_source']
                    })
    
    return results
```

### Step 6: Generate Validation Report

```yaml
validation_report:
  chart_id: trump_19460614_105400_jamaica_ny
  validated_at: 2026-03-04T15:00:00Z
  
  chart_yaml:
    valid: true
    errors: []
    
  index_yaml:
    valid: true
    errors: []
    
  provenance_integrity:
    valid: true
    missing_files: []
    broken_links: []
    
  overall_status: PASS | FAIL
  
  recommendations:
    - "Consider adding packs_dir to structure"
```

### Step 7: Block Invalid Operations

When called by other skills:

```python
def validate_before_pack(chart_id):
    """Block pack building if validation fails."""
    result = validate_chart_project(chart_id)
    
    if not result['overall_status'] == 'PASS':
        return {
            'blocked': True,
            'reason': 'Schema validation failed',
            'errors': result['errors']
        }
    
    return {'blocked': False}
```

## Important Nuances

### 1. Schema Versioning

Schemas are versioned:
- `chart.schema.v1.json`
- `index.schema.v1.json`

Future versions:
- `chart.schema.v2.json`

Validator should:
- Detect schema version from file
- Use appropriate schema version

### 2. Timezone Format

Accept multiple formats:
- UTC offset: `+04:00`, `-05:00`
- IANA timezone: `Asia/Yekaterinburg`
- Abbreviation: `MSK`, `EST`

### 3. Path Validation

- `canonical_source` must exist (relative to chart root)
- `external_source` may not exist (if archived)
- Check `external_source_exists` flag for consistency

### 4. Method Name Validation

Validate method names against known set:
- `natal_failover`
- `house_placidus`
- `secondary_progressions`
- `solar_arc`
- `synastry_matrix`

### 5. Summary Field Validation

Each method's `summary` field is flexible (free-form object), but should contain:
- `CASE_ID`
- `DATETIME_UTC`
- `OUTPUT_DIR`

### 6. Error Reporting

Report errors with context:
```
ERROR in chart.yaml:
  Path: birth.timezone
  Value: "+4"
  Issue: Does not match pattern '^[+-]\d{2}:\d{2}$'
  Fix: Use "+04:00" instead of "+4"
```

## Examples

### Example 1: Valid Chart-Project

**User says:** "Validate trump_19460614_105400_jamaica_ny"

**Actions:**
1. Load chart.yaml and INDEX.yaml
2. Validate against schemas
3. Check provenance integrity
4. Generate report

**Result:**
```yaml
overall_status: PASS
chart_yaml: valid
index_yaml: valid
provenance_integrity: valid
```

### Example 2: Invalid Timezone Format

**User says:** "Validate new chart with timezone '+4'"

**Actions:**
1. Validate chart.yaml
2. Detect timezone format error

**Result:**
```yaml
overall_status: FAIL
chart_yaml:
  valid: false
  errors:
    - path: birth.timezone
      message: "+4" does not match pattern
      fix: Use "+04:00"
```

### Example 3: Missing Output File

**User says:** "Validate after manual file deletion"

**Actions:**
1. Validate schemas (pass)
2. Check provenance integrity
3. Detect missing file

**Result:**
```yaml
overall_status: FAIL
provenance_integrity:
  valid: false
  missing_files:
    - charts/tuapse_.../outputs/natal_longitudes.csv
```

### Example 4: Pre-Pack Validation

**User says:** "Build delivery pack" (called by artifact-builder)

**Actions:**
1. artifact-builder calls schema-validator first
2. Validation passes → proceed
3. Validation fails → block with error

**Result:**
```
artifact-builder: Validation PASS, proceeding with pack build
```
or
```
artifact-builder: Validation FAIL, blocking pack build
  Errors: birth.timezone format invalid
```

## Troubleshooting

### Error: Schema file not found

- **Cause:** Schema path incorrect
- **Solution:** Check `artifacts/schemas/chart-project/` exists

### Error: YAML parsing fails

- **Cause:** Invalid YAML syntax
- **Solution:** Check indentation, quotes around special characters

### Error: False positive on external_source

- **Cause:** File archived but `external_source_exists` not updated
- **Solution:** Set `external_source_exists: false` after archive

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-014 | Chart project schema validation — this skill implements the validator |
| ASTRO-016 | Artifact serialization — skill validates serialization contracts |
| ASTRO-021 | Artifact builder — skill calls validator before building packs |

## Available Code / Tools

### PowerShell Scripts
- `artifacts/mcp-recipes/validate_chart_project.ps1` — Main validator implementation
- `artifacts/mcp-recipes/check_chart_provenance.ps1` — Provenance integrity check
- `artifacts/mcp-recipes/check_artifact_conformance.ps1` — Conformance checker

### Schemas
- `artifacts/schemas/chart-project/chart.schema.v1.json` — Chart metadata schema
- `artifacts/schemas/chart-project/index.schema.v1.json` — Provenance index schema

### Schema Validation Logic (from validate_chart_project.ps1)
- `Parse-ChartYaml` — Parse YAML manually (no external deps)
- `Parse-IndexYaml` — Parse INDEX.yaml
- `Validate-ChartSchema` — Check required fields
- `Validate-IndexSchema` — Check provenance structure
- `Check-ProvenanceIntegrity` — Verify file paths exist

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/schema-validator/`
- [ ] chart.yaml validated against JSON schema
- [ ] INDEX.yaml validated against JSON schema
- [ ] Provenance integrity check verifies file paths exist
- [ ] Validation report generated with clear errors
- [ ] Other skills can call validator and get blocking result
- [ ] Timezone formats validated correctly
- [ ] Method names validated against known set

