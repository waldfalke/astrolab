param(
  [string]$StdioCommand = "npx -y mcp-obsidian",
  [string]$ServerName = "obsidian",
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
$runDir = Join-Path $OutputBase ("obsidian_mcp_probe_" + $ts)
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$env:MCPORTER_CALL_TIMEOUT = $TimeoutMs.ToString()
$raw = ""
$exitCode = 1

try {
  $cmd = "npx -y mcporter list --stdio `"$StdioCommand`" --name `"$ServerName`" --schema"
  $raw = Invoke-Expression $cmd 2>&1 | Out-String
  $exitCode = $LASTEXITCODE
} catch {
  $raw = $_.Exception.Message
  $exitCode = 1
}

$toolNames = @()
foreach ($line in ($raw -split "`r?`n")) {
  if ($line -match "function\s+([a-zA-Z0-9_]+)\(") {
    $toolNames += $Matches[1]
  }
}
$toolNames = @($toolNames | Select-Object -Unique)

$health = if ($exitCode -eq 0 -and $toolNames.Count -gt 0) { "healthy" } else { "unhealthy" }

$row = [pscustomobject]@{
  provider = $ServerName
  mode = "stdio"
  stdio_command = $StdioCommand
  health = $health
  tool_count = $toolNames.Count
  tools = ($toolNames -join ";")
  checked_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
}

$row | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runDir "obsidian_mcp_probe.csv")
Set-Content -Path (Join-Path $runDir "raw_tools.txt") -Encoding UTF8 -Value $raw

$summary = @()
$summary += "RUN_DIR=$runDir"
$summary += "SERVER_NAME=$ServerName"
$summary += "STDIO_COMMAND=$StdioCommand"
$summary += "HEALTH=$health"
$summary += "TOOL_COUNT=$($toolNames.Count)"
Set-Content -Path (Join-Path $runDir "00_summary.txt") -Encoding UTF8 -Value $summary

Write-Output "Obsidian MCP probe completed: $runDir"
