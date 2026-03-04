# 09 PowerShell Style (Agent Edition)

This guide defines how AI agents must write and run PowerShell in this repo.

## Objectives

1. deterministic execution
2. locale-safe outputs
3. reproducible paths
4. clear failure signals

## Golden Rules

1. Always set strict failure behavior at script top:

```powershell
$ErrorActionPreference = "Stop"
```

2. Prefer absolute or repo-rooted paths for artifact-producing commands.
3. Treat UTC as primary time standard in recipe inputs and logs.
4. Use invariant formatting for numbers and CSV (`Write-InvariantCsv`).
5. Write summary outputs to `00_summary.txt` for every run.

## Parameter Design

Use typed params and mandatory constraints for required inputs.

```powershell
param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$DateTimeUtc,
  [double]$Orb = 1,
  [string]$OutputBase = ""
)
```

Conventions:

- IDs: `CaseId`, `ChartId`
- UTC datetime fields end with `Utc`
- Optional output root: `OutputBase`

## Quoting and argument safety

1. For timezone-like values, prefer variable binding when command-line parsing is fragile.

```powershell
$tz = "-04:00"
pwsh artifacts/mcp-recipes/build_chart_project.ps1 -BirthTimezone $tz ...
```

2. Use double quotes for interpolated strings.
3. Use `-LiteralPath` for files with `[]` in names.

## Path conventions

- recipes: `artifacts/mcp-recipes/`
- run outputs: `artifacts/results/<method_case_ts>/`
- chart projects: `charts/<chart_id>/`
- machine docs: `.agents/docs/`

## Output conventions

Every non-trivial run should produce:

1. `00_summary.txt`
2. raw JSON response files
3. normalized CSV files

Summary should include:

- method/script id + version
- input timestamps and coordinates
- counts (`MATCH_COUNT`, aspect counts)
- `OUTPUT_DIR`
- telemetry when applicable (`SWISS_RETRY_TOTAL`)

## Error handling pattern

- Throw on unrecoverable failures.
- Retry once for transient network/provider failures unless helper already retries.
- Distinguish blocking vs non-blocking known issues (see `08-known-issues.md`).

## Safe execution checklist

1. command uses expected recipe path
2. required params present
3. datetime is UTC where expected
4. output directory created
5. summary file exists
6. schema/provenance validation run for chart projects

## Minimal command patterns

Run recipe:

```powershell
pwsh artifacts/mcp-recipes/run_natal_with_failover.ps1 -CaseId demo -Latitude 44.1 -Longitude 39.07 -DateTimeUtc 1946-06-14T14:54:00Z
```

Read latest result folder:

```powershell
Get-ChildItem artifacts/results -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

Validate built chart:

```powershell
pwsh artifacts/mcp-recipes/check_chart_provenance.ps1 -ChartId <chart_id>
pwsh artifacts/mcp-recipes/validate_chart_project.ps1 -ChartId <chart_id>
```

