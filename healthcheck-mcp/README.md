# Healthcheck-MCP

A reusable, standalone MCP server for checking service health.

This tool provides a simple MCP interface to wait for TCP ports or HTTP endpoints to become available, intended for use in `docker-compose` or other scripting environments to solve "race condition" problems.

## Installation

This tool is designed to be used as a CLI application.

1.  **Install dependencies:**
    ```bash
    npm install
    ```
2.  **Make it available globally:**
    ```bash
    npm link
    ```
    This will create a symbolic link, and you can now call `healthcheck-mcp` from anywhere.

## Usage with `mcporter`

Once installed, you can register `healthcheck-mcp` as a `stdio` server in your `mcporter.json` file:

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

You can then use it via `mcporter`:
```bash
mcporter call healthcheck.wait_for type=tcp target=localhost:5432
```
