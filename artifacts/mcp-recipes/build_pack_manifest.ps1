param(
  [Parameter(Mandatory = $true)][ValidateSet("natal", "forecast", "synastry", "house", "natal_failover", "qc", "probe", "secondary_progressions", "solar_arc")][string]$PackType,
  [Parameter(Mandatory = $true)][string]$RunDir,
  [Parameter(Mandatory = $true)][string]$ClientId,
  [string]$Analyst = "TBD"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RunDir)) {
  throw "RunDir not found: $RunDir"
}

$runDirAbs = [System.IO.Path]::GetFullPath($RunDir)

$requiredByType = @{
  natal = @(
    "00_summary.txt",
    "01_ephemeris.json",
    "02_aspects.json",
    "03_moon_phase.json",
    "04_sun_events.json",
    "05_moon_events.json",
    "06_core_longitudes.csv"
  )
  forecast = @(
    "00_summary.txt",
    "01_compare_positions.json",
    "02_aspects_date1.json",
    "03_aspects_date2.json",
    "04_moon_phase_date2.json",
    "05_movement_ranked.csv"
  )
  synastry = @(
    "00_summary.txt",
    "01_chart_A_ephemeris.json",
    "02_chart_B_ephemeris.json",
    "03_synastry_aspect_matrix.csv",
    "04_synastry_aspect_matrix.json"
  )
  house = @(
    "00_summary.txt",
    "01_primary_positions.json",
    "02_houses_placidus.csv",
    "03_chart_points.csv",
    "04_planets_primary.csv",
    "05_additional_points.csv",
    "06_custom_point_aspects.csv"
  )
  natal_failover = @(
    "00_summary.txt",
    "03_backup_ephemeris.json",
    "04_backup_aspects.json",
    "05_backup_moon_phase.json",
    "06_backup_longitudes.csv"
  )
  qc = @(
    "00_summary.txt",
    "01_primary_positions.json",
    "02_backup_positions.json",
    "03_longitude_delta_qc.csv"
  )
  probe = @(
    "00_summary.txt",
    "provider_probe.csv",
    "raw_swissremote.txt",
    "raw_ephem.txt",
    "raw_vedastro.txt"
  )
  secondary_progressions = @(
    "00_summary.txt",
    "01_birth_positions.json",
    "02_progressed_positions.json",
    "03_progressed_planet_deltas.csv",
    "04_progressed_houses.csv",
    "05_progressed_chart_points.csv",
    "06_progressed_additional_points.csv",
    "07_progressed_to_natal_aspects.csv"
  )
  solar_arc = @(
    "00_summary.txt",
    "01_natal_positions.json",
    "02_progressed_reference_positions.json",
    "03_solar_arc_directed_positions.csv",
    "04_directed_to_natal_planets_aspects.csv",
    "05_directed_to_natal_points_aspects.csv"
  )
}

$required = $requiredByType[$PackType]
$missing = @()
foreach ($f in $required) {
  if (-not (Test-Path (Join-Path $runDirAbs $f))) {
    $missing += $f
  }
}

$status = if ($missing.Count -eq 0) { "READY" } else { "INCOMPLETE" }
$manifestPath = Join-Path $runDirAbs "PACK_MANIFEST.yaml"
$generatedAt = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")

$lines = @()
$lines += "pack_type: $PackType"
$lines += "client_id: $ClientId"
$lines += "analyst: $Analyst"
$lines += "generated_at: $generatedAt"
$lines += "run_dir: $runDirAbs"
$lines += "status: $status"
$lines += "required_files:"
foreach ($f in $required) {
  $exists = Test-Path (Join-Path $runDirAbs $f)
  $lines += "  - name: $f"
  $lines += "    exists: " + ($exists.ToString().ToLower())
}
$lines += "missing_files:"
if ($missing.Count -eq 0) {
  $lines += "  - none"
} else {
  foreach ($m in $missing) {
    $lines += "  - $m"
  }
}

Set-Content -Path $manifestPath -Encoding UTF8 -Value $lines
Write-Output "Manifest built: $manifestPath"
