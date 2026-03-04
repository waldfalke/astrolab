# 10 MCPorter Usage (Agent Edition)

Yes, this repository uses MCPorter via `npx mcporter`.

Evidence:

- `package.json` includes `"mcporter": "^0.7.3"`
- `artifacts/mcp-recipes/lib/mcp_helpers.ps1` calls `npx -y mcporter call ...`

## Why MCPorter here

1. standard MCP call envelope for HTTP/stdio providers
2. one consistent JSON output mode
3. easy provider switching (`swissremote` vs `ephem`)

## Canonical call shape

From helper (`Invoke-McpToolJson`):

```powershell
npx -y mcporter call --http-url <url> --name <server> <tool> key:value ... --output json
```

or for stdio mode:

```powershell
npx -y mcporter call --stdio "<command>" --name <server> <tool> key:value ... --output json
```

## Repo wrappers you should use first

1. `Invoke-EphemToolJson`
2. `Invoke-SwissPrimaryToolJson`
3. `Invoke-McpToolJson` only when you need a custom provider mode

Reason: wrappers already enforce invariants and retry semantics.

## Timeout control

Helper sets:

```powershell
$env:MCPORTER_CALL_TIMEOUT = <ms>
```

Default call timeout is `120000` ms.

## Result parsing contract

Agents must expect these failure forms:

1. non-zero process exit from `npx mcporter`
2. JSON with top-level `error`
3. JSON with `isError = true` and `content[].text`

Helper already normalizes these into thrown errors.

## Retry policy with swiss provider

`Invoke-SwissPrimaryToolJson` retries up to `MaxAttempts` (default 3) with backoff.

Telemetry fields now available in summary-producing recipes:

- `SWISS_RETRY_TOTAL`
- `SWISS_RETRY_BY_TOOL`

If retries > 0 and run still succeeds, treat as non-blocking known issue.

## Example: direct manual probe

```powershell
npx -y mcporter call --http-url https://ephemeris.fyi/mcp --name ephem get_ephemeris_data latitude:40.7 longitude:-73.8164 datetime:1946-06-14T14:54:00Z --output json
```

## Example: preferred repo-level usage

```powershell
pwsh artifacts/mcp-recipes/run_mcp_provider_probe.ps1
```

## Obsidian via MCPorter (stdio)

Preferred probe wrapper:

```powershell
pwsh artifacts/mcp-recipes/run_obsidian_mcp_probe.ps1 -StdioCommand "npx -y mcp-obsidian" -ServerName "obsidian"
```

Direct manual probe:

```powershell
npx -y mcporter list --stdio "npx -y mcp-obsidian" --name obsidian --schema
```

Guidance:

1. Keep file-based canvas loop as fallback (`run_canvas_do_extract.ps1`, `run_canvas_ai_update.ps1`).
2. Use MCP mode when interactive note/canvas operations are required.
3. Scope operations to the intended vault path and avoid broad write patterns.

## Agent do/don't for MCPorter

Do:

1. use repo wrappers/recipes first
2. keep UTC timestamps in arguments
3. persist raw provider JSON in run directories

Do not:

1. parse human text output when JSON is available
2. bypass helper invariants for production runs
3. treat one transient 504 as automatic hard failure
