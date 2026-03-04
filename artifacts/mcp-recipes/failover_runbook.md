# Failover Runbook (Primary -> Backup)

## Goal

Keep astrology processing operational when the primary MCP provider is unavailable.

## Providers

1. Primary: `https://www.theme-astral.me/mcp` (`swissremote`)
2. Backup: `https://ephemeris.fyi/mcp` (`ephem`)

## Trigger Conditions

1. Primary request timeout
2. Transport failure (`HTTP`, TLS, DNS)
3. MCP tool execution error from primary

## Runtime Policy

1. Try primary first for house-enabled output.
2. On primary failure, auto-route to backup.
3. Mark run as `DEGRADED` when fallback was used.
4. Require follow-up house-layer run when degraded output was delivered.

## Command Paths

1. Full run with failover:
   - `run_natal_with_failover.ps1`
2. House-layer recovery after degraded run:
   - `run_house_layer_placidus.ps1`
3. Cross-provider QC:
   - `run_cross_provider_qc.ps1`

## Incident Checklist

1. Capture failing command and timestamp.
2. Re-run with `run_natal_with_failover.ps1`.
3. Confirm `provider_used` and `run_status` in `00_summary.txt`.
4. Run `run_cross_provider_qc.ps1` for affected case.
5. If primary recovered, generate missing house-layer pack.

## Exit Criteria

1. A client-ready pack exists (`PACK_MANIFEST.yaml` status `READY`).
2. If degraded: additional house-layer pack produced after recovery.
3. QC report saved for audit trail.
