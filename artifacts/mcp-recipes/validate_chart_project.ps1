param(
  [string]$ChartId = "",
  [string]$ChartsRoot = "",
  [string]$SchemaRoot = "",
  [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ChartsRoot)) {
  $ChartsRoot = Join-Path $PSScriptRoot "..\..\charts"
}
if ([string]::IsNullOrWhiteSpace($SchemaRoot)) {
  $SchemaRoot = Join-Path $PSScriptRoot "..\schemas\chart-project"
}

$ChartsRoot = [System.IO.Path]::GetFullPath($ChartsRoot)
$SchemaRoot = [System.IO.Path]::GetFullPath($SchemaRoot)

$chartSchemaPath = Join-Path $SchemaRoot "chart.schema.v1.json"
$indexSchemaPath = Join-Path $SchemaRoot "index.schema.v1.json"

if (-not (Test-Path $chartSchemaPath)) { throw "Schema missing: $chartSchemaPath" }
if (-not (Test-Path $indexSchemaPath)) { throw "Schema missing: $indexSchemaPath" }
if (-not (Test-Path $ChartsRoot)) { throw "ChartsRoot missing: $ChartsRoot" }

$chartSchema = Get-Content -Raw -Path $chartSchemaPath | ConvertFrom-Json
$indexSchema = Get-Content -Raw -Path $indexSchemaPath | ConvertFrom-Json

function Clean-Scalar {
  param([string]$Value)
  if ($null -eq $Value) { return "" }
  $x = $Value.Trim()
  if ((($x.StartsWith('"')) -and ($x.EndsWith('"'))) -or (($x.StartsWith("'")) -and ($x.EndsWith("'")))) {
    if ($x.Length -ge 2) {
      return $x.Substring(1, $x.Length - 2)
    }
  }
  return $x
}

function Add-Diagnostic {
  param(
    [Parameter(Mandatory = $true)][System.Collections.Generic.List[object]]$Bag,
    [Parameter(Mandatory = $true)][string]$Severity,
    [Parameter(Mandatory = $true)][string]$Code,
    [Parameter(Mandatory = $true)][string]$Target,
    [Parameter(Mandatory = $true)][string]$Message
  )
  $Bag.Add([pscustomobject]@{
    severity = $Severity
    code = $Code
    target = $Target
    message = $Message
  }) | Out-Null
}

function Parse-ChartYaml {
  param([Parameter(Mandatory = $true)][string]$Path)

  $res = @{
    top = @{}
    nested = @{}
  }
  $section = ""
  foreach ($line in (Get-Content -Path $Path)) {
    if ($line -match "^\s*$") { continue }
    if ($line -match "^\s*#") { continue }

    if ($line -match "^([A-Za-z0-9_]+):\s*(.*)$") {
      $key = $Matches[1]
      $value = Clean-Scalar -Value $Matches[2]
      if ([string]::IsNullOrWhiteSpace($Matches[2])) {
        $section = $key
        $res.top[$key] = ""
        if (-not $res.nested.ContainsKey($section)) {
          $res.nested[$section] = @{}
        }
      } else {
        $res.top[$key] = $value
        $section = ""
      }
      continue
    }

    if (($section -ne "") -and ($line -match "^\s{2}([A-Za-z0-9_]+):\s*(.*)$")) {
      $k = $Matches[1]
      $v = Clean-Scalar -Value $Matches[2]
      $res.nested[$section][$k] = $v
      continue
    }
  }
  return $res
}

function Parse-IndexYaml {
  param([Parameter(Mandatory = $true)][string]$Path)

  $top = @{}
  $rawItems = @()
  $outItems = @()
  $mode = ""
  $current = $null
  $skipSummary = $false

  foreach ($line in (Get-Content -Path $Path)) {
    if ($line -match "^\s*$") { continue }
    if ($line -match "^\s*#") { continue }

    if ($line -match "^([A-Za-z0-9_]+):\s*(.*)$") {
      $k = $Matches[1]
      $v = Clean-Scalar -Value $Matches[2]
      $top[$k] = $v
      if ($k -eq "raw_methods" -or $k -eq "outputs") {
        $mode = $k
      } else {
        $mode = ""
      }
      $current = $null
      $skipSummary = $false
      continue
    }

    if ($mode -eq "raw_methods") {
      if ($line -match "^\s{2}-\s+none\s*$") {
        $current = $null
        $skipSummary = $false
        continue
      }
      if ($line -match "^\s{2}-\s+([A-Za-z0-9_]+):\s*(.*)$") {
        $current = @{}
        $k = $Matches[1]
        $v = Clean-Scalar -Value $Matches[2]
        $current[$k] = $v
        $rawItems += $current
        $skipSummary = $false
        continue
      }
      if ($current -ne $null) {
        if ($line -match "^\s{4}summary:\s*(.*)$") {
          $skipSummary = $true
          continue
        }
        if ($skipSummary -and ($line -match "^\s{6}[A-Za-z0-9_]+:\s*.*$")) {
          continue
        }
        if ($line -match "^\s{4}([A-Za-z0-9_]+):\s*(.*)$") {
          $k = $Matches[1]
          $v = Clean-Scalar -Value $Matches[2]
          $current[$k] = $v
          $skipSummary = $false
          continue
        }
      }
      continue
    }

    if ($mode -eq "outputs") {
      if ($line -match "^\s{2}-\s+none\s*$") {
        $current = $null
        continue
      }
      if ($line -match "^\s{2}-\s+([A-Za-z0-9_]+):\s*(.*)$") {
        $current = @{}
        $k = $Matches[1]
        $v = Clean-Scalar -Value $Matches[2]
        $current[$k] = $v
        $outItems += $current
        continue
      }
      if (($current -ne $null) -and ($line -match "^\s{4}([A-Za-z0-9_]+):\s*(.*)$")) {
        $k = $Matches[1]
        $v = Clean-Scalar -Value $Matches[2]
        $current[$k] = $v
        continue
      }
    }
  }

  return @{
    top = $top
    raw_methods = @($rawItems)
    outputs = @($outItems)
  }
}

function Validate-ChartProject {
  param(
    [Parameter(Mandatory = $true)][string]$ChartDir
  )

  $diagnostics = [System.Collections.Generic.List[object]]::new()
  $chartName = Split-Path -Path $ChartDir -Leaf
  $chartYamlPath = Join-Path $ChartDir "chart.yaml"
  $indexYamlPath = Join-Path $ChartDir "INDEX.yaml"

  if (-not (Test-Path $chartYamlPath)) {
    Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "chart_missing" -Target "$chartName/chart.yaml" -Message "chart.yaml missing"
  }
  if (-not (Test-Path $indexYamlPath)) {
    Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_missing" -Target "$chartName/INDEX.yaml" -Message "INDEX.yaml missing"
  }
  if ($diagnostics.Count -gt 0) {
    return [pscustomobject]@{
      chart_id = $chartName
      status = "FAIL"
      errors = @($diagnostics)
      error_count = @($diagnostics | Where-Object { $_.severity -eq "error" }).Count
      warning_count = @($diagnostics | Where-Object { $_.severity -eq "warning" }).Count
    }
  }

  $chartDoc = Parse-ChartYaml -Path $chartYamlPath
  $indexDoc = Parse-IndexYaml -Path $indexYamlPath

  foreach ($k in $chartSchema.required_top_level_keys) {
    if (-not $chartDoc.top.ContainsKey([string]$k)) {
      Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "chart_required_top_missing" -Target "chart.yaml:$k" -Message "Required top-level key missing"
    }
  }

  foreach ($sectionName in $chartSchema.required_nested_keys.PSObject.Properties.Name) {
    if (-not $chartDoc.nested.ContainsKey([string]$sectionName)) {
      Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "chart_required_section_missing" -Target "chart.yaml:$sectionName" -Message "Required section missing"
      continue
    }
    $sectionMap = $chartDoc.nested[[string]$sectionName]
    foreach ($rk in $chartSchema.required_nested_keys.$sectionName) {
      if (-not $sectionMap.ContainsKey([string]$rk)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "chart_required_nested_missing" -Target "chart.yaml:$sectionName.$rk" -Message "Required nested key missing"
      }
    }
  }

  foreach ($k in $indexSchema.required_top_level_keys) {
    if (-not $indexDoc.top.ContainsKey([string]$k)) {
      Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_required_top_missing" -Target "INDEX.yaml:$k" -Message "Required top-level key missing"
    }
  }

  foreach ($vkey in $indexSchema.required_top_level_values.PSObject.Properties.Name) {
    if ($indexDoc.top.ContainsKey([string]$vkey)) {
      $actual = [string]$indexDoc.top[[string]$vkey]
      $expected = [string]$indexSchema.required_top_level_values.$vkey
      if ($actual -ne $expected) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_required_value_mismatch" -Target "INDEX.yaml:$vkey" -Message ("Expected '{0}', got '{1}'" -f $expected, $actual)
      }
    }
  }

  if ($chartDoc.top.ContainsKey("chart_id") -and $indexDoc.top.ContainsKey("chart_id")) {
    $cidChart = [string]$chartDoc.top["chart_id"]
    $cidIndex = [string]$indexDoc.top["chart_id"]
    if ($cidChart -ne $cidIndex) {
      Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "chart_id_mismatch" -Target "chart.yaml/index.yaml" -Message ("chart_id mismatch: chart='{0}', index='{1}'" -f $cidChart, $cidIndex)
    }
  }

  if ($indexDoc.top.ContainsKey("chart_file")) {
    $chartFileRel = [string]$indexDoc.top["chart_file"]
    $chartFileAbs = Join-Path $ChartDir $chartFileRel
    if (-not (Test-Path $chartFileAbs)) {
      Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_chart_file_missing" -Target "INDEX.yaml:chart_file" -Message ("chart_file target not found: {0}" -f $chartFileRel)
    }
  }

  if ($indexDoc.raw_methods.Count -eq 0) {
    Add-Diagnostic -Bag $diagnostics -Severity "warning" -Code "index_raw_methods_empty" -Target "INDEX.yaml:raw_methods" -Message "No raw_methods entries found"
  }
  $rawIx = 0
  foreach ($item in $indexDoc.raw_methods) {
    $rawIx++
    foreach ($rk in $indexSchema.required_raw_method_item_keys) {
      if (-not $item.ContainsKey([string]$rk)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_raw_item_required_missing" -Target ("INDEX.yaml:raw_methods[{0}].{1}" -f $rawIx, $rk) -Message "Required raw method key missing"
      }
    }
    if ($item.ContainsKey("canonical_run_dir")) {
      $rel = [string]$item["canonical_run_dir"]
      $abs = Join-Path $ChartDir $rel
      if (-not (Test-Path $abs)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_canonical_run_missing" -Target ("INDEX.yaml:raw_methods[{0}].canonical_run_dir" -f $rawIx) -Message ("Canonical run path missing: {0}" -f $rel)
      }
    }
  }

  if ($indexDoc.outputs.Count -eq 0) {
    Add-Diagnostic -Bag $diagnostics -Severity "warning" -Code "index_outputs_empty" -Target "INDEX.yaml:outputs" -Message "No outputs entries found"
  }
  $outIx = 0
  foreach ($item in $indexDoc.outputs) {
    $outIx++
    foreach ($rk in $indexSchema.required_output_item_keys) {
      if (-not $item.ContainsKey([string]$rk)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_output_item_required_missing" -Target ("INDEX.yaml:outputs[{0}].{1}" -f $outIx, $rk) -Message "Required output key missing"
      }
    }
    if ($item.ContainsKey("file")) {
      $relOut = [string]$item["file"]
      $outAbs = Join-Path $ChartDir $relOut
      if (-not (Test-Path $outAbs)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_output_file_missing" -Target ("INDEX.yaml:outputs[{0}].file" -f $outIx) -Message ("Output file missing: {0}" -f $relOut)
      }
    }
    if ($item.ContainsKey("canonical_source")) {
      $relSrc = [string]$item["canonical_source"]
      $srcAbs = Join-Path $ChartDir $relSrc
      if (-not (Test-Path $srcAbs)) {
        Add-Diagnostic -Bag $diagnostics -Severity "error" -Code "index_canonical_source_missing" -Target ("INDEX.yaml:outputs[{0}].canonical_source" -f $outIx) -Message ("Canonical source missing: {0}" -f $relSrc)
      }
    }
  }

  $errCount = @($diagnostics | Where-Object { $_.severity -eq "error" }).Count
  $warnCount = @($diagnostics | Where-Object { $_.severity -eq "warning" }).Count
  $status = if ($errCount -eq 0) { "PASS" } else { "FAIL" }
  return [pscustomobject]@{
    chart_id = $chartName
    status = $status
    errors = @($diagnostics)
    error_count = $errCount
    warning_count = $warnCount
  }
}

$chartDirs = @()
if ([string]::IsNullOrWhiteSpace($ChartId)) {
  $chartDirs = @(Get-ChildItem -Path $ChartsRoot -Directory | Where-Object { (Test-Path (Join-Path $_.FullName "chart.yaml")) -or (Test-Path (Join-Path $_.FullName "INDEX.yaml")) })
} else {
  $d = Join-Path $ChartsRoot $ChartId
  if (-not (Test-Path $d)) { throw "Chart dir not found: $d" }
  $chartDirs = @([System.IO.DirectoryInfo]$d)
}

$reports = @()
foreach ($d in $chartDirs) {
  $reports += Validate-ChartProject -ChartDir $d.FullName
}

$total = $reports.Count
$failed = @($reports | Where-Object { $_.status -eq "FAIL" }).Count
$passed = $total - $failed
$errors = ($reports | ForEach-Object { $_.error_count } | Measure-Object -Sum).Sum
$warnings = ($reports | ForEach-Object { $_.warning_count } | Measure-Object -Sum).Sum

Write-Output ("CHARTS_CHECKED=" + $total)
Write-Output ("PASSED=" + $passed)
Write-Output ("FAILED=" + $failed)
Write-Output ("ERROR_COUNT=" + $errors)
Write-Output ("WARNING_COUNT=" + $warnings)

if (-not [string]::IsNullOrWhiteSpace($OutputJson)) {
  $payload = [pscustomobject]@{
    checked_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    charts_checked = $total
    passed = $passed
    failed = $failed
    error_count = $errors
    warning_count = $warnings
    reports = $reports
  }
  $payload | ConvertTo-Json -Depth 20 | Set-Content -Path $OutputJson -Encoding UTF8
}

if ($failed -gt 0) {
  foreach ($r in ($reports | Where-Object { $_.status -eq "FAIL" })) {
    Write-Output ("--- FAIL: " + $r.chart_id)
    foreach ($diag in $r.errors) {
      Write-Output ("[{0}] {1} {2} :: {3}" -f $diag.severity.ToUpperInvariant(), $diag.code, $diag.target, $diag.message)
    }
  }
  throw "Chart project validation failed."
}

Write-Output "Chart project validation: PASS"
