param(
  [ValidateSet('from-agents','to-agents')]
  [string]$Direction = 'from-agents',
  [switch]$IncludeQwen,
  [switch]$IncludePrivate,
  [switch]$CleanTarget
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$agentsSkills = Join-Path $root '.agents/skills'
$codexSkills = Join-Path $root '.codex/skills'
$qwenSkills = Join-Path $root '.qwen/skills'

if (-not (Test-Path $agentsSkills)) {
  throw "Missing agents skills root: $agentsSkills"
}

function Sync-SkillDirs {
  param(
    [string]$From,
    [string]$To,
    [switch]$AllowPrivate,
    [switch]$Clean
  )

  New-Item -ItemType Directory -Force -Path $To | Out-Null

  if ($Clean) {
    Get-ChildItem $To -Directory | ForEach-Object {
      if ($_.Name -eq 'astro-engineering-scanner' -and -not $AllowPrivate) { return }
      Remove-Item -Recurse -Force $_.FullName
    }
  }

  Get-ChildItem $From -Directory | ForEach-Object {
    if ($_.Name -eq 'astro-engineering-scanner' -and -not $AllowPrivate) { return }
    $target = Join-Path $To $_.Name
    if (Test-Path $target) {
      Remove-Item -Recurse -Force $target
    }
    Copy-Item -Recurse -Force $_.FullName $target
  }
}

if ($Direction -eq 'from-agents') {
  Sync-SkillDirs -From $agentsSkills -To $codexSkills -AllowPrivate:$IncludePrivate -Clean:$CleanTarget
  if ($IncludeQwen) {
    Sync-SkillDirs -From $agentsSkills -To $qwenSkills -AllowPrivate:$IncludePrivate -Clean:$CleanTarget
  }
  Write-Output "Synced skills from .agents to targets."
} else {
  Sync-SkillDirs -From $codexSkills -To $agentsSkills -AllowPrivate:$IncludePrivate -Clean:$CleanTarget
  Write-Output "Synced skills from .codex to .agents."
}
