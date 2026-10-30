"""Essential dignity per body by sign.

Ported from the recipes' Get-EssentialDignities
(lib/mcp_helpers.ps1): domicile / exaltation / detriment / fall / peregrine, resolved in that
precedence order. Scheme "modern" (outers rule Aqu/Pis/Sco; Mars=Aries, Jupiter=Sag, Saturn=Cap
only) or "traditional" (Mars also Scorpio, Jupiter also Pisces, Saturn also Aquarius; no outers).
Consumes the positions element's output; no engine, no I/O.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

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


# Shared classical subdivision operators; original Egyptian/Firmicus values retained.
RULERS = ("mars", "venus", "mercury", "moon", "sun", "mercury",
          "venus", "mars", "jupiter", "saturn", "saturn", "jupiter")
CLASSICAL = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
FIRMICUS = "https://penelope.uchicago.edu/Thayer/L/Roman/Texts/Firmicus_Maternus/Mathesis/2%2A.html"
PTOLEMY = "https://www.gutenberg.org/files/70850/70850-h/70850-h.htm"

# Egyptian terms as printed in Ashmand's Ptolemy I.23, not Firmicus's variant table.
TERMS = (
    ((6, "jupiter"), (12, "venus"), (20, "mercury"), (25, "mars"), (30, "saturn")),
    ((8, "venus"), (14, "mercury"), (22, "jupiter"), (27, "saturn"), (30, "mars")),
    ((6, "mercury"), (12, "jupiter"), (17, "venus"), (24, "mars"), (30, "saturn")),
    ((7, "mars"), (13, "venus"), (19, "mercury"), (26, "jupiter"), (30, "saturn")),
    ((6, "jupiter"), (11, "venus"), (18, "saturn"), (24, "mercury"), (30, "mars")),
    ((7, "mercury"), (17, "venus"), (21, "jupiter"), (28, "mars"), (30, "saturn")),
    ((6, "saturn"), (14, "mercury"), (21, "jupiter"), (28, "venus"), (30, "mars")),
    ((7, "mars"), (11, "venus"), (19, "mercury"), (24, "jupiter"), (30, "saturn")),
    ((12, "jupiter"), (17, "venus"), (21, "mercury"), (26, "saturn"), (30, "mars")),
    ((7, "mercury"), (14, "jupiter"), (22, "venus"), (26, "saturn"), (30, "mars")),
    ((7, "mercury"), (13, "venus"), (20, "jupiter"), (25, "mars"), (30, "saturn")),
    ((12, "venus"), (16, "jupiter"), (19, "mercury"), (28, "mars"), (30, "saturn")),
)
DECAN_CYCLE = ("mars", "sun", "venus", "mercury", "moon", "saturn", "jupiter")


def _number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _longitude(value, label: str) -> float:
    value = _number(value, label)
    if not 0 <= value < 360:
        raise ValueError(f"{label} must be in [0,360)")
    return value


def subdivisions(longitude: float) -> dict:
    """Half-open intervals; Firmicus II.13's 12x dodecatemorion, not a 13x variant."""
    longitude = _longitude(longitude, "longitude")
    sign = int(longitude // 30)
    degree = longitude - sign * 30
    start = 0
    for end, ruler in TERMS[sign]:
        if degree < end:
            term = {"ruler": ruler, "start_degree": start, "end_degree": end,
                    "source": f"Ptolemy I.23 (Egyptian table, Ashmand): {PTOLEMY}"}
            break
        start = end
    dodec = (sign * 30 + 12 * degree) % 360
    dodec_sign = int(dodec // 30)
    return {
        "term": term,
        "decan": {"number": int(degree // 10) + 1,
                  "ruler": DECAN_CYCLE[int(longitude // 10) % 7],
                  "source": f"Firmicus II.4.3: {FIRMICUS}"},
        "dodecatemorion": {"longitude": dodec, "sign": SIGNS[dodec_sign],
                           "ruler": RULERS[dodec_sign],
                           "phase_carrier": RULERS[dodec_sign],
                           "formula": "sign_start + 12 * degree_in_sign (mod 360)",
                           "source": f"Firmicus II.13.2-3: {FIRMICUS}"},
    }


_TRIPLICITY = (("sun", "jupiter"), ("venus", "moon"),
               ("saturn", "mercury"), ("mars", "mars"))
LILLY = "https://maestrosdelsaber.com/wp-content/uploads/ftp-files/Astrologia/Astro%20y%20Religion/Astro%20Lilly,%20William%20-%20Christian%20Astrology%20Vol%201%201647.pdf#page=125"


def compute_essential_states(longitudes: dict[str, float], chart_sect: str) -> dict:
    """Compatible classical conditions and directed holdings, without a reception verdict."""
    if chart_sect not in ("day", "night"):
        raise ValueError("chart_sect must be day or night")
    if not isinstance(longitudes, dict) or not longitudes or any(
        not isinstance(body, str) or re.fullmatch(r"[a-z][a-z0-9_]*", body) is None
        for body in longitudes
    ):
        raise ValueError("longitudes require normalized body IDs")
    tables = {}
    for name, identity, source, values in (
        ("domicile", "traditional_domiciles", PTOLEMY, _DOMICILE["traditional"]),
        ("exaltation", "classical_exaltation_fall", PTOLEMY, (_EXALT, _FALL)),
        ("triplicity", "lilly_ptolemaic_day_night_no_participant", LILLY, _TRIPLICITY),
        ("term", "egyptian_ashmand_ptolemy_i23", PTOLEMY, TERMS),
        ("face", "firmicus_ii4_3_chaldean", FIRMICUS, DECAN_CYCLE),
    ):
        raw = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
        tables[name] = {"id": identity, "source": source, "sha256": hashlib.sha256(raw).hexdigest()}
    bodies, holdings = {}, []
    for body, value in longitudes.items():
        longitude = _longitude(value, "longitude %s" % body)
        sign = int(longitude // 30)
        if body not in CLASSICAL:
            bodies[body] = {"sign": SIGNS[sign], "availability": "unsupported_traditional_body",
                            "dignities": [], "debilities": [], "peregrine": None, "owners": {}}
            continue
        division = subdivisions(longitude)
        owners = {
            "domicile": RULERS[sign],
            "exaltation": next((b for b, s in _EXALT.items() if s == SIGNS[sign]), None),
            "triplicity": _TRIPLICITY[sign % 4][chart_sect == "night"],
            "term": division["term"]["ruler"], "face": division["decan"]["ruler"],
            "detriment": RULERS[(sign + 6) % 12],
            "fall": next((b for b, s in _FALL.items() if s == SIGNS[sign]), None),
        }
        positive = ("domicile", "exaltation", "triplicity", "term", "face")
        negative = ("detriment", "fall")
        own = [kind for kind in positive if owners[kind] == body]
        bodies[body] = {"sign": SIGNS[sign], "availability": "available", "owners": owners,
                        "dignities": own, "debilities": [k for k in negative if owners[k] == body],
                        "peregrine": not own}
        for host in CLASSICAL:
            if host == body:
                continue
            dignities = [kind for kind in positive if owners[kind] == host]
            debilities = [kind for kind in negative if owners[kind] == host]
            if dignities or debilities:
                holdings.append({"guest": body, "host": host, "dignities": dignities,
                                 "debilities": debilities,
                                 "direction": "guest_in_host_dignities"})
    return {"profile": "selected-classical-v1", "chart_sect": chart_sect, "tables": tables,
            "bodies": bodies, "dignity_holdings": holdings}


