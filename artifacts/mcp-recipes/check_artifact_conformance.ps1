param(
  [string]$ResultsRoot = "",
  [string]$Filter = "*",
  [string]$RunDir = "",
  [string]$OutputCsv = "",
  [switch]$FailOnViolation
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ResultsRoot)) {
  $ResultsRoot = Join-Path $PSScriptRoot "..\results"
}
$ResultsRoot = [System.IO.Path]::GetFullPath($ResultsRoot)
if (-not (Test-Path $ResultsRoot)) {
  throw "Results root not found: $ResultsRoot"
}

if ([string]::IsNullOrWhiteSpace($OutputCsv)) {
  $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
  $OutputCsv = Join-Path $ResultsRoot ("artifact_conformance_" + $stamp + ".csv")
} else {
  $OutputCsv = [System.IO.Path]::GetFullPath($OutputCsv)
}

function Parse-SummaryMap {
  param([Parameter(Mandatory = $true)][string]$Path)

  $map = @{}
  if (-not (Test-Path $Path)) { return $map }
  foreach ($line in (Get-Content -Path $Path)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $idx = $line.IndexOf("=")
    if ($idx -le 0) { continue }
    $k = $line.Substring(0, $idx).Trim()
    $v = $line.Substring($idx + 1).Trim()
    if (-not $map.ContainsKey($k)) {
      $map[$k] = $v
    }
  }
  return $map
}

function Test-CsvCommaDecimals {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) { return $false }
  try {
    $rows = Import-Csv -Path $Path
  } catch {
    return $true
  }

  foreach ($row in $rows) {
    foreach ($prop in $row.PSObject.Properties) {
      $v = [string]$prop.Value
      if ($v -match '^-?\d+,\d+$') {
        return $true
      }
    }
  }
  return $false
}

function Get-Profile {
  param([Parameter(Mandatory = $true)][string]$RunName)

  if ($RunName.StartsWith("natal_failover_", [System.StringComparison]::OrdinalIgnoreCase)) {
    return [pscustomobject]@{
      script_id = "run_natal_with_failover"
      csv_headers = @{
        "06_backup_longitudes.csv" = '"body","longitude","longitude_string","longitude_30_string"'
      }
    }
  }

  if ($RunName.StartsWith("house_placidus_", [System.StringComparison]::OrdinalIgnoreCase)) {
    return [pscustomobject]@{
      script_id = "run_house_layer_placidus"
      csv_headers = @{
        "02_houses_placidus.csv" = '"house","longitude","sign","degree"'
        "03_chart_points.csv" = '"point","longitude","sign","degree"'
        "04_planets_primary.csv" = '"body","longitude","sign","degree"'
        "05_additional_points.csv" = '"point","longitude","sign","degree"'
        "06_custom_point_aspects.csv" = '"point","body","aspect","actual_angle","exact_angle","orb","orb_limit","is_exact"'
      }
    }
  }

  if ($RunName.StartsWith("secondary_progressions_", [System.StringComparison]::OrdinalIgnoreCase)) {
    return [pscustomobject]@{
      script_id = "run_secondary_progressions"
      csv_headers = @{
        "03_progressed_planet_deltas.csv" = '"body","natal_longitude","progressed_longitude","delta_forward_deg","delta_shortest_signed_deg","natal_sign","natal_degree","progressed_sign","progressed_degree"'
        "04_progressed_houses.csv" = '"house","longitude","sign","degree"'
        "05_progressed_chart_points.csv" = '"point","longitude","sign","degree"'
        "06_progressed_additional_points.csv" = '"point","longitude","sign","degree"'
        "07_progressed_to_natal_aspects.csv" = '"from_set","from_body","to_set","to_body","aspect","actual_angle","exact_angle","orb","orb_limit","is_exact"'
      }
    }
  }

  if ($RunName.StartsWith("solar_arc_", [System.StringComparison]::OrdinalIgnoreCase)) {
    return [pscustomobject]@{
      script_id = "run_solar_arc"
      csv_headers = @{
        "03_solar_arc_directed_positions.csv" = '"object_type","object","natal_longitude","directed_longitude","delta_forward_deg","natal_sign","natal_degree","directed_sign","directed_degree"'
        "04_directed_to_natal_planets_aspects.csv" = '"from_object","to_object","aspect","actual_angle","exact_angle","orb","orb_limit","is_exact"'
        "05_directed_to_natal_points_aspects.csv" = '"from_object","to_object","aspect","actual_angle","exact_angle","orb","orb_limit","is_exact"'
      }
    }
  }

  return $null
}

$requiredSummaryKeys = @(
  "SCRIPT_ID",
  "SCRIPT_VERSION",
  "RUN_STARTED_AT",
  "RUN_FINISHED_AT",
  "INPUT_HASH",
  "OUTPUT_HASH"
)

$runs = @()
if (-not [string]::IsNullOrWhiteSpace($RunDir)) {
  $fullRunDir = [System.IO.Path]::GetFullPath($RunDir)
  if (-not (Test-Path $fullRunDir)) {
    throw "RunDir not found: $fullRunDir"
  }
  $runs = @([System.IO.DirectoryInfo]$fullRunDir)
} else {
  $runs = @(Get-ChildItem -Path $ResultsRoot -Directory | Where-Object {
    $_.Name -ne "_archive" -and $_.Name -like $Filter
  })
}

$rows = @()
foreach ($run in $runs) {
  $profile = Get-Profile -RunName $run.Name
  if ($null -eq $profile) { continue }

  $violations = @()
  $summaryPath = Join-Path $run.FullName "00_summary.txt"
  $summary = Parse-SummaryMap -Path $summaryPath

  foreach ($k in $requiredSummaryKeys) {
    if (-not $summary.ContainsKey($k) -or [string]::IsNullOrWhiteSpace([string]$summary[$k])) {
      $violations += ("missing_summary_field:" + $k)
    }
  }

  if ($summary.ContainsKey("SCRIPT_ID")) {
    if ([string]$summary["SCRIPT_ID"] -ne [string]$profile.script_id) {
      $violations += ("script_id_mismatch:expected=" + $profile.script_id + ";actual=" + [string]$summary["SCRIPT_ID"])
    }
  }

  $headerMismatches = @()
  $commaDecimalFiles = @()
  foreach ($fileName in ($profile.csv_headers.Keys | Sort-Object)) {
    $path = Join-Path $run.FullName $fileName
    if (-not (Test-Path $path)) {
      $violations += ("missing_file:" + $fileName)
      continue
    }

    $expectedHeader = [string]$profile.csv_headers[$fileName]
    $actualHeader = (Get-Content -Path $path -TotalCount 1)
    if ([string]$actualHeader -ne $expectedHeader) {
      $headerMismatches += $fileName
      $violations += ("header_mismatch:" + $fileName)
    }

    if (Test-CsvCommaDecimals -Path $path) {
      $commaDecimalFiles += $fileName
      $violations += ("comma_decimal:" + $fileName)
    }
  }

  $rows += [pscustomobject]@{
    run_name = $run.Name
    run_dir = $run.FullName
    script_id = if ($summary.ContainsKey("SCRIPT_ID")) { [string]$summary["SCRIPT_ID"] } else { "" }
    has_required_summary_fields = ($violations | Where-Object { $_ -like "missing_summary_field:*" }).Count -eq 0
    header_mismatch_count = $headerMismatches.Count
    comma_decimal_file_count = $commaDecimalFiles.Count
    violation_count = $violations.Count
    status = if ($violations.Count -eq 0) { "PASS" } else { "FAIL" }
    violations = ($violations -join ";")
  }
}

if ($rows.Count -eq 0) {
  $rows = @([pscustomobject]@{
    run_name = ""
    run_dir = ""
    script_id = ""
    has_required_summary_fields = $false
    header_mismatch_count = 0
    comma_decimal_file_count = 0
    violation_count = 1
    status = "NO_RUNS"
    violations = "no_matching_runs"
  })
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutputCsv

$checked = @($rows | Where-Object { $_.status -ne "NO_RUNS" }).Count
$failed = @($rows | Where-Object { $_.status -eq "FAIL" }).Count
$passed = @($rows | Where-Object { $_.status -eq "PASS" }).Count

Write-Output ("RUNS_CHECKED=" + $checked)
Write-Output ("PASSED=" + $passed)
Write-Output ("FAILED=" + $failed)
Write-Output ("REPORT_PATH=" + $OutputCsv)

if ($FailOnViolation -and $failed -gt 0) {
  throw "Artifact conformance violations detected."
}

