# [TODO][TASK][P1] ASTRO-016 - Artifact Serialization and Observability

## Goal

Standardize artifact serialization and run metadata for reproducible downstream processing.

## Scope

1. Enforce serialization standards:
   - invariant numeric formatting
   - stable encoding and column conventions
2. Extend run summaries with observability metadata:
   - script id/version
   - input hash/output hash
   - run timestamps
3. Add conformance check for core recipes.

## Dependencies

1. ASTRO-001 (artifact recipes).

## Done Definition

1. Serialization contract is documented and applied to priority scripts.
2. Metadata fields present in summaries.
3. Conformance checks pass on representative runs.
