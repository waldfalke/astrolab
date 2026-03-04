using namespace System.Globalization

$script:SwissRetryTelemetry = [ordered]@{
  total_retries = 0
  by_tool = @{}
}

function Invoke-McpToolJson {
  param(
    [Parameter(Mandatory = $true)][ValidateSet("http", "stdio")][string]$Mode,
    [Parameter(Mandatory = $false)][string]$Url = "",
    [Parameter(Mandatory = $false)][string]$StdioCommand = "",
    [Parameter(Mandatory = $true)][string]$ServerName,
    [Parameter(Mandatory = $true)][string]$Tool,
    [Parameter(Mandatory = $false)][hashtable]$Args = @{},
    [int]$CallTimeoutMs = 120000
  )

  $argList = @("-y", "mcporter", "call")
  if ($Mode -eq "http") {
    if ([string]::IsNullOrWhiteSpace($Url)) {
      throw "Invoke-McpToolJson: Url is required for Mode=http"
    }
    $argList += @("--http-url", $Url)
  } else {
    if ([string]::IsNullOrWhiteSpace($StdioCommand)) {
      throw "Invoke-McpToolJson: StdioCommand is required for Mode=stdio"
    }
    $argList += @("--stdio", $StdioCommand)
  }

  $argList += @("--name", $ServerName, $Tool)

  foreach ($key in ($Args.Keys | Sort-Object)) {
    $value = $Args[$key]
    if ($null -eq $value) { continue }
    if ($value -is [array]) {
      $value = ($value -join ",")
    }
    if ($value -is [double] -or $value -is [single] -or $value -is [decimal]) {
      $value = $value.ToString([CultureInfo]::InvariantCulture)
    }
    if ($value -is [int] -or $value -is [long]) {
      $value = $value.ToString([CultureInfo]::InvariantCulture)
    }
    $argList += ("{0}:{1}" -f $key, $value)
  }

  $argList += @("--output", "json")
  $env:MCPORTER_CALL_TIMEOUT = $CallTimeoutMs.ToString([CultureInfo]::InvariantCulture)
  $raw = npx @argList
  if ($LASTEXITCODE -ne 0) {
    throw "mcporter call failed for tool: $Tool ($ServerName)"
  }

  try {
    $parsed = ($raw | ConvertFrom-Json)
    if ($parsed.PSObject.Properties.Name -contains "error") {
      throw "MCP tool error: $($parsed.error)"
    }
    if (($parsed.PSObject.Properties.Name -contains "isError") -and ($parsed.isError -eq $true)) {
      $msg = ""
      if ($parsed.PSObject.Properties.Name -contains "content") {
        $parts = @()
        foreach ($c in $parsed.content) {
          if ($c.PSObject.Properties.Name -contains "text") { $parts += [string]$c.text }
        }
        $msg = ($parts -join " | ")
      }
      if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "Unknown MCP tool error." }
      throw $msg
    }
    return $parsed
  } catch {
    throw "mcporter call/result handling failed for tool: $Tool ($ServerName)`n$($_.Exception.Message)`n$raw"
  }
}

function Invoke-EphemToolJson {
  param(
    [Parameter(Mandatory = $true)][string]$Tool,
    [Parameter(Mandatory = $false)][hashtable]$Args = @{}
  )

  return Invoke-McpToolJson -Mode "http" -Url "https://ephemeris.fyi/mcp" -ServerName "ephem" -Tool $Tool -Args $Args
}

function Invoke-SwissPrimaryToolJson {
  param(
    [Parameter(Mandatory = $true)][string]$Tool,
    [Parameter(Mandatory = $false)][hashtable]$Args = @{},
    [int]$MaxAttempts = 3
  )

  $attempt = 0
  while ($attempt -lt $MaxAttempts) {
    $attempt++
    try {
      return Invoke-McpToolJson -Mode "http" -Url "https://www.theme-astral.me/mcp" -ServerName "swissremote" -Tool $Tool -Args $Args
    } catch {
      if (-not $script:SwissRetryTelemetry.by_tool.ContainsKey($Tool)) {
        $script:SwissRetryTelemetry.by_tool[$Tool] = 0
      }
      $script:SwissRetryTelemetry.total_retries += 1
      $script:SwissRetryTelemetry.by_tool[$Tool] = [int]$script:SwissRetryTelemetry.by_tool[$Tool] + 1
      if ($attempt -ge $MaxAttempts) { throw }
      Start-Sleep -Seconds (2 * $attempt)
    }
  }
}

function Reset-SwissRetryTelemetry {
  $script:SwissRetryTelemetry = [ordered]@{
    total_retries = 0
    by_tool = @{}
  }
}

function Get-SwissRetryTelemetry {
  $toolParts = @()
  foreach ($k in ($script:SwissRetryTelemetry.by_tool.Keys | Sort-Object)) {
    $toolParts += ("{0}:{1}" -f $k, [int]$script:SwissRetryTelemetry.by_tool[$k])
  }

  return [pscustomobject]@{
    total_retries = [int]$script:SwissRetryTelemetry.total_retries
    by_tool = ($toolParts -join ",")
  }
}

function New-RunDirectory {
  param(
    [Parameter(Mandatory = $true)][string]$BaseDir,
    [Parameter(Mandatory = $true)][string]$Prefix
  )

  $ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
  $dir = Join-Path $BaseDir "${Prefix}_${ts}"
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  return $dir
}

function Write-JsonFile {
  param(
    [Parameter(Mandatory = $true)]$Data,
    [Parameter(Mandatory = $true)][string]$Path
  )

  $json = $Data | ConvertTo-Json -Depth 100
  Set-Content -Path $Path -Value $json -Encoding UTF8
}

function Get-BodyLongitudes {
  param(
    [Parameter(Mandatory = $true)]$Ephemeris,
    [string[]]$Bodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "chiron")
  )

  $rows = @()
  foreach ($body in $Bodies) {
    if ($Ephemeris.PSObject.Properties.Name -contains $body) {
      $node = $Ephemeris.$body
      if ($null -ne $node.apparentLongitude) {
        $rows += [pscustomobject]@{
          body = $body
          longitude = [double]$node.apparentLongitude
          longitude_string = $node.apparentLongitudeString
          longitude_30_string = $node.apparentLongitude30String
        }
      }
    }
  }
  return $rows
}

function Get-SwissBodyLongitudes {
  param(
    [Parameter(Mandatory = $true)]$SwissData,
    [string[]]$Bodies = @("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
  )

  $rows = @()
  if ($null -eq $SwissData.planets) { return $rows }

  foreach ($body in $Bodies) {
    if ($SwissData.planets.PSObject.Properties.Name -contains $body) {
      $node = $SwissData.planets.$body
      if ($null -ne $node.longitude) {
        $rows += [pscustomobject]@{
          body = $body.ToLowerInvariant()
          longitude = [double]$node.longitude
          sign = [string]$node.sign
          degree = [double]$node.degree
        }
      }
    }
  }
  return $rows
}

function Normalize-Longitude {
  param(
    [Parameter(Mandatory = $true)][double]$Longitude
  )

  $x = $Longitude % 360.0
  if ($x -lt 0) { $x += 360.0 }
  return $x
}

function Convert-LongitudeToSignDegree {
  param(
    [Parameter(Mandatory = $true)][double]$Longitude
  )

  $signs = @(
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
  )

  $lon = Normalize-Longitude -Longitude $Longitude
  $signIndex = [int][math]::Floor($lon / 30.0)
  $degInSign = $lon - (30.0 * $signIndex)

  return [pscustomobject]@{
    longitude = $lon
    sign = $signs[$signIndex]
    degree = [math]::Round($degInSign, 2)
  }
}

function Get-MinDelta360 {
  param(
    [Parameter(Mandatory = $true)][double]$A,
    [Parameter(Mandatory = $true)][double]$B
  )

  $d = [math]::Abs((Normalize-Longitude -Longitude $A) - (Normalize-Longitude -Longitude $B))
  if ($d -gt 180.0) { $d = 360.0 - $d }
  return $d
}

function Get-ClosestMajorAspect {
  param(
    [Parameter(Mandatory = $true)][double]$Angle,
    [double]$Orb = 2.0
  )

  $defs = @(
    [pscustomobject]@{ name = "conjunction"; angle = 0.0 },
    [pscustomobject]@{ name = "sextile"; angle = 60.0 },
    [pscustomobject]@{ name = "square"; angle = 90.0 },
    [pscustomobject]@{ name = "trine"; angle = 120.0 },
    [pscustomobject]@{ name = "opposition"; angle = 180.0 }
  )

  $best = $null
  foreach ($def in $defs) {
    $delta = [math]::Abs($Angle - [double]$def.angle)
    if (($null -eq $best) -or ($delta -lt $best.delta)) {
      $best = [pscustomobject]@{
        aspect = [string]$def.name
        exact_angle = [double]$def.angle
        delta = [double]$delta
      }
    }
  }

  if (($null -ne $best) -and ($best.delta -le $Orb)) {
    return $best
  }
  return $null
}

function Get-CustomPointAspects {
  param(
    [Parameter(Mandatory = $true)][array]$PlanetRows,
    [Parameter(Mandatory = $true)][array]$PointRows,
    [double]$Orb = 2.0
  )

  $rows = @()
  foreach ($point in $PointRows) {
    $pointLon = [double]$point.longitude
    foreach ($planet in $PlanetRows) {
      $planetLon = [double]$planet.longitude
      $angle = Get-MinDelta360 -A $pointLon -B $planetLon
      $hit = Get-ClosestMajorAspect -Angle $angle -Orb $Orb
      if ($null -eq $hit) { continue }

      $rows += [pscustomobject]@{
        point = [string]$point.point
        body = [string]$planet.body
        aspect = [string]$hit.aspect
        actual_angle = [math]::Round([double]$angle, 6)
        exact_angle = [double]$hit.exact_angle
        orb = [math]::Round([double]$hit.delta, 6)
        orb_limit = [double]$Orb
        is_exact = ([double]$hit.delta -le 0.2)
      }
    }
  }
  return ($rows | Sort-Object point, orb, body)
}

function Get-SwissNodePoints {
  param(
    [Parameter(Mandatory = $true)]$SwissData
  )

  $rows = @()
  $north = $null

  if (($null -ne $SwissData.planets) -and ($SwissData.planets.PSObject.Properties.Name -contains "North Node")) {
    $north = $SwissData.planets."North Node"
  } elseif (($null -ne $SwissData.additional_points) -and ($SwissData.additional_points.PSObject.Properties.Name -contains "North Node")) {
    $north = $SwissData.additional_points."North Node"
  }

  if ($null -ne $north) {
    $northLon = [double]$north.longitude
    $rows += [pscustomobject]@{
      point = "North Node"
      longitude = $northLon
      sign = [string]$north.sign
      degree = [double]$north.degree
    }

    if (($null -ne $SwissData.additional_points) -and ($SwissData.additional_points.PSObject.Properties.Name -contains "South Node")) {
      $south = $SwissData.additional_points."South Node"
      $rows += [pscustomobject]@{
        point = "South Node"
        longitude = [double]$south.longitude
        sign = [string]$south.sign
        degree = [double]$south.degree
      }
    } else {
      $southCoord = Convert-LongitudeToSignDegree -Longitude ($northLon + 180.0)
      $rows += [pscustomobject]@{
        point = "South Node"
        longitude = [double]$southCoord.longitude
        sign = [string]$southCoord.sign
        degree = [double]$southCoord.degree
      }
    }
  }

  return $rows
}

function Get-GalacticCenterPoint {
  param(
    [Parameter(Mandatory = $true)][string]$DateTimeUtc
  )

  # Reference: Astro.com Astrowiki table gives tropical GC at epoch 2000 as 26deg51' Sagittarius.
  # We propagate with mean precession in longitude (~50.29 arcsec/year; Swiss Ephemeris docs mention ~1 deg / 71.6 years).
  $gcJ2000Lon = 266.85
  $precessionDegPerYear = 50.29 / 3600.0
  $j2000Utc = [datetime]"2000-01-01T12:00:00Z"
  $t = [datetime]::Parse($DateTimeUtc, [CultureInfo]::InvariantCulture, [DateTimeStyles]::AssumeUniversal -bor [DateTimeStyles]::AdjustToUniversal)
  $years = ($t - $j2000Utc).TotalDays / 365.2422
  $gcLon = Normalize-Longitude -Longitude ($gcJ2000Lon + ($precessionDegPerYear * $years))
  $coord = Convert-LongitudeToSignDegree -Longitude $gcLon

  return [pscustomobject]@{
    point = "Galactic Center"
    longitude = [math]::Round([double]$coord.longitude, 9)
    sign = [string]$coord.sign
    degree = [double]$coord.degree
  }
}

function Convert-ToInvariantScalarString {
  param(
    [Parameter(Mandatory = $false)]$Value
  )

  if ($null -eq $Value) { return "" }

  if ($Value -is [bool]) {
    return ([string]$Value).ToUpperInvariant()
  }

  if ($Value -is [datetime]) {
    return ([datetime]$Value).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ", [CultureInfo]::InvariantCulture)
  }

  if (
    ($Value -is [double]) -or
    ($Value -is [single]) -or
    ($Value -is [decimal])
  ) {
    return [System.Convert]::ToString($Value, [CultureInfo]::InvariantCulture)
  }

  if (
    ($Value -is [int]) -or
    ($Value -is [long]) -or
    ($Value -is [int16]) -or
    ($Value -is [byte]) -or
    ($Value -is [uint16]) -or
    ($Value -is [uint32]) -or
    ($Value -is [uint64])
  ) {
    return [System.Convert]::ToString($Value, [CultureInfo]::InvariantCulture)
  }

  return [string]$Value
}

function Write-InvariantCsv {
  param(
    [Parameter(Mandatory = $true)][array]$Rows,
    [Parameter(Mandatory = $true)][string]$Path,
    [string[]]$Columns = @()
  )

  $selectedColumns = @($Columns)
  if ($selectedColumns.Count -eq 0 -and $Rows.Count -gt 0) {
    $selectedColumns = @($Rows[0].PSObject.Properties.Name)
  }

  if ($Rows.Count -eq 0) {
    if ($selectedColumns.Count -eq 0) {
      Set-Content -Path $Path -Encoding UTF8 -Value ""
      return
    }

    $header = '"' + ($selectedColumns -join '","') + '"'
    Set-Content -Path $Path -Encoding UTF8 -Value $header
    return
  }

  $normRows = @()
  foreach ($r in $Rows) {
    $out = [ordered]@{}
    foreach ($col in $selectedColumns) {
      $raw = $null
      if ($r.PSObject.Properties.Name -contains $col) {
        $raw = $r.$col
      }
      $out[$col] = Convert-ToInvariantScalarString -Value $raw
    }
    $normRows += [pscustomobject]$out
  }

  $normRows | ConvertTo-Csv -NoTypeInformation | Set-Content -Path $Path -Encoding UTF8
}

function Get-Sha256FromString {
  param(
    [Parameter(Mandatory = $true)][string]$Value
  )

  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    $hashBytes = $sha.ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hashBytes) -replace "-", "").ToLowerInvariant()
  } finally {
    $sha.Dispose()
  }
}

function Get-CanonicalMapHash {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Map
  )

  $lines = @()
  foreach ($k in ($Map.Keys | Sort-Object)) {
    $lines += ([string]$k + "=" + (Convert-ToInvariantScalarString -Value $Map[$k]))
  }
  return Get-Sha256FromString -Value ($lines -join "`n")
}

function Get-RunOutputHash {
  param(
    [Parameter(Mandatory = $true)][string]$RunDir,
    [string[]]$ExcludeFiles = @("00_summary.txt")
  )

  $ex = @{}
  foreach ($f in $ExcludeFiles) {
    $ex[$f.ToLowerInvariant()] = $true
  }

  $files = @(Get-ChildItem -Path $RunDir -File | Where-Object { -not $ex.ContainsKey($_.Name.ToLowerInvariant()) } | Sort-Object Name)
  $parts = @()
  foreach ($f in $files) {
    $h = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $parts += ($f.Name + ":" + $h)
  }
  return Get-Sha256FromString -Value ($parts -join "`n")
}

function Write-RunSummary {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$ScriptId,
    [Parameter(Mandatory = $true)][string]$ScriptVersion,
    [Parameter(Mandatory = $true)][datetime]$RunStartedAtUtc,
    [Parameter(Mandatory = $true)][datetime]$RunFinishedAtUtc,
    [Parameter(Mandatory = $true)][string]$InputHash,
    [Parameter(Mandatory = $true)][string]$OutputHash,
    [Parameter(Mandatory = $true)][hashtable]$Fields
  )

  $lines = @()
  $toSummarySafe = {
    param([string]$v)
    return $v.Replace("`r", " ").Replace("`n", " ").Trim()
  }

  $lines += "SCRIPT_ID=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $ScriptId))
  $lines += "SCRIPT_VERSION=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $ScriptVersion))
  $lines += "RUN_STARTED_AT=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $RunStartedAtUtc))
  $lines += "RUN_FINISHED_AT=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $RunFinishedAtUtc))
  $lines += "INPUT_HASH=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $InputHash))
  $lines += "OUTPUT_HASH=" + (& $toSummarySafe (Convert-ToInvariantScalarString -Value $OutputHash))

  foreach ($k in ($Fields.Keys | Sort-Object)) {
    $val = & $toSummarySafe (Convert-ToInvariantScalarString -Value $Fields[$k])
    $lines += ([string]$k + "=" + $val)
  }

  Set-Content -Path $Path -Encoding UTF8 -Value $lines
}
