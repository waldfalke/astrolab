param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$DateTimeUtc,
  [double]$CustomPointOrb = 2.0,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
$scriptId = "run_house_layer_placidus"
$scriptVersion = "1.2.0"
$runStartedAt = (Get-Date).ToUniversalTime()

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("house_placidus_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  latitude = $Latitude
  longitude = $Longitude
  datetime_utc = $DateTimeUtc
  custom_point_orb = $CustomPointOrb
}

$primary = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
  datetime = $DateTimeUtc
  latitude = $Latitude
  longitude = $Longitude
}

Write-JsonFile -Data $primary -Path (Join-Path $runDir "01_primary_positions.json")

$houseRows = @()
foreach ($n in (1..12)) {
  $k = [string]$n
  if ($primary.houses.PSObject.Properties.Name -contains $k) {
    $h = $primary.houses.$k
    $houseRows += [pscustomobject]@{
      house = $n
      longitude = [double]$h.longitude
      sign = [string]$h.sign
      degree = [double]$h.degree
    }
  }
}
Write-InvariantCsv -Rows @($houseRows | Sort-Object house) -Path (Join-Path $runDir "02_houses_placidus.csv")

$pointRows = @()
foreach ($p in @("Ascendant", "Midheaven", "IC", "Descendant", "Vertex", "ARMC")) {
  if ($primary.chart_points.PSObject.Properties.Name -contains $p) {
    $node = $primary.chart_points.$p
    $pointRows += [pscustomobject]@{
      point = $p
      longitude = [double]$node.longitude
      sign = [string]$node.sign
      degree = [double]$node.degree
    }
  }
}
Write-InvariantCsv -Rows $pointRows -Path (Join-Path $runDir "03_chart_points.csv")

$planetRows = Get-SwissBodyLongitudes -SwissData $primary

# Motion enrichment: retrograde (R), station (ST), and shadow phase.
$ephemCache = @{}
$centerUtc = Get-UtcDateTime -DateTimeUtc $DateTimeUtc
$stationThreshold = 0.05
$stationWindowDays = 15
$stationOrbDays = 2
$needRetroFallback = $false
$retroFallbackApplied = 0
$stationCount = 0
$shadowCount = 0

foreach ($row in $planetRows) {
  $body = ([string]$row.body).ToLowerInvariant()
  $speed = Get-BodySpeedDegPerDay -Cache $ephemCache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $centerUtc -Body $body
  if ($null -eq $speed) {
    $row | Add-Member -NotePropertyName speed_deg_day -NotePropertyValue ""
    $row | Add-Member -NotePropertyName motion_state -NotePropertyValue "unknown"
    $row | Add-Member -NotePropertyName shadow_state -NotePropertyValue "none"
    if ($null -eq $row.retrograde) { $row.retrograde = $false }
    continue
  }

  $row | Add-Member -NotePropertyName speed_deg_day -NotePropertyValue ([math]::Round([double]$speed, 6))
  $motionSign = Get-MotionSign -SpeedDegPerDay ([double]$speed) -StationThreshold $stationThreshold

  # Robust station detection: look for daily-motion sign flip near target datetime.
  $nearestStationDeltaDays = $null
  $dailyDeltas = @()
  for ($d = -$stationWindowDays; $d -lt $stationWindowDays; $d++) {
    $t1 = $centerUtc.AddDays($d)
    $t2 = $centerUtc.AddDays($d + 1)
    $lon1 = Get-BodyLongitudeAt -Cache $ephemCache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $t1 -Body $body
    $lon2 = Get-BodyLongitudeAt -Cache $ephemCache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $t2 -Body $body
    if ($null -eq $lon1 -or $null -eq $lon2) { continue }
    $dd = Get-SignedDelta360 -From $lon1 -To $lon2
    $dailyDeltas += [pscustomobject]@{
      day_offset = $d
      delta = [double]$dd
      sign = ($(if ($dd -gt 0) { 1 } elseif ($dd -lt 0) { -1 } else { 0 }))
    }
  }
  for ($i = 0; $i -lt ($dailyDeltas.Count - 1); $i++) {
    $a = $dailyDeltas[$i]
    $b = $dailyDeltas[$i + 1]
    if ($a.sign -eq 0 -or $b.sign -eq 0 -or $a.sign -ne $b.sign) {
      $stationAt = ([double]$a.day_offset) + 0.5
      $absDist = [math]::Abs($stationAt)
      if ($null -eq $nearestStationDeltaDays -or $absDist -lt $nearestStationDeltaDays) {
        $nearestStationDeltaDays = $absDist
      }
    }
  }
  $isStation = ($null -ne $nearestStationDeltaDays -and $nearestStationDeltaDays -le $stationOrbDays)

  if ($null -eq $row.retrograde -or [string]::IsNullOrWhiteSpace([string]$row.retrograde)) {
    $needRetroFallback = $true
    $retroFallbackApplied += 1
  }
  # Final normalized retrograde from kinematics to avoid provider mismatch.
  if ($motionSign -lt 0) {
    $row.retrograde = $true
  } elseif ($motionSign -gt 0) {
    $row.retrograde = $false
  } else {
    $nextLon = Get-BodyLongitudeAt -Cache $ephemCache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $centerUtc.AddHours(24) -Body $body
    $curLon = Get-BodyLongitudeAt -Cache $ephemCache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $centerUtc -Body $body
    if ($null -ne $nextLon -and $null -ne $curLon) {
      $row.retrograde = ((Get-SignedDelta360 -From $curLon -To $nextLon) -lt 0.0)
    } elseif ($null -eq $row.retrograde) {
      $row.retrograde = $false
    }
  }

  $motionState = "D"
  if ($isStation) {
    $motionState = "ST"
    $stationCount += 1
  } elseif ($row.retrograde) {
    $motionState = "R"
  }
  $row | Add-Member -NotePropertyName motion_state -NotePropertyValue $motionState

  # Shadow calculation deferred (method-specific, heavy). Keep schema stable.
  $row | Add-Member -NotePropertyName shadow_state -NotePropertyValue "none"
}

Write-InvariantCsv -Rows @($planetRows | Sort-Object body) -Path (Join-Path $runDir "04_planets_primary.csv")

$extraPointRows = @()
$extraPointRows += Get-SwissNodePoints -SwissData $primary
$extraPointRows += Get-GalacticCenterPoint -DateTimeUtc $DateTimeUtc
Write-InvariantCsv -Rows @($extraPointRows | Sort-Object point) -Path (Join-Path $runDir "05_additional_points.csv")

$customPointAspects = @(Get-CustomPointAspects -PlanetRows $planetRows -PointRows $extraPointRows -Orb $CustomPointOrb)
$customAspectPath = Join-Path $runDir "06_custom_point_aspects.csv"
if ($customPointAspects.Count -gt 0) {
  Write-InvariantCsv -Rows $customPointAspects -Path $customAspectPath
} else {
  Write-InvariantCsv -Rows @() -Path $customAspectPath -Columns @("point", "body", "aspect", "actual_angle", "exact_angle", "orb", "orb_limit", "is_exact")
}

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["DATETIME_UTC"] = $DateTimeUtc
$summaryFields["LATITUDE"] = $Latitude
$summaryFields["LONGITUDE"] = $Longitude
$summaryFields["PROVIDER"] = "swissremote"
$summaryFields["HOUSE_SYSTEM"] = "Placidus"
$summaryFields["HOUSE_COUNT"] = $houseRows.Count
$summaryFields["POINT_COUNT"] = $pointRows.Count
$summaryFields["PLANET_COUNT"] = $planetRows.Count
$summaryFields["RETROGRADE_FALLBACK"] = $needRetroFallback
$summaryFields["RETROGRADE_FALLBACK_COUNT"] = $retroFallbackApplied
$summaryFields["STATION_THRESHOLD_DEG_PER_DAY"] = $stationThreshold
$summaryFields["STATION_WINDOW_DAYS"] = $stationWindowDays
$summaryFields["STATION_ORB_DAYS"] = $stationOrbDays
$summaryFields["STATION_COUNT"] = $stationCount
$summaryFields["SHADOW_NON_NONE_COUNT"] = $shadowCount
$summaryFields["EXTRA_POINT_COUNT"] = $extraPointRows.Count
$summaryFields["CUSTOM_POINT_ORB"] = $CustomPointOrb
$summaryFields["CUSTOM_POINT_ASPECT_COUNT"] = $customPointAspects.Count
$summaryFields["GALACTIC_CENTER_MODEL"] = "TROPICAL_APPROX_PRECESSION"
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

Write-Output "House-layer Placidus completed: $runDir"
