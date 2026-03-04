param(
  [Parameter(Mandatory = $true)][string]$CaseId,
  [Parameter(Mandatory = $true)][double]$Latitude,
  [Parameter(Mandatory = $true)][double]$Longitude,
  [Parameter(Mandatory = $true)][string]$BirthDateTimeUtc,
  [Parameter(Mandatory = $true)][string]$CompareDateUtc,
  [Parameter(Mandatory = $true)][double]$SynLatB,
  [Parameter(Mandatory = $true)][double]$SynLonB,
  [Parameter(Mandatory = $true)][string]$SynDateBUtc,
  [double]$Orb = 6,
  [double]$MaxDeltaDeg = 1.0,
  [string]$ClientId = "demo-client",
  [string]$Analyst = "TBD",
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)

function Invoke-LocalRecipe {
  param(
    [Parameter(Mandatory = $true)][string]$ScriptName,
    [Parameter(Mandatory = $true)][string[]]$Arguments
  )
  $scriptPath = Join-Path $PSScriptRoot $ScriptName
  & powershell -ExecutionPolicy Bypass -File $scriptPath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Recipe failed: $ScriptName"
  }
}

Invoke-LocalRecipe -ScriptName "run_natal_with_failover.ps1" -Arguments @(
  "-CaseId", $CaseId,
  "-Latitude", $Latitude,
  "-Longitude", $Longitude,
  "-DateTimeUtc", $BirthDateTimeUtc,
  "-Orb", $Orb,
  "-OutputBase", $OutputBase
)

Invoke-LocalRecipe -ScriptName "run_house_layer_placidus.ps1" -Arguments @(
  "-CaseId", $CaseId,
  "-Latitude", $Latitude,
  "-Longitude", $Longitude,
  "-DateTimeUtc", $BirthDateTimeUtc,
  "-OutputBase", $OutputBase
)

Invoke-LocalRecipe -ScriptName "run_forecast_delta.ps1" -Arguments @(
  "-CaseId", $CaseId,
  "-Latitude", $Latitude,
  "-Longitude", $Longitude,
  "-Date1Utc", $BirthDateTimeUtc,
  "-Date2Utc", $CompareDateUtc,
  "-Orb", $Orb,
  "-OutputBase", $OutputBase
)

Invoke-LocalRecipe -ScriptName "run_synastry_matrix.ps1" -Arguments @(
  "-CaseId", $CaseId,
  "-LatA", $Latitude,
  "-LonA", $Longitude,
  "-DateAUtc", $BirthDateTimeUtc,
  "-LatB", $SynLatB,
  "-LonB", $SynLonB,
  "-DateBUtc", $SynDateBUtc,
  "-Orb", $Orb,
  "-OutputBase", $OutputBase
)

Invoke-LocalRecipe -ScriptName "run_cross_provider_qc.ps1" -Arguments @(
  "-CaseId", $CaseId,
  "-Latitude", $Latitude,
  "-Longitude", $Longitude,
  "-DateTimeUtc", $BirthDateTimeUtc,
  "-MaxDeltaDeg", $MaxDeltaDeg,
  "-OutputBase", $OutputBase
)

$latestNatalFailover = Get-ChildItem -Path $OutputBase -Directory -Filter ("natal_failover_{0}_*" -f $CaseId) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestHouse = Get-ChildItem -Path $OutputBase -Directory -Filter ("house_placidus_{0}_*" -f $CaseId) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestForecast = Get-ChildItem -Path $OutputBase -Directory -Filter ("forecast_{0}_*" -f $CaseId) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestSynastry = Get-ChildItem -Path $OutputBase -Directory -Filter ("synastry_{0}_*" -f $CaseId) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestQc = Get-ChildItem -Path $OutputBase -Directory -Filter ("qc_cross_provider_{0}_*" -f $CaseId) | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestNatalFailover) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pack_manifest.ps1") -PackType natal_failover -RunDir $latestNatalFailover.FullName -ClientId $ClientId -Analyst $Analyst
}
if ($latestHouse) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pack_manifest.ps1") -PackType house -RunDir $latestHouse.FullName -ClientId $ClientId -Analyst $Analyst
}
if ($latestForecast) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pack_manifest.ps1") -PackType forecast -RunDir $latestForecast.FullName -ClientId $ClientId -Analyst $Analyst
}
if ($latestSynastry) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pack_manifest.ps1") -PackType synastry -RunDir $latestSynastry.FullName -ClientId $ClientId -Analyst $Analyst
}
if ($latestQc) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pack_manifest.ps1") -PackType qc -RunDir $latestQc.FullName -ClientId $ClientId -Analyst $Analyst
}

Write-Output "Full workbench run completed for case: $CaseId"
