# get-ephe.ps1 — fetch the Swiss Ephemeris data files (.se1) for engine A (in-process pyswisseph).
#
# Without these files pyswisseph silently degrades to the Moshier model: planetary values drift by
# a few arcseconds and asteroid data is unavailable. Engine A therefore requires the same verified
# files as the pinned swiss-mcp container.
#
# SOURCE: the pinned `swiss-mcp` container image (/app/vendor/swisseph). Binaries are NOT
# committed to git — this script extracts them into infra/ephe/files/ (gitignored) and verifies
# every file against MANIFEST.sha256. A hash mismatch is a HARD failure: wrong files = silently
# different astrology.
#
# SOURCES:
#   docker (default) — docker cp from the running pinned container (local dev machine).
#   web              — raw.githubusercontent.com at the SAME pinned dm0lz commit the container
#                      image builds from (verified hash-identical 2026-07-03). For CI / Docker
#                      builds where no swiss-mcp container exists. NOTE: aloistr/swisseph MASTER
#                      files do NOT match (upstream evolves) — never fetch from master.
#
# USAGE:  pwsh infra/ephe/get-ephe.ps1 [-Source docker|web] [-Container swiss-mcp] [-OutDir <path>]

param(
  [ValidateSet("docker", "web")][string]$Source = "docker",
  [string]$Container = "swiss-mcp",
  [string]$OutDir = ""
)

# Must match infra/swiss-mcp/Dockerfile ARG DM0LZ_REF — the single pinned origin of the files.
$Dm0lzRef = "e164fced7699f0c574836895660f8f6f9b9c4bb8"

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $PSScriptRoot "files"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$manifestPath = Join-Path $PSScriptRoot "MANIFEST.sha256"
if (-not (Test-Path $manifestPath)) { throw "Manifest not found: $manifestPath" }

$expected = @{}
foreach ($line in Get-Content $manifestPath) {
  if ($line -match '^([0-9a-f]{64})\s+(\S+)$') { $expected[$Matches[2]] = $Matches[1] }
}
if ($expected.Count -eq 0) { throw "Manifest is empty or unparsable: $manifestPath" }

foreach ($name in $expected.Keys) {
  $dest = Join-Path $OutDir $name
  if ($Source -eq "web") {
    $url = "https://raw.githubusercontent.com/dm0lz/swiss-ephemeris-mcp-server/$Dm0lzRef/vendor/swisseph/$name"
    Invoke-WebRequest -Uri $url -OutFile $dest
  } else {
    docker cp "${Container}:/app/vendor/swisseph/$name" $dest | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "docker cp failed for $name (is container '$Container' running?)" }
  }
  $actual = (Get-FileHash -Algorithm SHA256 -Path $dest).Hash.ToLowerInvariant()
  if ($actual -ne $expected[$name]) {
    Remove-Item $dest -Force
    throw "SHA-256 MISMATCH for ${name}: expected $($expected[$name]), got $actual — refusing to keep the file"
  }
  Write-Output "OK $name ($actual)"
}

Write-Output "Ephemeris files ready in $OutDir (engine A will pick them up via SWISS_EPHE_PATH or the default repo path)."
