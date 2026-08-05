"""Tests for the solar-return composite (money-triad piece 2; recipe = run_solar_revolution.ps1).

Layers:
  1. Pure math — cross-aspects element (directed, endpoints never sorted).
  2. Self-validating property — the Sun at the found instant EQUALS the natal Sun longitude
     (the defining property of a solar return; no external golden needed).
  3. Recipe golden — instant + SR chart values witnessed by RUNNING run_solar_revolution.ps1 on
     the public Trump fixture (values in test_solar_golden.py, added after the witnessed run).

Engine note: property tests run on the default engine; engine A reproduces B1 strictly (Stage 1),
so they are container-independent when SWISS_ENGINE=a.
"""
from datetime import datetime, timezone

from astro.aspects import compute_cross_aspects
from astro.solar import compute_solar_return, find_solar_return_instant

NATAL_MOMENT = datetime(1946, 6, 14, 14, 54, 0, tzinfo=timezone.utc)
BIRTH_LAT, BIRTH_LON = 40.7, -73.8164
NATAL_SUN = 82.9284020277778  # planets_primary.csv golden

# Sun moves ~0.0000115 deg/s; bisection early-exit 5e-5 deg + 1 s truncation => < 7e-5 deg.
SUN_RETURN_TOL_DEG = 7e-5


def test_cross_aspects_directed_pure_math():
    hits = compute_cross_aspects({"saturn": 10.0}, {"moon": 100.5, "sun": 255.0}, orb=2.0)
    assert len(hits) == 1
    h = hits[0]
    assert (h["from_body"], h["to_body"], h["aspect"]) == ("saturn", "moon", "square")
    assert abs(h["orb"] - 0.5) < 1e-12
    # direction is meaning-bearing: swapping charts swaps the endpoints, not just labels
    swapped = compute_cross_aspects({"moon": 100.5}, {"saturn": 10.0}, orb=2.0)
    assert (swapped[0]["from_body"], swapped[0]["to_body"]) == ("moon", "saturn")


def test_return_instant_self_property():
    """Defining property of a solar return: transiting Sun at the found instant == natal Sun."""
    from astro.engine import compute_positions_series

    instant = find_solar_return_instant(NATAL_MOMENT, BIRTH_LAT, BIRTH_LON, 2025)
    assert instant.year == 2025 and instant.month == 6  # near the birthday
    sun = compute_positions_series([instant], BIRTH_LAT, BIRTH_LON, bodies=["sun"])[0]["sun"]
    d = abs(sun - NATAL_SUN)
    d = 360.0 - d if d > 180.0 else d
    assert d < SUN_RETURN_TOL_DEG


def test_solar_return_composite_structure():
    chart = compute_solar_return(NATAL_MOMENT, BIRTH_LAT, BIRTH_LON, 2025)
    assert chart["location"] == {"lat": BIRTH_LAT, "lon": BIRTH_LON, "relocated": False}
    ret = chart["return"]
    assert len(ret["houses"]["cusps"]) == 12
    assert set(ret["placements"].values()) <= set(range(1, 13))
    assert ret["sect"]["chart_sect"] in ("day", "night")
    # profection golden (recipe-witnessed in test_profection): age 79 -> Pisces/jupiter
    assert chart["profection"]["age_years"] == 79
    assert chart["profection"]["profected_sign"] == "Pisces"
    assert chart["profection"]["lord_of_year"] == "jupiter"
    assert chart["profection"]["lord_natal"] == {"sign": "Libra", "wholesign_house": 3}
    # aspects are directed return->natal over the classical 10, orb 2
    for a in chart["sr_to_natal_aspects"]:
        assert a["orb"] <= 2.0


def test_solar_return_matches_recipe_golden():
    """Witnessed golden (run_solar_revolution.ps1 on the public fixture, ReturnYear 2025, run
    solar_return_trump_sr2025_20260703_230939): the port converges with the PS recipe TO THE
    SECOND on the instant and to 1e-6 on positions/cusps/orbs — same bisection semantics, same
    engine numbers (A==B1 by Stage 1)."""
    chart = compute_solar_return(NATAL_MOMENT, BIRTH_LAT, BIRTH_LON, 2025)
    assert chart["return_instant_utc"] == "2025-06-13T16:57:23Z"
    pos, houses = chart["return"]["positions"], chart["return"]["houses"]
    assert abs(pos["jupiter"] - 90.87001844444444) < 1e-6
    assert abs(pos["mars"] - 147.96715922222222) < 1e-6
    assert abs(pos["mercury"] - 99.22847725) < 1e-6
    assert abs(houses["cusps"][0] - 174.27429975) < 1e-4
    assert abs(houses["cusps"][1] - 199.82543116666668) < 1e-4
    by_key = {
        (a["from_body"], a["to_body"], a["aspect"]): a["orb"]
        for a in chart["sr_to_natal_aspects"]
    }
    assert abs(by_key[("mercury", "mercury", "conjunction")] - 0.369443) < 1e-5
    assert abs(by_key[("mars", "mars", "conjunction")] - 1.191215) < 1e-5
    assert abs(by_key[("venus", "mercury", "sextile")] - 1.259897) < 1e-5
    assert abs(by_key[("sun", "moon", "opposition")] - 1.724582) < 1e-5


def test_relocation_changes_houses_not_positions():
    """Relocation (Seattle vs birth NYC) changes the house frame, never the planet longitudes."""
    home = compute_solar_return(NATAL_MOMENT, BIRTH_LAT, BIRTH_LON, 2025)
    away = compute_solar_return(
        NATAL_MOMENT, BIRTH_LAT, BIRTH_LON, 2025, sr_lat=47.6062, sr_lon=-122.3321
    )
    assert away["location"]["relocated"] is True
    assert away["return_instant_utc"] == home["return_instant_utc"]
    for b, lon in home["return"]["positions"].items():
        assert abs(away["return"]["positions"][b] - lon) < 1e-9, b
    assert abs(away["return"]["houses"]["angles"]["asc"]
               - home["return"]["houses"]["angles"]["asc"]) > 1.0
