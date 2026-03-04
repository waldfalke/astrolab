---
name: run-planner
description: Generates explicit execution plans for chart calculations. Breaks requests into ordered method runs with dependencies, tracks run metadata, produces handoff-ready task summaries. Use when user requests multi-step calculations like "натал + прогноз" or "full workbench".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output: run_plan.yaml
---

# Run Planner

Generate explicit execution plans for chart calculations with dependency tracking.

## Quick Start

**Input:**
```yaml
request: "Натал + прогноз для tuapse_19820613_133910"
chart_id: tuapse_19820613_133910
```

**Output:**
```yaml
plan_id: plan_tuapse_19820613_133910_20260304_150000
methods:
  - sequence: 1, method: natal_failover, depends_on: []
  - sequence: 2, method: house_placidus, depends_on: []
  - sequence: 3, method: secondary_progressions, depends_on: [natal_failover]
  - sequence: 4, method: solar_arc, depends_on: [natal_failover]
```

## Core Workflow

### 1. Parse Request

Extract: methods, chart_id, birth_data (if new).

### 2. Build Dependency Graph

```
natal_failover ─┬─→ secondary_progressions
                └─→ solar_arc
house_placidus ─┘ (independent)
```

### 3. Generate Plan

Topological sort → ordered sequence.

### 4. Track Status

| Status | Meaning |
|---|---|
| PENDING | Not started |
| RUNNING | In progress |
| COMPLETE | Done |
| FAILED | Error |
| SKIPPED | Dependency failed |

### 5. Handle Failures

If method fails → mark dependents as SKIPPED.

### 6. Handoff Summary

```yaml
execution_result:
  completed: 4
  failed: 0
next_recommended_action: |
  1. Build chart-project (chart-data-preparator)
  2. Generate pack (artifact-builder)
  3. Analyze (chart-analyst)
```

## Reference Documents

- `references/method-dependencies.md` — Full dependency graph
- `artifacts/mcp-recipes/failover_runbook.md` — Failover rules

## Scripts

- `artifacts/mcp-recipes/run_full_workbench.ps1` — Reference

## Parallel Groups

```
Group A: natal_failover, house_placidus (parallel)
Group B: secondary_progressions, solar_arc (parallel, after A)
```

## Examples

**Natal+forecast:** `4 methods, 2 parallel groups`

**Method failure:** `house_placidus FAILED → progressions SKIPPED`
