"""Golden and unit tests for sect and house placements.

Sect fixture provenance: Get-Sect (lib/mcp_helpers.ps1) was
RUN via pwsh over the Trump fixture's `02_primary_longitudes.csv` with the golden ASC
(2026-07-03); its output is embedded below. PoF golden is the swiss payload's own
`additional_points["Part of Fortune"]` (05_additional_points.csv) — a DAY chart, so the night
branch is covered by a unit case, not a fixture.

PLACEMENTS golden: no fixture CSV carries a house column, so the table below is hand-derived from
the golden cusps + longitudes (each row checkable by inspection) and agrees with the commonly
cited placements of this public chart (Sun 10th, Moon 4th, Mars 12th, Jupiter/Neptune 2nd).
"""
import csv
from pathlib import Path

import pytest

from astro.placements import compute_placements, house_of
from astro.sect import compute_part_of_fortune, compute_sect, signed_delta_deg

_LONGITUDES_CSV = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "trump" / "natal_failover" / "02_primary_longitudes.csv"
)

GOLDEN_ASC = 149.958846361111
GOLDEN_CUSPS = [
    149.958846361111, 173.004190666667, 201.199416194444, 234.35059875,
    269.341986166667, 301.743358972222, 329.958846361111, 353.004190666667,
    21.1994161944444, 54.35059875, 89.3419861666667, 121.743358972222,
]
# 05_additional_points.csv "Part of Fortune" (swiss payload's own derived point; day chart).
GOLDEN_POF = 328.23425852777774

# Witnessed Get-Sect output (chart_sect=day, sun_above_horizon=true, mercury_team=nocturnal).
GOLDEN_SECT_BODIES = {
    "sun": ("diurnal", True, "in_sect", "sect_light"),
    "moon": ("nocturnal", False, "out_of_sect", "luminary_out_of_sect"),
    "mercury": ("nocturnal", True, "out_of_sect", "neutral"),
    "venus": ("nocturnal", True, "out_of_sect", "benefic_contrary"),
    "mars": ("nocturnal", True, "out_of_sect", "malefic_contrary"),
    "jupiter": ("diurnal", False, "in_sect", "benefic_of_sect"),
    "saturn": ("diurnal", True, "in_sect", "malefic_of_sect"),
    "uranus": ("none", True, "n/a", "outer"),
    "neptune": ("none", False, "n/a", "outer"),
    "pluto": ("none", True, "n/a", "outer"),
}

# Hand-derived from GOLDEN_CUSPS + fixture longitudes; matches the chart's well-known placements.
GOLDEN_PLACEMENTS = {
    "sun": 10, "moon": 4, "mercury": 11, "venus": 11, "mars": 12, "jupiter": 2,
    "saturn": 11, "uranus": 10, "neptune": 2, "pluto": 12,
}


def _fixture_longitudes() -> dict[str, float]:
    with _LONGITUDES_CSV.open(encoding="utf-8-sig", newline="") as f:
        return {row["body"]: float(row["longitude"]) for row in csv.DictReader(f)}


def test_sect_matches_recipe_witnessed_golden():
    sect = compute_sect(_fixture_longitudes(), GOLDEN_ASC)
    assert sect["chart_sect"] == "day"
    assert sect["sun_above_horizon"] is True
    assert sect["mercury_team"] == "nocturnal"
    for body, (team, above, placement, role) in GOLDEN_SECT_BODIES.items():
        got = sect["bodies"][body]
        assert got["planet_team"] == team, body
        assert got["above_horizon"] is above, body
        assert got["placement"] == placement, body
        assert got["role"] == role, body


def test_night_chart_flips_roles_and_mercury_wrap():
    # Sun below the horizon (offset < 180 from ASC) -> night chart; Mercury just behind the Sun
    # across the 0-Aries wrap -> negative signed delta -> oriental -> diurnal.
    sect = compute_sect({"sun": 1.0, "mercury": 358.0, "moon": 10.0, "mars": 20.0}, asc=350.0)
    assert sect["chart_sect"] == "night"
    assert signed_delta_deg(1.0, 358.0) == -3.0
    assert sect["mercury_team"] == "diurnal"
    assert sect["bodies"]["moon"]["role"] == "sect_light"
    assert sect["bodies"]["mars"]["role"] == "malefic_of_sect"
    assert sect["bodies"]["mercury"]["placement"] == "out_of_sect"


def test_part_of_fortune_day_golden_and_night_flip():
    longitudes = _fixture_longitudes()
    pof = compute_part_of_fortune(
        GOLDEN_ASC, longitudes["sun"], longitudes["moon"], chart_sect="day"
    )
    assert abs(pof - GOLDEN_POF) < 1e-6
    # night formula is the reflection of the day one around the ASC
    night = compute_part_of_fortune(GOLDEN_ASC, longitudes["sun"], longitudes["moon"], "night")
    assert abs((pof - GOLDEN_ASC) % 360.0 + (night - GOLDEN_ASC) % 360.0 - 360.0) < 1e-9
    with pytest.raises(ValueError):
        compute_part_of_fortune(0.0, 0.0, 0.0, "dusk")


def test_placements_match_hand_derived_golden():
    got = compute_placements(_fixture_longitudes(), GOLDEN_CUSPS)
    assert got == GOLDEN_PLACEMENTS


def test_house_of_edges():
    cusps = [float(i * 30) for i in range(12)]  # whole-sign-like frame starting at 0 Aries
    assert house_of(0.0, cusps) == 1          # cusp-exact belongs to the house it opens
    assert house_of(29.999, cusps) == 1
    assert house_of(359.999, cusps) == 12
    # frame that wraps 0 Aries mid-house
    wrapped = [(340.0 + i * 30.0) % 360.0 for i in range(12)]
    assert house_of(350.0, wrapped) == 1
    assert house_of(5.0, wrapped) == 1
    assert house_of(15.0, wrapped) == 2
