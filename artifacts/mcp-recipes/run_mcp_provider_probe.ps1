param(
  [string]$OutputBase = "",
  [int]$TimeoutMs = 45000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null

$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$runDir = Join-Path $OutputBase ("provider_probe_" + $ts)
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$providers = @(
  [pscustomobject]@{ name = "swissremote"; url = "https://www.theme-astral.me/mcp"; family = "western" },
  [pscustomobject]@{ name = "ephem"; url = "https://ephemeris.fyi/mcp"; family = "western" },
  [pscustomobject]@{ name = "vedastro"; url = "https://mcp.vedastro.org/api/mcp"; family = "vedic" }
)

$rows = @()
foreach ($p in $providers) {
  $env:MCPORTER_CALL_TIMEOUT = $TimeoutMs.ToString()
  $out = ""
  try {
    $cmd = "npx -y mcporter list --http-url `"$($p.url)`" --name `"$($p.name)`" --schema"
    $out = Invoke-Expression $cmd 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
  } catch {
    $out = $_.Exception.Message
    $exitCode = 1
  }

  $toolNames = @()
  foreach ($line in ($out -split "`r?`n")) {
    if ($line -match "function\s+([a-zA-Z0-9_]+)\(") {
      $toolNames += $Matches[1]
    }
  }
  $toolNames = $toolNames | Select-Object -Unique

  $health = if ($exitCode -eq 0 -and $toolNames.Count -gt 0) { "healthy" } else { "unhealthy" }
  $rows += [pscustomobject]@{
    provider = $p.name
    family = $p.family
    url = $p.url
    health = $health
    tool_count = $toolNames.Count
    tools = ($toolNames -join ";")
    checked_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
  }

  Set-Content -Path (Join-Path $runDir ("raw_" + $p.name + ".txt")) -Encoding UTF8 -Value $out
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runDir "provider_probe.csv")

$summary = @()
$summary += "RUN_DIR=$runDir"
$summary += "PROVIDERS_CHECKED=" + $rows.Count
$summary += "HEALTHY=" + (($rows | Where-Object { $_.health -eq "healthy" }).Count)
$summary += "UNHEALTHY=" + (($rows | Where-Object { $_.health -ne "healthy" }).Count)
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Provider probe completed: $runDir"
