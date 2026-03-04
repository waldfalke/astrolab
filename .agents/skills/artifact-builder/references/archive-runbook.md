# Archive Runbook

## Overview

Archive old method runs to clean up `artifacts/results/` while preserving chart-project integrity.

## When to Archive

- Runs older than 30 days
- After delivery pack is built
- Before disk space runs low

## Archive Process

### Step 1: Identify Old Runs

```powershell
# Find runs older than 30 days
$oldRuns = Get-ChildItem "artifacts/results/" -Directory |
  Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) }
```

### Step 2: Create Archive Batch

```powershell
$batchName = "{0}_{1}_archive" -f $chartId, (Get-Date -Format "yyyyMMdd_HHmmss")
$archivePath = "artifacts/results/_archive/$batchName/"
New-Item -ItemType Directory -Force -Path $archivePath
```

### Step 3: Move Runs

```powershell
foreach ($run in $oldRuns) {
  Move-Item -Path $run.FullName -Destination $archivePath
}
```

### Step 4: Rewrite INDEX.yaml

Update `external_source` paths:

```yaml
# Before:
external_source: D:\Dev\CATMEastrolab\artifacts\results\natal_failover_...

# After:
external_source: D:\Dev\CATMEastrolab\artifacts\results\_archive\batch_...\natal_failover_...
```

### Step 5: Generate Verification Report

```json
{
  "archive_batch": "tuapse_19820613_20260304_143000_archive",
  "archived_at": "2026-03-04T14:30:00Z",
  "runs_archived": 4,
  "archive_location": "artifacts/results/_archive/...",
  "index_rewrite": {
    "external_sources_updated": 16,
    "all_paths_valid": true
  },
  "verification": {
    "all_files_moved": true,
    "all_links_updated": true,
    "canonical_sources_intact": true
  }
}
```

---

## Verification Checklist

After archive:

- [ ] All `canonical_source` paths still exist (in `methods/`)
- [ ] All `external_source` paths updated to archive location
- [ ] `external_source_exists` flags are correct
- [ ] No broken links in INDEX.yaml
- [ ] Verification report generated

---

## Recovery Procedure

If archive breaks something:

1. Check verification report for errors
2. Restore from `artifacts/results/_archive/` if needed
3. Manually fix INDEX.yaml entries
4. Re-run validation

---

## Archive Retention

| Archive Age | Action |
|---|---|
| < 90 days | Keep in `_archive/` |
| 90-365 days | Consider external backup |
| > 365 days | Delete if no client access needed |

**Note:** `canonical_source` files in `methods/` are NEVER archived — they stay with chart project.
