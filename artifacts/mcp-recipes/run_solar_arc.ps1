param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][string]$TargetDateUtc,
  [double]$Orb = 1.0,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$scriptId = "run_solar_arc"
$scriptVersion = "1.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()
Reset-SwissRetryTelemetry

function Parse-UtcDateTime {
  param([Parameter(Mandatory = $true)][string]$Value)
  return [datetime]::Parse(
    $Value,
    [System.Globalization.CultureInfo]::InvariantCulture,
    [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal
  )
}

function Get-SwissChartPointRows {
  param([Parameter(Mandatory = $true)]$SwissData)
  $rows = @()
  foreach ($p in @("Ascendant", "Midheaven", "IC", "Descendant", "Vertex", "ARMC")) {
    if ($SwissData.chart_points.PSObject.Properties.Name -contains $p) {
      $node = $SwissData.chart_points.$p
      $rows += [pscustomobject]@{
        point = $p
        longitude = [double]$node.longitude
        sign = [string]$node.sign
        degree = [double]$node.degree
      }
    }
  }
  return $rows
}

function Get-AspectRows {
  param(
    [Parameter(Mandatory = $true)][array]$FromRows,
    [Parameter(Mandatory = $true)][array]$ToRows,
    [double]$Orb = 1.0
  )

  $rows = @()
  foreach ($a in $FromRows) {
    foreach ($b in $ToRows) {
      $angle = Get-MinDelta360 -A ([double]$a.longitude) -B ([double]$b.longitude)
      $hit = Get-ClosestMajorAspect -Angle $angle -Orb $Orb
      if ($null -eq $hit) { continue }

      $rows += [pscustomobject]@{
        from_object = [string]$a.object
        to_object = [string]$b.object
        aspect = [string]$hit.aspect
        actual_angle = [math]::Round([double]$angle, 6)
        exact_angle = [double]$hit.exact_angle
        orb = [math]::Round([double]$hit.delta, 6)
        orb_limit = [double]$Orb
        is_exact = ([double]$hit.delta -le 0.2)
      }
    }
  }
  return ($rows | Sort-Object orb, from_object, to_object)
}

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("solar_arc_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  latitude = $Latitude
  longitude = $Longitude
  birth_datetime_utc = $BirthDateTimeUtc
  target_datetime_utc = $TargetDateUtc
  orb = $Orb
}

$birthDt = Parse-UtcDateTime -Value $BirthDateTimeUtc
$targetDt = Parse-UtcDateTime -Value $TargetDateUtc
if ($targetDt -le $birthDt) {
  throw "TargetDateUtc must be later than BirthDateTimeUtc."
}

$ageDays = ($targetDt - $birthDt).TotalDays
$ageYears = $ageDays / 365.2422
$progressedDt = $birthDt.AddDays($ageYears)

$birthUtcIso = $birthDt.ToString("yyyy-MM-ddTHH:mm:ssZ")
$targetUtcIso = $targetDt.ToString("yyyy-MM-ddTHH:mm:ssZ")
$progressedUtcIso = $progressedDt.ToString("yyyy-MM-ddTHH:mm:ssZ")

$natal = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $birthUtcIso
  latitude = $Latitude
  longitude = $Longitude
}

$progressedRef = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $progressedUtcIso
  latitude = $Latitude
  longitude = $Longitude
}

Write-JsonFile -Data $natal -Path (Join-Path $runDir "01_natal_positions.json")
Write-JsonFile -Data $progressedRef -Path (Join-Path $runDir "02_progressed_reference_positions.json")

$natalPlanets = @(Get-SwissBodyLongitudes -SwissData $natal)
$progressedPlanets = @(Get-SwissBodyLongitudes -SwissData $progressedRef)

$natalSun = $natalPlanets | Where-Object { $_.body -eq "sun" } | Select-Object -First 1
$progressedSun = $progressedPlanets | Where-Object { $_.body -eq "sun" } | Select-Object -First 1
if (($null -eq $natalSun) -or ($null -eq $progressedSun)) {
  throw "Sun longitude is required to compute Solar Arc."
}

$solarArcDeg = Normalize-Longitude -Longitude ([double]$progressedSun.longitude - [double]$natalSun.longitude)

$natalPoints = @(Get-SwissChartPointRows -SwissData $natal)
$natalNodes = @(Get-SwissNodePoints -SwissData $natal)

$baseObjects = @()
foreach ($p in $natalPlanets) {
  $baseObjects += [pscustomobject]@{
    object_type = "planet"
    object = [string]$p.body
    natal_longitude = [double]$p.longitude
    natal_sign = [string]$p.sign
    natal_degree = [double]$p.degree
  }
}
foreach ($p in $natalPoints) {
  $baseObjects += [pscustomobject]@{
    object_type = "chart_point"
    object = [string]$p.point
    natal_longitude = [double]$p.longitude
    natal_sign = [string]$p.sign
    natal_degree = [double]$p.degree
  }
}
foreach ($p in $natalNodes) {
  $baseObjects += [pscustomobject]@{
    object_type = "node"
    object = [string]$p.point
    natal_longitude = [double]$p.longitude
    natal_sign = [string]$p.sign
    natal_degree = [double]$p.degree
  }
}

$directedRows = @()
foreach ($obj in $baseObjects) {
  $directedLon = Normalize-Longitude -Longitude ([double]$obj.natal_longitude + [double]$solarArcDeg)
  $coord = Convert-LongitudeToSignDegree -Longitude $directedLon
  $directedRows += [pscustomobject]@{
    object_type = [string]$obj.object_type
    object = [string]$obj.object
    natal_longitude = [math]::Round([double]$obj.natal_longitude, 9)
    directed_longitude = [math]::Round([double]$coord.longitude, 9)
    delta_forward_deg = [math]::Round([double]$solarArcDeg, 9)
    natal_sign = [string]$obj.natal_sign
    natal_degree = [double]$obj.natal_degree
    directed_sign = [string]$coord.sign
    directed_degree = [double]$coord.degree
  }
}
Write-InvariantCsv -Rows @($directedRows | Sort-Object object_type, object) -Path (Join-Path $runDir "03_solar_arc_directed_positions.csv")

$fromDirected = @()
foreach ($d in $directedRows) {
  $fromDirected += [pscustomobject]@{
    object = ("directed:" + [string]$d.object)
    longitude = [double]$d.directed_longitude
  }
}

$toNatalPlanets = @()
foreach ($p in $natalPlanets) {
  $toNatalPlanets += [pscustomobject]@{
    object = ("natal:" + [string]$p.body)
    longitude = [double]$p.longitude
  }
}

$toNatalPoints = @()
foreach ($p in $natalPoints) {
  $toNatalPoints += [pscustomobject]@{
    object = ("natal:" + [string]$p.point)
    longitude = [double]$p.longitude
  }
}
foreach ($p in $natalNodes) {
  $toNatalPoints += [pscustomobject]@{
    object = ("natal:" + [string]$p.point)
    longitude = [double]$p.longitude
  }
}

$aspectPlanets = @(Get-AspectRows -FromRows $fromDirected -ToRows $toNatalPlanets -Orb $Orb)
$aspectPlanetsPath = Join-Path $runDir "04_directed_to_natal_planets_aspects.csv"
if ($aspectPlanets.Count -gt 0) {
  Write-InvariantCsv -Rows $aspectPlanets -Path $aspectPlanetsPath
} else {
  Write-InvariantCsv -Rows @() -Path $aspectPlanetsPath -Columns @("from_object", "to_object", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$aspectPoints = @(Get-AspectRows -FromRows $fromDirected -ToRows $toNatalPoints -Orb $Orb)
$aspectPointsPath = Join-Path $runDir "05_directed_to_natal_points_aspects.csv"
if ($aspectPoints.Count -gt 0) {
  Write-InvariantCsv -Rows $aspectPoints -Path $aspectPointsPath
} else {
  Write-InvariantCsv -Rows @() -Path $aspectPointsPath -Columns @("from_object", "to_object", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["METHOD"] = "SOLAR_ARC_DIRECTIONS"
$summaryFields["BIRTH_UTC"] = $birthUtcIso
$summaryFields["TARGET_UTC"] = $targetUtcIso
$summaryFields["PROGRESSED_REFERENCE_UTC"] = $progressedUtcIso
$summaryFields["LATITUDE"] = $Latitude
$summaryFields["LONGITUDE"] = $Longitude
$summaryFields["AGE_YEARS"] = [math]::Round($ageYears, 9)
$summaryFields["SOLAR_ARC_DEG"] = [math]::Round([double]$solarArcDeg, 9)
$summaryFields["ORB"] = $Orb
$summaryFields["DIRECTED_OBJECT_COUNT"] = $directedRows.Count
$summaryFields["DIRECTED_TO_NATAL_PLANET_ASPECT_COUNT"] = $aspectPlanets.Count
$summaryFields["DIRECTED_TO_NATAL_POINT_ASPECT_COUNT"] = $aspectPoints.Count
$retryTelemetry = Get-SwissRetryTelemetry
$summaryFields["SWISS_RETRY_TOTAL"] = $retryTelemetry.total_retries
$summaryFields["SWISS_RETRY_BY_TOOL"] = $retryTelemetry.by_tool
$summaryFields["OUTPUT_DIR"] = $runDir

$runFinishedAt = (Get-Date).ToUniversalTime()
$outputHash = Get-RunOutputHash -RunDir $runDir -ExcludeFiles @("00_summary.txt")
Write-RunSummary `
  -Path (Join-Path $runDir "00_summary.txt") `
  -ScriptId $scriptId `
  -ScriptVersion $scriptVersion `
  -RunStartedAtUtc $runStartedAt `
  -RunFinishedAtUtc $runFinishedAt `
  -InputHash $inputHash `
  -OutputHash $outputHash `
  -Fields $summaryFields

Write-Output "Solar arc completed: $runDir"
