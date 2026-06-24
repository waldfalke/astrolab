# CURRENT_WORK - CATMEastrolab

**Last Updated:** 2026-06-24
**Active focus:** **Project picture corrected, not code written.** A real `assembly` rescope showed the
session had been working a graph-blocked transformation — the order was inverted. Rebuilt the forest to
the owner's three-tense model: **NOW = fix the instrumentarium (foundation)**; TOMORROW = the one holistic
reading-skill applied to charts (soljar/natal/transits/clock); DAY-AFTER = sell to robots. Recorded the
stage-conveyor model (#129) and LIFTED the Zakharian copyright everywhere. Still open: the #1/#93 vertical
"kingdoms" need untangling by stage. Earlier this session (still valid): headless first slice (rising_hands
FastMCP tool), engine-agnosticism #115, claim-discipline §3a/§3b, build-with-verification workflow.

## Rising-sign clock — mundane product + NKS process (2026-06-22/23, Opus)

| Status | Item | Notes |
|---|---|---|
| ✅ | Mundane clock Stage-1 MVP | natal-free "космограмма качества времени дня"; verified end-to-end 22–23.06 Krasnodar |
| ✅ | Standard template | `artifacts/report-templates/rising-clock-mundane.html` — de-identified, format rules in leading comment (that comment IS the standard) |
| ✅ | Twin-gated orchestrator | `artifacts/mcp-recipes/run_mundane_day.ps1` — data→twin→template→PDF, younger sibling of run_transit_day; gate blocks PDF without twin |
| ✅ | Crystallized to NKS | bildung `#101` (bianhua `#96` Stage-1); driving hints #91/#95/#97 realized |
| ✅ | run_transit_day protocol | natal transit-day twin-gated orchestrator (built earlier this session) |
| ✅ | verstakify refresh | SessionStart orient + PostToolUse git-push hooks + NKS allow-list in `.claude/settings.json` |
| ✅ | NKS process-weave | first tensions/bianhua sweep; 3 vimarshas anchored; sweep ritual woven into `/save` Step 6 + `/load` Step 2 + git-push hook |

Format standard (the rules we suffered to find): 12 watches as bold-header paragraphs (no period),
достоинство ≠ фаза, phase = archetype word (never the P⟨⟩ formula), "восходящий градус" not "горизонт",
НА квадрате / В оппозиции, high planets not a flat background, retro-only climate, two layers
technical→human, twin before prose. Memory: `rising-clock-mundane-format`. Tasklog:
`TaskLogs/20260623_nks_capability_audit_and_process_weave.md`.

**Next:**
- Stage-2 «свадьба» of the clock with natal (`#98`, anantara after MVP) — personal overlay on the
  general mechanics.
- 14 standing weave tensions (11 grundsatz + 2 vollzug) — a focused `design`/`weaving` pass: they need
  applying-kriya nodes, decided per-principle (pitfall #85), not blanket-linked.
- `#94` scoring-engine vs determinization line (parked samshaya).

## Instrumentarium contour + MCPization plan (2026-06-23, Opus)

The project began as a headless MCP function factory (webMCP, aA2A) but the graph had drifted entirely
into reading-craft — `semantic_search` found zero nodes for the product layer. Returned it to the map.

| Status | Item | Notes |
|---|---|---|
| ✅ | Contour #102 «Инструментарий» | 5th root holon — *чем* исполняется машина (substrate/капсулы/MCP/гейты), vs #67 принципы |
| ✅ | Retrospective wiring | engine #103, substrate #104, kriyas #105/#106/#107 → `upadhi` to 13 principles → **weave 14→2** |
| ✅ | Prospective plan (hints) | #108 капсула-скилл → #109 headless-MCP → #111 L402 (anantara) · #110 изоляция-прогон |
| ✅ | Bianhua #112 | «Инструментарий становится планируемым слоем и headless-продуктом» — owner map, holds headless visible |
| ✅ | MCPization plan + gap audit | 33 recipes classified (atomic/orchestrator/infra/copyright); 8 gaps; tasklog `20260623_mcpization_plan.md` |
| ✅ | Language decision | **Python + pyswisseph + FastMCP** (not PowerShell-shim) — pyswisseph in-process kills provider dep (G4+G5); PS recipe = golden reference |
| ✅ | Test granularity | function=unit/golden · skill=workflow-scenario · gate=assertion; one skill-capsule per workflow-genre |
| ✅ | G7 fix | recipes README named dead provider theme-astral.me → corrected to self-hosted swiss |

**Next (instrumentarium):**
- Stage 1 — first MCP function: `astro.rising_hands(date,lat,lon,tz)` in Python+pyswisseph+FastMCP +
  golden test vs the PowerShell recipe. Proves language + contract (G1/G2/G3) + provider-removal (G5).
- ~~G6 copyright allow-list (exclude phase)~~ — copyright restriction **LIFTED 2026-06-24** (#50 retired; phase free for client/product) · G8 L402 billing (#111, послезавтра).
- Refactor `.agents/skills/` into workflow-capsules with a test harness (fixture + invariants).

## Headless MCP — first slice + engine-agnosticism + element/composite views (2026-06-24, Opus)

Built the first real headless slice via verstakify+Superpowers (TDD skills run as EXPLICIT isolated
subagents, not inlined; every GREEN verified by me, not on the subagent's word).

| Status | Item | Notes |
|---|---|---|
| ✅ | First MCP tool | `astro/server.py` — FastMCP tool `rising_hands`, typed inputSchema (G2) + stateless dict (G3); in-memory round-trips the golden |
| ✅ | rising_hands engine | `astro/rising_hands.py` + `astro/engine.py` — B1 (client of our pinned swiss-mcp v2.10.03) computes 12 watches; golden green by construction |
| ✅ | Pinned stack | `pyproject.toml` + `uv.lock` (fastmcp 3.4.2, mcp 1.28, pytest 9.1.1) — reproducibility gap closed, like the pinned ephemeris node |
| ✅ | Engine-agnosticism #115 | engine behind thin `compute_asc_series`; B1 default, A (pyswisseph) optional group `engine-a`; golden arbiter; per-function choice. Fork #113 CLOSED — A==B1 (drift 0, same v2.10.03), A ~1000× faster; A deploy needs C-build (Win), B1 needs none. Soft preference: the fast in-process one. |
| ✅ | Supply-chain #114 | own ephemeris node, never a 3rd-party API (theme-astral.me was the realized risk); hosting it = release req (G5) |
| ✅ | Two views split | holarchic reading-ontology (natal HOLON #116, ELEMENT #117 — not "atom", reading organ #121, reading #122) vs instrumentarium (natal COMPOSITE #119, structure #118, SCENARIO #120). Linked via the natal-structure estafeta, roles kept separate. |

Terminology fixed: **element / composite / scenario** (NOT atomic-design atoms/molecules/organisms — those are just holon layers misnamed; holarchy absorbs them). Tasklog: `TaskLogs/20260623_mcpization_plan.md`.

**HONEST status (built ≠ trustworthy):** the MCP tool is in-memory only — transport-as-process,
auth, failover NOT done (G5 deploy layer). rising_hands covers only watches (no phases/objects/spheres).
Natal is a SPEC in the graph (#116–122), not code yet. A-engine pass depends on the optional install.

**Next:**
- Natal in code: implement composite #119 (assemble elements → structure), golden on Trump fixture.
- Transport-as-process (HTTP) → toward G5 deploy (hosting + TLS + auth).
- Widen `rising_hands` to the full function (phases/objects/spheres) OR prove the conveyor on a 2nd function.
- Fix "атомарн" → "элемент" wording in #109 (term-drift hygiene).

## Rescope via assembly + forest rebuild + copyright lift (2026-06-24 late, Opus)

The session had drifted deep into meta (claim-discipline, build-with-verification, overclaim). Updated
verstak (`→6ab7b848da84`, got `assembly`/`inquiry`/`integrity`), ran a real `assembly`, and the graph
gave an OBJECTIVE rescope signal — the session was working a **graph-blocked** transformation.

| Status | Item | Notes |
|---|---|---|
| ✅ | Rescope: order was inverted | #112 (headless) was BLOCKED `after #78/#55`, yet the session worked it. Owner's three-tense model: NOW = fix instrumentarium (foundation); TOMORROW = reading-soljar/clock/transits on it; DAY-AFTER = sell to robots. |
| ✅ | Forest rebuilt | deleted `anantara #112→#78`; #112 = foundation, **committed-now**; #26 (phase-soljar) → `upeksha` (tomorrow); #55 reframed as the ONE holistic reading-skill, per-chart readings are applications (`#26→#55`). |
| ✅ | Owner's model (bildung #129) | horizontal **stage-conveyor** (compute→data→analyze→text); a CHART goes through it whole; METHODS feed the compute-pot (общий котёл); origin (ours/Zakharian) = separate rights-axis. (+#127/#128 rescope bildungs.) |
| ✅ | Copyright LIFTED | Zakharian phase restriction removed EVERYWHERE (graph #50 retired + #12 unlinked; memory; 5 recipes; report-standards; tasklog/CURRENT_WORK). KEPT epistemic honesty (z/h,D anumita-ceiling — knowledge-quality, not a bar). |
| ⚠️ | Disease found, NOT fixed | contours #1 (phase-soljar-reading) & #93 (clock) are vertical KINGDOMS mixing all axes (stages+method+chart+origin); #1 dups holistic #30, #93 also glues compute+text. Untangle by stage = big separate work. |

**Language discipline (owner flagged hard):** NKS jargon (bianhua/anga/anantara/telos) leaked badly into
owner-facing talk this session. Memory rule exists (`report-plain-russian-no-nks-jargon`) — keep the graph
INSIDE, report in plain Russian at the boundary.

**Next (NOW = fix instrumentarium):**
- Untangle the #1/#93 kingdoms by stage-conveyor (big).
- Verify the 13-computation map against recipes myself (debt); then port-vs-shell-out #124; then build.

## Composites study + claim-discipline (2026-06-24, Opus)

Followed the owner's process (study → record WHOLE feature → see forks → decompose → build via
Superpowers), NOT grab-a-piece-and-code. The session's hard turn was the owner catching me **lying
despite NKS**.

| Status | Item | Notes |
|---|---|---|
| ✅ | 13 composites studied | Explore over recipes+docs; whole feature recorded in `TaskLogs/20260624_composites_mcpization_feature.md` (natal/SR/synastry/progressions/directions/transits/clock/phase/profection/coverage/windows — all already PowerShell recipes) |
| ✅ | Fork named: PORT vs SHELL-OUT (#124) | How recipe-logic reaches Python. `rising_hands` was a PORT, not a wrap — I'd glossed it. Decided by MEASUREMENT like the engine fork #113. |
| ⚠️ | Fork measured (partial) | Spike on dignities+sect: golden PASS; PORT ~66 lines / zero runtime deps; SHELL-OUT of a real recipe drags pwsh+swiss+2nd recipe. Split-hypothesis (thin→port, heavy→shell-out) supported. **shell-out parse-recipe branch only analyzed, not built.** #124 NOT closed — owner's call. |
| ✅ | Overclaim lesson + #125 | Owner: "ты лжёшь несмотря на NKS". Root: the apparatus STRUCTURES what you feed it, you set the mode yourself; Superpowers called half (TDD yes, verification-before-completion no). `prati-paksha` #125 → anga harness-closure #78. |
| ✅ | claim-discipline §3a | `.agents/AGENTS.md`: verification before any done/passing claim; report PROJECT state not the machine; verified=ran-and-saw; tests fail-loud not skip-green; oracle-where-buildable / adversary-where-judgemental. **Directive layer — a threshold, on willpower, NOT a gate.** |
| ✅ | Understanding crystallized | `bildung` defense-doubles (oracle ⊕ adversary; build-gate doesn't cross compilation→judgement) |

**HONEST (built ≠ trustworthy):** composites are STUDIED + planned, **not built**. Fork #124 measured
only on the easy half. Directives hold on my willpower — the only non-willpower layer (screaming test +
CI) is NOT done. Map of 13 composites is Explore's word, **not re-verified by me against recipes**.

**Next:**
- Mechanical layer (the only thing not on willpower): agnosticism test that SCREAMS instead of
  skip-green (closes §3a for real); CI on clean checkout. By TDD, with `verification-before-completion`
  run explicitly on the code.
- Close fork #124 with the owner's decision (split?) → then decompose the 13 composites in NKS.
- Re-verify the 13-composite map against recipes myself (honest debt — it's a subagent's word).
- Fix "атомарн"→"элемент" in #109.

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
- Zones #84: TIME-axis DONE+verified (2d3b43f — carrier_windows zone tail/core/horizon, ±3mo scan decoupled from SR anchor, threaded to coverage_factors; tail proven on owner solar-2026; pitfall #15). DOMAIN-axis POSTURE DONE+verified (bf09167 — coverage_factors `zone` column → sphere_ledger zone_core/horizon/tail + posture hint; tail-only sphere proven on fixture). #84 CONSCIOUSLY DEFERRED (owner 2026-06-21, factors already plentiful): (1) **wider orb-horizon for spheres** — full "horizon saves a тихий sphere" needs a separate wider scan (orb 2-3°) for the sphere axis only; FROZEN until a future long-cycle module (slow-planet cycles) — decide there. Open question for thaw (from a SOURCE, not memory): does the up-to-3° orb apply to trans-Saturnian/outer planets or only classical? (2) far-horizon extrapolation — same trigger; (3) real-chart end-to-end of the domain axis — do it on the next real client run, not separately.
- dispositions rework per #87 (offload to cheap model + ensemble); rising-sign-clock product (#91, ~40% new).
- Lena run still pending owner decision (this chat scoped current SR 2025, Krasnodar, no relocation; the other chat had Seattle+gender — reconcile).

**Blockers:** none. Deep night — stopping after the prose fix.
