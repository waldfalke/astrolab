"""Transport-as-process test: the MCP server runs as a separate process over
StreamableHTTP, and a network client gets the same goldens as the in-memory tests.

This is the honest boundary the in-memory tests do not cross: process isolation + HTTP transport.
Scope is local HTTP transport only. Authentication, TLS, and remote hosting are separate concerns.

The subprocess needs the swiss-mcp engine (localhost:8000) reachable, same as the other B1 goldens.
"""
import os
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastmcp import Client

_ROOT = Path(__file__).resolve().parents[1]
_PUBLIC_ROOT = _ROOT / "distribution" / "public"
if not (_PUBLIC_ROOT / "PUBLIC_SURFACE.txt").is_file():
    _PUBLIC_ROOT = _ROOT
_STARTUP_TIMEOUT_S = 30.0


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(port: int, proc: subprocess.Popen, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
            raise RuntimeError("server process died on startup:\n%s" % out)
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.15)
    raise TimeoutError("server did not open port %d within %ss" % (port, timeout_s))


@pytest.fixture()
def http_server_url():
    port = _free_port()
    env = dict(os.environ, ASTRO_MCP_TRANSPORT="http", ASTRO_MCP_PORT=str(port))
    proc = subprocess.Popen(
        [sys.executable, "-m", "astro.server"],
        cwd=_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_port(port, proc, _STARTUP_TIMEOUT_S)
        yield "http://127.0.0.1:%d/mcp" % port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


async def _call_over_http(url: str, name: str, args: dict):
    async with Client(url) as client:
        return await client.call_tool(name, args)


def test_natal_golden_over_http_subprocess(http_server_url):
    import asyncio

    result = asyncio.run(_call_over_http(
        http_server_url,
        "natal",
        dict(datetime_utc="1946-06-14T14:54:00Z", lat=40.7, lon=-73.8164),
    ))
    chart = result.data
    assert abs(chart["positions"]["sun"] - 82.9284020277778) < 1e-6
    assert abs(chart["houses"]["angles"]["asc"] - 149.958846361111) < 1e-6
    assert chart["dignities"]["saturn"] == {"sign": "Cancer", "dignity": "detriment"}


def test_rising_hands_golden_over_http_subprocess(http_server_url):
    import asyncio

    result = asyncio.run(_call_over_http(
        http_server_url,
        "rising_hands",
        dict(date="2026-06-22", lat=45.04, lon=38.98, tz=3),
    ))
    watches = result.data["watches"]
    assert len(watches) == 12
    assert watches[0] == {"start_local": "02:44", "asc_sign": "Близнецы"}


def test_chart_workflow_example_over_http_subprocess(http_server_url):
    result = subprocess.run(
        [
            sys.executable,
            str(_PUBLIC_ROOT / "examples" / "call_mcp.py"),
            "chart_workflow",
            "--url",
            http_server_url,
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary["natal_moment_utc"] == "1946-06-14T14:54:00Z"
    assert summary["solar_return_instant_utc"] == "2025-06-13T16:57:23Z"
    assert summary["profection"] == {"age": 79, "lord_of_year": "jupiter"}
    assert summary["solar_conjunction_exact_date"] == "2025-06-13"
    assert summary["transit_event_count"] > 0
