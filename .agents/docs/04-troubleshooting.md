# 04 Troubleshooting

## Symptom: swiss provider 504/400 appears, run still completes

Action:

1. Check run summary fields:
   - `SWISS_RETRY_TOTAL`
   - `SWISS_RETRY_BY_TOOL`
2. If retries > 0, record in TaskLog as provider instability.
3. Re-run once before escalating.

## Symptom: timezone argument issues in `build_chart_project.ps1`

Action:

1. Provide both `BirthDateTimeLocal` and `BirthDateTimeUtc`.
2. `BirthTimezone` is optional; script derives it when empty.

## Symptom: transit recipe ambiguity

Action:

- Use `run_transits_to_natal.ps1`, not `run_synastry_matrix.ps1` for transit tasks.

## Symptom: comma decimal in CSV

Action:

- Use scripts that call `Write-InvariantCsv`.
- For legacy files, regenerate with updated recipe.

## Symptom: agent cannot find skills

Action:

1. Confirm canonical path exists: `.agents/skills/`
2. Sync to runtime path:

```powershell
pwsh .agents/scripts/sync-skills.ps1 -Direction from-agents
```

3. Retry workflow.
