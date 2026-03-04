# Provider Profiles

## Primary Provider: Swiss Ephemeris (swissremote)

**URL:** `https://www.theme-astral.me/mcp`

**Tools:**
- `get_planet_positions` — Planetary longitudes, signs, houses, retrograde status
- `get_house_cusps` — Placidus house cusps
- `get_aspects` — Major aspects (conjunction, opposition, trine, square, sextile)
- `get_synastry` — Cross-chart aspect matrix

**Authentication:** API key via `SWISS_REMOTE_API_KEY` environment variable

**Response Format:**
```json
{
  "planets": [
    {"name": "Sun", "longitude": 72.453, "sign": "Gemini", "sign_degree": 22.45, "house": 10, "retrograde": false}
  ],
  "houses": [
    {"number": 1, "cusp": 256.34, "sign": "Sagittarius"}
  ],
  "aspects": [
    {"planet1": "Sun", "planet2": "Moon", "type": "sextile", "angle": 84.44, "orb": 5.56}
  ]
}
```

**Latency:** ~1-2 seconds typical

**Reliability:** 95%+ uptime, occasional timeouts during peak hours

---

## Backup Provider: Ephemeris (ephem)

**URL:** `https://ephemeris.fyi/mcp`

**Tools:**
- `positions` — Planetary longitudes
- `aspects` — Aspect calculations
- `moon_phase` — Moon phase information

**Authentication:** None required (public API)

**Response Format:**
```json
{
  "data": {
    "bodies": [
      {"id": "sun", "lon": 72.451, "sign": "gemini", "deg": 22.45}
    ]
  }
}
```

**Latency:** ~500ms typical

**Reliability:** 99%+ uptime, no auth issues

---

## Fallback Provider: Vedastro

**URL:** `https://mcp.vedastro.org/api/mcp`

**Tools:**
- `GetPlanetaryPositions` — Vedic-style planetary positions
- `GetHouseCusps` — Whole sign houses (not Placidus)

**Authentication:** API key via `VEDASTRO_API_KEY` environment variable

**Use Case:** Last resort when both primary and backup unavailable

**Note:** Uses different house system and ephemeris — QC comparison not recommended

---

## Failover Decision Tree

```
Start: User requests calculation
  │
  ├─→ Call Primary (swissremote)
  │   ├─ Success → Call Backup for QC → Compare → Return result
  │   └─ Timeout/Error → Retry (max 2)
  │       └─ Still failing → Switch to Backup
  │
  ├─→ Call Backup (ephemeris)
  │   ├─ Success → Mark DEGRADED, skip QC → Return result
  │   └─ Timeout/Error → Retry (max 2)
  │       └─ Still failing → Switch to Fallback
  │
  └─→ Call Fallback (vedastro)
      ├─ Success → Mark DEGRADED, skip QC → Return result
      └─ Failure → Return FAILED, suggest retry later
```

---

## QC Thresholds

| Metric | Threshold | Action |
|---|---|---|
| Max planet delta | 1.0° | QC FAIL if exceeded |
| Typical delta | 0.01° - 0.1° | Expected range |
| Orb for QC | 6° | Only check planets within orb |

---

## Error Codes

| Code | Meaning | Action |
|---|---|---|
| `TIMEOUT` | Provider didn't respond in 30s | Retry or failover |
| `AUTH_FAILED` | Invalid/missing API key | Fix credentials, don't failover |
| `RATE_LIMITED` | Too many requests | Wait and retry (exponential backoff) |
| `TOOL_NOT_FOUND` | Tool unavailable on provider | Switch provider |
| `INVALID_PARAMS` | Bad input parameters | Fix params, don't retry |
