param(
  [string]$RunsRoot = "",
  [string]$Filter = "*",
  [string]$ArchiveRoot = "",
  [string]$ChartsRoot = "",
  [string]$ChartId = "",
  [switch]$Execute,
  [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RunsRoot)) {
  $RunsRoot = Join-Path $PSScriptRoot "..\results"
}
if ([string]::IsNullOrWhiteSpace($ArchiveRoot)) {
  $ArchiveRoot = Join-Path $PSScriptRoot "..\results\_archive"
}
if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}

$RunsRoot = [System.IO.Path]::GetFullPath($RunsRoot)
$ArchiveRoot = [System.IO.Path]::GetFullPath($ArchiveRoot)
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)

if (-not (Test-Path $RunsRoot)) { throw "RunsRoot not found: $RunsRoot" }
if (-not (Test-Path $ChartsRoot)) { throw "ChartsRoot not found: $ChartsRoot" }
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null

$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$batchName = "archive_batch_" + $ts
$batchDir = Join-Path $ArchiveRoot $batchName

$reportPathProvided = -not [string]::IsNullOrWhiteSpace($ReportPath)
if ($reportPathProvided) {
  $ReportPath = [System.IO.Path]::GetFullPath($ReportPath)
} else {
  if ($Execute) {
    $ReportPath = Join-Path $batchDir "archive_report.json"
  } else {
    $ReportPath = Join-Path $ArchiveRoot ("archive_report_dryrun_" + $ts + ".json")
  }
}

$runs = @(Get-ChildItem -Path $RunsRoot -Directory | Where-Object {
  $_.Name -like $Filter -and $_.FullName -ne $ArchiveRoot -and $_.Name -ne "_archive"
})

if ($runs.Count -eq 0) {
  if (-not $reportPathProvided) {
    $ReportPath = Join-Path $ArchiveRoot ("archive_report_empty_" + $ts + ".json")
  }
  $emptyReportDir = Split-Path -Path $ReportPath -Parent
  if (-not [string]::IsNullOrWhiteSpace($emptyReportDir)) {
    New-Item -ItemType Directory -Force -Path $emptyReportDir | Out-Null
  }
  $emptyReport = [pscustomobject]@{
    mode = $(if ($Execute) { "execute" } else { "dry-run" })
    runs_root = $RunsRoot
    archive_root = $ArchiveRoot
    batch_dir = $batchDir
    moved_count = 0
    affected_charts = @()
    index_updates = @()
    verification = @()
    generated_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
  }
  $emptyReport | ConvertTo-Json -Depth 10 | Set-Content -Path $ReportPath -Encoding UTF8
  Write-Output "CANDIDATE_RUNS=0"
  Write-Output "AFFECTED_CHARTS=0"
  Write-Output ("MODE=" + $(if ($Execute) { "execute" } else { "dry-run" }))
  Write-Output "REPORT_PATH=$ReportPath"
  Write-Output "No runs matched filter."
  exit 0
}

$plan = @()
foreach ($r in $runs) {
  $src = [System.IO.Path]::GetFullPath($r.FullName)
  $dst = Join-Path $batchDir $r.Name
  $plan += [pscustomobject]@{
    name = $r.Name
    source = $src
    destination = $dst
  }
}

function Rewrite-PathByMap {
  param(
    [Parameter(Mandatory = $true)][string]$Value,
    [Parameter(Mandatory = $true)][array]$MapRows
  )

  foreach ($m in $MapRows) {
    $old = [string]$m.source
    $new = [string]$m.destination
    if ($Value.Equals($old, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $new
    }
    $prefix = $old + "\"
    if ($Value.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
      $suffix = $Value.Substring($old.Length)
      return ($new + $suffix)
    }
  }
  return $Value
}

function Get-ChartDirs {
  param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string]$SingleChartId = ""
  )

  if ([string]::IsNullOrWhiteSpace($SingleChartId)) {
    return @(Get-ChildItem -Path $Root -Directory | Where-Object { Test-Path (Join-Path $_.FullName "INDEX.yaml") })
  }
  $d = Join-Path $Root $SingleChartId
  if (-not (Test-Path (Join-Path $d "INDEX.yaml"))) {
    throw "Chart index not found: $d"
  }
  return @([System.IO.DirectoryInfo]$d)
}

function Update-ChartIndexByMap {
  param(
    [Parameter(Mandatory = $true)][string]$IndexPath,
    [Parameter(Mandatory = $true)][array]$MapRows,
    [switch]$WriteChanges
  )

  $lines = Get-Content -Path $IndexPath
  $out = @()
  $changes = 0

  foreach ($line in $lines) {
    if ($line -match "^(\s*)(source_run_dir|external_source_run_dir|external_source):\s*(.+)$") {
      $indent = $Matches[1]
      $key = $Matches[2]
      $raw = $Matches[3].Trim()
      $oldValue = $raw
      $newValue = Rewrite-PathByMap -Value $oldValue -MapRows $MapRows
      if ($newValue -ne $oldValue) { $changes++ }
      $out += ($indent + $key + ": " + $newValue)
      continue
    }
    $out += $line
  }

  if ($WriteChanges -and ($changes -gt 0)) {
    Set-Content -Path $IndexPath -Encoding UTF8 -Value $out
  }

  return $changes
}

function Verify-ExternalRefs {
  param([Parameter(Mandatory = $true)][string]$IndexPath)

  $lines = Get-Content -Path $IndexPath
  $total = 0
  $missing = 0

  foreach ($line in $lines) {
    if ($line -match "^\s*(external_source_run_dir|external_source):\s*(.+)$") {
      $p = $Matches[2].Trim()
      if ($p -eq "n/a") { continue }
      $total++
      if (-not (Test-Path $p)) { $missing++ }
    }
  }
  return [pscustomobject]@{
    total = $total
    missing = $missing
  }
}

$chartDirs = Get-ChartDirs -Root $ChartsRoot -SingleChartId $ChartId
$indexUpdates = @()
$affectedCharts = @()

if ($Execute) {
  New-Item -ItemType Directory -Force -Path $batchDir | Out-Null
  foreach ($p in $plan) {
    Move-Item -Path $p.source -Destination $p.destination -Force
  }
}

foreach ($c in $chartDirs) {
  $idx = Join-Path $c.FullName "INDEX.yaml"
  $changeCount = Update-ChartIndexByMap -IndexPath $idx -MapRows $plan -WriteChanges:$Execute
  if ($changeCount -gt 0) {
    $affectedCharts += $c.Name
  }
  $verify = Verify-ExternalRefs -IndexPath $idx
  $indexUpdates += [pscustomobject]@{
    chart_id = $c.Name
    index_path = $idx
    changed_lines = $changeCount
    external_refs_total = $verify.total
    external_refs_missing = $verify.missing
  }
}

$verificationFail = @($indexUpdates | Where-Object { $_.external_refs_missing -gt 0 }).Count
$report = [pscustomobject]@{
  mode = $(if ($Execute) { "execute" } else { "dry-run" })
  runs_root = $RunsRoot
  archive_root = $ArchiveRoot
  batch_dir = $batchDir
  moved_count = $plan.Count
  moved_runs = $plan
  affected_charts = @($affectedCharts | Sort-Object -Unique)
  index_updates = $indexUpdates
  verification = [pscustomobject]@{
    charts_checked = $chartDirs.Count
    charts_with_missing_external_refs = $verificationFail
  }
  generated_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
}

if ($Execute -and -not (Test-Path $batchDir)) {
  New-Item -ItemType Directory -Force -Path $batchDir | Out-Null
}
$reportDir = Split-Path -Path $ReportPath -Parent
if (-not [string]::IsNullOrWhiteSpace($reportDir)) {
  New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}
$report | ConvertTo-Json -Depth 20 | Set-Content -Path $ReportPath -Encoding UTF8

Write-Output ("MODE=" + $(if ($Execute) { "execute" } else { "dry-run" }))
Write-Output ("CANDIDATE_RUNS=" + $plan.Count)
Write-Output ("AFFECTED_CHARTS=" + (@($affectedCharts | Sort-Object -Unique).Count))
Write-Output ("VERIFICATION_FAIL_CHARTS=" + $verificationFail)
Write-Output ("BATCH_DIR=" + $batchDir)
Write-Output ("REPORT_PATH=" + $ReportPath)

if ($verificationFail -gt 0) {
  throw "Archive completed with missing external refs in one or more chart indexes."
}

if ($Execute) {
  Write-Output "Archive run complete (execute)."
} else {
  Write-Output "Archive run complete (dry-run)."
}
