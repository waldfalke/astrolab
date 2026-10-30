"""Physical references and synthetic boundary arithmetic; no personal chart data."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path

import pytest

from astro import engine
from astro import dignities

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/fixtures/body-states/swiss-reference.json"
MOMENT = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)


def test_body_states_matches_direct_swiss_reference():
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    # Same Swiss/files: measured Win/Linux Venus speed drift is 3.47e-9 deg/day (2026-03-20).
    for case in reference["cases"]:
        moment = datetime.fromisoformat(case["moment_utc"].replace("Z", "+00:00"))
        result = engine.compute_body_states_series([moment], engine="a")[0]
        assert result["moment_utc"] == case["moment_utc"]
        assert set(result["bodies"]) == set(engine.DEFAULT_BODIES)
        assert result["obliquity"]["true_obliquity_deg"] == pytest.approx(case["obliquity"][0], abs=1e-10)
        for body, raw in case["bodies"].items():
            row = result["bodies"][body]
            for field, expected in (("longitude_deg", raw["ecliptic"][0]),
                                    ("latitude_deg", raw["ecliptic"][1]),
                                    ("distance_au", raw["ecliptic"][2]),
                                    ("longitude_speed_deg_per_day", raw["ecliptic"][3]),
                                    ("declination_deg", raw["equatorial"][1])):
                tolerance = 1e-8 if field == "longitude_speed_deg_per_day" else 1e-10
                assert row[field] == pytest.approx(expected, abs=tolerance), (case["moment_utc"], body, field)
            assert row["id"] == body and row["name"] and row["model"]


def test_body_states_declination_uses_real_latitude():
    state = engine.compute_body_states_series([MOMENT], engine="a")[0]
    row = state["bodies"]["moon"]
    longitude, latitude = map(math.radians, (row["longitude_deg"], row["latitude_deg"]))
    epsilon = math.radians(state["obliquity"]["true_obliquity_deg"])
    independent = math.degrees(math.asin(math.sin(latitude) * math.cos(epsilon)
                                         + math.cos(latitude) * math.sin(epsilon) * math.sin(longitude)))
    beta_zero = math.degrees(math.asin(math.sin(longitude) * math.sin(epsilon)))
    assert abs(row["latitude_deg"]) > 1
    assert row["declination_deg"] == pytest.approx(independent, abs=1e-6)
    assert abs(row["declination_deg"] - beta_zero) > 1


def test_body_states_speed_matches_wrapped_central_difference():
    before, at, after = engine.compute_body_states_series(
        [MOMENT - timedelta(days=0.001), MOMENT, MOMENT + timedelta(days=0.001)], engine="a")
    for body, row in at["bodies"].items():
        delta = (after["bodies"][body]["longitude_deg"]
                 - before["bodies"][body]["longitude_deg"] + 180) % 360 - 180
        assert row["longitude_speed_deg_per_day"] == pytest.approx(delta / 0.002, abs=1e-4)


def test_body_states_rejects_b1_without_fallback(monkeypatch):
    def forbidden():
        raise AssertionError("unsupported engine must not initialize engine A")
    monkeypatch.setattr(engine, "_init_swe", forbidden)
    with pytest.raises(ValueError, match="only engine A"):
        engine.compute_body_states_series([MOMENT], engine="b1")


def test_body_states_rejects_environment_ephemeris_override(monkeypatch):
    # Even a currently matching override can hide a different effective Swiss search path.
    monkeypatch.setenv("SE_EPHE_PATH", str(ROOT / "infra/ephe/files"))
    with pytest.raises(RuntimeError, match="SE_EPHE_PATH.*SWISS_EPHE_PATH"):
        engine.compute_body_states_series([MOMENT], engine="a")


@pytest.mark.parametrize("missing", [False, True])
def test_body_states_requires_verified_ephemeris(monkeypatch, tmp_path, missing):
    for name in engine._SWE_RUNTIME_FILES:
        (tmp_path / name).write_bytes(b"not an ephemeris")
    if missing:
        (tmp_path / engine._SWE_RUNTIME_FILES[0]).unlink()
    monkeypatch.setattr(engine, "_SWE_EPHE_PATH", str(tmp_path))
    with pytest.raises(RuntimeError, match="ephemeris"):
        engine.compute_body_states_series([MOMENT], engine="a")


def test_body_states_refuses_moshier_return_flags(monkeypatch):
    swe = engine._init_swe()
    original = swe.calc_ut
    def fallback(jd, body, flags=0):
        values, returned = original(jd, body, flags)
        return values, ((returned & ~swe.FLG_SWIEPH) | swe.FLG_MOSEPH
                        if body != swe.ECL_NUT else returned)
    monkeypatch.setattr(swe, "calc_ut", fallback)
    with pytest.raises(RuntimeError, match="flags|fallback"):
        engine.compute_body_states_series([MOMENT], engine="a")


@pytest.mark.parametrize("moments,bodies", [
    ([datetime(2000, 1, 1)], None), (["2000-01-01"], None),
    ([MOMENT], ["made_up"]), ([MOMENT], ["sun", "sun"]), ([MOMENT], []),
])
def test_body_states_rejects_invalid_input(moments, bodies):
    with pytest.raises((ValueError, TypeError)):
        engine.compute_body_states_series(moments, bodies=bodies, engine="a")


def test_body_states_provenance_has_no_host_paths():
    state = engine.compute_body_states_series([MOMENT], bodies=["north_node", "lilith", "chiron"], engine="a")[0]
    provenance = state["provenance"]
    assert provenance["engine"] == "a"
    assert provenance["swiss_version"] == "2.10.03"
    assert provenance["pyswisseph_version"] and provenance["operator_sha256"]
    assert set(provenance["ephemeris_files"]) == set(engine._SWE_RUNTIME_FILES)
    assert all(len(value) == 64 for value in provenance["ephemeris_files"].values())
    assert state["coordinate_system"]["center"] == "geocentric"
    assert state["coordinate_system"]["zodiac"] == "tropical"
    assert state["bodies"]["north_node"]["model"] == "true_node"
    assert state["bodies"]["lilith"]["model"] == "mean_apogee"
    assert str(ROOT) not in json.dumps(state)


def synthetic_inputs():
    positions = dict(sun=0.0, moon=100.0, mercury=190.0, venus=340.0, mars=130.0,
                     jupiter=30.0, saturn=300.0, uranus=60.0, neptune=330.0, pluto=200.0)
    natal = {"moment_utc": "2000-01-01T12:00:00Z", "positions": positions,
             "sect": {"chart_sect": "day"}, "houses": {"angles": {"asc": 10.0}}}
    snapshot = {"version": "0.1.0", "moment_utc": natal["moment_utc"],
                "coordinate_system": dict(engine.BODY_STATE_COORDINATES),
                "obliquity": {"true_obliquity_deg": 23.4, "mean_obliquity_deg": 23.4},
                "bodies": {body: {"id": body, "name": body.title(), "model": "solar_system_body",
                                  "longitude_deg": longitude, "latitude_deg": 0.0, "distance_au": 1.0,
                                  "longitude_speed_deg_per_day": 1.0, "declination_deg": 10.0}
                           for body, longitude in positions.items()},
                "provenance": {"source": "synthetic arithmetic fixture, not measured sky"}}
    return natal, snapshot


def carrier(natal, snapshot):
    from astro.carrier_states import compute_carrier_states
    return compute_carrier_states(natal, snapshot)


def test_essential_states_preserve_compatible_dignities_and_debilities():
    virgo = dignities.compute_essential_states({"mercury": 155.0}, "day")["bodies"]["mercury"]
    pisces = dignities.compute_essential_states({"mercury": 335.0}, "day")["bodies"]["mercury"]
    cancer = dignities.compute_essential_states({"mars": 92.0}, "night")["bodies"]["mars"]
    assert {"domicile", "exaltation"} <= set(virgo["dignities"])
    assert set(pisces["debilities"]) == {"detriment", "fall"}
    assert cancer["debilities"] == ["fall"]
    assert {"triplicity", "term"} <= set(cancer["dignities"])
    assert dignities.compute_dignities({"mercury": 335.0}, "traditional")["mercury"]["dignity"] == "detriment"


@pytest.mark.parametrize("longitude,day,night", [
    (15, "sun", "jupiter"), (45, "venus", "moon"),
    (75, "saturn", "mercury"), (105, "mars", "mars"),
])
def test_lilly_triplicity_day_night_without_participant(longitude, day, night):
    for sect, owner in (("day", day), ("night", night)):
        result = dignities.compute_essential_states({"sun": float(longitude)}, sect)
        assert result["bodies"]["sun"]["owners"]["triplicity"] == owner
        assert result["profile"] == "selected-classical-v1"
        assert result["tables"]["triplicity"]["id"] == "lilly_ptolemaic_day_night_no_participant"


def test_holdings_are_directed_and_minor_dignities_keep_the_owner():
    result = dignities.compute_essential_states({"sun": 38.0, "moon": 15.0, "uranus": 38.0}, "day")
    # Moon Aries 15°: Sun exaltation, day triplicity and second face. Sun Taurus: Moon exaltation.
    rows = {(r["guest"], r["host"]): r for r in result["dignity_holdings"]}
    assert rows["moon", "sun"]["dignities"] == ["exaltation", "triplicity", "face"]
    assert rows["sun", "moon"]["dignities"] == ["exaltation"]
    assert result["bodies"]["sun"]["owners"]["term"] == "mercury"
    assert "term" not in result["bodies"]["sun"]["dignities"]
    assert result["bodies"]["uranus"]["availability"] == "unsupported_traditional_body"
    assert result["bodies"]["uranus"]["peregrine"] is None
    assert "verdict" not in json.dumps(result) and "score" not in json.dumps(result)
    assert all(len(table["sha256"]) == 64 and table["source"] for table in result["tables"].values())


@pytest.mark.parametrize("distance,condition", [
    (17 / 60 - 1e-9, "cazimi"), (17 / 60, "cazimi"), (17 / 60 + 1e-9, "combust"),
    (8.5 - 1e-9, "combust"), (8.5, "combust"), (8.5 + 1e-9, "under_beams"),
    (17 - 1e-9, "under_beams"), (17, "under_beams"), (17 + 1e-9, "free"),
])
def test_solar_thresholds(distance, condition):
    natal, state = synthetic_inputs()
    natal["positions"]["mercury"] = state["bodies"]["mercury"]["longitude_deg"] = distance
    assert carrier(natal, state)["bodies"]["mercury"]["solar"]["condition"] == condition


@pytest.mark.parametrize("longitude,direction", [(0, "conjunction"), (180, "opposition"),
                                                 (1, "east_of_sun"), (359, "west_of_sun")])
def test_solar_direction_wrap_and_self(longitude, direction):
    natal, state = synthetic_inputs()
    natal["positions"]["mercury"] = state["bodies"]["mercury"]["longitude_deg"] = float(longitude)
    result = carrier(natal, state)
    assert result["bodies"]["mercury"]["solar"]["direction"] == direction
    assert result["bodies"]["sun"]["solar"]["condition"] == "not_applicable"


@pytest.mark.parametrize("speed,direction", [(1, "direct"), (-1, "retrograde"), (0, "zero_instantaneous")])
def test_motion_is_instantaneous(speed, direction):
    natal, state = synthetic_inputs()
    state["bodies"]["mars"]["longitude_speed_deg_per_day"] = speed
    assert carrier(natal, state)["bodies"]["mars"]["motion"]["direction"] == direction


@pytest.mark.parametrize("declination,oob", [(23.4 - 1e-9, False), (23.4, False),
                                          (23.4 + 1e-9, True), (-23.4 - 1e-9, True)])
def test_oob_mean_obliquity_boundary(declination, oob):
    natal, state = synthetic_inputs()
    state["bodies"]["mars"]["declination_deg"] = declination
    row = carrier(natal, state)["bodies"]["mars"]["declination"]
    assert row["oob"] is oob
    assert row["excess_deg"] == pytest.approx(max(0, abs(declination) - 23.4))


@pytest.mark.parametrize("a,b,aspect", [(10, 11 - 1e-9, "parallel"), (10, 11, "parallel"),
    (10, 11 + 1e-9, None), (10, -11, "contraparallel"), (-10, -11, "parallel"),
    (0, 0, "parallel"), (0, 0.5, None)])
def test_declination_pairs_hemispheres_and_boundaries(a, b, aspect):
    natal, state = synthetic_inputs()
    state["bodies"]["moon"]["declination_deg"] = a
    state["bodies"]["venus"]["declination_deg"] = b
    pairs = [r for r in carrier(natal, state)["declination_aspects"]
             if {r["body1"], r["body2"]} == {"moon", "venus"}]
    assert len(pairs) == (0 if aspect is None else 1)
    if pairs:
        assert pairs[0]["aspect"] == aspect and pairs[0]["orb_limit_deg"] == 1.0


@pytest.mark.parametrize("field,bad", [("longitude_deg", True), ("longitude_deg", float("nan")),
    ("latitude_deg", False), ("latitude_deg", 91), ("distance_au", -1),
    ("longitude_speed_deg_per_day", float("inf")), ("declination_deg", True),
    ("declination_deg", float("nan")), ("declination_deg", -91)])
def test_carrier_rejects_invalid_external_numeric_state(field, bad):
    natal, state = synthetic_inputs()
    state["bodies"]["mars"][field] = bad
    with pytest.raises(ValueError):
        carrier(natal, state)


@pytest.mark.parametrize("mutation", [
    lambda n, s: s.update(moment_utc="1999-01-01T00:00:00Z"),
    lambda n, s: s["coordinate_system"].update(center="heliocentric"),
    lambda n, s: s["obliquity"].update(mean_obliquity_deg=True),
    lambda n, s: s["obliquity"].update(true_obliquity_deg=float("nan")),
    lambda n, s: s["bodies"].pop("mars"),
    lambda n, s: s["bodies"]["mars"].update(id="venus"),
    lambda n, s: s["bodies"]["mars"].update(longitude_deg=131),
    lambda n, s: n["positions"].update(mars=True),
    lambda n, s: n["sect"].update(chart_sect="night"),
    lambda n, s: s.update(provenance={}),
])
def test_carrier_rejects_mismatched_or_incomplete_context(mutation):
    natal, state = synthetic_inputs()
    mutation(natal, state)
    with pytest.raises(ValueError):
        carrier(natal, state)


def test_carrier_preserves_inputs_provenance_and_conditional_limits():
    natal, state = synthetic_inputs()
    original = copy.deepcopy((natal, state))
    result = carrier(natal, state)
    assert (natal, state) == original
    assert result["input_provenance"] == state["provenance"]
    assert result["availability"]["future_perfection"] == "not_calculated"
    assert result["availability"]["heliacal_visibility"] == "not_calculated"
    assert result["availability"]["station_events"] == "not_calculated"
    assert len(result["input_sha256"]["body_states"]) == 64
