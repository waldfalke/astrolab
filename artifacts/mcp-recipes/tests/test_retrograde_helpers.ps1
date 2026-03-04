param()

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\..\lib\mcp_helpers.ps1"

function Assert-True {
  param(
    [Parameter(Mandatory = $true)][bool]$Condition,
    [Parameter(Mandatory = $true)][string]$Message
  )
  if (-not $Condition) {
    throw "ASSERT_TRUE failed: $Message"
  }
}

function Assert-Equal {
  param(
    [Parameter(Mandatory = $true)]$Expected,
    [Parameter(Mandatory = $true)]$Actual,
    [Parameter(Mandatory = $true)][string]$Message
  )
  if ($Expected -ne $Actual) {
    throw "ASSERT_EQUAL failed: $Message (expected=$Expected actual=$Actual)"
  }
}

# Get-SignedDelta360 basic wrap checks.
Assert-Equal -Expected 20 -Actual (Get-SignedDelta360 -From 350 -To 10) -Message "wrap forward delta"
Assert-Equal -Expected -20 -Actual (Get-SignedDelta360 -From 10 -To 350) -Message "wrap backward delta"
Assert-Equal -Expected -2 -Actual (Get-SignedDelta360 -From 1 -To 359) -Message "small negative wrap"

# Primary retrograde extraction from swiss-like nodes.
$nodeA = [pscustomobject]@{ longitude = 10.0; retrograde = $true }
$nodeB = [pscustomobject]@{ longitude = 10.0; direction = "direct" }
$nodeC = [pscustomobject]@{ longitude = 10.0; speed = -0.12 }
Assert-Equal -Expected $true -Actual (Get-SwissRetrogradeFromNode -Node $nodeA) -Message "direct retrograde boolean"
Assert-Equal -Expected $false -Actual (Get-SwissRetrogradeFromNode -Node $nodeB) -Message "direction direct"
Assert-Equal -Expected $true -Actual (Get-SwissRetrogradeFromNode -Node $nodeC) -Message "negative speed means retrograde"

# Fallback motion window detection.
$prev = [pscustomobject]@{
  mercury = [pscustomobject]@{ apparentLongitude = 15.0 }
  jupiter = [pscustomobject]@{ apparentLongitude = 100.0 }
}
$next = [pscustomobject]@{
  mercury = [pscustomobject]@{ apparentLongitude = 13.0 }  # backward across 2 days -> retro
  jupiter = [pscustomobject]@{ apparentLongitude = 102.0 } # forward across 2 days -> direct
}
$retroMap = Get-RetrogradeMapFromEphemerisWindow -PrevEphemeris $prev -NextEphemeris $next -Bodies @("mercury", "jupiter")
Assert-True -Condition $retroMap.ContainsKey("mercury") -Message "mercury key exists"
Assert-Equal -Expected $true -Actual $retroMap["mercury"] -Message "mercury retro from fallback"
Assert-Equal -Expected $false -Actual $retroMap["jupiter"] -Message "jupiter direct from fallback"

# Shadow state classifier.
$loop = [pscustomobject]@{
  srx_time = [datetime]"2026-03-15T00:00:00Z"
  srx_lon = 15.0
  sd_time = [datetime]"2026-04-10T00:00:00Z"
  sd_lon = 5.0
}
Assert-Equal -Expected "pre" -Actual (Get-ShadowStateForBody -Loops @($loop) -AtUtc ([datetime]"2026-03-01T00:00:00Z") -Longitude 10.0 -MotionSign 1) -Message "pre-shadow in zone before SRx"
Assert-Equal -Expected "retro" -Actual (Get-ShadowStateForBody -Loops @($loop) -AtUtc ([datetime]"2026-03-20T00:00:00Z") -Longitude 9.0 -MotionSign -1) -Message "retro phase between stations"
Assert-Equal -Expected "post" -Actual (Get-ShadowStateForBody -Loops @($loop) -AtUtc ([datetime]"2026-04-20T00:00:00Z") -Longitude 11.0 -MotionSign 1) -Message "post-shadow in zone after SD"
Assert-Equal -Expected "none" -Actual (Get-ShadowStateForBody -Loops @($loop) -AtUtc ([datetime]"2026-04-20T00:00:00Z") -Longitude 40.0 -MotionSign 1) -Message "none outside shadow zone"

Write-Output "OK: retrograde helper tests passed"
