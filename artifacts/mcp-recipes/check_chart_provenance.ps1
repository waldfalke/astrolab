param(
  [string]$ChartId = "",
  [string]$ChartsRoot = "",
  [switch]$FailOnExternalMissing,
  [string]$OutputCsv = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)

if (-not (Test-Path $ChartsRoot)) {
  throw "ChartsRoot not found: $ChartsRoot"
}

$chartDirs = @()
if ([string]::IsNullOrWhiteSpace($ChartId)) {
  $chartDirs = @(Get-ChildItem -Path $ChartsRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName "INDEX.yaml") })
} else {
  $d = Join-Path $ChartsRoot $ChartId
  if (-not (Test-Path (Join-Path $d "INDEX.yaml"))) {
    throw "Chart index not found: $d"
  }
  $chartDirs = @([System.IO.DirectoryInfo]$d)
}

function Clean-Value {
  param([string]$Value)
  $x = $Value.Trim()
  if (($x.StartsWith("'") -and $x.EndsWith("'")) -or ($x.StartsWith('"') -and $x.EndsWith('"'))) {
    return $x.Substring(1, $x.Length - 2)
  }
  return $x
}

$rows = @()
foreach ($chart in $chartDirs) {
  $chartPath = $chart.FullName
  $indexPath = Join-Path $chartPath "INDEX.yaml"
  $lines = Get-Content -Path $indexPath

  foreach ($line in $lines) {
    if ($line -match "^\s*canonical_run_dir:\s*(.+)$") {
      $rel = Clean-Value -Value $Matches[1]
      if ([string]::IsNullOrWhiteSpace($rel)) { continue }
      $abs = Join-Path $chartPath $rel
      $exists = Test-Path $abs
      $rows += [pscustomobject]@{
        chart_id = $chart.Name
        ref_type = "canonical_run_dir"
        ref = $rel
        exists = $exists
        path = $abs
      }
    } elseif ($line -match "^\s*canonical_source:\s*(.+)$") {
      $rel = Clean-Value -Value $Matches[1]
      if ([string]::IsNullOrWhiteSpace($rel)) { continue }
      $abs = Join-Path $chartPath $rel
      $exists = Test-Path $abs
      $rows += [pscustomobject]@{
        chart_id = $chart.Name
        ref_type = "canonical_source"
        ref = $rel
        exists = $exists
        path = $abs
      }
    } elseif ($line -match "^\s*external_source:\s*(.+)$") {
      $ext = Clean-Value -Value $Matches[1]
      if (($ext -eq "n/a") -or [string]::IsNullOrWhiteSpace($ext)) { continue }
      $exists = Test-Path $ext
      $rows += [pscustomobject]@{
        chart_id = $chart.Name
        ref_type = "external_source"
        ref = $ext
        exists = $exists
        path = $ext
      }
    }
  }
}

if (-not [string]::IsNullOrWhiteSpace($OutputCsv)) {
  $rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutputCsv
}

$canonRows = @($rows | Where-Object { $_.ref_type -like "canonical_*" })
$canonFail = @($canonRows | Where-Object { -not $_.exists }).Count
$extRows = @($rows | Where-Object { $_.ref_type -eq "external_source" })
$extFail = @($extRows | Where-Object { -not $_.exists }).Count

Write-Output ("CHARTS_CHECKED=" + $chartDirs.Count)
Write-Output ("CANONICAL_REFS=" + $canonRows.Count)
Write-Output ("CANONICAL_MISSING=" + $canonFail)
Write-Output ("EXTERNAL_REFS=" + $extRows.Count)
Write-Output ("EXTERNAL_MISSING=" + $extFail)

if ($canonFail -gt 0) {
  $bad = $canonRows | Where-Object { -not $_.exists } | Select-Object -First 20
  $bad | Format-Table chart_id, ref_type, ref -AutoSize | Out-String | Write-Output
  throw "Canonical provenance integrity check failed."
}

if ($FailOnExternalMissing -and ($extFail -gt 0)) {
  throw "External provenance check failed."
}

Write-Output "Chart provenance integrity: PASS"
