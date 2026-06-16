# TaskLog — Coverage ledger rebuilt as a keyed contract (script↔model seam)

- **Date:** 2026-06-15
- **Cynefin:** Complicated build (known contract design) guarding a Complex activity (chart reading).
- **Status:** DONE (core); one narrow remainder deferred.

## Scope
Make reading *completeness* and *honesty* hold on structure, not on the reader's memory — by turning
`build_coverage_ledger.ps1` into a keyed three-artifact contract at the script↔model seam, so the
script does only what a script can (enumerate, key, verify form) and the model does only what it must
(salience, valence, sufficiency).

## What was built
`artifacts/mcp-recipes/build_coverage_ledger.ps1` rewritten. Shared key `factor_id`:
- **`coverage_factors.csv`** — machine; every factor enumerated from the data + stable `factor_id`.
  Regenerated freely.
- **`coverage_dispositions.csv`** — semantic, **model-owned**. Script **appends new keys only, never
  rewrites existing rows** (hand edits survive regen — kills the prior overwrite bug by construction,
  not by careful merge).
- **`coverage_report.md`** — verifier (read-only): JOIN + structural checks + joined ledger + tallies.

### Key discipline (advisor catch)
Aspect endpoints are **never sorted**. Cross-frame aspects (`sr2n` / `transit` / `prog2n` / `dir2n`)
carry direction (SR-Saturn→natal-Moon ≠ natal-Saturn→SR-Moon); sorting would symmetrize the directed
= anti-pattern #5 baked into the contract. Stability comes from deterministic enumeration, not sorting.

### Three structural checks (the mechanizable part of acceptance gate 2)
- **completeness** — every `factor_id` has a non-blank salience (else: hole / «лысый соляр»).
- **basis integrity** — every `factor_id` cited in a `basis` exists in the data. This is
  **anti-FABRICATED-basis** (catches phantom corroboration, e.g. aspects imported from another chart),
  **not** anti-cherry-pick — selective demotion of a real factor stays the model's burden.
- **pole⇒basis** — `valence_resolved=yes` ⇒ `basis` non-empty (no «nice» pole-collapse). Schema
  separates *salience* from *valence-resolution* so this is mechanical.

## Verified (on a test chart, private — not named here)
135 factors, 118 holes (= the 118 that needed judgement; 17 auto-quiet). Injected 3 test dispositions:
re-run reported `+0 new keys` (append-only holds, edits survived), `DANGLING_BASIS=1` (phantom
`*.ghostplanet` caught), `UNSUPPORTED_POLE=1` (pole resolved with empty basis caught). Test rows cleared.

## Carriers kept in sync
- Canonical `docs/semantic-base.md` «Полнота обхода» — artifact subsection rewritten to the
  three-file keyed contract + directed-key rule + three checks.
- Skill `reading-discipline` digest updated; mirrored to `.claude/` + `.codex/` via `sync-skills.ps1`.

## Deferred (narrow remainder)
Rank-convergence detector across passes — snapshot dispositions and diff salience pass-to-pass to
*mechanically* see «ledger stabilized» (fixpoint by budget). Currently rests on the re-entrant ritual,
not a detector.

## Self-check
- [x] Recipe is the single source; raw + dispositions land in chart `packs/` (private).
- [x] Script verifies *form* of honesty; model supplies *substance* — seam respected.
- [x] No client identifiers in this log (PII stays in `.private/`).
