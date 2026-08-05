# Output contract

Astrolab returns structured calculation artifacts, not client prose.

- UTC instants use ISO 8601 with a trailing `Z`.
- Ecliptic longitudes are decimal degrees in `[0, 360)`.
- Body and angle keys are lowercase ASCII identifiers.
- Houses are Placidus unless a tool explicitly states another frame.
- Aspect records name both endpoints, aspect type, actual angle, and orb.
- Functions return dictionaries and lists and do not write client data to disk.

The caller owns persistence, presentation, interpretation, and final report composition. A future
versioned report-kit schema will package several calculation artifacts together; it is not part of
the current public API.

