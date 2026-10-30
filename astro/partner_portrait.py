"""Engine-free partner-portrait derivatives; calculation evidence, never final prose."""
from __future__ import annotations

import copy
import json
import math

from astro.aspects import MAJOR_ASPECTS
from astro.dignities import (SIGNS, CLASSICAL, RULERS, TERMS, DECAN_CYCLE, FIRMICUS, PTOLEMY,
                             _number, _longitude, subdivisions, compute_dignities)
from astro.phases import compute_phase_states
from astro.placements import house_of
from astro.sect import compute_part_of_fortune, compute_sect

VERSION = "0.1.0"
VALENS = "https://ceskaastrologie.cz/wp-content/uploads/2020/12/Valens.pdf"
GREENBAUM = "https://www.tarothermeneutics.com/tarotliterature/articles/daimon.pdf"


def _point(longitude: float, cusps: list) -> dict:
    sign = int(longitude // 30)
    return {"longitude": longitude, "sign": SIGNS[sign], "degree_in_sign": longitude % 30,
            "ruler": RULERS[sign], "phase_carrier": RULERS[sign],
            "house": house_of(longitude, cusps), **subdivisions(longitude)}


def contact_motion(from_body: str, to_body: str, error: float, speeds: dict) -> dict:
    """Instantaneous orb derivative, with direction of the motions that close it.

    error = (to - from) minus the nearest directed exact ray. No prediction of
    perfection, station, prohibition or sign ingress is made by this local model.
    """
    if from_body not in speeds or to_body not in speeds:
        return {"status": "unavailable", "reason": "missing_speed", "direction": None}
    if math.isclose(error, 0, abs_tol=1e-9):
        return {"status": "exact", "direction": None, "orb_rate_deg_per_day": None}
    rate = math.copysign(1, error) * (speeds[to_body] - speeds[from_body])
    if math.isclose(rate, 0, abs_tol=1e-12):
        return {"status": "stationary_relative", "direction": None,
                "orb_rate_deg_per_day": rate}
    direction = None
    if rate < 0:
        from_closes = error * speeds[from_body] > 0
        to_closes = error * speeds[to_body] < 0
        direction = ("mutual" if from_closes and to_closes else
                     f"{from_body}->{to_body}" if from_closes else f"{to_body}->{from_body}")
    return {"status": "applying_local" if rate < 0 else "separating_local",
            "direction": direction, "orb_rate_deg_per_day": rate}


def compute_partner_portrait(natal: dict, *, partner: str, speeds: dict | None = None,
                             orb: float = 6.0) -> dict:
    """Retain the full natal and add named derivatives; no ephemeris or I/O."""
    if partner not in ("women", "men"):
        raise ValueError("partner must be women or men")
    orb = _number(orb, "orb")
    if not 0 <= orb <= 15:
        raise ValueError("orb must be in [0,15]")
    if not isinstance(natal, dict) or not isinstance(natal.get("positions"), dict):
        raise ValueError("expected a compute_natal JSON object with positions")
    positions = {body: _longitude(lon, f"position {body}") for body, lon in natal["positions"].items()}
    if not set(CLASSICAL) <= positions.keys():
        raise ValueError("all seven classical bodies are required")
    houses = natal.get("houses", {})
    if not isinstance(houses, dict) or not isinstance(houses.get("angles"), dict):
        raise ValueError("houses with cusps and angles are required")
    cusps = houses.get("cusps")
    if not isinstance(cusps, list):
        raise ValueError("houses.cusps must be a list of 12 longitudes")
    asc = _longitude(houses["angles"].get("asc"), "ASC")
    dsc = _longitude(houses["angles"].get("dsc"), "DSC")
    # The shared operator validates the moment and ordered, complete house frame.
    phases = compute_phase_states(positions, cusps=cusps, moment_utc=natal.get("moment_utc"))
    if natal.get("moment_utc") is None:
        raise ValueError("natal.moment_utc is required")
    if not math.isclose(asc, cusps[0], abs_tol=1e-7) or not math.isclose(dsc, cusps[6], abs_tol=1e-7):
        raise ValueError("ASC/DSC must match cusps 1/7")
    if not math.isclose((dsc - asc) % 360, 180, abs_tol=1e-7):
        raise ValueError("ASC and DSC must be opposite")
    # Accepted angle rounding must not put the seventh cusp into house VI.
    asc, dsc = cusps[0], cusps[6]
    # JSON round-trips turn the operator's tuple cusps into lists; compare both
    # complete payloads in their serialized representation, including the states.
    if "phases" in natal and (
        json.dumps(natal["phases"], sort_keys=True, allow_nan=False)
        != json.dumps(phases, sort_keys=True, allow_nan=False)
    ):
        raise ValueError("natal phases are stale or incompatible with the shared operator")
    sect = compute_sect(positions, asc)["chart_sect"]
    if natal.get("sect", {}).get("chart_sect") != sect:
        raise ValueError("natal sect is missing or inconsistent with Sun/ASC")
    fortune = compute_part_of_fortune(asc, positions["sun"], positions["moon"], sect)
    stored_fortune = natal.get("points", {}).get("part_of_fortune")
    if stored_fortune is not None and not math.isclose(
            _longitude(stored_fortune, "natal Fortune"), fortune, abs_tol=1e-7):
        raise ValueError("natal Fortune is inconsistent with sect")
    speed_values = {}
    if speeds is not None:
        if not isinstance(speeds, dict) or speeds.get("moment_utc") != natal["moment_utc"]:
            raise ValueError("speeds must identify the same moment_utc as natal")
        if speeds.get("units") != "deg/day" or not isinstance(speeds.get("source"), str) or not speeds["source"].strip():
            raise ValueError("speeds require units deg/day and a nonempty source")
        if not isinstance(speeds.get("values"), dict) or not speeds["values"]:
            raise ValueError("speeds.values must be a nonempty body-to-speed map")
        for body, value in speeds["values"].items():
            if body not in positions:
                raise ValueError(f"speed body {body} is absent from natal")
            speed_values[body] = _number(value, f"speed {body}")

    day = sect == "day"
    values = {**positions, "asc": asc}
    definitions = (
        ("fortune", "moon" if day else "sun", "sun" if day else "moon", f"Valens II.3; sect convention: {VALENS}"),
        ("spirit", "sun" if day else "moon", "moon" if day else "sun", f"Valens II.22K/23P (Riley p.14); Greenbaum App.8A: {GREENBAUM}"),
        ("eros_paulus", "venus" if day else "spirit", "spirit" if day else "venus", f"Paulus 23 via Greenbaum App.10B p.476: {GREENBAUM}"),
        ("eros_valens", "spirit" if day else "fortune", "fortune" if day else "spirit", f"Valens IV.25; Greenbaum App.10B p.475: {VALENS}"),
        ("marriage_valens_general", "venus" if day else "jupiter", "jupiter" if day else "venus", f"Valens II.37K/38P: {VALENS}"),
        ("marriage_valens_male", "venus", "sun", f"Valens II.38K: {VALENS}"),
        ("marriage_valens_female", "mars", "moon", f"Valens II.38K: {VALENS}"),
    )
    lots = {}
    for name, add, subtract, source in definitions:
        value = (asc + values[add] - values[subtract]) % 360
        values[name] = value
        lots[name] = {**_point(value, cusps), "formula": f"ASC + {add} - {subtract} (mod 360)",
                      "dependencies": ["asc", add, subtract], "source": source}

    luminary, desire = ("moon", "venus") if partner == "women" else ("sun", "mars")
    seventh = _point(dsc, cusps)
    carriers = list(dict.fromkeys((luminary, desire, seventh["ruler"])))
    contacts = []
    rays = [(name, angle) for name, angle in MAJOR_ASPECTS]
    rays += [(name, 360 - angle) for name, angle in MAJOR_ASPECTS if angle not in (0, 180)]
    rays.append(("conjunction", 360.0))
    for carrier in carriers:
        for target in sorted(positions):
            if target == carrier:
                continue
            delta = (positions[target] - positions[carrier]) % 360
            name, exact = min(rays, key=lambda row: abs(delta - row[1]))
            error = delta - exact
            if abs(error) <= orb:
                contacts.append({"from_body": carrier, "to_body": target, "aspect": name,
                                 "directed_ray_deg": exact % 360, "orb_deg": abs(error),
                                 "signed_error_deg": error,
                                 "motion": contact_motion(carrier, target, error, speed_values)})
    contacts.sort(key=lambda row: (row["orb_deg"], row["from_body"], row["to_body"]))
    return {
        "recipe": "partner-portrait", "version": VERSION, "partner": partner,
        "settings": {"dignities": "traditional", "phase_rulership": "modern", "orb_deg": orb,
                     "motion_model": "instantaneous_orb_derivative; no future_perfection"},
        "natal": copy.deepcopy(natal), "sect": sect,
        "phase_states": phases, "phase_origin": "natal.phases" if "phases" in natal else "shared_operator",
        "traditional_dignities": compute_dignities(positions, scheme="traditional"),
        "significators": {"luminary": luminary, "desire": desire, "seventh_ruler": seventh["ruler"],
                          "in_seventh": [body for body, lon in positions.items() if house_of(lon, cusps) == 7]},
        "seventh": seventh, "lots": lots,
        "body_subdivisions": {body: subdivisions(lon) for body, lon in positions.items()},
        "contacts": contacts, "motion_input": copy.deepcopy(speeds),
        "unavailable_operators": {"marriage_paulus": "primary formula text not verified in this kit"},
    }


