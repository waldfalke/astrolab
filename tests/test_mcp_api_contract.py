"""The public MCP contract must match the server's discovery response exactly."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from fastmcp import Client

from astro.server import mcp


_ROOT = Path(__file__).resolve().parents[1]
_DOC_CANDIDATES = (
    _ROOT / "distribution" / "public" / "docs" / "mcp-api.md",
    _ROOT / "docs" / "mcp-api.md",
)
_DOC = next((path for path in _DOC_CANDIDATES if path.is_file()), _DOC_CANDIDATES[0])
_CONTRACT_BLOCK = re.compile(
    r"<!-- mcp-contract:start -->\s*"
    r"```json\s*(?P<contract>.*?)\s*```\s*"
    r"<!-- mcp-contract:end -->",
    re.DOTALL,
)
_PROJECTION_KEYS = ("name", "description", "inputSchema", "outputSchema")


def _documented_contract() -> list[dict]:
    text = _DOC.read_text(encoding="utf-8")
    match = _CONTRACT_BLOCK.search(text)
    assert match is not None, "mcp-api.md has no machine-readable MCP contract block"
    return json.loads(match.group("contract"))


async def _discovered_contract() -> list[dict]:
    async with Client(mcp) as client:
        tools = await client.list_tools()

    projection = []
    for tool in tools:
        wire = tool.model_dump(by_alias=True, exclude_none=True)
        wire.pop("_meta", None)
        projection.append({key: wire[key] for key in _PROJECTION_KEYS})
    return projection


def test_documented_contract_matches_mcp_discovery():
    assert _documented_contract() == asyncio.run(_discovered_contract())
