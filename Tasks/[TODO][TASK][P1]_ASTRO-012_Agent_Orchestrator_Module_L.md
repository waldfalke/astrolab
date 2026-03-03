# [TODO][TASK][P1] ASTRO-012 - Agent Orchestrator Module

## Goal

Implement orchestration layer that executes method run-plans and updates chart projects deterministically.

## Scope

1. Run-plan schema (`yaml/json`) and validator.
2. Method dependency execution graph.
3. Structured run report and partial-failure handling.
4. Automatic refresh of chart `methods/`, `outputs/`, and `INDEX.yaml`.

## Done Definition

1. `src/agent` module created with run-plan executor.
2. One end-to-end run-plan executes natal + house + progressions + solar arc.
3. Reproducible outputs from same plan and inputs.
