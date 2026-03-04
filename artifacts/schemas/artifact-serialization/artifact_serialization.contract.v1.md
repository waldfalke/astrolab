# Artifact Serialization Contract v1

## Scope

Applies to core recipe outputs:

1. `run_natal_with_failover.ps1`
2. `run_house_layer_placidus.ps1`
3. `run_secondary_progressions.ps1`
4. `run_solar_arc.ps1`

## CSV Rules

1. UTF-8 encoding.
2. Comma-delimited CSV with quoted header.
3. Invariant numeric formatting:
   - decimal separator: `.`
   - no locale-dependent decimal comma.
4. Stable column order per output file.

## Summary Rules (`00_summary.txt`)

Summary is a newline-separated `KEY=VALUE` document.

Required observability keys:

1. `SCRIPT_ID`
2. `SCRIPT_VERSION`
3. `RUN_STARTED_AT`
4. `RUN_FINISHED_AT`
5. `INPUT_HASH`
6. `OUTPUT_HASH`

Operational key:

1. `OUTPUT_DIR`

Constraints:

1. Values must be single-line (no embedded newlines).
2. `INPUT_HASH` and `OUTPUT_HASH` are lowercase SHA-256 hex digests.
3. Timestamps must be UTC ISO-like strings.

## Hash Definitions

1. `INPUT_HASH`:
   - SHA-256 over canonical `key=value` lines sorted by key for script input map.
2. `OUTPUT_HASH`:
   - SHA-256 over sorted top-level run artifacts as `filename:file_sha256`.
   - `00_summary.txt` excluded from output hash.

## Conformance Validation

Use:

`artifacts/mcp-recipes/check_artifact_conformance.ps1`

Checks:

1. Required summary keys present.
2. `SCRIPT_ID` matches run prefix profile.
3. Expected CSV headers match.
4. No decimal-comma numeric values in CSV cells.
