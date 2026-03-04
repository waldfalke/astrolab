param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$DateTimeUtc,
  [double]$Orb = 6,
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\lib\mcp_helpers.ps1"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("natal_" + $CaseId)

$ephemeris = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $DateTimeUtc
}

$aspects = Invoke-EphemToolJson -Tool "calculate_aspects" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $DateTimeUtc
  orb = $Orb
}

$moonPhase = Invoke-EphemToolJson -Tool "get_moon_phase" -Args @{
  datetime = $DateTimeUtc
}

$sunEvents = Invoke-EphemToolJson -Tool "get_daily_events" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $DateTimeUtc
  body = "sun"
}

$moonEvents = Invoke-EphemToolJson -Tool "get_daily_events" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $DateTimeUtc
  body = "moon"
}

Write-JsonFile -Data $ephemeris -Path (Join-Path $runDir "01_ephemeris.json")
Write-JsonFile -Data $aspects -Path (Join-Path $runDir "02_aspects.json")
Write-JsonFile -Data $moonPhase -Path (Join-Path $runDir "03_moon_phase.json")
Write-JsonFile -Data $sunEvents -Path (Join-Path $runDir "04_sun_events.json")
Write-JsonFile -Data $moonEvents -Path (Join-Path $runDir "05_moon_events.json")

$positions = Get-BodyLongitudes -Ephemeris $ephemeris
$positions | Sort-Object body | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runDir "06_core_longitudes.csv")

$moonPhaseName = "n/a"
if ($null -ne $moonPhase.PSObject.Properties["phaseQuarterString"]) {
  $moonPhaseName = [string]$moonPhase.phaseQuarterString
}

$summary = @()
$summary += "CASE_ID=$CaseId"
$summary += "DATETIME_UTC=$DateTimeUtc"
$summary += "LATITUDE=$Latitude"
$summary += "LONGITUDE=$Longitude"
$summary += "ORB=$Orb"
$summary += "ASPECT_COUNT=" + ($aspects.aspects.Count)
$summary += "MOON_PHASE=" + $moonPhaseName
$summary += "OUTPUT_DIR=$runDir"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Natal snapshot completed: $runDir"
