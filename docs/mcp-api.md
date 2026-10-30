# MCP tools

The server exposes eleven tools. MCP discovery is the runtime authority for input validation. The
JSON block below records the public discovery contract and is checked against the running server by
`tests/test_mcp_api_contract.py`.

## Signatures

### `rising_hands`

Required inputs: `date: string`, `lat: number`, `lon: number`, `tz: integer`.

Returns twelve ordered watches with local start time and rising sign.

### `natal`

Required inputs: `datetime_utc: string`, `lat: number`, `lon: number`.

Optional inputs: `orb: number = 6.0`, `scheme: string = "modern"`.

Returns positions, Placidus houses and angles, aspects, dignities, phases, sect, placements, and
calculated points in one structure.

### `phase_states`

Required inputs: `positions: object`, `moment_utc: string`.

Optional inputs: `cusps: array | null = null`, `asc_longitude: number | null = null`.

Transforms supplied body longitudes into phase states. It does not calculate ephemerides or verify
where the longitudes came from. Supply either twelve real cusps or an explicit ASC; with neither,
house-dependent states remain unavailable.

### `profection`

Required inputs: `natal_datetime_utc: string`, `lat: number`, `lon: number`,
`return_year: integer`.

There are no optional inputs.

Returns age, profected house and sign, lord of the year, and the lord's natal placement.

### `solar_return`

Required inputs: `natal_datetime_utc: string`, `birth_lat: number`, `birth_lon: number`,
`return_year: integer`.

Optional inputs: `sr_lat: number | null = null`, `sr_lon: number | null = null`,
`orb: number = 2.0`, `scheme: string = "modern"`.

Returns the calculated return instant, natal and return phase states, return chart structure,
directed return-to-natal aspects, and annual profection.

### `transits`

Required inputs: `natal_datetime_utc: string`, `lat: number`, `lon: number`,
`range_start_utc: string`, `range_end_utc: string`.

Optional inputs: `step_days: number = 7.0`, `orb: number = 1.0`,
`solar_year_start_utc: string | null = null`.

Returns dated exact-pass events and merged carrier windows. Every timeline event includes
`estimated_exact_instant_utc`; every carrier window includes the corresponding
`estimated_peak_instant_utc` of its tightest pass. These instants come from interpolation over the
configured sampling step and are not separately refined astronomical roots.

For a phase-aware reading, select an event that carries a conclusion, calculate `natal` at its
estimated instant, then pass only that response's `positions` to `phase_states` without cusps.
This provides Z/z/D for the transiting body without inventing local H/h for a period scan.

### `body_states`

Required input: `datetime_utc: string`. Optional: `bodies: string[] | null = null`.

Independent Engine A physical API, default ten planets; additionally supports `north_node`
(true node), `lilith` (mean apogee), and `chiron`. UTC includes seconds and `Z` or `+00:00`;
up to six fractional digits are retained. Returns `version`, `moment_utc`, `coordinate_system`,
named `bodies`, true/mean `obliquity`, and `provenance`. Geocentric tropical apparent coordinates
of date carry real latitude, longitude speed, equatorial declination, units, body model,
requested/returned Swiss flags, library versions and verified runtime file/operator hashes.
The file set is not a claim that each file was read for every body. B1 full states are unsupported;
no engine fallback is made. Nonempty `SE_EPHE_PATH` is rejected: configure `SWISS_EPHE_PATH`.


### `partner_portrait_kit`

Optional input: `document = "manifest"`, one of `manifest`, `recipe`, `sources`, `twin`, `html`,
`boundary`. This is a closed document-ID allowlist, not a filesystem or URL reader.

The manifest contains `kit_id`, `kit_version`, `profile`, `available_layers`, `unavailable_layers`
and exactly five `documents`. Each entry names `id`, `role`, relative `source_path`, `mime_type`,
`byte_length`, `sha256`, and `required=true`. A document response adds the entire UTF-8 `content`;
the hash and length refer to those exact bytes without newline normalization. HTML is source data.
Missing/invalid required material returns an error. Neither checkout access nor MCP resource
support is required. `manifest_sha256` hashes the manifest without that field, serialized as
UTF-8 JSON with sorted keys, `ensure_ascii=False`, compact separators and no nonfinite numbers.


### `partner_portrait`

Required inputs: `datetime_utc: string`, `lat: number`, `lon: number`,
`partner: "women" | "men"`. Optional: `orb: number = 6.0`, finite in `[0,15]`.
Nonzero fractional seconds are explicitly rejected to preserve the existing natal boundary;
the standalone physical API retains them. Coordinates must be finite, `lat` in `[-90,90]`
and `lon` in `[-180,180]`. Requires selected Engine A and a usable Placidus input.

Read `partner_portrait_kit` manifest and all five documents before interpreting or choosing images.
The product fixes tropical/geocentric Placidus, ten planets, traditional rulership,
`selected-classical-v1`, five major aspects and the common modern phase operator. Women selects
Moon/Venus/VII; men Sun/Mars/VII. Birth source/time quality remains the author's responsibility;
unknown time does not support this full house/DSC product.

Returns the full `natal`, shared `phase_states`, existing lots/subdivisions/directed contacts,
real `motion_input`, `body_states`, engine-free `carrier_states`, `provenance` and `kit` equal to
the actually readable manifest. Carrier layers include instantaneous motion, solar geometry,
declination/OOB/pairs, compatible essential dignities/debilities and directed dignity-holdings
evidence. Tables preserve separately identified Lilly/Ptolemaic day/night triplicity without a
participant, Egyptian/Ashmand terms and Firmicus/Chaldean faces. `tables.*.sha256` hashes each
selected serialized JSON table, not historical book bytes. No score or automatic reception
verdict is calculated. Future perfection, station events and heliacal visibility remain unavailable.
The server supplies materials and numbers; the user's model composes the interpretation and prose.

The nine preexisting tool signatures, defaults, descriptions and results remain unchanged.
New calculation/runtime errors return bounded messages without absolute host paths.


### `horary_kit`

Optional `document = "manifest"`: `manifest`, `recipe`, `sources`, `twin`, `html`, `boundary`.
Read the manifest and all five complete UTF-8 documents before calculations or judgment.
Like partner kit, this fixed-ID reader returns exact bytes, hashes and lengths; no checkout,
resource support, hidden local reference or filesystem path is required. Its recipe contains
all nested input fields and the phase sources contain the portable semantic kernel.


### `horary`

Required `input: object` follows `astrolab.horary.input.v1`, fully described in the kit recipe.
One reviewed accepted question and an explicit fixed asked/received date/time/place are required;
missing data must be clarified. Engine A only, tropical/geocentric Regiomontanus, traditional
rulers, seven classical event bodies, ten shared physical/carrier/phase bodies. `past_days`
defaults to 3; past/future scan bounds are integers 3..366. H/h unavailable.

Returns `{facts, wheel_svg, kit, provenance}`. Physical states use verified ephemerides without
fallback; unsupported Regiomontanus geometry stops before houses/sect/SVG. The model reviews
radicality before outcome, writes the twin and reading; the server writes no files or prose and
returns `radicality_verdict=null`. The kit hash binds actual documents. Input/facts canonical JSON
hashes are supplied for client metadata; see [output contract](output-contract.md#horary).


## Examples

With the HTTP server listening on `127.0.0.1:8400`:

```console
uv run python examples/call_mcp.py rising_hands
uv run python examples/call_mcp.py natal
uv run python examples/call_mcp.py chart_workflow
uv run python examples/call_mcp.py invalid_input
uv run python examples/call_mcp.py products_workflow
```

The first two commands print individual structured results. `chart_workflow` performs one connected
natal -> solar return -> transit task and checks the relationships between the three responses.
`products_workflow` verifies both complete kits against the allowed source bytes, exercises body,
partner and horary calculations and rejects an unaccepted horary input. It prints a compact summary.
`invalid_input` sends an extra `scheme` field to `profection` and succeeds only when the MCP
boundary rejects it.

## Value checks

Datetime inputs marked UTC must contain an explicit zero offset (`Z` or `+00:00`). Latitudes are
limited to `-90..90`, longitudes to `-180..180`, and orbs cannot be negative. Transit ranges must
end after they start and `step_days` must be greater than zero. Solar-return relocation accepts
`sr_lat` and `sr_lon` only as a complete pair. `phase_states` accepts lowercase ASCII body names
and either `cusps` or `asc_longitude`, never both.

## Discovery contract

`additionalProperties: false` means that each tool rejects input fields not listed in its schema.
The current functions return plain dictionaries, so discovery describes every output as an open
object rather than enumerating its fields.

<!-- mcp-contract:start -->
```json
[
  {
    "name": "rising_hands",
    "description": "Compute the day's rising-sign watches (the floating rising-sign clock, minute hand).",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "date": {
          "type": "string",
          "description": "day to scan, \"yyyy-MM-dd\"."
        },
        "lat": {
          "type": "number",
          "description": "observation latitude (degrees)."
        },
        "lon": {
          "type": "number",
          "description": "observation longitude (degrees)."
        },
        "tz": {
          "type": "integer",
          "description": "local-time DISPLAY offset in whole hours (e.g. 3 for Krasnodar)."
        }
      },
      "required": [
        "date",
        "lat",
        "lon",
        "tz"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "natal",
    "description": "Assemble the natal chart structure for a UTC birth instant.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "datetime_utc": {
          "type": "string",
          "description": "birth instant in UTC, \"yyyy-MM-ddTHH:MM:SSZ\" (ISO 8601)."
        },
        "lat": {
          "type": "number",
          "description": "birth latitude (degrees)."
        },
        "lon": {
          "type": "number",
          "description": "birth longitude (degrees)."
        },
        "orb": {
          "default": 6.0,
          "type": "number",
          "description": "major-aspect orb in degrees."
        },
        "scheme": {
          "default": "modern",
          "type": "string",
          "description": "essential-dignity scheme, \"modern\" or \"traditional\"."
        }
      },
      "required": [
        "datetime_utc",
        "lat",
        "lon"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "phase_states",
    "description": "Transform supplied body longitudes into phase states; no ephemeris is calculated.\n\nThe caller supplies positions for one UTC instant and may supply either twelve real\nhouse cusps or an explicit ASC for the equal-house special case. With neither, H/h\nremain unavailable. The input hash identifies the supplied values, not their source.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "positions": {
          "additionalProperties": {
            "type": "number"
          },
          "type": "object"
        },
        "moment_utc": {
          "type": "string"
        },
        "cusps": {
          "anyOf": [
            {
              "items": {
                "type": "number"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "asc_longitude": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "required": [
        "positions",
        "moment_utc"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "profection",
    "description": "Annual profection (whole-sign timelord) of a solar year, straight from birth data.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "natal_datetime_utc": {
          "type": "string",
          "description": "birth instant in UTC, \"yyyy-MM-ddTHH:MM:SSZ\" (ISO 8601)."
        },
        "lat": {
          "type": "number",
          "description": "birth latitude (degrees)."
        },
        "lon": {
          "type": "number",
          "description": "birth longitude (degrees)."
        },
        "return_year": {
          "type": "integer",
          "description": "calendar year of the solar return (age = return_year - birth year)."
        }
      },
      "required": [
        "natal_datetime_utc",
        "lat",
        "lon",
        "return_year"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "solar_return",
    "description": "Solar-return chart for a solar year: TRUE Sun-return instant (bisection, not the naive\nbirthday chart) + the SR chart cast at that instant for the return location.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "natal_datetime_utc": {
          "type": "string",
          "description": "birth instant in UTC, \"yyyy-MM-ddTHH:MM:SSZ\" (ISO 8601)."
        },
        "birth_lat": {
          "type": "number"
        },
        "birth_lon": {
          "type": "number"
        },
        "return_year": {
          "type": "integer",
          "description": "calendar year of the return."
        },
        "sr_lat": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "sr_lon": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "orb": {
          "default": 2.0,
          "type": "number",
          "description": "cross-aspect orb in degrees (return->natal, classical 10 bodies)."
        },
        "scheme": {
          "default": "modern",
          "type": "string",
          "description": "essential-dignity scheme, \"modern\" or \"traditional\"."
        }
      },
      "required": [
        "natal_datetime_utc",
        "birth_lat",
        "birth_lon",
        "return_year"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "transits",
    "description": "Transit timeline over a period: dated exact-pass EVENTS of transiting bodies (sun..pluto +\nnorth node; no Moon — daily steps can't resolve it) over natal planets and angles, plus\nCARRIER WINDOWS — slow movers' retro passes merged into one open->exact(s)->close theme.\nEvent and peak instants are estimates from the configured sampling step, not separately\nrefined astronomical roots.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "natal_datetime_utc": {
          "type": "string",
          "description": "birth instant in UTC, \"yyyy-MM-ddTHH:MM:SSZ\"."
        },
        "lat": {
          "type": "number"
        },
        "lon": {
          "type": "number"
        },
        "range_start_utc": {
          "type": "string"
        },
        "range_end_utc": {
          "type": "string"
        },
        "step_days": {
          "default": 7.0,
          "type": "number",
          "description": "sampling step (use 2-3 for clean carrier windows; default 7)."
        },
        "orb": {
          "default": 1.0,
          "type": "number",
          "description": "event orb in degrees (default 1.0)."
        },
        "solar_year_start_utc": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "OPTIONAL solar-return instant — adds zone (tail/core/horizon) to\neach carrier window and drops themes that closed before the year opened."
        }
      },
      "required": [
        "natal_datetime_utc",
        "lat",
        "lon",
        "range_start_utc",
        "range_end_utc"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "body_states",
    "description": "Calculate named physical states and provenance with Engine A; fractional UTC seconds are retained.\n\nGeocentric tropical apparent coordinates of date include real latitude, numerical longitude\nspeed and equatorial declination. Default: ten planets. Also supports true north node,\nmean-apogee Lilith and Chiron. This is independent of partner portraits and calculates no prose.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "datetime_utc": {
          "type": "string"
        },
        "bodies": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "required": [
        "datetime_utc"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "partner_portrait_kit",
    "description": "Read the partner portrait manifest or one of its five complete UTF-8 documents by fixed ID.\n\nNo checkout or resource support is required. Hashes and byte lengths identify the exact\ndelivered texts. HTML is returned as source data; this tool accepts no filesystem path.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "document": {
          "default": "manifest",
          "enum": [
            "manifest",
            "recipe",
            "sources",
            "twin",
            "html",
            "boundary"
          ],
          "type": "string"
        }
      },
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "partner_portrait",
    "description": "Build partner portrait calculations; read partner_portrait_kit before interpreting or choosing images.\n\nRequires known birth time at whole UTC seconds and selected Engine A. Fixed tropical,\ngeocentric, Placidus, ten-planet selected-classical-v1 profile; women uses Moon/Venus/VII,\nmen Sun/Mars/VII. Returns the natal, common phases, physical/carrier states, existing\nderivatives and exact readable-kit manifest. The user's model writes the interpretation.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "datetime_utc": {
          "type": "string"
        },
        "lat": {
          "type": "number"
        },
        "lon": {
          "type": "number"
        },
        "partner": {
          "enum": [
            "women",
            "men"
          ],
          "type": "string"
        },
        "orb": {
          "default": 6.0,
          "type": "number"
        }
      },
      "required": [
        "datetime_utc",
        "lat",
        "lon",
        "partner"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "horary_kit",
    "description": "Read the horary manifest or one of five complete UTF-8 documents by fixed ID.\n\nRead the manifest and all five before horary calculations or judgment. The recipe includes\nthe full input contract; no checkout or hidden reference is needed. Hashes identify exact\ndelivered bytes. HTML is source data; no filesystem path is accepted.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "document": {
          "default": "manifest",
          "enum": [
            "manifest",
            "recipe",
            "sources",
            "twin",
            "html",
            "boundary"
          ],
          "type": "string"
        }
      },
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  {
    "name": "horary",
    "description": "Compute reviewed horary facts and wheel SVG; read horary_kit and all five documents first.\n\ninput follows astrolab.horary.input.v1 in the recipe: one accepted question and a fixed,\nexplicit asked/received moment/place. Engine A only, tropical/geocentric Regiomontanus,\ntraditional rulership; seven event planets, ten common physical/carrier/phase states.\npast_days defaults to 3; past_days and scan_days accept integers 3..366. H/h unavailable.\nReturns facts, wheel_svg, kit and provenance; no files, prose or automatic radicality.\nThe client model judges the chart before its outcome and writes the twin and reading.",
    "inputSchema": {
      "additionalProperties": false,
      "properties": {
        "input": {
          "additionalProperties": true,
          "type": "object"
        }
      },
      "required": [
        "input"
      ],
      "type": "object"
    },
    "outputSchema": {
      "additionalProperties": true,
      "type": "object"
    }
  }
]
```
<!-- mcp-contract:end -->
