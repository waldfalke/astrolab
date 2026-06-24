export const meta = {
  name: 'build-with-verification',
  description: 'W-model build: every left-branch artifact (the SPEC) is tested AT CREATION, and impl is tested against it — both by a SEPARATE tester agent that goes to the source of truth ITSELF, never trusting the builder. Verification is a code-phase (control-flow), not the model\'s goodwill. Closes the overclaim hole (NKS astrolab #125/#126).',
  phases: [
    { title: 'understand', detail: 'orient NKS + read the independent source of truth' },
    { title: 'spec', detail: 'write the RED golden against an INDEPENDENT oracle' },
    { title: 'spec-critique', detail: 'ADVERSARY refutes the spec itself (tautology/mutation/independence)' },
    { title: 'build', detail: 'TDD to GREEN against the verified spec' },
    { title: 'verify', detail: 'impl-check on CLEAN checkout + adversary refute' },
    { title: 'record', detail: 'NKS pratyakshita ONLY if both survived' },
  ],
}
// args: { task, sourceOfTruth (e.g. recipe path), goldenFixture (e.g. Trump chart id) }

const VERDICT = { type: 'object', required: ['refuted', 'reason'],
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' }, evidence: { type: 'string' } } }

phase('understand')
const ctx = await agent(
  `Orient NKS realm astrolab, then read the INDEPENDENT source of truth: ${args?.sourceOfTruth}. ` +
  `Return what "${args?.task}" must do and WHICH independent oracle defines "correct" (a real recipe ` +
  `output / live system / the owner — NOT the engine the impl will reuse).`,
  { phase: 'understand', schema: { type: 'object', required: ['mustDo', 'oracleSource'],
    properties: { mustDo: { type: 'string' }, oracleSource: { type: 'string' } } } })

phase('spec')
const spec = await agent(
  `Write the RED golden test for "${args?.task}". Assert against the INDEPENDENT oracle ` +
  `(${ctx?.oracleSource}) — the REAL recipe output / fixture ${args?.goldenFixture}, NEVER "by construction". ` +
  `Return: the test code, exactly what it asserts, and where the oracle value came from.`,
  { phase: 'spec', schema: { type: 'object', required: ['testCode', 'asserts', 'oracleProvenance'],
    properties: { testCode: { type: 'string' }, asserts: { type: 'string' }, oracleProvenance: { type: 'string' } } } })

// ── THE LAYER THE OWNER NAMED: verify the SPEC, not just impl-against-spec ──
phase('spec-critique')
const specVerdict = await agent(
  `You are a SEPARATE TESTER (W-model), NOT the spec author. First go to the source of truth ` +
  `${args?.sourceOfTruth} YOURSELF and build your OWN understanding of correct — do NOT trust the author's ` +
  `asserts/provenance below; a gap between your independent read of the source and the author's spec IS a ` +
  `spec defect. Now REFUTE this golden ` +
  `as a valid oracle. Test: ${spec?.testCode}\nAsserts: ${spec?.asserts}\nOracle: ${spec?.oracleProvenance}\n` +
  `Refute on ANY of:\n` +
  `- TAUTOLOGY: does the impl reuse the same engine/source the test compares to? Then it agrees by ` +
  `construction and catches nothing. (This is exactly how "6 passed" lied — A==B1, same swiss engine.)\n` +
  `- MUTATION: would a deliberately-broken impl actually FAIL this test? If a plausible wrong impl passes, ` +
  `the test is a stub.\n` +
  `- INDEPENDENCE: is the oracle value from reality/recipe, or smuggled from the thing under test?\n` +
  `- COMPLETENESS / AMBIGUITY: does it assert what it claims? edge cases? one clear meaning?\n` +
  `Default refuted=true if uncertain. A hollow oracle is worse than no test — it manufactures false trust.`,
  { phase: 'spec-critique', schema: VERDICT })

if (specVerdict?.refuted) {
  // do NOT build on a hollow oracle. Surface and stop — the spec must be repaired first.
  log(`SPEC REFUTED — not building on a hollow oracle: ${specVerdict.reason}`)
  return { stopped: 'spec-refuted', spec, specVerdict }
}

phase('build')
const built = await agent(
  `TDD against the VERIFIED spec. Watch RED fail for the right reason, write MINIMAL code to GREEN, refactor. ` +
  `Iron Law: no production code without a failing test first. Test: ${spec?.testCode}`,
  { phase: 'build', agentType: 'general-purpose',
    schema: { type: 'object', required: ['greenProof', 'filesTouched'],
      properties: { greenProof: { type: 'string' }, filesTouched: { type: 'array', items: { type: 'string' } } } } })

phase('verify')
const verdict = await agent(
  `You are a SEPARATE TESTER (W-model), NOT the builder — do NOT trust the builder's green-proof below; ` +
  `RUN IT YOURSELF. verification-before-completion + ADVERSARY. (1) Run the suite on a CLEAN checkout ` +
  `(no ad-hoc optional installs) and report PROJECT state, not a primed machine. (2) Then REFUTE "it passes": ` +
  `skip-green hiding an unverified claim? machine-only? coverage gap? claim wider than evidence? ` +
  `Builder's claim (verify, don't trust): ${built?.greenProof}\nDefault refuted=true if uncertain — evidence before assertion.`,
  { phase: 'verify', schema: VERDICT })

phase('record')
const trustworthy = !specVerdict?.refuted && !verdict?.refuted
// caller records NKS pratyakshita ONLY if trustworthy; otherwise anumita/kalpita with the open gap.
return { task: args?.task, spec, specVerdict, built, verdict, trustworthy,
  note: trustworthy ? 'spec verified + impl verified on clean checkout'
                    : `NOT trustworthy: ${verdict?.refuted ? verdict.reason : specVerdict.reason}` }
