"""Golden tests for annual profection.

Fixture provenance: Get-AnnualProfection
(lib/mcp_helpers.ps1) was RUN via pwsh (2026-07-03) on the Trump fixture's golden ASC
(149.958846361111, Leo rising) for ages 0/1/7/12/79/100; output embedded below. The lord-location
helper is checked against the SR recipe's whole-sign arithmetic (sign-index difference from the
ASC sign, 1-based).
"""
from astro.profection import compute_profection, locate_wholesign

GOLDEN_ASC = 149.958846361111  # Leo

# (age -> step, house, sign, lord) witnessed from the recipe function.
GOLDEN_PROFECTIONS = {
    0: (0, 1, "Leo", "sun"),
    1: (1, 2, "Virgo", "mercury"),
    7: (7, 8, "Pisces", "jupiter"),
    12: (0, 1, "Leo", "sun"),
    79: (7, 8, "Pisces", "jupiter"),
    100: (4, 5, "Sagittarius", "jupiter"),
}


def test_profection_matches_recipe_witnessed_golden():
    for age, (step, house, sign, lord) in GOLDEN_PROFECTIONS.items():
        got = compute_profection(GOLDEN_ASC, age)
        assert got["profection_step"] == step, age
        assert got["profected_house"] == house, age
        assert got["profected_sign"] == sign, age
        assert got["lord_of_year"] == lord, age
        assert got["asc_sign"] == "Leo", age


def test_locate_wholesign_from_asc():
    # Trump fixture: Jupiter 197.45 (Libra), ASC Leo -> whole-sign house 3 (Leo=1, Virgo=2, Libra=3)
    got = locate_wholesign(197.452071888889, GOLDEN_ASC)
    assert got == {"sign": "Libra", "wholesign_house": 3}
    # wrap: Cancer body with Leo ASC -> 12th whole-sign house
    got = locate_wholesign(98.86, GOLDEN_ASC)
    assert got == {"sign": "Cancer", "wholesign_house": 12}
