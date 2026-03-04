# 08 Known Issues

This file exists to keep agents calm and deterministic around expected noise.

## KI-001: Swiss provider transient 504/400

Symptoms:

- log lines mention `swissremote appears offline` or HTTP 400/504
- recipe still exits with code 0 and writes full output

Interpretation:

- non-blocking transient upstream instability

Action:

1. Check `SWISS_RETRY_TOTAL` and `SWISS_RETRY_BY_TOOL` in summary.
2. If output exists and validation passes, continue.
3. Record in TaskLog.

## KI-002: Locale CSV decimal comma in legacy synastry outputs

Symptoms:

- numbers like `82,928095` in old `03_synastry_aspect_matrix.csv`

Interpretation:

- legacy formatting path before invariant CSV fix

Action:

1. Re-run recipe with current code.
2. Use regenerated file with dot-decimals.

## KI-003: Transit recipe naming confusion

Symptoms:

- old flows use `run_synastry_matrix.ps1` for transit tasks

Interpretation:

- historical workaround, not the preferred method

Action:

- use `run_transits_to_natal.ps1` for transit jobs

## KI-004: Birth timezone argument fragility in older invocations

Symptoms:

- old command examples fail on `-BirthTimezone` parsing edge cases

Interpretation:

- invocation formatting issue; script now supports derived timezone

Action:

1. Pass `BirthDateTimeLocal` + `BirthDateTimeUtc`.
2. Leave `BirthTimezone` empty if needed.

## KI-005: Private skill intentionally absent from canonical layer

Symptoms:

- `astro-engineering-scanner` not found in `.agents/skills`

Interpretation:

- expected by policy (private skill)

Action:

- do not treat as failure in public workflows
