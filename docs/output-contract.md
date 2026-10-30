# Output contract

Astrolab returns structured calculation artifacts, not client prose.

- UTC instants use ISO 8601 with `Z` or an explicit `+00:00` offset.
- Ecliptic longitudes are decimal degrees in `[0, 360)`.
- Body and angle keys are lowercase ASCII identifiers.
- Houses are Placidus unless a tool explicitly states another frame.
- Aspect records name both endpoints, aspect type, actual angle, and orb.
- Phase records preserve their source positions, moment, house frame and input hash. A phase is a
  state of a body in that frame; it is not a second dignity or an independently calculated event.
- Functions return dictionaries and lists and do not write client data to disk.

The caller owns persistence, presentation, interpretation, and final report composition. A future
versioned report-kit schema will package several calculation artifacts together; it is not part of
the current public API.


Transit events preserve `estimated_exact_instant_utc`; carrier windows preserve
`estimated_peak_instant_utc`. Both are sampling/interpolation estimates, not separately refined
roots. The published `exact_date` behavior is retained. The workbench experiment's `peak_utc`,
`exact_utc` and context/clipping fields are not part of this release's public transit contract.

`body_states` provides independently verified physical states; `partner_portrait` combines the
fixed natal product with common physical/carrier/phase states. `partner_portrait_kit` and
`horary_kit` each supply five exact documents by closed IDs. Read the relevant kit first;
the user's model composes the reading. See [MCP tools](mcp-api.md) for the full contracts.

## Horary

Read `horary_kit` manifest and all five required documents before `horary(input)`.
They include the full input contract, method, semantic phase core, empty working twin,
reference HTML and report boundary. A document ID is not a path. Content hashes and lengths
identify the exact UTF-8 bytes; the manifest hash uses sorted compact UTF-8 JSON without its
`manifest_sha256` field.

`horary` returns `{facts, wheel_svg, kit, provenance}` without server file writes. Its fixed
profile is tropical/geocentric Regiomontanus, traditional house rulership,
`selected-classical-v1`, seven classical event planets and ten common physical/phase bodies.
An accepted question and a previously fixed real asked/received moment/place are required.
`past_days` defaults to 3; `past_days` and future `scan_days` are integers 3..366.
Extending either range preserves the question chart; the coverage bounds limit claims about
missing events. Unsupported Regiomontanus geometry is an adapter error before houses/sect/SVG,
separate from astrological deferral. Unknown planetary hour is separate from no agreement.

`facts` includes the input, chart, verified `body_states`, shared `carrier_states`, planetary
hour, consideration facts, ordered events with root residuals, `phases`, own-time physical/phase
`phase_samples`, coverage and provenance. H/h remain unavailable; geometric houses are not
phase houses. Common `solar.condition` is an angular-distance label; the chosen Lilly combustion
rule additionally uses same-sign evidence. Declination/OOB/pairs can qualify conditions without
replacing classical perfection. `radicality_verdict` stays null: the client model reviews
radicality before outcome, interprets, writes the twin and then the reading. The response
contains no automatic judgment or client prose.

`kit` equals the actually readable manifest; `provenance` binds its hash and relative operator
hashes. `provenance.input_sha256` and `facts_sha256` hash the input and facts objects using
UTF-8 `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)`.
Use these supplied hashes in MCP-authored twin/HTML metadata; they identify objects and do not
hash arbitrary client file formatting. The CLI manifest instead hashes original input bytes
and actual output file bytes. Filled client files belong under `.private/`; the local CLI
creates a new directory with `facts.json`, `wheel.svg`, then `manifest.json`, preserving
existing outputs. Calculation tests and method compliance do not prove life-event predictions.

