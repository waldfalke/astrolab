# 02 Workflows

## Workflow: Trump-like full run

Use when task asks for: natal + directions + progressions + current transit.

1. Resolve birth data with source links.
2. Convert to UTC timestamp.
3. Run:
   - `run_natal_with_failover.ps1`
   - `run_house_layer_placidus.ps1`
   - `run_secondary_progressions.ps1`
   - `run_solar_arc.ps1`
   - `run_transits_to_natal.ps1`
4. Build chart project via `build_chart_project.ps1`.
5. Validate provenance and schema.
6. Record issues and weirdness in TaskLog.

## Workflow: Agent skill update

1. Edit canonical skill in `.agents/skills/<skill>/`.
2. Sync to execution layer:
   - `pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents`
3. Run skill smoke tests.
4. Update TaskLog + docs if behavior changed.

## Workflow: Public-safe release

1. `git status -sb --ignored`
2. Ensure ignored paths stay ignored:
   - `.qwen/`
   - `.tools/`
   - runtime outputs under `artifacts/results|tmp|skill-smoke|result-packs`
   - private skill path if applicable
3. Commit only intended tracked changes.
