#!/usr/bin/env node

const { checkTcpPort } = require('./tcp-check');
const { checkHttpEndpoint } = require('./http-check');
const fs = require('fs');
const path = require('path');

const MCP_SCHEMA = {
    "protocolVersion": "1.0",
    "id": "healthcheck-mcp",
    "displayName": "Health Check Server",
    "description": "A server that provides tools to check the health of other services.",
    "tools": [
        {
            "name": "wait_for",
            "description": "Waits for a TCP port or an HTTP endpoint to become available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["tcp", "http"],
                        "description": "The type of health check to perform."
                    },
                    "target": {
                        "type": "string",
                        "description": "The target to check. For TCP, 'host:port'. For HTTP, a full URL."
                    },
                    "retries": {
                        "type": "number",
                        "description": "The number of times to retry.",
                        "default": 10
                    },
                    "timeout": {
                        "type": "number",
                        "description": "The timeout in milliseconds for each attempt.",
                        "default": 2000
                    }
                },
                "required": ["type", "target"]
            }
        }
    ]
};

async function handleRequest(request) {
    if (request.toolName !== 'wait_for') {
        throw new Error(`Unknown tool: ${request.toolName}`);
    }

    const { type, target, retries = 10, timeout = 2000 } = request.args;

    for (let i = 0; i < retries; i++) {
        try {
            if (type === 'tcp') {
                const [host, port] = target.split(':');
                if (!host || !port) throw new Error("Invalid target format for TCP. Expected 'host:port'.");
                await checkTcpPort(host, parseInt(port, 10), timeout);
                return { success: true, message: `${target} is available.` };
            } else if (type === 'http') {
                await checkHttpEndpoint(target, timeout);
                return { success: true, message: `${target} is available.` };
            } else {
                throw new Error(`Unknown check type: ${type}`);
            }
        } catch (error) {
            console.error(`Attempt ${i + 1} of ${retries} failed: ${error.message}`);
            if (i === retries - 1) {
                throw error; // Rethrow last error
            }
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s between retries
        }
    }
}


function main() {
    let buffer = '';
    process.stdin.on('data', chunk => {
        buffer += chunk;
    });

    process.stdin.on('end', async () => {
        try {
            const request = JSON.parse(buffer);
            if (request.mcp_action === 'describe') {
                process.stdout.write(JSON.stringify(MCP_SCHEMA));
                return;
            }

            if (request.mcp_action === 'get_agent_manual') {
                const manualPath = path.join(__dirname, '..', 'AGENTS.md');
                const manual = fs.readFileSync(manualPath, 'utf8');
                process.stdout.write(JSON.stringify({ manual }));
                return;
            }

            const result = await handleRequest(request);
            process.stdout.write(JSON.stringify({ result }));

        } catch (error) {
            process.stdout.write(JSON.stringify({ error: { message: error.message } }));
            process.exit(1);
        }
    });
}

main();
