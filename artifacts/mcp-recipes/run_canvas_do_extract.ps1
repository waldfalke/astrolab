param(
  [Parameter(Mandatory = $true)][string]$CanvasPath,
  [string]$OutJson = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CanvasPath)) {
  throw "Canvas file not found: $CanvasPath"
}

$canvas = Get-Content -Raw $CanvasPath | ConvertFrom-Json
$nodes = @($canvas.nodes)
$edges = @($canvas.edges)

$doNodes = @(
  $nodes | Where-Object {
    $_.type -eq "text" -and
    -not [string]::IsNullOrWhiteSpace($_.text) -and
    $_.text.TrimStart().StartsWith("[DO]")
  }
)

$nodeById = @{}
foreach ($n in $nodes) { $nodeById[$n.id] = $n }

$result = @()
foreach ($n in $doNodes) {
  $linkedEdges = @($edges | Where-Object { $_.fromNode -eq $n.id -or $_.toNode -eq $n.id })
  $links = @()
  foreach ($e in $linkedEdges) {
    $otherId = if ($e.fromNode -eq $n.id) { $e.toNode } else { $e.fromNode }
    $otherNode = $nodeById[$otherId]
    $otherPreview = ""
    if ($null -ne $otherNode -and $otherNode.PSObject.Properties.Name -contains "text") {
      $otherPreview = [string]$otherNode.text
      if ($otherPreview.Length -gt 120) {
        $otherPreview = $otherPreview.Substring(0, 120) + "..."
      }
    }
    $links += [pscustomobject]@{
      edge_id = [string]$e.id
      from = [string]$e.fromNode
      to = [string]$e.toNode
      label = [string]$e.label
      other_node_id = [string]$otherId
      other_node_type = if ($null -ne $otherNode) { [string]$otherNode.type } else { "" }
      other_node_preview = $otherPreview
    }
  }

  $result += [pscustomobject]@{
    node_id = [string]$n.id
    x = [int]$n.x
    y = [int]$n.y
    text = [string]$n.text
    links = $links
  }
}

$summary = [pscustomobject]@{
  canvas_path = (Resolve-Path $CanvasPath).Path
  do_count = $result.Count
  do_items = $result
}

Write-Output ("Canvas: {0}" -f $summary.canvas_path)
Write-Output ("[DO] nodes: {0}" -f $summary.do_count)

foreach ($item in $summary.do_items) {
  Write-Output ""
  Write-Output ("- node_id: {0}" -f $item.node_id)
  Write-Output ("  text: {0}" -f $item.text.Replace("`n", " "))
  if (@($item.links).Count -eq 0) {
    Write-Output "  links: none"
  } else {
    Write-Output ("  links: {0}" -f @($item.links).Count)
    foreach ($lnk in $item.links) {
      Write-Output ("    * {0} -> {1} label='{2}' other={3}" -f $lnk.from, $lnk.to, $lnk.label, $lnk.other_node_id)
    }
  }
}

if (-not [string]::IsNullOrWhiteSpace($OutJson)) {
  $outDir = Split-Path -Parent $OutJson
  if (-not [string]::IsNullOrWhiteSpace($outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  }
  $summary | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $OutJson
  Write-Output ("Saved JSON: {0}" -f (Resolve-Path $OutJson).Path)
}
