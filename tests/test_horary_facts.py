"""Numerical and intake boundaries; no test asserts an astrological prediction."""
import copy
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
from astro import engine, horary
from astro.carrier_states import compute_carrier_states
from astro.phases import compute_phase_states

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("horary_facts", ROOT / "artifacts/mcp-recipes/horary_facts.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


def example():
    return json.loads((ROOT / "artifacts/mcp-recipes/examples/horary-input.example.json").read_text(encoding="utf-8"))


def test_reviewed_question_and_explicit_time_are_required():
    cfg = example()
    assert recipe.validate_input(cfg) == datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    for section, key, value in [
        ("intake", "status", "needs_clarification"),
        ("intake", "single_question_basis", ""),
        ("question", "outcome_test", ""),
        ("question", "domain", "diagnosis"),
        ("moment", "local", "2026-01-15T12:00:00"),
        ("moment", "local", "2026-01-15T12:00:00+03:00"),
        ("moment", "latitude", float("nan")),
        ("moment", "latitude", True),
        ("moment", "kind", "server_time"),
    ]:
        bad = copy.deepcopy(cfg)
        bad[section][key] = value
        with pytest.raises(ValueError):
            recipe.validate_input(bad)


def test_nonexistent_dst_time_and_unexplained_repeat_are_rejected():
    cfg = example()
    cfg["moment"]["local"] = "2026-03-29T01:30:00+00:00"
    with pytest.raises(ValueError, match="timezone"):
        recipe.validate_input(cfg)
    cfg = example()
    cfg["intake"]["previous_question"] = {"status": "new_circumstances"}
    with pytest.raises(ValueError, match="previous"):
        recipe.validate_input(cfg)


def test_a_real_repeated_hour_is_disambiguated_by_explicit_offset():
    cfg = example()
    cfg["moment"]["local"] = "2026-10-25T01:30:00+01:00"
    assert recipe.validate_input(cfg).hour == 0
    cfg["moment"]["local"] = "2026-10-25T01:30:00+00:00"
    assert recipe.validate_input(cfg).hour == 1


def test_nonfinite_limits_and_bad_phase_instants_are_rejected():
    for field, value in [("scan_days", True), ("scan_days", 0), ("scan_days", 367),
                         ("past_days", True), ("past_days", 2), ("past_days", 367), ("past_days", 3.0),
                         ("phase_samples_utc", ["2026-01-16T12:00:00.3Z"]),
                         ("phase_samples_utc", "2026-01-16T12:00:00Z")]:
        cfg = example()
        cfg[field] = value
        with pytest.raises(ValueError):
            recipe.validate_input(cfg)


def test_root_search_keeps_endpoints_and_turning_point_without_wrap_false_root():
    assert recipe.roots(lambda t: t - 1, [0, 1, 2]) == [1]
    assert recipe.roots(lambda t: (t - .5) ** 2, [0, .5, 1]) == [.5]
    assert recipe.roots(lambda t: (179 + 2*t + 180) % 360 - 180, [0, 1], angular=True) == []
    assert recipe.roots(lambda t: t - .4, [0, 1])[0] == pytest.approx(.4, abs=1e-8)


def test_unequal_hours_start_at_sunrise_and_night_continues_planetary_day():
    # Symbolic 1 JD = 24 h; Friday starts with Venus, then repeats the Chaldean order.
    day = recipe.planetary_hour(100.25, 100, 100.5, 101, "venus")
    night = recipe.planetary_hour(100.75, 100, 100.5, 101, "venus")
    assert day["number"] == 7 and day["ruler"] == "sun"
    assert night["number"] == 19 and night["ruler"] == "jupiter"
    boundary = recipe.planetary_hour(100.5, 100, 100.5, 101, "venus")
    assert boundary["number"] == 13 and boundary["ruler"] == "mars"
    assert recipe.planetary_hour(100 - .01, 100, 100.5, 101, "venus") is None


def test_hour_agreement_and_geometric_house_boundary():
    assert recipe.hour_agreement("mars", 125, "day")["same_nature"] is True
    assert recipe.hour_agreement("mars", 125, "day")["same_ruler"] is False
    assert recipe.hour_agreement("mars", 95, "night")["triplicity"] is True
    cusps = [i * 30.0 for i in range(12)]
    assert recipe.geometric_house(180 - 1e-12, cusps) == 7


def test_output_must_be_private_and_existing_output_is_preserved(tmp_path):
    with pytest.raises(ValueError, match="private"):
        recipe.output_path(tmp_path / "public")
    target = tmp_path / ".PRIVATE" / "case"
    assert recipe.output_path(target) == target.resolve()
    target.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        recipe.output_path(target)


def test_synthetic_chart_uses_local_swiss_and_records_limits():
    cfg = example()
    cfg["scan_days"] = 3
    facts = recipe.compute_facts(cfg)
    assert facts["method"] == "horary-v1"
    assert len(facts["chart"]["bodies"]) == 10
    assert all(row["sign"] and 0 <= row["degree"] < 30 for row in facts["chart"]["bodies"])
    assert len(facts["chart"]["cusps"]) == 12
    assert facts["planetary_hour"]["status"] == "available"
    assert facts["radicality_verdict"] is None
    assert facts["coverage"]["moon_to_ingress_complete"] is True
    assert facts["phases"]["house_frame"] == "unavailable"
    assert all(p["H_house"] is None for p in facts["phases"]["states"].values())
    assert all(row["swiss_flag"] & 2 for row in facts["chart"]["bodies"])
    events = facts["events"]
    assert events == sorted(events, key=lambda e: (e["jd"], e["kind"], e["bodies"]))
    assert any(e["kind"] == "ingress" and e["bodies"] == ["moon"] for e in events)
    assert all(e["residual"] < 1e-6 for e in events)
    assert not any("prediction" in e for e in events)


def test_finer_grid_and_explicit_event_phase_sample_agree():
    cfg = example()
    cfg["scan_days"] = 3
    cfg["phase_samples_utc"] = ["2026-01-16T00:00:00Z"]
    coarse = recipe.compute_facts(cfg, step_minutes=30)
    fine = recipe.compute_facts(cfg, step_minutes=15)
    key = lambda e: (e["kind"], e["bodies"], e.get("aspect"), e.get("boundary_longitude"))
    assert [key(e) for e in coarse["events"]] == [key(e) for e in fine["events"]]
    assert all(abs(a["jd"]-b["jd"])*86400 < .1 for a,b in zip(coarse["events"], fine["events"]))
    sample = fine["phase_samples"][0]
    assert sample["phases"]["house_frame"] == "unavailable"
    assert sample["positions"]["moon"] != fine["chart"]["positions"]["moon"]


def test_explicit_past_extends_history_without_changing_question_chart():
    cfg = example()
    cfg["scan_days"] = 3
    cfg.pop("past_days", None)
    short = recipe.compute_facts(cfg)
    extended = dict(cfg, past_days=10)
    coarse = recipe.compute_facts(extended)
    fine = recipe.compute_facts(extended, step_minutes=15)
    assert short["coverage"]["past_days"] == 3
    assert coarse["coverage"]["past_days"] == 10
    assert coarse["moment_utc"] == short["moment_utc"]
    assert coarse["input"]["question"] == short["input"]["question"]
    assert coarse["chart"] == short["chart"]
    contact = lambda facts: [e for e in facts["events"] if e["kind"] == "aspect"
                            and e["bodies"] == ["sun", "mars"] and e["aspect"] == "conjunction"]
    assert not contact(short)
    event, = contact(coarse)
    refined, = contact(fine)
    assert abs((datetime.fromisoformat(event["utc"]) - datetime(2026, 1, 9, 11, 41,
               tzinfo=timezone.utc)).total_seconds()) < 120
    assert event["residual"] < 1e-6
    assert abs(event["jd"] - refined["jd"]) * 86400 < .1


def test_after_midnight_uses_previous_planetary_day():
    cfg = example()
    cfg["scan_days"] = 3
    cfg["moment"]["local"] = "2026-01-15T02:00:00+00:00"
    assert recipe.compute_facts(cfg)["planetary_hour"]["day_lord"] == "mercury"


def test_horary_requires_verified_ephemerides(monkeypatch, tmp_path):
    cfg = dict(example(), scan_days=3)
    monkeypatch.setattr(horary, "roots", lambda *a, **k: pytest.fail("scan ran before manifest gate"))
    monkeypatch.setenv("SE_EPHE_PATH", str(tmp_path))
    with pytest.raises(RuntimeError, match="SE_EPHE_PATH"):
        horary.compute_facts(cfg)
    monkeypatch.delenv("SE_EPHE_PATH")
    engine._init_swe()
    altered = tmp_path / "altered-ephe"
    altered.mkdir()
    for name in engine._SWE_RUNTIME_FILES:
        shutil.copyfile(Path(engine._SWE_EPHE_PATH) / name, altered / name)
    path = altered / "se00433s.se1"
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    monkeypatch.setattr(engine, "_SWE_EPHE_PATH", str(altered))
    with pytest.raises(RuntimeError, match="verified ephemeris"):
        horary.compute_facts(cfg)


@pytest.mark.parametrize("fault", ["moshier", "missing_speed", "equatorial", "nan", "short_vector"])
def test_scan_rejects_wrong_flags_and_nonfinite_vectors(monkeypatch, fault):
    swe = engine._init_swe()
    calculate = swe.calc_ut
    def verified_then_fault(*args, **kwargs):
        physical = engine.compute_body_states_series(*args, **kwargs)
        def broken(jd, body, flags=0):
            values, returned = calculate(jd, body, flags)
            if fault == "moshier":
                returned = swe.FLG_MOSEPH | swe.FLG_SPEED
            elif fault == "missing_speed":
                returned = swe.FLG_SWIEPH
            elif fault == "equatorial":
                returned |= swe.FLG_EQUATORIAL
            elif fault == "nan":
                values = (*values[:5], float("nan"))
            else:
                values = values[:4]
            return values, returned
        monkeypatch.setattr(swe, "calc_ut", broken)
        return physical
    monkeypatch.setattr(horary, "compute_body_states_series", verified_then_fault, raising=False)
    with pytest.raises(RuntimeError, match="Swiss flags|Swiss vector"):
        horary.compute_facts(dict(example(), scan_days=3))


@pytest.mark.parametrize("geometry", ["polar", "zero_arc", "multiple_turns", "nonfinite_angle"])
def test_unsupported_regiomontanus_geometry_stops_before_house_derivatives(monkeypatch, geometry):
    cfg = dict(example(), scan_days=3)
    swe = engine._init_swe()
    if geometry == "polar":
        cfg["moment"].update(local="2026-01-15T12:00:00+01:00", timezone="Europe/Oslo",
                             latitude=69.6492, longitude=18.9553)
    else:
        calculate = swe.houses_ex
        def broken(*args):
            cusps, angles = calculate(*args)
            cusps, angles = list(cusps), list(angles)
            if geometry == "zero_arc":
                cusps[1] = cusps[0]
            elif geometry == "multiple_turns":
                cusps[1], cusps[2] = cusps[2], cusps[1]
            else:
                angles[1] = float("nan")
            return cusps, angles
        monkeypatch.setattr(swe, "houses_ex", broken)
    monkeypatch.setattr(horary, "compute_sect", lambda *a: pytest.fail("sect ran on unsupported geometry"))
    with pytest.raises(RuntimeError, match="unsupported Regiomontanus geometry"):
        horary.compute_facts(cfg)


def test_unknown_hour_does_not_mean_no_agreement(monkeypatch):
    swe = engine._init_swe()
    monkeypatch.setattr(swe, "rise_trans", lambda *a, **k: (-2, (0,) * 10))
    facts = horary.compute_facts(dict(example(), scan_days=3))
    assert facts["planetary_hour"]["status"] == "unavailable"
    assert "agreement" not in facts["planetary_hour"]


def test_horary_uses_shared_physical_carrier_and_phase_operators():
    cfg = dict(example(), scan_days=3, phase_samples_utc=["2026-01-16T00:00:00Z"])
    facts = horary.compute_facts(cfg)
    physical = facts["body_states"]
    chart = facts["chart"]
    context = {"moment_utc": physical["moment_utc"], "positions": chart["positions"],
               "houses": {"angles": chart["angles"]}, "sect": {"chart_sect": chart["sect"]}}
    assert facts["carrier_states"] == compute_carrier_states(context, physical)
    assert facts["phases"] == compute_phase_states(chart["positions"], moment_utc=physical["moment_utc"])
    assert physical["moment_utc"] == "2026-01-15T12:00:00Z"
    for row in chart["bodies"]:
        state = physical["bodies"][row["body"]]
        assert row["longitude"] == state["longitude_deg"]
        assert row["speed_deg_day"] == state["longitude_speed_deg_per_day"]
    sample, = facts["phase_samples"]
    assert sample["body_states"] == engine.compute_body_states_series(
        [datetime(2026, 1, 16, tzinfo=timezone.utc)], engine="a")[0]
    assert sample["phases"] == compute_phase_states(sample["positions"],
        moment_utc=sample["body_states"]["moment_utc"])
    assert sample["phases"]["house_frame"] == "unavailable"
    assert "carrier_states" not in sample
    assert "astro/horary.py" in facts["provenance"]["source_sha256"]
