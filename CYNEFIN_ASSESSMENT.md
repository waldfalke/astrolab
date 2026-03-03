# CYNEFIN_ASSESSMENT - CATMEastrolab

**Date:** 2026-03-01

## Summary

| Domain | Current task types | Execution mode |
|---|---|---|
| Clear | Runbook execution, manifest generation, packaging | Standardize and automate |
| Complicated | Provider selection, tool-mapping, quality rules | Compare options and fix contracts |
| Complex | Multi-provider trust model, interpretation boundaries, method fusion | Probe-test-learn with controlled pilots |
| Chaotic | None | Incident mode only on production outages |

## Task Mapping

| ID | Task | Domain | Why |
|---|---|---|---|
| ASTRO-001 | MCP result artifacts | Complicated | Tool semantics + payload normalization required |
| ASTRO-002 | Task scaffold | Clear | Known process pattern from reference project |
| ASTRO-003 | Multi-provider profile | Complicated | API differences and auth topology |
| ASTRO-004 | House-layer capability | Complex | Depends on provider quality, verification, and method constraints |
| ASTRO-005 | Client output packs | Complicated | Needs consistent templates + QC criteria |
| ASTRO-006 | Multilingual knowledge ingestion | Complex | Source quality and term disambiguation are non-trivial |

## Operating Rule

1. `Clear` -> execute directly with checklist.
2. `Complicated` -> document assumptions and alternatives before locking.
3. `Complex` -> run short spike, measure, then commit.
