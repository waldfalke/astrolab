# 11 Anti-Patterns (Agent Edition)

This list captures failure modes that repeatedly cause bad or irreproducible runs.

## AP-001: Free-form computation outside recipes

Bad:

- manually computing positions/aspects outside `artifacts/mcp-recipes`

Why bad:

- breaks reproducibility and provenance model

Do instead:

- run recipe scripts and keep generated artifacts

## AP-002: Using synastry script as default transit path

Bad:

- using `run_synastry_matrix.ps1` for transit tasks by default

Why bad:

- semantic mismatch, harder maintenance

Do instead:

- use `run_transits_to_natal.ps1`

## AP-003: Locale-dependent CSV export

Bad:

- `Export-Csv` directly on numeric rows in locale-sensitive contexts

Why bad:

- decimal comma/dot inconsistency across environments

Do instead:

- `Write-InvariantCsv`

## AP-004: Ignoring summary files

Bad:

- checking only terminal output and skipping `00_summary.txt`

Why bad:

- misses run metadata, counts, retries, hashes

Do instead:

- parse/read `00_summary.txt` first for operational status

## AP-005: No TaskLog for non-trivial work

Bad:

- producing artifacts without recording source, UTC, and issues

Why bad:

- impossible handoff and weak auditability

Do instead:

- create TaskLog using `06-tasklog-template.md`

## AP-006: Failing hard on every 500/400 mention

Bad:

- stopping immediately when log mentions transient provider error

Why bad:

- many runs complete successfully with retries

Do instead:

- check exit code, output files, validation, retry telemetry

## AP-007: Writing canonical skills in runtime folders

Bad:

- editing `.codex/skills` or `.qwen/skills` as source of truth

Why bad:

- drift between agents and hard-to-track updates

Do instead:

- author in `.agents/skills`, then sync

## AP-008: Relative path ambiguity in run commands

Bad:

- commands that depend on unknown current directory

Why bad:

- non-reproducible CI/agent behavior

Do instead:

- run from repo root or use explicit absolute paths

## AP-009: Missing final validation on chart project

Bad:

- building chart project and stopping there

Why bad:

- silent broken links/schema regressions

Do instead:

- always run:
  - `check_chart_provenance.ps1`
  - `validate_chart_project.ps1`

## AP-010: Hidden local-only changes in ignored paths

Bad:

- relying on artifacts in ignored dirs without documenting source run dirs

Why bad:

- another agent cannot reproduce

Do instead:

- include run directory references in TaskLog and `INDEX.yaml`
