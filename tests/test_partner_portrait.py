"""Engine-free arithmetic and delivery contract; positions below are synthetic, not a sky."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from astro.aspects import compute_aspects
from astro.dignities import compute_dignities
from astro.phases import compute_phase_states
from astro.placements import compute_placements
from astro.sect import compute_part_of_fortune, compute_sect

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "artifacts/mcp-recipes/partner_portrait.py"
spec = importlib.util.spec_from_file_location("partner_portrait", SCRIPT)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


def natal(sun=250.0):
    positions = dict(sun=sun, moon=100.0, mercury=190.0, venus=340.0,
                     mars=130.0, jupiter=30.0, saturn=300.0,
                     uranus=60.0, neptune=330.0, pluto=200.0)
    cusps = [(10.0 + 30 * i) % 360 for i in range(12)]
    sect = compute_sect(positions, 10.0)
    points = {"part_of_fortune": compute_part_of_fortune(
        10.0, sun, 100.0, sect["chart_sect"])}
    return {"moment_utc": "2000-01-01T12:00:00Z", "location": {"lat": 0, "lon": 0},
            "positions": positions, "houses": {"cusps": cusps,
                "angles": {"asc": 10.0, "dsc": 190.0, "mc": 280.0, "ic": 100.0}},
            "sect": sect, "points": points, "aspects": compute_aspects(positions),
            "dignities": compute_dignities(positions),
            "placements": compute_placements({**positions, **points}, cusps),
            "extension": {"preserve": [1, "unselected material"]}}


@pytest.mark.parametrize("sun,expected", [
    (250.0, {"fortune": 220, "spirit": 160, "eros_paulus": 190,
             "eros_valens": 310, "marriage_valens_general": 320,
             "marriage_valens_male": 100, "marriage_valens_female": 40}),
    (70.0, {"fortune": 340, "spirit": 40, "eros_paulus": 70,
            "eros_valens": 310, "marriage_valens_general": 60,
            "marriage_valens_male": 280, "marriage_valens_female": 40}),
])
def test_independent_day_night_lot_arithmetic(sun, expected):
    result = recipe.compute_partner_portrait(natal(sun), partner="women")
    assert {name: row["longitude"] for name, row in result["lots"].items()} == expected
    assert all(row["formula"] and row["source"] and row["dependencies"]
               for row in result["lots"].values())


def test_firmicus_worked_example_and_wrap():
    # Mathesis II.13.3: Aries 5°05′, twelve times = 61°, i.e. Gemini 1°.
    assert recipe.subdivisions(5 + 5 / 60)["dodecatemorion"]["longitude"] == pytest.approx(61)
    assert recipe.subdivisions(0)["dodecatemorion"]["longitude"] == 0
    assert recipe.subdivisions(359.999)["dodecatemorion"]["longitude"] < 360


@pytest.mark.parametrize("longitude,term,decan", [
    (0, "jupiter", "mars"), (5.99999, "jupiter", "mars"),
    (6, "venus", "mars"), (10, "venus", "sun"),
    (20, "mars", "venus"), (30, "venus", "mercury"),
    (77, "mars", "mars"), (359.999, "saturn", "mars"),
])
def test_primary_tables_and_half_open_boundaries(longitude, term, decan):
    result = recipe.subdivisions(longitude)
    assert result["term"]["ruler"] == term
    assert result["decan"]["ruler"] == decan


def test_both_adapters_and_whole_input_are_preserved():
    source = natal()
    original = copy.deepcopy(source)
    women = recipe.compute_partner_portrait(source, partner="women")
    men = recipe.compute_partner_portrait(source, partner="men")
    assert women["significators"]["luminary"] == "moon"
    assert women["significators"]["desire"] == "venus"
    assert men["significators"]["luminary"] == "sun"
    assert men["significators"]["desire"] == "mars"
    assert women["seventh"]["ruler"] == "venus"  # DSC Libra 10°
    assert women["seventh"]["dodecatemorion"]["longitude"] == 300
    assert source == original == women["natal"] == men["natal"]
    assert women["lots"] == men["lots"]
    assert "phase" not in women["lots"]["fortune"]


def test_shared_phase_fallback_and_stale_rejection():
    source = natal()
    result = recipe.compute_partner_portrait(source, partner="women")
    expected = compute_phase_states(source["positions"], cusps=source["houses"]["cusps"],
                                    moment_utc=source["moment_utc"])
    assert result["phase_states"] == expected
    source["phases"] = expected
    assert recipe.compute_partner_portrait(source, partner="men")["phase_origin"] == "natal.phases"
    source["positions"]["venus"] = 341
    with pytest.raises(ValueError, match="phase"):
        recipe.compute_partner_portrait(source, partner="men")


def test_serialized_phase_round_trip_and_tampered_state():
    source = natal()
    source["phases"] = compute_phase_states(source["positions"],
        cusps=source["houses"]["cusps"], moment_utc=source["moment_utc"])
    source = json.loads(json.dumps(source))  # real saved-input boundary: tuple -> list
    result = recipe.compute_partner_portrait(source, partner="men")
    assert result["phase_origin"] == "natal.phases"
    assert result["natal"] == source
    source["phases"]["states"]["venus"]["Z"] = "tampered"
    with pytest.raises(ValueError, match="phase"):
        recipe.compute_partner_portrait(source, partner="men")


def test_seventh_uses_exact_cusp_after_tolerant_angle_match():
    source = natal()
    source["houses"]["angles"]["asc"] -= 1e-12
    source["houses"]["angles"]["dsc"] -= 1e-12
    result = recipe.compute_partner_portrait(source, partner="women")
    assert result["seventh"]["house"] == 7
    assert result["seventh"]["longitude"] == source["houses"]["cusps"][6]
    assert result["natal"]["houses"]["angles"]["dsc"] == 190 - 1e-12


def test_motion_unavailable_without_speed_and_directed_when_present():
    source = natal()
    source["positions"].update(moon=100, venus=164)
    source.pop("points")
    result = recipe.compute_partner_portrait(source, partner="women")
    contact = next(row for row in result["contacts"] if row["from_body"] == "moon"
                   and row["to_body"] == "venus")
    assert contact["motion"]["status"] == "unavailable"
    motion = {"moment_utc": source["moment_utc"], "units": "deg/day",
              "source": "synthetic arithmetic, not measured sky", "values": {"moon": 13, "venus": 1}}
    result = recipe.compute_partner_portrait(source, partner="women", speeds=motion)
    contact = next(row for row in result["contacts"] if row["from_body"] == "moon"
                   and row["to_body"] == "venus")
    assert contact["motion"]["status"] == "applying_local"
    assert contact["motion"]["direction"] == "moon->venus"
    assert contact["motion"]["orb_rate_deg_per_day"] == -12


def test_motion_target_can_apply_to_sun_and_exact_is_not_guessed():
    assert recipe.contact_motion("sun", "mercury", -2, {"sun": 1, "mercury": 1.2}) == {
        "status": "applying_local", "direction": "mercury->sun",
        "orb_rate_deg_per_day": pytest.approx(-0.2)}
    assert recipe.contact_motion("sun", "mars", 4, {"sun": 1, "mars": -0.5})["direction"] == "mutual"
    assert recipe.contact_motion("sun", "mercury", 4, {"sun": 1, "mercury": 1.2})["status"] == "separating_local"
    assert recipe.contact_motion("sun", "mercury", 0, {"sun": 1, "mercury": 1.2})["status"] == "exact"
    assert recipe.contact_motion("moon", "venus", 2, {"moon": 1, "venus": 1})["status"] == "stationary_relative"


@pytest.mark.parametrize("mutate", [
    lambda n: n["positions"].update(moon=float("nan")),
    lambda n: n["positions"].update(moon=True),
    lambda n: n["positions"].update(moon=360),
    lambda n: n["positions"].pop("saturn"),
    lambda n: n["houses"]["cusps"].__setitem__(1, 10),
    lambda n: n["houses"]["angles"].update(dsc=192),
    lambda n: n["sect"].update(chart_sect="night"),
])
def test_invalid_natal_is_rejected(mutate):
    source = natal()
    mutate(source)
    with pytest.raises(ValueError):
        recipe.compute_partner_portrait(source, partner="women")


def test_invalid_speed_metadata_and_options_are_rejected():
    source = natal()
    for speed in ({"moment_utc": "1999-01-01T00:00:00Z", "units": "deg/day", "source": "x", "values": {"moon": 13}},
                  {"moment_utc": source["moment_utc"], "units": "deg/hour", "source": "x", "values": {"moon": 13}},
                  {"moment_utc": source["moment_utc"], "units": "deg/day", "source": "", "values": {"moon": 13}},
                  {"moment_utc": source["moment_utc"], "units": "deg/day", "source": "x", "values": {"moon": float("inf")}}):
        with pytest.raises(ValueError):
            recipe.compute_partner_portrait(source, partner="women", speeds=speed)
    with pytest.raises(ValueError):
        recipe.compute_partner_portrait(source, partner="unknown")
    with pytest.raises(ValueError):
        recipe.compute_partner_portrait(source, partner="men", orb=16)


@pytest.mark.parametrize("private_name", [".private", ".PRIVATE"])
def test_cli_preserves_bytes_hashes_and_refuses_overwrite_or_private_escape(tmp_path, private_name):
    source = tmp_path / "natal.json"
    raw = (json.dumps(natal(), ensure_ascii=False, indent=2) + "\n").encode()
    source.write_bytes(raw)
    output = tmp_path / "run"
    command = [sys.executable, str(SCRIPT), "--natal", str(source),
               "--partner", "men", "--output", str(output)]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert (output / "sources/natal.json").read_bytes() == raw
    data = json.loads((output / "01_partner_portrait.json").read_text(encoding="utf-8"))
    import hashlib
    assert data["provenance"]["input_sha256"]["natal.json"] == hashlib.sha256(raw).hexdigest()
    assert "OUTPUT_HASH=" in (output / "00_summary.txt").read_text()
    assert subprocess.run(command, capture_output=True).returncode != 0
    private = tmp_path / private_name
    private.mkdir()
    private_source = private / "natal.json"
    private_source.write_bytes(raw)
    escaped = tmp_path / "escape"
    blocked = subprocess.run([sys.executable, str(SCRIPT), "--natal", str(private_source),
                              "--partner", "women", "--output", str(escaped)], capture_output=True)
    assert blocked.returncode != 0
    assert not escaped.exists()


def test_importable_core_preserves_legacy_arithmetic_and_interfaces():
    from astro.partner_portrait import compute_partner_portrait, contact_motion, subdivisions

    for partner in ("women", "men"):
        source = natal()
        result = compute_partner_portrait(source, partner=partner)
        assert result == recipe.compute_partner_portrait(source, partner=partner)
        assert result["lots"]["eros_paulus"]["longitude"] == 190
        assert result["lots"]["marriage_valens_general"]["longitude"] == 320
        assert result["natal"] == source
        assert result["motion_input"] is None
    assert subdivisions(6)["term"]["ruler"] == "venus"
    assert contact_motion("sun", "mercury", -2, {"sun": 1, "mercury": 1.2})["direction"] == "mercury->sun"


def test_importable_core_consumes_actual_body_state_speeds():
    from datetime import datetime, timezone
    from astro.engine import DEFAULT_BODIES, compute_body_states_series
    from astro.natal import compute_natal
    from astro.carrier_states import compute_carrier_states
    from astro.partner_portrait import compute_partner_portrait

    moment = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    chart = compute_natal(moment, 0.0, 0.0, bodies=list(DEFAULT_BODIES), scheme="traditional", engine="a")
    physical = compute_body_states_series([moment], engine="a")[0]
    states = compute_carrier_states(chart, physical)
    speeds = {"moment_utc": physical["moment_utc"], "units": "deg/day",
              "source": json.dumps(physical["provenance"], sort_keys=True),
              "values": {body: row["longitude_speed_deg_per_day"] for body, row in physical["bodies"].items()}}
    for partner in ("women", "men"):
        result = compute_partner_portrait(chart, partner=partner, speeds=speeds)
        assert result["contacts"]
        assert all(row["motion"]["status"] != "unavailable" for row in result["contacts"])
        assert result["phase_states"] == chart["phases"]
        assert result["motion_input"] == speeds
    assert states["profile"] == "selected-classical-v1"
    assert set(states["bodies"]) == set(DEFAULT_BODIES)


def test_cli_provenance_tracks_importable_core(tmp_path):
    import hashlib
    source = tmp_path / "natal.json"
    source.write_text(json.dumps(natal()), encoding="utf-8")
    output = tmp_path / "run"
    result = subprocess.run([sys.executable, str(SCRIPT), "--natal", str(source),
                             "--partner", "women", "--output", str(output)], capture_output=True)
    assert result.returncode == 0, result.stderr
    payload = (output / "01_partner_portrait.json").read_bytes()
    data = json.loads(payload)
    assert data["provenance"]["operator_sha256"]["astro/partner_portrait.py"] == hashlib.sha256(
        (REPO / "astro/partner_portrait.py").read_bytes()).hexdigest()
    assert (output / "00_summary.txt").read_text().endswith(f"OUTPUT_HASH={hashlib.sha256(payload).hexdigest()}\n")
