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
$scriptId = "run_natal_with_failover"
$scriptVersion = "1.1.0"
$runStartedAt = (Get-Date).ToUniversalTime()

New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null
$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("natal_failover_" + $CaseId)
$inputHash = Get-CanonicalMapHash -Map @{
  script_id = $scriptId
  script_version = $scriptVersion
  case_id = $CaseId
  latitude = $Latitude
  longitude = $Longitude
  datetime_utc = $DateTimeUtc
  orb = $Orb
}

$providerUsed = "swissremote"
$runStatus = "FULL"
$failureMessage = ""
$primary = $null
$backup = $null

try {
  $primary = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{
    datetime = $DateTimeUtc
    latitude = $Latitude
    longitude = $Longitude
  }
  Write-JsonFile -Data $primary -Path (Join-Path $runDir "01_primary_positions.json")
  $primaryRows = Get-SwissBodyLongitudes -SwissData $primary
  Write-InvariantCsv -Rows @($primaryRows | Sort-Object body) -Path (Join-Path $runDir "02_primary_longitudes.csv")
} catch {
  $providerUsed = "ephem"
  $runStatus = "DEGRADED"
  $failureMessage = $_.Exception.Message
  if (-not [string]::IsNullOrWhiteSpace($failureMessage) -and $failureMessage.Length -gt 500) {
    $failureMessage = $failureMessage.Substring(0, 500) + "..."
  }
}

$backup = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
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

Write-JsonFile -Data $backup -Path (Join-Path $runDir "03_backup_ephemeris.json")
Write-JsonFile -Data $aspects -Path (Join-Path $runDir "04_backup_aspects.json")
Write-JsonFile -Data $moonPhase -Path (Join-Path $runDir "05_backup_moon_phase.json")

$backupRows = Get-BodyLongitudes -Ephemeris $backup
Write-InvariantCsv -Rows @($backupRows | Sort-Object body) -Path (Join-Path $runDir "06_backup_longitudes.csv")

$summaryFields = [ordered]@{}
$summaryFields["CASE_ID"] = $CaseId
$summaryFields["DATETIME_UTC"] = $DateTimeUtc
$summaryFields["LATITUDE"] = $Latitude
$summaryFields["LONGITUDE"] = $Longitude
$summaryFields["ORB"] = $Orb
$summaryFields["PROVIDER_USED"] = $providerUsed
$summaryFields["RUN_STATUS"] = $runStatus
$summaryFields["PRIMARY_AVAILABLE"] = ($null -ne $primary)
$summaryFields["BACKUP_AVAILABLE"] = ($null -ne $backup)
$summaryFields["ASPECT_COUNT"] = $aspects.aspects.Count
if (-not [string]::IsNullOrWhiteSpace($failureMessage)) {
  $summaryFields["PRIMARY_FAILURE"] = $failureMessage
}
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

Write-Output "Natal with failover completed: $runDir"
