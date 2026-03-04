# Task Log: ASTRO-030 - build_chart_project timezone robustness

**Date:** 2026-03-04
**Status:** DONE
**Priority:** P1

## Problem
`build_chart_project.ps1` failed hard when `-BirthTimezone` argument was missing/not parsed.

## Implementation
- Made `-BirthTimezone` optional.
- Added resolver to derive timezone from `BirthDateTimeLocal` and `BirthDateTimeUtc` when timezone is empty.
- Format normalized to `+HH:MM` / `-HH:MM`.

## Verification
Smoke run with empty timezone:
- Chart: `trump_tz_derive_smoke`
- Result chart.yaml contains `timezone: -04:00` derived from inputs.
