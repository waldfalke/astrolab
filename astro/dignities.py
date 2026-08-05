"""Essential dignity per body by sign.

Ported from the recipes' Get-EssentialDignities
(lib/mcp_helpers.ps1): domicile / exaltation / detriment / fall / peregrine, resolved in that
precedence order. Scheme "modern" (outers rule Aqu/Pis/Sco; Mars=Aries, Jupiter=Sag, Saturn=Cap
only) or "traditional" (Mars also Scorpio, Jupiter also Pisces, Saturn also Aquarius; no outers).
Consumes the positions element's output; no engine, no I/O.
"""
from __future__ import annotations

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_OPPOSITE = {s: SIGNS[(i + 6) % 12] for i, s in enumerate(SIGNS)}

_DOMICILE = {
    "modern": {
        "sun": ("Leo",), "moon": ("Cancer",), "mercury": ("Gemini", "Virgo"),
        "venus": ("Taurus", "Libra"), "mars": ("Aries",), "jupiter": ("Sagittarius",),
        "saturn": ("Capricorn",), "uranus": ("Aquarius",), "neptune": ("Pisces",),
        "pluto": ("Scorpio",),
    },
    "traditional": {
        "sun": ("Leo",), "moon": ("Cancer",), "mercury": ("Gemini", "Virgo"),
        "venus": ("Taurus", "Libra"), "mars": ("Aries", "Scorpio"),
        "jupiter": ("Sagittarius", "Pisces"), "saturn": ("Capricorn", "Aquarius"),
    },
}

_EXALT = {
    "sun": "Aries", "moon": "Taurus", "mercury": "Virgo", "venus": "Pisces",
    "mars": "Capricorn", "jupiter": "Cancer", "saturn": "Libra",
}
_FALL = {
    "sun": "Libra", "moon": "Scorpio", "mercury": "Pisces", "venus": "Virgo",
    "mars": "Cancer", "jupiter": "Capricorn", "saturn": "Aries",
}


def sign_of(longitude: float) -> str:
    """Zodiac sign (English name) of an ecliptic longitude."""
    return SIGNS[int((longitude % 360.0) // 30.0)]


def compute_dignities(
    longitudes: dict[str, float], scheme: str = "modern"
) -> dict[str, dict[str, str]]:
    """Essential dignity of each body: {body -> {"sign", "dignity"}}.

    Precedence (as in the recipe): domicile > exaltation > detriment > fall > peregrine.
    """
    if scheme not in _DOMICILE:
        raise ValueError("unknown scheme %r (expected 'modern' or 'traditional')" % scheme)
    domicile = _DOMICILE[scheme]
    out: dict[str, dict[str, str]] = {}
    for body, lon in longitudes.items():
        sign = sign_of(lon)
        homes = domicile.get(body, ())
        if sign in homes:
            status = "domicile"
        elif _EXALT.get(body) == sign:
            status = "exaltation"
        elif sign in (_OPPOSITE[h] for h in homes):
            status = "detriment"
        elif _FALL.get(body) == sign:
            status = "fall"
        else:
            status = "peregrine"
        out[body] = {"sign": sign, "dignity": status}
    return out
