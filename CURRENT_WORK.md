# CURRENT_WORK - CATMEastrolab

**Last Updated:** 2026-06-20
**Active focus:** Solar-gift harness quality + reading-method architecture. This chat (Opus) ran control
reads (Mitya, owner transit-day), fixed real harness bugs, and laid the conceptual spine of the reading
machine into NKS (#85–#91). Two new products scoped (transit-day reading, rising-sign clock).

## Harness Improvement (2026-06-19)

| Status | Item | Notes |
|---|---|---|
| ✅ | Gate path (A1) | Assert-DeliverableReady now checks packs/, not _model_input/ |
| ✅ | Phase files in model_input | 12_monthly_phase_windows + phase_vectors + zakharian_dignities copied to pkg |
| ✅ | Cognitive order (B2) | Prose first, dispositions retroactively; BRIEF reordered + reworded |
| ✅ | AllowEmptyCollection bug | Write-InvariantCsv crashed at binding on charts with no custom point aspects |
| ✅ | Phase inline, not a section | BRIEF + [[PHASE_NOTE]] redefined — phase goes inside sphere/portrait/window text |
| ✅ | Gender as structural param | -Gender added to orchestrator; BRIEF section on significator flip + derived chains |
| ✅ | License → proprietary | Apache 2.0 replaced; contact stribojich@gmail.com |
| ✅ | README full setup | Docker, tzdata (Windows mandatory), Node LTS warning, smoke tests, Claude Code wiring |
| ✅ | Carrier windows A3 | Merged by theme (retro passes); 54→~40; verified card-agnostic on 3 charts |
| 🟡 | Client run gift_198612052020 | Opus running; deterministic spine done; model step pending |
| 🟢 | Fortune + Lilith missing from coverage | Harness gap — engine computes, packs don't include. Deferred. |
| 🟢 | coverage_versions.csv not gated | B3 pattern — behavior avoids ungated work. Deferred. |
| 🟢 | BRIEF slim (A9) | Still ~long; some deduplication with report-standards/prose-style. Deferred. |
| 🟢 | A2 basis contract | BRIEF vs validator self-contradiction on basis column. Deferred. |
| 🟢 | B6 visual proof (PDF screenshot) | Auto-screenshot page 1 still TODO. Deferred. |

## Reading-method architecture (2026-06-20, this chat — Opus)

NKS realm `astrolab` grundsatz/method spine laid down. These are the conceptual centre of the harness:

| Node | What |
|---|---|
| #85 | **Грань детерминизации** — determinize a factor's PROPERTY (orb/date/merge/zone), never its ROLE in the whole (carrying/charged/important = model's discrimination). |
| #86 | **Усиление различения процессом, не алгоритмом** — re-pass, deferred axis (axis crystallizes at the END, not as a premise), falsify-to-stability (one round, criterion = layer-convergence). Snaps A4. |
| #87 | **Механика vs когниция** — completeness accounting = cheap model + script; semantic re-check = "second doctor" (ensemble #76). Take the dispositions-CSV bookkeeping off the strong model. |
| #88 | **Углы первоклассны** (ASC-DSC, MC-IC) — transit to a natal angle outweighs planet; don't conflate "approx time → ◐" (reliability) with "secondary" (weight). |
| #89 | **Производные дома (N-от-M)** — "9 = деньги кризиса". DEFERRED until a selection criterion exists (144 derivatives → Barnum). |
| #90 | **Транзит «на день»** — a day is a range of events; three time-hands (slow=background, Moon=hourly, rising ASC/MC=minute-timer); window roles invert with scale. → `docs/transit-day-reading.md`. |
| #91 | **«Часы восходящего знака»** — separate utilitarian product (intraday astro time-mgmt). ~60% core is ours. → `docs/rising-sign-clock-spec.md`. |

Also landed this chat:
- **Astro-language un-burned** (prose-style §0): planet names are FLESH, not jargon; sphere "no planets/dates" rule REVOKED (semantic-base); sphere size follows eventfulness (no word-count cap).
- **Range-fix (683808a):** forecast anchored to SR-instant, not "now" → any ReturnYear (2020/2025/2030) reads correctly; transits cover the chosen solar year, directions/progressions to that year's moment.
- **Pitfalls #11–14:** magic number, anxious tone, overfit-to-one-chart, angles under-read.
- **CLIENTS.yaml** (`.private`) — owner/Lissa/Mitya/Lena registry (PII, git-ignored).
- **Mitya control run** (Sonnet on the fixed harness) — strongest twin/prose yet; verified numbers; confirmed the day's fixes hold on a fresh chart. Owner transit-day PDF built (three time-hands + rising-sign clock + angles).

## Active Client Run

**Chart:** gift_198612052020 (1986-12-05 20:20, Krasnodar, UTC+3 winter → 17:20Z)
**Gender:** female
**SR year:** 2025, relocated to Seattle (SR cast at Seattle coords)
**Status:** Opus 4.8 running orchestrator; deterministic spine complete; model step (twin→prose) pending
**Note:** Relocation timing is operationally unresolved — client was still in Krasnodar at SR instant (Dec 5), moved Jan 9. Seattle SR angles are an operative assumption, not marked in the current report draft.

## Open Findings from Blind-Run Analysis

See `TaskLogs/20260619_blind_run_findings.md` for full triage.

Key open items:
- **B3** — coverage_versions.csv empty by gate-avoidance (repeating pattern from the blind run)
- **Fortune/Lilith** — computed by engine, absent from coverage_factors; model can't judge or consciously drop what it can't see
- **A6** — chart.yaml stores `timezone: +04:00` instead of IANA zone (minor, semantic drift)
- **A7** — Sun longitude discrepancy 2.5″ across pipelines (minor, ironic for a SHA-pinned project)

## L402 Proof of Vision (subproject — paused)

| Status | ID | Task | Next Action |
|---|---|---|---|
| 🟢 | L402-APR-001 | Aperture in docker-compose | Add service + aperture.yaml |
| 🟢 | L402-APR-002 | lnd-client + setup-channel | Write setup-channel.sh |
| 🟢 | L402-APR-004 | Strip L402 from mock-api | Remove gRPC, keep clean backend |
| 🔴 | L402-APR-003 | client-agent real payment | Blocked by APR-001 + APR-002 |
| 🔴 | L402-APR-005 | E2E test | Blocked by ALL |

**Entry:** `l402-proof-of-vision/AGENTS.md` | **BACKLOG:** `l402-proof-of-vision/BACKLOG.md`

## Progress Log

### 2026-03-06 23:50 [Chat-1: Opus]

**Completed:**
- Fixed 3 LND/bitcoind Docker blockers (rpcbind, tlsextradomain, lightning.proto)
- bitcoind + lnd + mock-api working with real Lightning invoices
- Deep research of Lightning MCP ecosystem (6 tools analyzed)
- Key decision: Aperture for server-side L402, refined-element for client-side
- Created Phase 2 task specs (APR-001..005) with DAG

**Next:** Start APR-001 + APR-002 + APR-004 in parallel

---

### 2026-06-19 [Chat-2: Sonnet + Opus parallel]

**Completed:**
- Harness philosophy confirmed: loosen rules, enable top model — not add gates (эталон came from a bug that bypassed gates)
- A1 fixed: gate now reads packs/
- B2 fixed: cognitive order — prose before dispositions (BRIEF reordered, reworded to retroactive check)
- AllowEmptyCollection bug fixed: Write-InvariantCsv @() was crashing at PowerShell binding level on charts with zero custom point aspects; house-layer recipe deterministically failed on this chart (gift_198612052020); Opus found it via controlled experiment; one attribute added
- Phase files added to model_input: 12_monthly_phase_windows.csv, phase_vectors.csv, zakharian_dignities.csv
- Phase layer: BRIEF rule added — phase is a quality of the body, goes inline in sphere/portrait/window text; [[PHASE_NOTE]] redefined (not a standalone section)
- Gender as structural reading parameter: -Gender param added to run_solar_gift.ps1; manifest.json carries it; BRIEF section added explaining significator flip (female: husband = Sun+Mars on DSC; male: wife = Moon+Venus on DSC) + derived-house co-flip + requirement to flag relational stratum as under-determined if gender unknown
- License: Apache 2.0 → proprietary commercial (stribojich@gmail.com)
- README: complete setup guide — Docker, tzdata mandatory on Windows, Node LTS warning + nvm-windows pointer, smoke tests with expected markers, Claude Code .mcp.json auto-pickup note

**In Progress:**
- Opus model running gift_198612052020 (client female, 1986-12-05, SR 2025 Seattle) — deterministic spine complete, model step pending

**Deferred (next session):**
- Fortune + Lilith missing from coverage (harness gap — engine computes, packs don't include)
- coverage_versions.csv gating (B3 — empty because ungated)
- BRIEF slim A9, basis contract A2, visual proof B6

**Key insight logged:**
- Insider-info firewall was too blunt: gender is NOT biography — it's a structural method parameter (like coordinates). Blind reading without gender is systematically under-determined in the entire relational/derivative stratum (significators, 7th-house objects, derived chains, biological domains). See memory: insider-info-firewall.md updated.
- Self-assessment from Opus: Fortune/Lilith invisible to model (not in coverage_factors, engine computed them); PoF in Virgo → Mercury is double-lord (chart ruler + Fortune ruler); this amplification was missed entirely.

---

### 2026-06-20 03:00 [Chat-3: Opus]

**Completed:**
- Reading-method spine into NKS: #85 determinization line (property vs role-in-whole), #86 strengthen discrimination by process not algorithm (re-pass, deferred axis, falsify-to-stability), #87 mechanics vs cognition (take dispositions bookkeeping off the strong model; second-doctor ensemble), #88 angles first-class, #89 derived houses (deferred), #90 transit-day method, #91 rising-sign-clock product.
- Astro-language un-burned (prose-style §0); sphere "no planets/dates" rule revoked (semantic-base); sphere size follows eventfulness (removed a 150-250 word cap I'd wrongly introduced).
- Range-fix (683808a): forecast anchored to SR-instant → any ReturnYear works (past/current/future), not just "the one starting now".
- A3 merge-by-theme verified card-agnostic on 3 charts (owner/Lissa/Mitya).
- HARNESS_PITFALLS.md registry (#11-14: magic number, anxious tone, overfit-to-one-chart, angles under-read).
- CLIENTS.yaml private registry (owner/Lissa/Mitya/Lena).
- Mitya control run reviewed (Sonnet on fixed harness — strongest output yet, numbers verified).
- Owner transit-day PDF (.private/charts/ownerday/) — three time-hands + rising-sign clock + angles; method doc docs/transit-day-reading.md; rising-sign-clock spec docs/rising-sign-clock-spec.md.

**In Progress:**
- Owner transit-day PDF — "Сегодня по областям" section being rewritten from a dry table to prose (what each area means today + the concrete events inside).

**Next:**
- Zones #84: TIME-axis DONE+verified (commit 2d3b43f — carrier_windows zone tail/core/horizon, ±3mo scan decoupled from SR anchor, threaded to coverage_factors; tail proven on owner solar-2026; pitfall #15). REMAINING: DOMAIN-axis zone on sphere_ledger (wider orb-horizon for spheres) + far-horizon extrapolation (deferred).
- dispositions rework per #87 (offload to cheap model + ensemble); rising-sign-clock product (#91, ~40% new).
- Lena run still pending owner decision (this chat scoped current SR 2025, Krasnodar, no relocation; the other chat had Seattle+gender — reconcile).

**Blockers:** none. Deep night — stopping after the prose fix.
