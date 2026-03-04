param(
  [Parameter(Mandatory = $true)][string]$CanvasPath,
  [Parameter(Mandatory = $true)][string]$TargetNodeId,
  [Parameter(Mandatory = $true)][ValidateSet("in_progress", "done", "blocked")][string]$Status,
  [string]$Message = "",
  [string]$Label = "status",
  [switch]$NoEdge
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CanvasPath)) {
  throw "Canvas file not found: $CanvasPath"
}

$canvas = Get-Content -Raw $CanvasPath | ConvertFrom-Json
$nodes = @($canvas.nodes)
$edges = @($canvas.edges)

$targetNode = $nodes | Where-Object { $_.id -eq $TargetNodeId } | Select-Object -First 1
if ($null -eq $targetNode) {
  throw "Target node not found: $TargetNodeId"
}

$aiNodeId = "ai_status_$TargetNodeId"
$aiNode = $nodes | Where-Object { $_.id -eq $aiNodeId } | Select-Object -First 1

$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$msgPart = if ([string]::IsNullOrWhiteSpace($Message)) { "" } else { "`n$Message" }
$aiText = "[AI] $Status$msgPart`nupdated: $timestamp"

if ($null -eq $aiNode) {
  $newX = [int]$targetNode.x + 420
  $newY = [int]$targetNode.y
  $aiNode = [pscustomobject]@{
    id = $aiNodeId
    type = "text"
    x = $newX
    y = $newY
    width = 340
    height = 180
    text = $aiText
  }
  $nodes += $aiNode
} else {
  $aiNode.text = $aiText
}

if (-not $NoEdge) {
  $edgeId = "ai_edge_$TargetNodeId"
  $edge = $edges | Where-Object { $_.id -eq $edgeId } | Select-Object -First 1
  if ($null -eq $edge) {
    $edge = [pscustomobject]@{
      id = $edgeId
      fromNode = $aiNodeId
      fromSide = "left"
      toNode = $TargetNodeId
      toSide = "right"
      label = $Label
    }
    $edges += $edge
  } else {
    $edge.fromNode = $aiNodeId
    $edge.toNode = $TargetNodeId
    $edge.label = $Label
  }
}

$canvas.nodes = $nodes
$canvas.edges = $edges
$canvas | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $CanvasPath

Write-Output "Canvas updated."
Write-Output ("AI node: {0}" -f $aiNodeId)
Write-Output ("Target node: {0}" -f $TargetNodeId)
Write-Output ("Status: {0}" -f $Status)
