"""Meta-test: the engine-A guard itself SCREAMS instead of skip-greening (claim-discipline §3a).

Simulates the pyswisseph-absent machine by patching importlib.util.find_spec, and asserts the two
modes: hard FAILURE when REQUIRE_ENGINE_A is set, explicit (message-carrying) skip otherwise.
"""
import importlib.util
import sys
import threading
from types import SimpleNamespace

import pytest

import astro.engine as engine
from tests.conftest import require_engine_a


def _no_spec(name, *args, **kwargs):
    return None


def test_guard_fails_loud_when_engine_a_required(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", _no_spec)
    monkeypatch.setenv("REQUIRE_ENGINE_A", "1")
    with pytest.raises(pytest.fail.Exception, match="NOT verified"):
        require_engine_a()


def test_guard_skips_with_explicit_message_otherwise(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", _no_spec)
    monkeypatch.delenv("REQUIRE_ENGINE_A", raising=False)
    with pytest.raises(pytest.skip.Exception, match="NOT verified"):
        require_engine_a()


def test_guard_passes_through_when_engine_a_present():
    # pyswisseph IS installed in this environment; the guard must be a no-op.
    require_engine_a()


def _reset_engine_a(monkeypatch):
    monkeypatch.setattr(engine, "_SWE_EPHE_PATH", None)


def test_init_swe_rejects_missing_ephemeris_directory(monkeypatch, tmp_path):
    _reset_engine_a(monkeypatch)
    missing_dir = tmp_path / "missing"
    monkeypatch.setenv("SWISS_EPHE_PATH", str(missing_dir))

    with pytest.raises(RuntimeError) as caught:
        engine._init_swe()

    message = str(caught.value)
    assert str(missing_dir) in message
    assert "pwsh infra/ephe/get-ephe.ps1 -Source web" in message
    assert "SWISS_EPHE_PATH" in message


def test_init_swe_rejects_incomplete_ephemeris_directory(monkeypatch, tmp_path):
    _reset_engine_a(monkeypatch)
    monkeypatch.setenv("SWISS_EPHE_PATH", str(tmp_path))
    for filename in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (tmp_path / filename).touch()

    with pytest.raises(RuntimeError) as caught:
        engine._init_swe()

    message = str(caught.value)
    assert "se00433s.se1" in message
    assert "pwsh infra/ephe/get-ephe.ps1 -Source web" in message
    assert "SWISS_EPHE_PATH" in message


def test_init_swe_sets_valid_ephemeris_path_on_every_call(monkeypatch, tmp_path):
    _reset_engine_a(monkeypatch)
    monkeypatch.setenv("SWISS_EPHE_PATH", str(tmp_path))
    for filename in ("sepl_18.se1", "semo_18.se1", "seas_18.se1", "se00433s.se1"):
        (tmp_path / filename).touch()

    calls = []
    fake_swe = SimpleNamespace(set_ephe_path=calls.append)
    monkeypatch.setitem(sys.modules, "swisseph", fake_swe)

    assert engine._init_swe() is fake_swe
    assert engine._init_swe() is fake_swe

    worker_results = []

    def initialize_twice():
        worker_results.append(engine._init_swe())
        worker_results.append(engine._init_swe())

    worker = threading.Thread(target=initialize_twice)
    worker.start()
    worker.join()

    assert worker_results == [fake_swe, fake_swe]
    assert calls == [str(tmp_path)] * 4
