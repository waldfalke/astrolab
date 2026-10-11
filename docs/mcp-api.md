# MCP tools

The server exposes six tools. MCP discovery is the runtime authority for input validation. The
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

Returns dated exact-pass events and merged carrier windows.

## Examples

With the HTTP server listening on `127.0.0.1:8400`:

```console
uv run python examples/call_mcp.py rising_hands
uv run python examples/call_mcp.py natal
uv run python examples/call_mcp.py chart_workflow
uv run python examples/call_mcp.py invalid_input
```

The first two commands print individual structured results. `chart_workflow` performs one connected
natal -> solar return -> transit task and checks the relationships between the three responses.
The final command sends an extra `scheme` field to `profection` and succeeds only when the MCP
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
    "description": "Transit timeline over a period: dated exact-pass EVENTS of transiting bodies (sun..pluto +\nnorth node; no Moon — daily steps can't resolve it) over natal planets and angles, plus\nCARRIER WINDOWS — slow movers' retro passes merged into one open->exact(s)->close theme.",
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
  }
]
```
<!-- mcp-contract:end -->
