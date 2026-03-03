# BACKLOG - CATMEastrolab

**Project:** Astro processing workbench (artifact-first)  
**Updated:** 2026-03-02

## Legend

- Status: `TODO` `IN_PROGRESS` `DONE` `BLOCKED`
- Priority: `P0` `P1` `P2`
- Cynefin: `Clear` `Complicated` `Complex`

## Active Tasks

| Status | ID | Priority | Cynefin | Task |
|---|---|---|---|---|
| DONE | ASTRO-001 | P0 | Complicated | MCP result artifact pack (natal/forecast/synastry + manifests) |
| DONE | ASTRO-002 | P0 | Clear | Project task-management scaffold (CURRENT_WORK/BACKLOG/Tasks/TaskLogs) |
| DONE | ASTRO-003 | P1 | Complicated | Multi-provider MCP profile (primary/backup switching, failover runbook, validated runs) |
| DONE | ASTRO-004 | P1 | Complex | House-layer capability (Placidus-ready provider + cross-check protocol) |
| DONE | ASTRO-007 | P1 | Complicated | Chart-as-project systemization (`charts/<chart_id>`, raw-by-method, outputs, `INDEX.yaml`) |
| DONE | ASTRO-013 | P0 | Complicated | Provenance integrity hardening (`canonical_source`, stable source mapping after archive/moves) |
| DONE | ASTRO-014 | P0 | Complicated | Chart project schema validation (`chart.yaml` / `INDEX.yaml` contracts + validator) |
| DONE | ASTRO-015 | P1 | Complicated | Safe archive utility with index rewrite and verification report |
| TODO | ASTRO-016 | P1 | Complicated | Artifact serialization and observability standards (locale-safe CSV + run metadata hashes) |
| TODO | ASTRO-008 | P1 | Complicated | Target modular architecture blueprint (core/providers/methods/products/agent boundaries) |
| TODO | ASTRO-009 | P1 | Complex | Renderer module for chart wheel image generation (SVG/PNG) |
| TODO | ASTRO-010 | P1 | Complicated | Obsidian integration module (notes + canvas export) |
| TODO | ASTRO-011 | P1 | Complicated | Core backbone and provider adapter extraction from recipe scripts |
| TODO | ASTRO-012 | P1 | Complex | Agent orchestrator module with explicit run plans and chart project updates |
| TODO | ASTRO-005 | P1 | Complicated | Professional client output packs (templated delivery folders with QC gates) |
| TODO | ASTRO-006 | P2 | Complex | Secondary knowledge ingestion flow (multi-language corpus with validation) |

## Dependency Graph (DAG)

1. `ASTRO-001 -> ASTRO-003`
2. `ASTRO-001 -> ASTRO-004`
3. `ASTRO-003 -> ASTRO-007`
4. `ASTRO-004 -> ASTRO-007`
5. `ASTRO-007 -> ASTRO-013`
6. `ASTRO-007 -> ASTRO-014`
7. `ASTRO-013 -> ASTRO-015`
8. `ASTRO-001 -> ASTRO-016`
9. `ASTRO-008 -> ASTRO-011`
10. `ASTRO-013 -> ASTRO-011`
11. `ASTRO-014 -> ASTRO-011`
12. `ASTRO-011 -> ASTRO-012`
13. `ASTRO-008 -> ASTRO-009`
14. `ASTRO-011 -> ASTRO-009`
15. `ASTRO-008 -> ASTRO-010`
16. `ASTRO-007 -> ASTRO-010`
17. `ASTRO-014 -> ASTRO-010`
18. `ASTRO-014 -> ASTRO-005`
19. `ASTRO-016 -> ASTRO-005`
20. `ASTRO-011 -> ASTRO-005`
21. `ASTRO-011 -> ASTRO-006`

## State Audit Snapshot

| Finding Type | Observation | Impact | Linked Tasks |
|---|---|---|---|
| Strength | Archive rewrite automation implemented (dry-run/execute + report + verification) | External lineage drift risk reduced | ASTRO-015 |
| Gap | Schema validator exists but is not yet a mandatory gate in all delivery flows | Contract drift risk in unattended runs | ASTRO-005 |
| Hole | CSV/summary serialization is not fully standardized | Fragile downstream ingestion | ASTRO-016 |
| Excess Complexity Risk | Product modules may start before backbone stabilization | Rework in renderer/obsidian | ASTRO-008, ASTRO-011, ASTRO-009, ASTRO-010 |
| Gap | Client packs currently lack hardened contract gates | Delivery quality drift | ASTRO-005, ASTRO-014, ASTRO-016 |
| Gap | Knowledge ingestion not wired to modular backbone | Parallel silos risk | ASTRO-006, ASTRO-011 |

## TaskLog References

1. `TaskLogs/task_log_ASTRO-001_mcp_result_artifact_pack_20260301.md`
2. `TaskLogs/task_log_ASTRO-003_004_provider_house_layer_20260301.md`
3. `TaskLogs/task_log_ASTRO-007_chart_project_systemization_20260302.md`
4. `TaskLogs/task_log_ASTRO-008_architecture_target_modular_stack_20260302.md`
5. `TaskLogs/task_log_ASTRO-009_renderer_module_20260302.md`
6. `TaskLogs/task_log_ASTRO-010_obsidian_integration_module_20260302.md`
7. `TaskLogs/task_log_ASTRO-011_core_backbone_and_provider_adapters_20260302.md`
8. `TaskLogs/task_log_ASTRO-012_agent_orchestrator_module_20260302.md`
9. `TaskLogs/task_log_ASTRO-013_provenance_integrity_20260302.md`
10. `TaskLogs/task_log_ASTRO-014_chart_project_schema_validation_20260302.md`
11. `TaskLogs/task_log_ASTRO-015_safe_archive_and_index_rewrite_20260302.md`
12. `TaskLogs/task_log_ASTRO-016_artifact_serialization_and_observability_20260302.md`
