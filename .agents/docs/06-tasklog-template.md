# 06 TaskLog Template

Copy this template for non-trivial runs.

```markdown
# Task Log: <ID> - <title>

**Date:** YYYY-MM-DD
**Workspace:** `D:\\Dev\\CATMEastrolab`
**Status:** TODO|DONE|BLOCKED
**Priority:** P0|P1|P2
**Cynefin Domain:** Clear|Complicated|Complex

## Objective

1. ...
2. ...

## Inputs and Sources

- Source 1: <URL or file>
- Source 2: <URL or file>
- Key timestamps in UTC: ...

## Commands Executed

1. `pwsh artifacts/mcp-recipes/...`
2. `python .codex/skills/...`

## Artifacts Produced

- `artifacts/results/...`
- `charts/<chart_id>/...`

## Validation

- provenance: PASS|FAIL
- schema: PASS|FAIL

## Issues / Oddities

1. ...
2. ...

## Decision / Next Step

- ...
```

Mandatory fields for astrology runs:

- birth local datetime
- birth timezone
- birth UTC datetime
- coordinates
- target/transit UTC datetime
- method run directories
