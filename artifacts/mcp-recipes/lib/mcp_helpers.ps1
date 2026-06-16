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
    if ($Url -like "http://*") { $argList += "--allow-http" }
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
  $exitCode = $LASTEXITCODE

  # Parse stdout first, then judge success. On Windows + Node 25 the mcporter StreamableHTTP
  # client can crash on process teardown (libuv UV_HANDLE_CLOSING -> exit 0xC0000409) AFTER
  # emitting a complete, valid JSON result. A usable payload must win over a teardown-only
  # nonzero exit; the exit code is honored only when no parseable JSON came back.
  $parsed = $null
  try { $parsed = ($raw | ConvertFrom-Json) } catch { $parsed = $null }
  if ($null -eq $parsed) {
    throw "mcporter call failed for tool: $Tool ($ServerName) (exit=$exitCode, no JSON returned)`n$raw"
  }

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
      # Primary swiss engine self-hosted from dm0lz/swiss-ephemeris-mcp-server (the public
      # theme-astral.me demo was decommissioned). Override with $env:SWISS_MCP_URL if relocated.
      $swissUrl = if ($env:SWISS_MCP_URL) { $env:SWISS_MCP_URL } else { "http://localhost:8000/mcp" }
      return Invoke-McpToolJson -Mode "http" -Url $swissUrl -ServerName "swissremote" -Tool $Tool -Args $Args
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
      $retro = Get-SwissRetrogradeFromNode -Node $node
      if ($null -ne $node.longitude) {
        $rows += [pscustomobject]@{
          body = $body.ToLowerInvariant()
          longitude = [double]$node.longitude
          sign = [string]$node.sign
          degree = [double]$node.degree
          retrograde = $retro
        }
      }
    }
  }
  return $rows
}

function Get-SwissRetrogradeFromNode {
  param(
    [Parameter(Mandatory = $true)]$Node
  )

  if ($null -eq $Node) { return $null }

  $boolKeys = @("retrograde", "isRetrograde", "is_retrograde")
  foreach ($k in $boolKeys) {
    if ($Node.PSObject.Properties.Name -contains $k) {
      $v = $Node.$k
      if ($null -eq $v) { return $null }
      if ($v -is [bool]) { return [bool]$v }
      $s = ([string]$v).Trim().ToLowerInvariant()
      if ($s -in @("true", "1", "yes", "y", "r", "retrograde", "backward")) { return $true }
      if ($s -in @("false", "0", "no", "n", "d", "direct", "forward")) { return $false }
    }
  }

  $dirKeys = @("direction", "motion", "state")
  foreach ($k in $dirKeys) {
    if ($Node.PSObject.Properties.Name -contains $k) {
      $s = ([string]$Node.$k).Trim().ToLowerInvariant()
      if ($s -match "retro|back") { return $true }
      if ($s -match "direct|forward") { return $false }
    }
  }

  $speedKeys = @("speed", "longitudeSpeed", "longitude_speed", "speed_longitude")
  foreach ($k in $speedKeys) {
    if ($Node.PSObject.Properties.Name -contains $k) {
      try {
        $n = [double]$Node.$k
        if ($n -lt 0) { return $true }
        if ($n -gt 0) { return $false }
      } catch {
        continue
      }
    }
  }

  return $null
}

function Get-SignedDelta360 {
  param(
    [Parameter(Mandatory = $true)][double]$From,
    [Parameter(Mandatory = $true)][double]$To
  )

  $a = Normalize-Longitude -Longitude $From
  $b = Normalize-Longitude -Longitude $To
  $d = $b - $a
  if ($d -gt 180.0) { $d -= 360.0 }
  if ($d -le -180.0) { $d += 360.0 }
  return $d
}

function Get-RetrogradeMapFromEphemerisWindow {
  param(
    [Parameter(Mandatory = $true)]$PrevEphemeris,
    [Parameter(Mandatory = $true)]$NextEphemeris,
    [string[]]$Bodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
  )

  $result = @{}
  foreach ($body in $Bodies) {
    if (-not ($PrevEphemeris.PSObject.Properties.Name -contains $body)) { continue }
    if (-not ($NextEphemeris.PSObject.Properties.Name -contains $body)) { continue }

    $prev = $PrevEphemeris.$body
    $next = $NextEphemeris.$body
    if ($null -eq $prev -or $null -eq $next) { continue }
    if ($null -eq $prev.apparentLongitude -or $null -eq $next.apparentLongitude) { continue }

    $delta = Get-SignedDelta360 -From ([double]$prev.apparentLongitude) -To ([double]$next.apparentLongitude)
    $speedDegDay = $delta / 2.0
    $result[$body.ToLowerInvariant()] = ($speedDegDay -lt 0.0)
  }
  return $result
}

function Shift-UtcIsoDateTime {
  param(
    [Parameter(Mandatory = $true)][string]$DateTimeUtc,
    [Parameter(Mandatory = $true)][double]$Hours
  )

  $dt = [datetime]::Parse(
    $DateTimeUtc,
    [CultureInfo]::InvariantCulture,
    [DateTimeStyles]::AssumeUniversal -bor [DateTimeStyles]::AdjustToUniversal
  )
  return $dt.AddHours($Hours).ToString("yyyy-MM-ddTHH:mm:ssZ", [CultureInfo]::InvariantCulture)
}

function Get-UtcDateTime {
  param(
    [Parameter(Mandatory = $true)][string]$DateTimeUtc
  )

  return [datetime]::Parse(
    $DateTimeUtc,
    [CultureInfo]::InvariantCulture,
    [DateTimeStyles]::AssumeUniversal -bor [DateTimeStyles]::AdjustToUniversal
  )
}

function Convert-UtcDateTimeToIso {
  param(
    [Parameter(Mandatory = $true)][datetime]$DateTimeUtc
  )

  return $DateTimeUtc.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", [CultureInfo]::InvariantCulture)
}

function Get-EphemSnapshotAt {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Cache,
    [Parameter(Mandatory = $true)][double]$Latitude,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][datetime]$DateTimeUtc
  )

  $key = Convert-UtcDateTimeToIso -DateTimeUtc $DateTimeUtc
  if (-not $Cache.ContainsKey($key)) {
    $Cache[$key] = Invoke-EphemToolJson -Tool "get_ephemeris_data" -Args @{
      latitude = $Latitude
      longitude = $Longitude
      datetime = $key
    }
  }
  return $Cache[$key]
}

function Get-BodyLongitudeAt {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Cache,
    [Parameter(Mandatory = $true)][double]$Latitude,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][datetime]$DateTimeUtc,
    [Parameter(Mandatory = $true)][string]$Body
  )

  $snap = Get-EphemSnapshotAt -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $DateTimeUtc
  $k = $Body.ToLowerInvariant()
  if (-not ($snap.PSObject.Properties.Name -contains $k)) { return $null }
  $node = $snap.$k
  if ($null -eq $node -or $null -eq $node.apparentLongitude) { return $null }
  return [double]$node.apparentLongitude
}

function Get-BodySpeedDegPerDay {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Cache,
    [Parameter(Mandatory = $true)][double]$Latitude,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][datetime]$DateTimeUtc,
    [Parameter(Mandatory = $true)][string]$Body
  )

  $a = Get-BodyLongitudeAt -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $DateTimeUtc.AddHours(-12) -Body $Body
  $b = Get-BodyLongitudeAt -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $DateTimeUtc.AddHours(12) -Body $Body
  if ($null -eq $a -or $null -eq $b) { return $null }
  return (Get-SignedDelta360 -From $a -To $b)
}

function Get-MotionSign {
  param(
    [Parameter(Mandatory = $false)][double]$SpeedDegPerDay = 0.0,
    [double]$StationThreshold = 0.05
  )

  if ([math]::Abs($SpeedDegPerDay) -le $StationThreshold) { return 0 }
  if ($SpeedDegPerDay -gt 0) { return 1 }
  return -1
}

function Find-StationTimeBetween {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Cache,
    [Parameter(Mandatory = $true)][double]$Latitude,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][string]$Body,
    [Parameter(Mandatory = $true)][datetime]$StartUtc,
    [Parameter(Mandatory = $true)][datetime]$EndUtc,
    [double]$StationThreshold = 0.05
  )

  $a = $StartUtc
  $b = $EndUtc
  $sa = Get-BodySpeedDegPerDay -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $a -Body $Body
  $sb = Get-BodySpeedDegPerDay -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $b -Body $Body
  if ($null -eq $sa -or $null -eq $sb) { return $null }
  $signA = Get-MotionSign -SpeedDegPerDay $sa -StationThreshold $StationThreshold
  $signB = Get-MotionSign -SpeedDegPerDay $sb -StationThreshold $StationThreshold
  if ($signA -eq $signB) { return $null }

  for ($i = 0; $i -lt 25; $i++) {
    $midTicks = [long](($a.Ticks + $b.Ticks) / 2)
    $mid = [datetime]::SpecifyKind([datetime]::new($midTicks), [DateTimeKind]::Utc)
    $sm = Get-BodySpeedDegPerDay -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $mid -Body $Body
    if ($null -eq $sm) { break }
    $signM = Get-MotionSign -SpeedDegPerDay $sm -StationThreshold $StationThreshold
    if ($signM -eq 0) {
      return $mid
    }
    if ($signA -eq $signM) {
      $a = $mid
      $sa = $sm
      $signA = $signM
    } else {
      $b = $mid
      $sb = $sm
      $signB = $signM
    }
  }

  $t = [datetime]::SpecifyKind([datetime]::new([long](($a.Ticks + $b.Ticks) / 2)), [DateTimeKind]::Utc)
  return $t
}

function Get-RetrogradeLoops {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Cache,
    [Parameter(Mandatory = $true)][double]$Latitude,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][datetime]$CenterUtc,
    [Parameter(Mandatory = $true)][string]$Body,
    [int]$WindowDays = 120,
    [int]$StepDays = 5,
    [double]$StationThreshold = 0.05
  )

  $stations = @()
  $start = $CenterUtc.AddDays(-$WindowDays)
  $end = $CenterUtc.AddDays($WindowDays)
  $cursor = $start
  while ($cursor -lt $end) {
    $next = $cursor.AddDays($StepDays)
    if ($next -gt $end) { $next = $end }
    $s1 = Get-BodySpeedDegPerDay -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $cursor -Body $Body
    $s2 = Get-BodySpeedDegPerDay -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $next -Body $Body
    if ($null -eq $s1 -or $null -eq $s2) {
      $cursor = $next
      continue
    }
    $m1 = Get-MotionSign -SpeedDegPerDay $s1 -StationThreshold $StationThreshold
    $m2 = Get-MotionSign -SpeedDegPerDay $s2 -StationThreshold $StationThreshold
    if ($m1 -ne $m2) {
      $st = Find-StationTimeBetween -Cache $Cache -Latitude $Latitude -Longitude $Longitude -Body $Body -StartUtc $cursor -EndUtc $next -StationThreshold $StationThreshold
      if ($null -ne $st) {
        $lonSt = Get-BodyLongitudeAt -Cache $Cache -Latitude $Latitude -Longitude $Longitude -DateTimeUtc $st -Body $Body
        if ($null -ne $lonSt) {
          $stations += [pscustomobject]@{
            time = $st
            lon = [double]$lonSt
            from_sign = $m1
            to_sign = $m2
            type = ($(if ($m1 -ge 0 -and $m2 -le 0) { "SRx" } else { "SD" }))
          }
        }
      }
    }
    $cursor = $next
  }

  $stations = @($stations | Sort-Object time)
  $loops = @()
  for ($i = 0; $i -lt $stations.Count; $i++) {
    $a = $stations[$i]
    if ($a.type -ne "SRx") { continue }
    for ($j = $i + 1; $j -lt $stations.Count; $j++) {
      $b = $stations[$j]
      if ($b.type -ne "SD") { continue }
      $loops += [pscustomobject]@{
        srx_time = $a.time
        srx_lon = [double]$a.lon
        sd_time = $b.time
        sd_lon = [double]$b.lon
      }
      break
    }
  }
  return $loops
}

function Test-LongitudeInForwardArc {
  param(
    [Parameter(Mandatory = $true)][double]$StartLon,
    [Parameter(Mandatory = $true)][double]$EndLon,
    [Parameter(Mandatory = $true)][double]$Lon
  )

  $start = Normalize-Longitude -Longitude $StartLon
  $end = Normalize-Longitude -Longitude $EndLon
  $x = Normalize-Longitude -Longitude $Lon
  $arc = ($end - $start + 360.0) % 360.0
  $p = ($x - $start + 360.0) % 360.0
  return ($p -le $arc)
}

function Get-ShadowStateForBody {
  param(
    [Parameter(Mandatory = $true)][array]$Loops,
    [Parameter(Mandatory = $true)][datetime]$AtUtc,
    [Parameter(Mandatory = $true)][double]$Longitude,
    [Parameter(Mandatory = $true)][int]$MotionSign
  )

  if ($Loops.Count -eq 0) { return "none" }
  $lon = Normalize-Longitude -Longitude $Longitude

  $best = $null
  $bestDist = [double]::PositiveInfinity
  foreach ($loop in $Loops) {
    $start = [datetime]$loop.srx_time
    $end = [datetime]$loop.sd_time
    $dist = 0.0
    if ($AtUtc -lt $start) {
      $dist = ($start - $AtUtc).TotalDays
    } elseif ($AtUtc -gt $end) {
      $dist = ($AtUtc - $end).TotalDays
    } else {
      $dist = 0.0
    }
    if ($dist -lt $bestDist) {
      $bestDist = $dist
      $best = $loop
    }
  }
  if ($null -eq $best) { return "none" }

  if ($AtUtc -ge [datetime]$best.srx_time -and $AtUtc -le [datetime]$best.sd_time) {
    return "retro"
  }

  $inZone = Test-LongitudeInForwardArc -StartLon ([double]$best.sd_lon) -EndLon ([double]$best.srx_lon) -Lon $lon
  if (-not $inZone) { return "none" }

  if ($AtUtc -lt [datetime]$best.srx_time -and $MotionSign -ge 0) { return "pre" }
  if ($AtUtc -gt [datetime]$best.sd_time -and $MotionSign -ge 0) { return "post" }
  return "none"
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

function Get-MeanObliquityDeg {
  # Mean obliquity of the ecliptic (IAU 1980 / Meeus), degrees. Used as the OOB threshold:
  # a body is out-of-bounds when |declination| exceeds this value.
  param(
    [Parameter(Mandatory = $true)][string]$DateTimeUtc
  )

  $t = Get-UtcDateTime -DateTimeUtc $DateTimeUtc
  $j2000 = [datetime]::SpecifyKind([datetime]::new(2000, 1, 1, 12, 0, 0), [DateTimeKind]::Utc)
  $T = ($t - $j2000).TotalDays / 36525.0
  $seconds = 84381.448 - (46.8150 * $T) - (0.00059 * $T * $T) + (0.001813 * $T * $T * $T)
  return ($seconds / 3600.0)
}

function Get-EphemDeclinations {
  # Apparent geocentric declination (degrees) per body from an ephem get_ephemeris_data snapshot.
  # ephem stores it as node.apparent.dDec in RADIANS (signed); we convert to degrees.
  # Source note: longitude-only engines cannot supply this — declination depends on ecliptic
  # latitude (why Moon/Pluto go OOB), which ephem carries and the swiss wrapper does not.
  param(
    [Parameter(Mandatory = $true)]$Ephemeris,
    [string[]]$Bodies = @("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "chiron")
  )

  $rows = @()
  foreach ($body in $Bodies) {
    if ($Ephemeris.PSObject.Properties.Name -contains $body) {
      $node = $Ephemeris.$body
      if (($null -ne $node) -and ($null -ne $node.apparent) -and ($null -ne $node.apparent.dDec)) {
        $decDeg = [double]$node.apparent.dDec * 180.0 / [math]::PI
        $rows += [pscustomobject]@{
          body = $body
          declination_deg = [math]::Round($decDeg, 6)
        }
      }
    }
  }
  return $rows
}

function Get-DeclinationAspects {
  # Parallels / contraparallels between two declination sets (each row: body, declination_deg).
  # Parallel  = same hemisphere, |dA - dB| <= orb  (acts like a conjunction).
  # Contraparallel = opposite hemisphere, |dA + dB| <= orb  (acts like an opposition).
  # SameSet=$true compares a set with itself (i<j, no self-pairs) for internal aspects.
  param(
    [Parameter(Mandatory = $true)][array]$FromRows,
    [Parameter(Mandatory = $true)][array]$ToRows,
    [double]$Orb = 1.0,
    [string]$FromPrefix = "",
    [string]$ToPrefix = "",
    [string]$Scope = "",
    [bool]$SameSet = $false
  )

  $rows = @()
  for ($i = 0; $i -lt $FromRows.Count; $i++) {
    $a = $FromRows[$i]
    $da = [double]$a.declination_deg
    $jStart = if ($SameSet) { $i + 1 } else { 0 }
    for ($j = $jStart; $j -lt $ToRows.Count; $j++) {
      if ($SameSet -and ($i -eq $j)) { continue }
      $b = $ToRows[$j]
      $db = [double]$b.declination_deg
      $sameSign = (($da -ge 0) -eq ($db -ge 0))
      if ($sameSign) {
        $orbDelta = [math]::Abs($da - $db)
        $type = "parallel"
      } else {
        $orbDelta = [math]::Abs($da + $db)
        $type = "contraparallel"
      }
      if ($orbDelta -le $Orb) {
        $rows += [pscustomobject]@{
          scope = $Scope
          from_object = ($FromPrefix + [string]$a.body)
          to_object = ($ToPrefix + [string]$b.body)
          type = $type
          from_decl = [math]::Round($da, 4)
          to_decl = [math]::Round($db, 4)
          orb = [math]::Round($orbDelta, 4)
          orb_limit = [double]$Orb
          is_exact = ($orbDelta -le 0.2)
        }
      }
    }
  }
  return $rows
}

function Get-EssentialDignities {
  # Essential dignity per body (domicile / exaltation / detriment / fall / peregrine) by sign.
  # Domicile/detriment is geometric (covered by the phase layer too); exaltation/fall is tabular.
  # Scheme: "modern" (outers rule Aqu/Pis/Sco; Mars=Aries, Jupiter=Sag, Saturn=Cap only) or
  # "traditional" (Mars also Scorpio, Jupiter also Pisces, Saturn also Aquarius; no outers).
  param(
    [Parameter(Mandatory = $true)][array]$Rows,
    [string]$Scheme = "modern"
  )

  $opposite = @{
    "Aries" = "Libra"; "Taurus" = "Scorpio"; "Gemini" = "Sagittarius"; "Cancer" = "Capricorn";
    "Leo" = "Aquarius"; "Virgo" = "Pisces"; "Libra" = "Aries"; "Scorpio" = "Taurus";
    "Sagittarius" = "Gemini"; "Capricorn" = "Cancer"; "Aquarius" = "Leo"; "Pisces" = "Virgo"
  }
  if ($Scheme -eq "traditional") {
    $domicile = @{
      sun = @("Leo"); moon = @("Cancer"); mercury = @("Gemini", "Virgo"); venus = @("Taurus", "Libra");
      mars = @("Aries", "Scorpio"); jupiter = @("Sagittarius", "Pisces"); saturn = @("Capricorn", "Aquarius")
    }
  } else {
    $domicile = @{
      sun = @("Leo"); moon = @("Cancer"); mercury = @("Gemini", "Virgo"); venus = @("Taurus", "Libra");
      mars = @("Aries"); jupiter = @("Sagittarius"); saturn = @("Capricorn");
      uranus = @("Aquarius"); neptune = @("Pisces"); pluto = @("Scorpio")
    }
  }
  $exalt = @{ sun = "Aries"; moon = "Taurus"; mercury = "Virgo"; venus = "Pisces"; mars = "Capricorn"; jupiter = "Cancer"; saturn = "Libra" }
  $fall = @{ sun = "Libra"; moon = "Scorpio"; mercury = "Pisces"; venus = "Virgo"; mars = "Cancer"; jupiter = "Capricorn"; saturn = "Aries" }

  $rowsOut = @()
  foreach ($r in $Rows) {
    $body = ([string]$r.body).ToLowerInvariant()
    $coord = Convert-LongitudeToSignDegree -Longitude ([double]$r.longitude)
    $sign = [string]$coord.sign
    $status = "peregrine"

    if ($domicile.ContainsKey($body) -and ($domicile[$body] -contains $sign)) {
      $status = "domicile"
    } elseif ($exalt.ContainsKey($body) -and ($exalt[$body] -eq $sign)) {
      $status = "exaltation"
    } elseif ($domicile.ContainsKey($body) -and (@($domicile[$body] | ForEach-Object { $opposite[$_] }) -contains $sign)) {
      $status = "detriment"
    } elseif ($fall.ContainsKey($body) -and ($fall[$body] -eq $sign)) {
      $status = "fall"
    }

    $rowsOut += [pscustomobject]@{
      body = $body
      sign = $sign
      dignity = $status
    }
  }
  return $rowsOut
}

function Get-Sect {
  # Hellenistic sect. Returns the chart sect (day/night) and per-body membership + role.
  #   - Day chart  = Sun above the horizon; Night chart = Sun below.
  #   - Above-horizon test via the ASC->DESC arc: whole below-horizon half (houses 1-6) is
  #     (lon - ASC) mod 360 in [0,180); the above-horizon half (7-12) is [180,360).
  #   - Diurnal team: Sun, Jupiter, Saturn.  Nocturnal team: Moon, Venus, Mars.
  #   - Mercury takes sect by ORIENTALITY (oriental/morning-star = diurnal), computed from a
  #     signed Sun->Mercury angle (NOT a raw longitude compare, which breaks near 0 Aries):
  #     negative delta => Mercury behind the Sun (lower lon, rises earlier) => oriental => diurnal.
  #   - in_sect  = planet's team matches the chart sect; out_of_sect otherwise.
  #   - Roles (by chart sect): sect_light, benefic_of_sect / benefic_contrary,
  #     malefic_of_sect (constructive) / malefic_contrary (harsh).
  # Outer planets carry no classical sect (team="none", role="outer").
  param(
    [Parameter(Mandatory = $true)][array]$Rows,
    [Parameter(Mandatory = $true)][double]$AscLongitude
  )

  $byBody = @{}
  foreach ($r in $Rows) { $byBody[([string]$r.body).ToLowerInvariant()] = [double]$r.longitude }
  if (-not $byBody.ContainsKey("sun")) { throw "Get-Sect requires the Sun longitude in -Rows" }
  $sunLon = $byBody["sun"]

  $sunOff = ((($sunLon - $AscLongitude) % 360.0) + 360.0) % 360.0
  $sunAbove = ($sunOff -ge 180.0)
  $chartSect = if ($sunAbove) { "day" } else { "night" }
  $chartTeam = if ($sunAbove) { "diurnal" } else { "nocturnal" }

  $diurnal = @("sun", "jupiter", "saturn")
  $nocturnal = @("moon", "venus", "mars")

  $mercuryTeam = "none"
  if ($byBody.ContainsKey("mercury")) {
    $d = Get-SignedDelta360 -From $sunLon -To $byBody["mercury"]
    $mercuryTeam = if ($d -lt 0) { "diurnal" } else { "nocturnal" }
  }

  if ($chartSect -eq "day") {
    $roles = @{ sun = "sect_light"; jupiter = "benefic_of_sect"; venus = "benefic_contrary"; saturn = "malefic_of_sect"; mars = "malefic_contrary"; moon = "luminary_out_of_sect" }
  } else {
    $roles = @{ moon = "sect_light"; venus = "benefic_of_sect"; jupiter = "benefic_contrary"; mars = "malefic_of_sect"; saturn = "malefic_contrary"; sun = "luminary_out_of_sect" }
  }

  $rowsOut = @()
  foreach ($r in $Rows) {
    $body = ([string]$r.body).ToLowerInvariant()
    $lon = [double]$r.longitude
    $team = if ($diurnal -contains $body) { "diurnal" } elseif ($nocturnal -contains $body) { "nocturnal" } elseif ($body -eq "mercury") { $mercuryTeam } else { "none" }
    $placement = if ($team -eq "none") { "n/a" } elseif ($team -eq $chartTeam) { "in_sect" } else { "out_of_sect" }
    $role = if ($team -eq "none") { "outer" } elseif ($roles.ContainsKey($body)) { $roles[$body] } else { "neutral" }
    $off = ((($lon - $AscLongitude) % 360.0) + 360.0) % 360.0
    $rowsOut += [pscustomobject]@{
      body = $body
      sign = [string](Convert-LongitudeToSignDegree -Longitude $lon).sign
      planet_team = $team
      above_horizon = ($off -ge 180.0)
      placement = $placement
      role = $role
    }
  }

  return [pscustomobject]@{
    chart_sect = $chartSect
    sun_above_horizon = $sunAbove
    mercury_team = $mercuryTeam
    rows = $rowsOut
  }
}

function Get-AnnualProfection {
  # Annual profection (whole-sign): the Ascendant advances one whole sign per completed year.
  #   profected house = (age mod 12) + 1 ; profected sign = ASC sign advanced by (age mod 12) signs.
  #   Lord of Year = TRADITIONAL ruler of the profected sign (Hellenistic technique => traditional
  #   rulerships, no modern outers). Age is completed years at the solar return.
  param(
    [Parameter(Mandatory = $true)][double]$AscLongitude,
    [Parameter(Mandatory = $true)][int]$AgeYears
  )

  $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
  $rulerTrad = @{
    Aries = "mars"; Taurus = "venus"; Gemini = "mercury"; Cancer = "moon"; Leo = "sun"; Virgo = "mercury";
    Libra = "venus"; Scorpio = "mars"; Sagittarius = "jupiter"; Capricorn = "saturn"; Aquarius = "saturn"; Pisces = "jupiter"
  }

  $ascNorm = Normalize-Longitude -Longitude $AscLongitude
  $ascIdx = [int][math]::Floor($ascNorm / 30.0)
  $step = $AgeYears % 12
  $profIdx = ($ascIdx + $step) % 12
  $profSign = $signs[$profIdx]

  return [pscustomobject]@{
    age_years = $AgeYears
    profection_step = $step
    asc_sign = $signs[$ascIdx]
    profected_house = $step + 1
    profected_sign = $profSign
    lord_of_year = $rulerTrad[$profSign]
  }
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
