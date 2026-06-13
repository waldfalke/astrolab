# CURRENT_WORK - CATMEastrolab

**Last Updated:** 2026-03-06
**Session Goal:** L402 Phase 2 — интеграция Aperture как L402 reverse proxy для реального Lightning-платежа.

## Active Tasks

| Status | ID | Task | Notes |
|---|---|---|---|
| ✅ | ASTRO-001 | MCP result artifact pack | Базовые recipe-артефакты готовы |
| ✅ | ASTRO-002 | Task management scaffold | Контур `BACKLOG/Tasks/TaskLogs` внедрен |
| ✅ | ASTRO-003 | Multi-provider MCP profile | Primary/backup + failover runbook |
| ✅ | ASTRO-004 | House-layer (Placidus-ready) | Рабочие house/QC рецепты |
| ✅ | ASTRO-007 | Chart project systemization | `charts/<chart_id>`, `methods`, `outputs`, `INDEX.yaml` |
| ✅ | ASTRO-013 | Provenance integrity | Canonical provenance + checker внедрены |
| ✅ | ASTRO-014 | Chart project schema validation | Схемы + валидатор внедрены |
| ✅ | ASTRO-015 | Safe archive and index rewrite | Реализован архиватор + перепривязка индексов + отчет |
| 🟢 | ASTRO-016 | Serialization and observability | Стандартизация CSV/summary/hash метаданных |
| 🟢 | ASTRO-008 | Target modular architecture | Формализация границ модулей |
| 🟢 | ASTRO-011 | Core backbone and provider adapters | Экстракция ядра из recipes |
| 🟢 | ASTRO-012 | Agent orchestrator | Run-plan executor поверх модулей |
| 🟢 | ASTRO-009 | Renderer module | SVG/PNG колесо из нормализованных данных |
| 🟢 | ASTRO-010 | Obsidian integration | Notes + Canvas export |
| 🟢 | ASTRO-005 | Client output packs | Delivery pack контур с QC-гейтами |
| 🟢 | ASTRO-006 | Multilingual knowledge ingestion | RU/EN артефактный канал методик |

**Legend:** 🟢 Ready | 🟡 In Progress | 🔴 Blocked | ✅ Done

## L402 Proof of Vision (subproject)

| Status | ID | Task | Next Action |
|---|---|---|---|
| 🟢 | L402-APR-001 | Aperture в docker-compose | Добавить сервис + aperture.yaml |
| 🟢 | L402-APR-002 | lnd-client + setup-channel | Написать setup-channel.sh |
| 🟢 | L402-APR-004 | Strip L402 из mock-api | Убрать gRPC, оставить чистый backend |
| 🔴 | L402-APR-003 | client-agent real payment | Blocked by APR-001 + APR-002 |
| 🔴 | L402-APR-005 | E2E test | Blocked by ALL |

**Entry:** `l402-proof-of-vision/AGENTS.md` | **BACKLOG:** `l402-proof-of-vision/BACKLOG.md`

**Docker state:** bitcoind + lnd healthy, lnd-client defined, Aperture not yet added.

### Progress Log

#### 2026-03-06 23:50 [Chat-1: Opus]

**Completed:**
- Fixed 3 LND/bitcoind Docker blockers (rpcbind, tlsextradomain, lightning.proto)
- bitcoind + lnd + mock-api working with real Lightning invoices
- Deep research of Lightning MCP ecosystem (6 tools analyzed)
- Key decision: Aperture for server-side L402, refined-element for client-side
- Created Phase 2 task specs (APR-001..005) with DAG
- Created subproject structure: AGENTS.md, docs/architecture.md, docs/docker-gotchas.md
- Updated global agent docs: `.agents/docs/14-l402-lightning-stack.md`, EXTERNAL_CAPABILITIES_MAP.md §3
- Created `/save` and `/load` commands

**In Progress:**
- Phase 2 tasks ready to start (APR-001 + APR-002 + APR-004 parallelizable)

**Next:**
- Start APR-001 (Aperture), APR-002 (lnd-client channel), APR-004 (clean mock-api) in parallel

---

## Current State (Audit)

1. Сильная сторона: расчетный контур работает end-to-end (natal/house/progressions/solar arc).
2. Сильная сторона: chart-project модель внедрена и применена на реальном кейсе.
3. Сильная сторона: безопасный архиватор с перепривязкой индексов и verification-отчетом внедрен.
4. Критичный риск: валидатор схем есть, но не включен как обязательный gate для всех delivery flow.
5. Риск роста сложности: product-модули (renderer/obsidian) нельзя запускать до стабилизации backbone/hardening.

## Critical Path (Next)

1. ASTRO-016
2. ASTRO-008 -> ASTRO-011 -> ASTRO-012
3. ASTRO-011 -> ASTRO-009 и ASTRO-010
4. ASTRO-014 + ASTRO-016 + ASTRO-011 -> ASTRO-005

## Quality Questions (mandatory)

1. Что не сделано?
2. Что избыточно усложнено?
3. Где остались структурные дыры?
4. Что нужно стабилизировать до новых фич?
5. Что можно упростить без потери качества?
