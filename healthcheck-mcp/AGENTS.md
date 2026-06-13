# Agent Manual: Healthcheck-MCP

## 1. Purpose

This skill provides a tool named `wait_for` to solve "race condition" problems in scripting and orchestration environments, especially within `docker-compose`. It allows a process to pause and wait until another service is ready to accept connections before proceeding.

## 2. Tool: `wait_for`

### Description
Asynchronously checks and waits for a TCP port or an HTTP endpoint to become available. It will retry several times before failing.

### Parameters
- `type`: (string, required) The type of check. Must be either `"tcp"` or `"http"`.
- `target`: (string, required) The resource to check.
    - For `type: "tcp"`, this is a string in `"host:port"` format (e.g., `"bitcoind:18443"`).
    - For `type: "http"`, this is a full URL (e.g., `"http://localhost:3000/health"`).
- `retries`: (number, optional, default: 10) The total number of attempts to make.
- `timeout`: (number, optional, default: 2000) The timeout in milliseconds for each individual attempt.

### Returns
- On success, returns a JSON object with `{ "success": true, "message": "<target> is available." }`.
- On failure (after all retries), throws an error.

## 3. Usage Examples

### Waiting for a TCP port in a script
```bash
# This command will wait up to 20 seconds (10 retries * 2s) for 'my-database'
# to open port 5432 before proceeding.
mcporter call healthcheck.wait_for type=tcp target=my-database:5432
```

### Waiting for an HTTP endpoint
```bash
# This command waits for a web server's health check endpoint to return 2xx.
mcporter call healthcheck.wait_for type=http target=http://my-api/health retries=5
```

## 4. Integration with `mcporter`

This tool is designed to be registered as a `stdio` server in a `mcporter.json` configuration file. After installing it as a package, its command will be available globally.

**Example `mcporter.json` entry:**
```json
{
  "mcpServers": {
    "healthcheck": {
      "description": "A reusable MCP server for checking service health.",
      "command": "healthcheck-mcp"
    }
  }
}
```
