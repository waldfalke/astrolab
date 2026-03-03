# Task Log: ASTRO-012 - Agent Orchestrator Module

**Date:** 2026-03-02  
**Workspace:** `D:\Dev\CATMEastrolab`  
**Status:** Planned (module not implemented)

## Objective

Introduce orchestration module that executes method pipelines over chart projects using explicit run plans.

## Why This Module

1. Current flow is command/script level; run plans are implicit.
2. Need deterministic and inspectable pipeline execution for multiple methods.
3. Required for scalable batch processing and future UI/board triggers.

## Scope

1. Run-plan model:
   - input chart project
   - selected methods
   - parameters (orb, target date, house system, etc.)
2. Pipeline execution:
   - method dependency order
   - retries/failover integration via provider adapters
   - structured run logs
3. Project update hooks:
   - refresh `methods/*`
   - refresh `outputs/*`
   - regenerate `INDEX.yaml`

## Out of Scope (initial)

1. Autonomous interpretation text generation.
2. UI chat session management.
3. Distributed queue/workers.

## Interfaces

1. `runPlan(planPath | planObject) -> runReport`
2. `runForChart(chartId, methodSet, params) -> updated chart project`
3. `validatePlan(plan) -> diagnostics`

## Quality Gates

1. Full pipeline run is reproducible from run plan + inputs.
2. Failures are isolated per method with non-destructive partial outputs.
3. Orchestrator never bypasses chart provenance updates.

## Deliverables

1. `src/agent/*`
2. run-plan schema (`json/yaml`)
3. execution report schema and artifact
