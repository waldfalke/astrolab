"""Engine-free conditions over a supplied physical snapshot; hashes identify, not authenticate."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta
import hashlib
from itertools import combinations
import json

from astro.dignities import _longitude, _number, compute_essential_states
from astro.engine import BODY_STATE_COORDINATES
from astro.sect import compute_sect


def compute_carrier_states(natal: dict, body_states: dict) -> dict:
    """Validate supplied coordinates/context before deriving selected-classical-v1 conditions."""
    if not isinstance(natal, dict) or not isinstance(body_states, dict):
        raise ValueError("natal and body_states must be objects")
    try:
        moment = datetime.fromisoformat(natal["moment_utc"].replace("Z", "+00:00"))
        if (moment.tzinfo is None or moment.utcoffset() != timedelta(0)
                or natal["moment_utc"] != body_states["moment_utc"]):
            raise ValueError("snapshot must identify the same UTC moment")
        if (body_states["version"] != "0.1.0"
                or body_states["coordinate_system"] != BODY_STATE_COORDINATES):
            raise ValueError("unsupported physical coordinate system or version")
        provenance = body_states["provenance"]
        if not isinstance(provenance, dict) or not provenance:
            raise ValueError("snapshot provenance is required")
        positions = {b: _longitude(v, "natal longitude") for b, v in natal["positions"].items()}
        physical = body_states["bodies"]
        if not isinstance(physical, dict) or set(positions) != set(physical) or "sun" not in positions:
            raise ValueError("physical body coverage must match natal and include Sun")
        asc = _longitude(natal["houses"]["angles"]["asc"], "ASC")
        sect = natal["sect"]["chart_sect"]
        if compute_sect(positions, asc)["chart_sect"] != sect:
            raise ValueError("natal sect disagrees with Sun/ASC")
        obliquity = body_states["obliquity"]
        for name in ("true_obliquity_deg", "mean_obliquity_deg"):
            if not 0 < _number(obliquity[name], name) < 90:
                raise ValueError("invalid obliquity")
        for body, row in physical.items():
            if (not isinstance(row, dict) or row["id"] != body
                    or not all(isinstance(row[k], str) and row[k].strip() for k in ("name", "model"))):
                raise ValueError("body identity and model are required")
            longitude = _longitude(row["longitude_deg"], "physical longitude")
            if abs((longitude - positions[body] + 180) % 360 - 180) > 1e-7:
                raise ValueError("physical and natal longitudes disagree")
            if not -90 <= _number(row["latitude_deg"], "latitude") <= 90:
                raise ValueError("physical latitude out of range")
            if not -90 <= _number(row["declination_deg"], "declination") <= 90:
                raise ValueError("physical declination out of range")
            if _number(row["distance_au"], "distance") <= 0:
                raise ValueError("physical distance must be positive")
            _number(row["longitude_speed_deg_per_day"], "longitude speed")
        hashes = {name: hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                  separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
                  for name, value in (("natal", natal), ("body_states", body_states))}
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("incomplete or invalid natal/physical state") from exc
    essential = compute_essential_states(positions, sect)
    bodies = {}
    epsilon = obliquity["mean_obliquity_deg"]
    for body, row in physical.items():
        speed = row["longitude_speed_deg_per_day"]
        signed = (positions[body] - positions["sun"] + 180) % 360 - 180
        separation = abs(signed)
        direction = ("conjunction" if signed == 0 else "opposition" if separation == 180 else
                     "east_of_sun" if signed > 0 else "west_of_sun")
        condition = ("not_applicable" if body == "sun" else "cazimi" if separation <= 17 / 60 else
                     "combust" if separation <= 8.5 else "under_beams" if separation <= 17 else "free")
        declination = row["declination_deg"]
        bodies[body] = {
            "motion": {"longitude_speed_deg_per_day": speed,
                       "direction": "direct" if speed > 0 else "retrograde" if speed < 0 else "zero_instantaneous"},
            "solar": {"signed_elongation_deg": signed, "separation_deg": separation,
                      "direction": direction, "condition": condition},
            "declination": {"declination_deg": declination, "oob": abs(declination) > epsilon,
                            "excess_deg": max(0.0, abs(declination) - epsilon),
                            "threshold_deg": epsilon, "threshold_model": "mean_obliquity_of_date"},
            "essential": essential["bodies"][body],
        }
    pairs = []
    for first, second in combinations(sorted(physical), 2):
        a, b = physical[first]["declination_deg"], physical[second]["declination_deg"]
        if (a > 0 and b > 0) or (a < 0 and b < 0) or a == b == 0:
            aspect, orb = "parallel", abs(a - b)
        elif (a > 0 and b < 0) or (a < 0 and b > 0):
            aspect, orb = "contraparallel", abs(a + b)
        else:
            continue
        if orb <= 1.0:
            pairs.append({"body1": first, "body2": second, "aspect": aspect,
                          "orb_deg": orb, "orb_limit_deg": 1.0})
    return {"version": "0.1.0", "profile": essential["profile"], "moment_utc": natal["moment_utc"],
            "input_sha256": hashes, "input_provenance": copy.deepcopy(provenance), "bodies": bodies,
            "tables": essential["tables"], "dignity_holdings": essential["dignity_holdings"],
            "declination_aspects": pairs,
            "availability": {"physical_conditions": "derived_from_supplied_snapshot",
                             **{key: "not_calculated" for key in (
                                 "future_perfection", "station_events", "heliacal_visibility",
                                 "acceleration", "historical_relative_speed", "fixed_stars", "antiscia")}}}
