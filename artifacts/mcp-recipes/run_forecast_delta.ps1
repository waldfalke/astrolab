param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$Date1Utc,
  [Parameter(Mandatory = $true)][string]$Date2Utc,
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
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("forecast_" + $CaseId)

$compare = Invoke-EphemToolJson -Tool "compare_positions" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  date1 = $Date1Utc
  date2 = $Date2Utc
}

$aspects1 = Invoke-EphemToolJson -Tool "calculate_aspects" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $Date1Utc
  orb = $Orb
}

$aspects2 = Invoke-EphemToolJson -Tool "calculate_aspects" -Args @{
  latitude = $Latitude
  longitude = $Longitude
  datetime = $Date2Utc
  orb = $Orb
}

$moon2 = Invoke-EphemToolJson -Tool "get_moon_phase" -Args @{
  datetime = $Date2Utc
}

Write-JsonFile -Data $compare -Path (Join-Path $runDir "01_compare_positions.json")
Write-JsonFile -Data $aspects1 -Path (Join-Path $runDir "02_aspects_date1.json")
Write-JsonFile -Data $aspects2 -Path (Join-Path $runDir "03_aspects_date2.json")
Write-JsonFile -Data $moon2 -Path (Join-Path $runDir "04_moon_phase_date2.json")

$movementRows = @()
foreach ($prop in $compare.comparison.PSObject.Properties) {
  $movementRows += [pscustomobject]@{
    body = $prop.Name
    date1_position = [double]$prop.Value.date1_position
    date2_position = [double]$prop.Value.date2_position
    movement = [double]$prop.Value.movement
    direction = [string]$prop.Value.direction
    abs_movement = [math]::Abs([double]$prop.Value.movement)
  }
}
$movementRows | Sort-Object abs_movement -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runDir "05_movement_ranked.csv")

$summary = @()
$summary += "CASE_ID=$CaseId"
$summary += "DATE1_UTC=$Date1Utc"
$summary += "DATE2_UTC=$Date2Utc"
$summary += "LATITUDE=$Latitude"
$summary += "LONGITUDE=$Longitude"
$summary += "ORB=$Orb"
$summary += "ASPECT_COUNT_DATE1=" + ($aspects1.aspects.Count)
$summary += "ASPECT_COUNT_DATE2=" + ($aspects2.aspects.Count)
$summary += "OUTPUT_DIR=$runDir"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Forecast delta completed: $runDir"
