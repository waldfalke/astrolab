param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeLocal,
  [Parameter(Mandatory = $true)][string]$BirthTimezone,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [string]$DisplayName = "",
  [string]$NatalFailoverRunDir = "",
  [string]$HouseRunDir = "",
  [string]$SecondaryProgressionsRunDir = "",
  [string]$SolarArcRunDir = "",
  [string]$ChartsRoot = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)

$chartDir = Join-Path $ChartsRoot $ChartId
$methodsDir = Join-Path $chartDir "methods"
$outputsDir = Join-Path $chartDir "outputs"
$packsDir = Join-Path $chartDir "packs"

New-Item -ItemType Directory -Force -Path $ChartsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $chartDir | Out-Null
New-Item -ItemType Directory -Force -Path $methodsDir | Out-Null
New-Item -ItemType Directory -Force -Path $outputsDir | Out-Null
New-Item -ItemType Directory -Force -Path $packsDir | Out-Null

function Get-RunSummaryMap {
  param(
    [Parameter(Mandatory = $true)][string]$RunDir
  )

  $map = @{}
  $summaryPath = Join-Path $RunDir "00_summary.txt"
  if (-not (Test-Path $summaryPath)) { return $map }

  $lines = Get-Content -Path $summaryPath
  foreach ($line in $lines) {
    $eqIndex = $line.IndexOf("=")
    if ($eqIndex -lt 1) { continue }
    $k = $line.Substring(0, $eqIndex).Trim()
    $v = $line.Substring($eqIndex + 1).Trim()
    if (-not [string]::IsNullOrWhiteSpace($k)) {
      $map[$k] = $v
    }
  }
  return $map
}

function Copy-MethodRun {
  param(
    [Parameter(Mandatory = $true)][string]$MethodName,
    [string]$SourceRunDir = ""
  )

  if ([string]::IsNullOrWhiteSpace($SourceRunDir)) { return $null }
  if (-not (Test-Path $SourceRunDir)) {
    throw "Run dir does not exist: $SourceRunDir"
  }

  $srcAbs = [System.IO.Path]::GetFullPath($SourceRunDir)
  $runName = Split-Path -Path $srcAbs -Leaf
  $methodDir = Join-Path $methodsDir $MethodName
  $targetRunDir = Join-Path $methodDir $runName

  New-Item -ItemType Directory -Force -Path $methodDir | Out-Null
  if (Test-Path $targetRunDir) {
    Remove-Item -Path $targetRunDir -Recurse -Force
  }
  Copy-Item -Path $srcAbs -Destination $targetRunDir -Recurse -Force

  $summary = Get-RunSummaryMap -RunDir $targetRunDir

  return [pscustomobject]@{
    method = $MethodName
    source_run_dir = $srcAbs
    source_run_exists = (Test-Path $srcAbs)
    project_run_dir = $targetRunDir
    canonical_run_dir = ("methods/" + $MethodName + "/" + $runName)
    run_name = $runName
    summary = $summary
  }
}

function Copy-OutputArtifact {
  param(
    [Parameter(Mandatory = $true)][string]$MethodName,
    [Parameter(Mandatory = $true)][string]$RunName,
    [Parameter(Mandatory = $true)][string]$RunDir,
    [string]$ExternalRunDir = "",
    [Parameter(Mandatory = $true)][string]$SourceFileName,
    [Parameter(Mandatory = $true)][string]$OutputFileName,
    [Parameter(Mandatory = $true)][string]$Label
  )

  $sourcePath = Join-Path $RunDir $SourceFileName
  if (-not (Test-Path $sourcePath)) { return $null }

  $destPath = Join-Path $outputsDir $OutputFileName
  Copy-Item -Path $sourcePath -Destination $destPath -Force

  $externalSourceFile = ""
  $externalSourceExists = $false
  if (-not [string]::IsNullOrWhiteSpace($ExternalRunDir)) {
    $externalSourceFile = Join-Path $ExternalRunDir $SourceFileName
    $externalSourceExists = (Test-Path $externalSourceFile)
  }

  return [pscustomobject]@{
    label = $Label
    output_file = ("outputs/" + $OutputFileName)
    canonical_source = ("methods/" + $MethodName + "/" + $RunName + "/" + $SourceFileName)
    external_source = $externalSourceFile
    external_source_exists = $externalSourceExists
  }
}

$runs = @()
$runNatal = Copy-MethodRun -MethodName "natal_failover" -SourceRunDir $NatalFailoverRunDir
$runHouse = Copy-MethodRun -MethodName "house_placidus" -SourceRunDir $HouseRunDir
$runSecondary = Copy-MethodRun -MethodName "secondary_progressions" -SourceRunDir $SecondaryProgressionsRunDir
$runSolarArc = Copy-MethodRun -MethodName "solar_arc" -SourceRunDir $SolarArcRunDir
foreach ($r in @($runNatal, $runHouse, $runSecondary, $runSolarArc)) {
  if ($null -ne $r) { $runs += $r }
}

$outputArtifacts = @()

if ($null -ne $runNatal) {
  $outputArtifacts += Copy-OutputArtifact -MethodName "natal_failover" -RunName $runNatal.run_name -RunDir $runNatal.project_run_dir -ExternalRunDir $runNatal.source_run_dir -SourceFileName "00_summary.txt" -OutputFileName "natal_failover_summary.txt" -Label "Natal failover summary"
  $outputArtifacts += Copy-OutputArtifact -MethodName "natal_failover" -RunName $runNatal.run_name -RunDir $runNatal.project_run_dir -ExternalRunDir $runNatal.source_run_dir -SourceFileName "06_backup_longitudes.csv" -OutputFileName "natal_longitudes.csv" -Label "Natal longitudes"
  $outputArtifacts += Copy-OutputArtifact -MethodName "natal_failover" -RunName $runNatal.run_name -RunDir $runNatal.project_run_dir -ExternalRunDir $runNatal.source_run_dir -SourceFileName "04_backup_aspects.json" -OutputFileName "natal_aspects.json" -Label "Natal aspects"
}

if ($null -ne $runHouse) {
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "00_summary.txt" -OutputFileName "house_summary.txt" -Label "House layer summary"
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "02_houses_placidus.csv" -OutputFileName "houses_placidus.csv" -Label "House cusps"
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "03_chart_points.csv" -OutputFileName "chart_points.csv" -Label "Chart points"
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "04_planets_primary.csv" -OutputFileName "planets_primary.csv" -Label "Primary planets"
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "05_additional_points.csv" -OutputFileName "additional_points.csv" -Label "Additional points"
  $outputArtifacts += Copy-OutputArtifact -MethodName "house_placidus" -RunName $runHouse.run_name -RunDir $runHouse.project_run_dir -ExternalRunDir $runHouse.source_run_dir -SourceFileName "06_custom_point_aspects.csv" -OutputFileName "custom_point_aspects.csv" -Label "Custom point aspects"
}

if ($null -ne $runSecondary) {
  $outputArtifacts += Copy-OutputArtifact -MethodName "secondary_progressions" -RunName $runSecondary.run_name -RunDir $runSecondary.project_run_dir -ExternalRunDir $runSecondary.source_run_dir -SourceFileName "00_summary.txt" -OutputFileName "secondary_progressions_summary.txt" -Label "Secondary progressions summary"
  $outputArtifacts += Copy-OutputArtifact -MethodName "secondary_progressions" -RunName $runSecondary.run_name -RunDir $runSecondary.project_run_dir -ExternalRunDir $runSecondary.source_run_dir -SourceFileName "03_progressed_planet_deltas.csv" -OutputFileName "secondary_progressions_planet_deltas.csv" -Label "Secondary progressed planet deltas"
  $outputArtifacts += Copy-OutputArtifact -MethodName "secondary_progressions" -RunName $runSecondary.run_name -RunDir $runSecondary.project_run_dir -ExternalRunDir $runSecondary.source_run_dir -SourceFileName "07_progressed_to_natal_aspects.csv" -OutputFileName "secondary_progressions_aspects.csv" -Label "Secondary progressed to natal aspects"
}

if ($null -ne $runSolarArc) {
  $outputArtifacts += Copy-OutputArtifact -MethodName "solar_arc" -RunName $runSolarArc.run_name -RunDir $runSolarArc.project_run_dir -ExternalRunDir $runSolarArc.source_run_dir -SourceFileName "00_summary.txt" -OutputFileName "solar_arc_summary.txt" -Label "Solar arc summary"
  $outputArtifacts += Copy-OutputArtifact -MethodName "solar_arc" -RunName $runSolarArc.run_name -RunDir $runSolarArc.project_run_dir -ExternalRunDir $runSolarArc.source_run_dir -SourceFileName "03_solar_arc_directed_positions.csv" -OutputFileName "solar_arc_directed_positions.csv" -Label "Solar arc directed positions"
  $outputArtifacts += Copy-OutputArtifact -MethodName "solar_arc" -RunName $runSolarArc.run_name -RunDir $runSolarArc.project_run_dir -ExternalRunDir $runSolarArc.source_run_dir -SourceFileName "04_directed_to_natal_planets_aspects.csv" -OutputFileName "solar_arc_planet_aspects.csv" -Label "Solar arc to natal planets"
  $outputArtifacts += Copy-OutputArtifact -MethodName "solar_arc" -RunName $runSolarArc.run_name -RunDir $runSolarArc.project_run_dir -ExternalRunDir $runSolarArc.source_run_dir -SourceFileName "05_directed_to_natal_points_aspects.csv" -OutputFileName "solar_arc_point_aspects.csv" -Label "Solar arc to natal points"
}

$outputArtifacts = @($outputArtifacts | Where-Object { $null -ne $_ })

$chartYaml = @()
$chartYaml += "chart_id: $ChartId"
$chartYaml += "display_name: " + ($(if ([string]::IsNullOrWhiteSpace($DisplayName)) { $ChartId } else { $DisplayName }))
$chartYaml += "birth:"
$chartYaml += "  local_datetime: $BirthDateTimeLocal"
$chartYaml += "  timezone: $BirthTimezone"
$chartYaml += "  utc_datetime: $BirthDateTimeUtc"
$chartYaml += "location:"
$chartYaml += "  latitude: $Latitude"
$chartYaml += "  longitude: $Longitude"
$chartYaml += "structure:"
$chartYaml += "  methods_dir: methods"
$chartYaml += "  outputs_dir: outputs"
$chartYaml += "  packs_dir: packs"
Set-Content -Path (Join-Path $chartDir "chart.yaml") -Encoding UTF8 -Value $chartYaml

$nowIso = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
$indexLines = @()
$indexLines += "chart_id: $ChartId"
$indexLines += "generated_at: $nowIso"
$indexLines += "chart_file: chart.yaml"
$indexLines += "provenance_model: canonical_source_v1"
$indexLines += "raw_methods:"
if ($runs.Count -eq 0) {
  $indexLines += "  - none"
} else {
  foreach ($r in $runs) {
    $method = [string]$r.method
    $runName = [string]$r.run_name
    $projectRunRel = "methods/$method/$runName"
    $indexLines += "  - method: $method"
    $indexLines += "    run_name: $runName"
    $indexLines += "    project_run_dir: $projectRunRel"
    $indexLines += "    canonical_run_dir: " + [string]$r.canonical_run_dir
    $indexLines += "    source_run_dir: " + [string]$r.source_run_dir
    $indexLines += "    external_source_run_dir: " + [string]$r.source_run_dir
    $indexLines += "    external_source_run_exists: " + [string]$r.source_run_exists
    $summaryMap = $r.summary
    if (($null -ne $summaryMap) -and ($summaryMap.Count -gt 0)) {
      $indexLines += "    summary:"
      foreach ($k in ($summaryMap.Keys | Sort-Object)) {
        $v = [string]$summaryMap[$k]
        $indexLines += ("      {0}: {1}" -f $k, $v)
      }
    } else {
      $indexLines += "    summary: {}"
    }
  }
}

$indexLines += "outputs:"
if ($outputArtifacts.Count -eq 0) {
  $indexLines += "  - none"
} else {
  foreach ($o in $outputArtifacts) {
    $indexLines += "  - label: " + [string]$o.label
    $indexLines += "    file: " + [string]$o.output_file
    $indexLines += "    source: " + [string]$o.canonical_source
    $indexLines += "    canonical_source: " + [string]$o.canonical_source
    if (-not [string]::IsNullOrWhiteSpace([string]$o.external_source)) {
      $indexLines += "    external_source: " + [string]$o.external_source
      $indexLines += "    external_source_exists: " + [string]$o.external_source_exists
    } else {
      $indexLines += "    external_source: n/a"
      $indexLines += "    external_source_exists: False"
    }
  }
}

Set-Content -Path (Join-Path $chartDir "INDEX.yaml") -Encoding UTF8 -Value $indexLines

Write-Output "Chart project built: $chartDir"
