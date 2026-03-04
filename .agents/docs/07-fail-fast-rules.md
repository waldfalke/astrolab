# 07 Fail-Fast Rules

Rules to prevent wasted loops and noisy failures.

## Stop immediately if

1. Required source data is unknown and cannot be verified from a reliable source.
2. Chart project validation returns `FAILED > 0` after one corrective retry.
3. Recipe exits non-zero twice in a row with the same error.
4. Required run directory was not created by recipe.

## Continue (do not block) if

1. Swiss provider shows transient `504/400` but run exits zero and artifacts are complete.
2. `SWISS_RETRY_TOTAL > 0` but output hashes and validation are consistent.
3. Warning-only conditions with successful provenance/schema checks.

## Retry policy

1. One immediate retry for network/provider transient failures.
2. If second run fails with same signature, log and escalate.

## Escalation package

When blocked, include:

- command used
- exact error line
- run directory path
- summary file content (`00_summary.txt`)
- suggested workaround attempt
