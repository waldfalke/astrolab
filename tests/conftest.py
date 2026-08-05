"""Shared test guards.

The A-vs-B1 tests verify the engine boundary. A silent skip when
pyswisseph is absent would report success without running the comparison. The guard
makes the gap LOUD: an explicit skip message locally, a hard FAILURE when REQUIRE_ENGINE_A is set
(the mode for CI / release checks).
"""
import importlib.util
import os

import pytest


def require_engine_a() -> None:
    """Skip loudly — or FAIL when REQUIRE_ENGINE_A is set — if engine A is unavailable."""
    if importlib.util.find_spec("swisseph") is not None:
        return
    msg = (
        "engine A (pyswisseph) is NOT installed — A-vs-B1 agnosticism was NOT verified on "
        "this run"
    )
    if os.environ.get("REQUIRE_ENGINE_A"):
        pytest.fail("REQUIRE_ENGINE_A is set: " + msg)
    pytest.skip(msg + " (set REQUIRE_ENGINE_A=1 to make this a failure)")
