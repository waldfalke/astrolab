# [DONE][TASK][P1] ASTRO-015 - Safe Archive and Index Rewrite

## Goal

Archive run directories safely while preserving discoverability and index consistency.

## Delivered

1. Implement `archive_runs.ps1` with:
   - dry-run mode
   - execute mode
2. Move selected runs to archive root batch folder.
3. Rewrite affected chart index fields:
   - `source_run_dir`
   - `external_source_run_dir`
   - `external_source`
4. Emit archive report with moved runs, affected charts, and verification.
5. Update recipe documentation with usage examples.

## Dependencies

1. ASTRO-013 (provenance integrity model).

## Done Definition

1. Archive command updates indexes automatically - achieved.
2. Post-archive verification confirms no broken external refs - achieved.
3. Archive report generated for each run - achieved.
