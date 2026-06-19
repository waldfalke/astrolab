param(
  [Parameter(Mandatory = $true)][string]$ChartId,
  [Parameter(Mandatory = $true)][string]$ChartsRoot,   # MUST be under .private (PII)
  [Parameter(Mandatory = $true)][string]$ProseMd,      # model output (the [[SECTION]] contract)
  [string]$SolarReturnRunDir = "",
  [string]$NatalRunDir = "",
  [string]$TransitTimelineCsv = "",
  [string]$OutputBase = ""
)

# ============================================================================================
# Assemble the grand report — the deterministic BACK HALF of run_solar_gift.
#
#   Twin symmetry: WINDOW chapters (time axis, carrier_windows) + SPHERE sections (domain axis,
#   sphere_summary) both expand here. The model gives PROSE (prose.md); every NUMBER (techblocks)
#   and every WHEEL is produced HERE from compute — the model never hand-builds either.
#
# Provenance: stamps a run-dir + manifest.json with SHA256 of each source (template, prose, data,
# wheels) so the deliverable is reproducible and auditable (the blind run lost the gate output;
# nothing about the assembly should be unrecorded). PII stays under .private.
# ============================================================================================

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\lib\mcp_helpers.ps1"
$scriptId = "run_assemble_report"; $scriptVersion = "0.1.0"
$here = $PSScriptRoot
$repo = [System.IO.Path]::GetFullPath((Join-Path $here "..\.."))

if ($ChartsRoot -notmatch "\.private") { throw "GUARD: ChartsRoot must be under .private (client PII) — got '$ChartsRoot'." }
$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)
$chartDir = Join-Path $ChartsRoot $ChartId
if (-not (Test-Path $chartDir)) { throw "chart project not found: $chartDir" }
$packs = Join-Path $chartDir "packs"
if ([string]::IsNullOrWhiteSpace($OutputBase)) { $OutputBase = Join-Path $chartDir "_runs" }
$env:PYTHONIOENCODING = "utf-8"

function LatestDir($base, $prefix) {
  $d = Get-ChildItem -Path $base -Directory -Filter "$prefix*" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($d) { return $d.FullName } else { return "" }
}
if ([string]::IsNullOrWhiteSpace($SolarReturnRunDir)) { $SolarReturnRunDir = LatestDir $OutputBase "solar_return_$ChartId" }
if ([string]::IsNullOrWhiteSpace($NatalRunDir))       { $NatalRunDir = LatestDir $OutputBase "natal_failover_$ChartId" }
if ([string]::IsNullOrWhiteSpace($TransitTimelineCsv)) {
  $tt = LatestDir $OutputBase "transit_timeline_$ChartId"; if ($tt) { $TransitTimelineCsv = Join-Path $tt "03_carrier_windows.csv" }
}
foreach ($p in @($SolarReturnRunDir, $NatalRunDir, $TransitTimelineCsv, $ProseMd)) {
  if ([string]::IsNullOrWhiteSpace($p) -or -not (Test-Path $p)) { throw "missing required input: '$p'" }
}

$runDir = New-RunDirectory -BaseDir $OutputBase -Prefix ("assemble_report_" + $ChartId)
$wheels = Join-Path $runDir "wheels"; New-Item -ItemType Directory -Force -Path $wheels | Out-Null

# ── 1. render wheels (real SVGs — the model never hand-draws) ─────────────────────────────────
Write-Host "  rendering wheels..."
function RenderWheel($outerCsv, $destName) {
  $renderBase = Join-Path $runDir "_render_tmp"
  $argv = @("-ChartId", $ChartId, "-ChartsRoot", $ChartsRoot, "-OutputBase", $renderBase)
  if ($outerCsv) { $argv += @("-OuterPlanetsCsv", $outerCsv) }
  & pwsh -NoProfile -File (Join-Path $here "run_renderer.ps1") @argv 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "renderer failed for $destName" }
  $rd = LatestDir $renderBase ("renderer_" + $ChartId)
  $svg = Join-Path $rd "01_chart_wheel.svg"
  if (Test-Path $svg) { Copy-Item $svg (Join-Path $wheels $destName) -Force }
}
# natal (no outer ring) + SR biwheel (SR planets as outer ring)
RenderWheel $null "natal.svg"
$srPlanets = Join-Path $SolarReturnRunDir "02_return_planets.csv"
RenderWheel $srPlanets "sr.svg"

# window biwheels — ONLY for windows the model selected (prose [[WINDOW open=...]]). Outer ring =
# REAL transit positions at the window's PEAK date (one swiss call per chosen window), so the wheel's
# "натал + транзит" caption is true, not a placeholder.
$chartYaml = Get-Content (Join-Path $chartDir "chart.yaml") -Raw
$lat = ([regex]::Match($chartYaml, 'latitude:\s*([-0-9.]+)')).Groups[1].Value
$lon = ([regex]::Match($chartYaml, 'longitude:\s*([-0-9.]+)')).Groups[1].Value
$carrierRows = @(Import-Csv $TransitTimelineCsv)
function PeakOf($open) {
  $r = $carrierRows | Where-Object { $_.window_open -eq $open } | Select-Object -First 1
  if (-not $r) { return "" }
  $ex = ($r.exact_dates -split ';')[0].Trim(); if ($ex) { return $ex } else { return $open }
}
$selectedOpens = @()
foreach ($line in (Get-Content $ProseMd)) {
  $m = [regex]::Match($line, '^\s*\[\[WINDOW\s+open=([0-9-]+)')
  if ($m.Success) { $selectedOpens += $m.Groups[1].Value }
}
foreach ($open in ($selectedOpens | Select-Object -Unique)) {
  $peak = PeakOf $open
  $ringCsv = Join-Path $wheels ("transit_ring_" + $open + ".csv")
  try {
    $chart = Invoke-SwissPrimaryToolJson -Tool "calculate_planetary_positions" -Args @{ datetime = "${peak}T12:00:00Z"; latitude = [double]$lat; longitude = [double]$lon }
    $inv = [System.Globalization.CultureInfo]::InvariantCulture
    $ringRows = @(Get-SwissBodyLongitudes -SwissData $chart) | ForEach-Object {
      [pscustomobject]@{ body = $_.body; longitude = ([double]$_.longitude).ToString($inv) }   # invariant: dot decimal (renderer parses)
    }
    $ringRows | Export-Csv $ringCsv -NoTypeInformation -Encoding UTF8
    RenderWheel $ringCsv ("window_" + $open + ".svg")
  } catch {
    Write-Host "  WARN: transit ring for window $open failed ($($_.Exception.Message)) — natal-only wheel" -ForegroundColor Yellow
    RenderWheel $null ("window_" + $open + ".svg")
  }
}
Write-Host ("  wheels: natal + sr + {0} window(s)" -f ($selectedOpens | Select-Object -Unique).Count)

# ── 2. assemble HTML (deterministic fill from prose + compute) ────────────────────────────────
$stamp = (Get-ChildItem $runDir).CreationTime  # avoid Date.now in scripts; use run-dir stamp
$htmlOut = Join-Path $packs ("grand_report_" + $ChartId + ".html")
& python (Join-Path $here "assemble_report.py") `
  "--template" (Join-Path $repo "artifacts\report-templates\grand-report.html") `
  "--prose" $ProseMd "--out" $htmlOut `
  "--sr-dir" $SolarReturnRunDir "--carrier" $TransitTimelineCsv `
  "--outputs" (Join-Path $chartDir "outputs") "--natal-dir" $NatalRunDir `
  "--sphere-summary" (Join-Path $packs "sphere_summary.csv") "--renders" $wheels
if ($LASTEXITCODE -ne 0) { throw "assemble_report.py failed (exit $LASTEXITCODE)" }

# ── 3. HTML -> PDF via playwright (chromium) ──────────────────────────────────────────────────
$pdfOut = Join-Path $packs ("grand_report_" + $ChartId + ".pdf")
$pyPdf = @"
import sys
from playwright.sync_api import sync_playwright
src, dst = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('file:///' + src.replace('\\','/'))
    pg.pdf(path=dst, format='A4', print_background=True,
           margin={'top':'14mm','bottom':'14mm','left':'12mm','right':'12mm'})
    b.close()
print('pdf -> ' + dst)
"@
$pyPdfFile = Join-Path $runDir "_html2pdf.py"
Set-Content -Path $pyPdfFile -Value $pyPdf -Encoding UTF8
& python $pyPdfFile $htmlOut $pdfOut 2>&1 | ForEach-Object { $_ }
if ($LASTEXITCODE -ne 0) { throw "HTML->PDF (playwright) failed — is chromium installed? (python -m playwright install chromium)" }

# ── 4. provenance manifest (SHA256 of every source + product) ─────────────────────────────────
function Sha($p) { if (Test-Path $p) { (Get-FileHash -Algorithm SHA256 $p).Hash } else { "" } }
$manifest = [ordered]@{
  script = $scriptId; version = $scriptVersion; chart_id = $ChartId
  inputs = [ordered]@{
    template = Sha (Join-Path $repo "artifacts\report-templates\grand-report.html")
    prose = Sha $ProseMd; carrier = Sha $TransitTimelineCsv
    sphere_summary = Sha (Join-Path $packs "sphere_summary.csv")
    sr_dir = $SolarReturnRunDir; natal_dir = $NatalRunDir
  }
  products = [ordered]@{ html = Sha $htmlOut; pdf = Sha $pdfOut }
  wheels = (Get-ChildItem $wheels -Filter *.svg | ForEach-Object { $_.Name })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $runDir "manifest.json") -Encoding UTF8

Write-Host "  assembled report:" -ForegroundColor Green
Write-Host "    HTML: $htmlOut"
Write-Host "    PDF:  $pdfOut"
Write-Host "    provenance: $(Join-Path $runDir 'manifest.json')"
