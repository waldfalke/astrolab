param(
  [string]$VaultRoot = "",
  [string]$ServerName = "obsidian",
  [string]$NoteFile = "ai_e2e_check.md",
  [string]$NoteFolder = "Astrolab/exports",
  [string]$OutputBase = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($VaultRoot)) {
  $VaultRoot = Join-Path (Get-Location) "obsidian-vault"
}
$VaultRoot = [System.IO.Path]::GetFullPath($VaultRoot)

if ([string]::IsNullOrWhiteSpace($OutputBase)) {
  $OutputBase = Join-Path $PSScriptRoot "..\results"
}
$OutputBase = [System.IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path $OutputBase | Out-Null

$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$runDir = Join-Path $OutputBase ("obsidian_mcp_e2e_" + $ts)
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$stdioCommand = "npx -y obsidian-mcp"
$stdioArg = $VaultRoot.Replace('\','/')

function Invoke-Step {
  param(
    [string]$Name,
    [string]$Tool,
    [hashtable]$Args
  )
  $argList = @(
    "-y", "mcporter", "call",
    "--stdio", $stdioCommand,
    "--stdio-arg", $stdioArg,
    "--name", $ServerName,
    $Tool
  )
  foreach ($k in ($Args.Keys | Sort-Object)) {
    $v = [string]$Args[$k]
    $argList += ("{0}:{1}" -f $k, $v)
  }
  $argList += @("--output", "json")

  $out = npx @argList 2>&1 | Out-String
  Set-Content -Encoding UTF8 -Path (Join-Path $runDir "$Name.json") -Value $out
  return $out
}

$vaultName = Split-Path -Leaf $VaultRoot
$createdText = "# AI E2E Check`ncreated via mcporter"
$appendText = "`nupdated via mcporter edit-note"

$out1 = Invoke-Step -Name "01_list_vaults" -Tool "list-available-vaults" -Args @{}
$out2 = Invoke-Step -Name "02_create_note" -Tool "create-note" -Args @{
  vault = $vaultName
  filename = $NoteFile
  folder = $NoteFolder
  content = $createdText
}
$out3 = Invoke-Step -Name "03_read_note_before_edit" -Tool "read-note" -Args @{
  vault = $vaultName
  filename = $NoteFile
  folder = $NoteFolder
}
$out4 = Invoke-Step -Name "04_edit_note_append" -Tool "edit-note" -Args @{
  vault = $vaultName
  filename = $NoteFile
  folder = $NoteFolder
  operation = "append"
  content = $appendText
}
$out5 = Invoke-Step -Name "05_read_note_after_edit" -Tool "read-note" -Args @{
  vault = $vaultName
  filename = $NoteFile
  folder = $NoteFolder
}

$ok = (
  $out1 -match '"success":\s*true' -and
  $out2 -match '"success":\s*true' -and
  $out3 -match '"success":\s*true' -and
  $out4 -match '"success":\s*true' -and
  $out5 -match '"success":\s*true'
)

$summary = @()
$summary += "RUN_DIR=$runDir"
$summary += "VAULT_ROOT=$VaultRoot"
$summary += "VAULT_NAME=$vaultName"
$summary += "NOTE=$NoteFolder/$NoteFile"
$summary += "SERVER_NAME=$ServerName"
$summary += "STDIO_COMMAND=$stdioCommand $stdioArg"
$summary += "E2E_STATUS=$(if ($ok) { 'PASS' } else { 'FAIL' })"
Set-Content -Encoding UTF8 -Path (Join-Path $runDir "00_summary.txt") -Value $summary

if (-not $ok) {
  throw "Obsidian MCP E2E failed. See $runDir"
}

Write-Output "Obsidian MCP E2E completed: $runDir"
