param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$DateTimeUtc,
  [double]$MaxDeltaDeg = 1.0,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)

function Get-MinDelta360 {
  param([double]$A, [double]$B)
  $d = [math]::Abs($A - $B)
  if ($d -gt 180) { $d = 360 - $d }
  return $d
}

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("qc_cross_provider_" + $CaseId)

$primary = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $DateTimeUtc
  latitude = $Latitude
  longitude = $Longitude
}
$backup = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $DateTimeUtc
}

Write-JsonFile -Data $primary -Path (Join-Path $runDir "01_primary_positions.json")
Write-JsonFile -Data $backup -Path (Join-Path $runDir "02_backup_positions.json")

$primaryRows = Get-SwissBodyLongitudes -SwissData $primary
$backupRows = Get-BodyLongitudes -Ephemeris $backup

$mapPrimary = @{}
foreach ($r in $primaryRows) { $mapPrimary[$r.body] = [double]$r.longitude }
$mapBackup = @{}
foreach ($r in $backupRows) { $mapBackup[$r.body] = [double]$r.longitude }

$commonBodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "chiron")
$rows = @()
foreach ($b in $commonBodies) {
  if (-not $mapPrimary.ContainsKey($b)) { continue }
  if (-not $mapBackup.ContainsKey($b)) { continue }

  $p = [double]$mapPrimary[$b]
  $e = [double]$mapBackup[$b]
  $delta = Get-MinDelta360 -A $p -B $e
  $rows += [pscustomobject]@{
    body = $b
    primary_longitude = [math]::Round($p, 9)
    backup_longitude = [math]::Round($e, 9)
    abs_delta_deg = [math]::Round($delta, 9)
    within_threshold = ($delta -le $MaxDeltaDeg)
  }
}

$rows | Sort-Object abs_delta_deg -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runDir "03_longitude_delta_qc.csv")

$failCount = ($rows | Where-Object { -not $_.within_threshold }).Count
$qcStatus = if ($failCount -eq 0) { "PASS" } else { "FAIL" }

$summary = @()
$summary += "CASE_ID=$CaseId"
$summary += "DATETIME_UTC=$DateTimeUtc"
$summary += "LATITUDE=$Latitude"
$summary += "LONGITUDE=$Longitude"
$summary += "PRIMARY=swissremote"
$summary += "BACKUP=ephem"
$summary += "MAX_DELTA_DEG=$MaxDeltaDeg"
$summary += "CHECKED_BODIES=" + $rows.Count
$summary += "FAIL_COUNT=$failCount"
$summary += "QC_STATUS=$qcStatus"
$summary += "OUTPUT_DIR=$runDir"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Cross-provider QC completed: $runDir"
