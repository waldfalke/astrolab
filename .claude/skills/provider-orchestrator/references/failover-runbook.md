# Failover Decision Rules

## When to Failover

Failover from primary to backup is triggered by:

1. **Timeout** — No response within 30 seconds
2. **Transport Error** — HTTP failure, TLS error, DNS failure
3. **MCP Tool Error** — Tool execution exception from primary
4. **Rate Limit** — 429 Too Many Requests (after retry exhaustion)

## When NOT to Failover

Do NOT failover for:

1. **Auth Errors** — `AUTH_FAILED`, `401 Unauthorized`, `403 Forbidden`
   - These are configuration issues, not provider issues
   - User must fix credentials before retry

2. **Invalid Parameters** — `400 Bad Request`
   - Fix the input parameters first

3. **Tool Not Found** — Provider doesn't have requested tool
   - This is a capability mismatch, not availability issue

## Retry Logic

```
Attempt 1: Call primary
  ↓ (failure)
Attempt 2: Retry primary (wait 1s)
  ↓ (failure)
Attempt 3: Retry primary (wait 2s)
  ↓ (failure)
Failover: Switch to backup
```

**Backoff:** Exponential (1s, 2s, 4s...)
**Max Retries:** 2 (3 total attempts)

---

## QC Decision Rules

### When to Run QC

| Scenario | QC Required? |
|---|---|
| Primary available | YES — call backup for comparison |
| Primary failed, backup used | NO — skip QC |
| Fallback used | NO — skip QC |
| User explicitly requests | YES — always |

### QC Pass/Fail Criteria

```
For each planet:
  delta = |primary_lon - backup_lon|
  if delta > 180: delta = 360 - delta  # shortest arc

max_delta = max(all planet deltas)

if max_delta < 1.0°:
  QC = PASS
else:
  QC = FAIL (flag specific planets)
```

### QC Failure Handling

If QC fails:

1. Flag specific planets with high delta
2. Include delta values in report
3. Still return primary data (it's usually correct)
4. Mark for manual review if delta > 2.0°

---

## Status Reporting

### Run Status Values

| Status | When Used |
|---|---|
| `FULL` | Primary used, QC passed |
| `DEGRADED` | Backup or fallback used |
| `FAILED` | All providers unavailable |

### Provider Status Format

```
PROVIDER STATUS:
  Primary (swissremote): AVAILABLE → USED
  Backup (ephemeris): AVAILABLE → QC ONLY
  Fallback (vedastro): NOT USED

RUN STATUS: FULL
```

---

## Incident Checklist

When failover occurs:

- [ ] Capture failing command and timestamp
- [ ] Note failover reason (timeout, auth, etc.)
- [ ] Confirm backup provider used
- [ ] Check `00_summary.txt` for `provider_used` and `run_status`
- [ ] Run cross-provider QC when primary recovers
- [ ] Generate missing house-layer pack if degraded

---

## Recovery Procedure

After primary provider recovers:

1. Re-run affected calculations with primary
2. Run cross-provider QC to confirm recovery
3. Generate any missing packs (house-layer, etc.)
4. Update incident log
