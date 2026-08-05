"""Golden and table tests for essential dignities.

Fixture provenance: the recipe function
Get-EssentialDignities (lib/mcp_helpers.ps1) was RUN over the Trump fixture's
`02_primary_longitudes.csv` (pwsh, 2026-07-03) and its output embedded below. The Trump chart is
dignity-poor (one detriment, rest peregrine), so table coverage comes from synthetic unit cases
exercising every dignity class and the modern/traditional scheme fork.
"""
import csv
from pathlib import Path

from astro.dignities import compute_dignities, sign_of

_LONGITUDES_CSV = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "trump" / "natal_failover" / "02_primary_longitudes.csv"
)

# Witnessed output of Get-EssentialDignities -Scheme modern on the fixture longitudes.
# (traditional gives the identical table on this chart — no outer/extra-home sign is occupied.)
GOLDEN_DIGNITIES = {
    "sun": ("Gemini", "peregrine"),
    "moon": ("Sagittarius", "peregrine"),
    "mercury": ("Cancer", "peregrine"),
    "venus": ("Cancer", "peregrine"),
    "mars": ("Leo", "peregrine"),
    "jupiter": ("Libra", "peregrine"),
    "saturn": ("Cancer", "detriment"),
    "uranus": ("Gemini", "peregrine"),
    "neptune": ("Libra", "peregrine"),
    "pluto": ("Leo", "peregrine"),
}


def _mid(sign_index: int) -> float:
    return sign_index * 30.0 + 15.0


def test_fixture_matches_recipe_witnessed_golden():
    with _LONGITUDES_CSV.open(encoding="utf-8-sig", newline="") as f:
        longitudes = {row["body"]: float(row["longitude"]) for row in csv.DictReader(f)}
    for scheme in ("modern", "traditional"):
        got = compute_dignities(longitudes, scheme=scheme)
        for body, (sign, dignity) in GOLDEN_DIGNITIES.items():
            assert got[body]["sign"] == sign, (scheme, body)
            assert got[body]["dignity"] == dignity, (scheme, body)


def test_dignity_classes_and_scheme_fork():
    # Leo=4, Taurus=1, Cancer=3, Scorpio=7, Aquarius=10, Libra=6
    cases_modern = {
        "sun": (_mid(4), "domicile"),      # Sun in Leo
        "moon": (_mid(1), "exaltation"),   # Moon in Taurus
        "mars": (_mid(3), "fall"),         # Mars in Cancer
        "venus": (_mid(7), "detriment"),   # Venus in Scorpio (opp. Taurus)
        "uranus": (_mid(10), "domicile"),  # modern: Uranus rules Aquarius
    }
    got = compute_dignities({b: lon for b, (lon, _) in cases_modern.items()}, scheme="modern")
    for body, (_, dignity) in cases_modern.items():
        assert got[body]["dignity"] == dignity, body

    # Scheme fork: Scorpio/Aquarius change hands between schemes.
    trad = compute_dignities(
        {"mars": _mid(7), "saturn": _mid(10), "uranus": _mid(10)}, scheme="traditional"
    )
    assert trad["mars"]["dignity"] == "domicile"      # traditional: Mars rules Scorpio
    assert trad["saturn"]["dignity"] == "domicile"    # traditional: Saturn rules Aquarius
    assert trad["uranus"]["dignity"] == "peregrine"   # no outers in the traditional scheme
    mod = compute_dignities({"mars": _mid(7), "saturn": _mid(10)}, scheme="modern")
    assert mod["mars"]["dignity"] == "peregrine"      # modern Mars home is Aries only...
    assert mod["saturn"]["dignity"] == "peregrine"    # ...and Saturn's is Capricorn only


def test_sign_of_boundaries():
    assert sign_of(0.0) == "Aries"
    assert sign_of(29.999) == "Aries"
    assert sign_of(30.0) == "Taurus"
    assert sign_of(359.999) == "Pisces"
    assert sign_of(360.0) == "Aries"
    assert sign_of(-1.0) == "Pisces"
