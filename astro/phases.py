"""Zakharian body states, ported from run_phase_vectors.ps1 v0.2.0.

Z uses the modern domicile cycle. H/h are a project extrapolation onto the
actual cusp frame; an equal-ASC frame is available only when explicitly asked.
The model's dignity is reported separately from the natal engine's dignity.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime


OPERATOR_VERSION = "0.2.0"

_SIGN_NAMES = (
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион",
    "Стрелец", "Козерог", "Водолей", "Рыбы",
)
_DOMICILE = {
    "sun": (5,), "moon": (4,), "mercury": (3, 6), "venus": (2, 7),
    "mars": (1,), "jupiter": (9,), "saturn": (10,), "uranus": (11,),
    "neptune": (12,), "pluto": (8,),
}
_SIGN_RULER = (
    "mars", "venus", "mercury", "moon", "sun", "mercury", "venus",
    "pluto", "jupiter", "saturn", "uranus", "neptune",
)
_PHASE_NAME = (
    "Импульс", "Ресурс", "Связь", "База", "Творчество", "Служение",
    "Зеркало", "Трансформация", "Стратегия", "Результат", "Оптимизация", "Архив",
)
_PHASE_RULER = (
    "Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий",
    "Венера", "Плутон", "Юпитер", "Сатурн", "Уран", "Нептун",
)
_EXALT = (
    "sun", "moon", "", "jupiter", "pluto", "uranus", "saturn",
    "neptune", "", "mars", "mercury", "venus",
)
_FALL = (
    "saturn", "neptune", "", "mars", "mercury", "venus", "sun",
    "moon", "", "jupiter", "pluto", "uranus",
)


def _longitude(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a numeric longitude")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    normalized = number % 360.0
    # A negative subnormal is mathematically just below 360°, but float modulo
    # rounds it to 360.0; keep it in the final sign instead of indexing sign 13.
    if normalized == 360.0:
        return math.nextafter(360.0, 0.0)
    return normalized


def _phase(point_index: int, anchor_index: int) -> int:
    return (point_index - anchor_index) % 12 + 1


def _micro(offset: float, step: float) -> int:
    return max(1, min(12, math.floor(offset / step) + 1))


def _dignity(body: str, sign_index: int) -> str:
    if _SIGN_RULER[sign_index - 1] == body:
        return "домицил"
    if _SIGN_RULER[(sign_index + 5) % 12] == body:
        return "изгнание"
    if _EXALT[sign_index - 1] == body:
        return "экзальтация"
    if _FALL[sign_index - 1] == body:
        return "падение"
    return "перегрин"


def _validated_cusps(cusps: Sequence[float]) -> tuple[float, ...]:
    if len(cusps) != 12:
        raise ValueError("house frame requires 12 cusps")
    values = tuple(_longitude(lon, f"cusp {i}") for i, lon in enumerate(cusps, 1))
    spans = tuple((values[(i + 1) % 12] - values[i]) % 360 for i in range(12))
    if any(span == 0 for span in spans) or not math.isclose(sum(spans), 360.0, abs_tol=1e-6):
        raise ValueError("12 cusps must be distinct, ordered, and cover 360 degrees")
    return values


def _house(longitude: float, cusps: tuple[float, ...]) -> tuple[int, float, float]:
    for i, start in enumerate(cusps):
        end = cusps[(i + 1) % 12]
        contains = ((start <= longitude < end) if start < end else
                    (longitude >= start or longitude < end))
        if contains:
            span = (end - start) % 360
            offset = longitude - start if longitude >= start else longitude + 360.0 - start
            return i + 1, offset, span
    raise ValueError("longitude does not fall in the supplied house frame")


def compute_phase_states(
    positions: Mapping[str, float], *, cusps: Sequence[float] | None = None,
    asc_longitude: float | None = None, moment_utc: str | None = None,
) -> dict:
    """Compute states for any body subset, with explicit frame and input provenance.

    Unsupported bodies retain a row with unavailable Z rather than an invented domicile.
    Missing dispositors leave D unavailable. Without cusps or explicit ASC, H/h are unavailable.
    """
    if cusps is not None and asc_longitude is not None:
        raise ValueError("choose either real cusps or an explicit equal-house ASC")
    if moment_utc is not None:
        if not isinstance(moment_utc, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", moment_utc
        ):
            raise ValueError("moment_utc must be an exact UTC instant")
        try:
            datetime.fromisoformat(moment_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("moment_utc is invalid") from exc
    frame_cusps = _validated_cusps(cusps) if cusps is not None else None
    asc = _longitude(asc_longitude, "asc_longitude") if asc_longitude is not None else None
    frame = "placidus" if frame_cusps is not None else ("equal_asc" if asc is not None else "unavailable")
    normalized = {body: _longitude(lon, f"position {body}") for body, lon in positions.items()}
    canonical_input = {
        "operator_version": OPERATOR_VERSION,
        "moment_utc": moment_utc,
        "house_frame": frame,
        "positions": normalized,
        "cusps": frame_cusps,
        "asc_longitude": asc,
    }
    input_bytes = json.dumps(canonical_input, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    states = {}
    for body, longitude in normalized.items():
        sign_index = math.floor(longitude / 30.0) + 1
        deg_in_sign = longitude - (sign_index - 1) * 30.0
        if body not in _DOMICILE:
            states[body] = {
                "body": body, "longitude": longitude,
                "sign": _SIGN_NAMES[sign_index - 1],
                "deg_in_sign": deg_in_sign,
                "dignity_zakharian": None,
                "ruler_by_position": None, "ruler_by_phase": None,
                "Z": None, "Z_phase_name": None,
                "z_micro": None, "z_micro_name": None,
                "H_house": None, "H_phase_name": None,
                "h_micro": None, "h_micro_name": None,
                "D_pos_ruler_sign": None, "D_pos_ruler_phase": None,
                "D_pos_ruler_phasename": None,
                "vector": None, "house_frame": frame, "tier": None,
                "availability": {"Z": "unsupported_body", "z": "unsupported_body",
                                 "H": "unsupported_body", "h": "unsupported_body",
                                 "D": "unsupported_body"},
            }
            continue

        z_phases = [_phase(sign_index, home) for home in _DOMICILE[body]]
        z = _micro(deg_in_sign, 2.5)
        house, h = None, None
        if frame_cusps is not None:
            house, offset, span = _house(longitude, frame_cusps)
            h = max(1, min(12, math.floor(12.0 * offset / span) + 1))
        elif asc is not None:
            offset = _longitude(longitude - asc, "offset from ASC")
            house = math.floor(offset / 30.0) + 1
            h = _micro(offset - math.floor(offset / 30.0) * 30.0, 2.5)

        ruler = _SIGN_RULER[sign_index - 1]
        ruler_sign = None
        d_phase = None
        if ruler in normalized:
            ruler_sign_index = math.floor(normalized[ruler] / 30.0) + 1
            ruler_sign = _SIGN_NAMES[ruler_sign_index - 1]
            d_phase = min(
                (_phase(ruler_sign_index, home) for home in _DOMICILE[ruler]),
                key=lambda phase: phase - 1,
            )
        z_text = "/".join(map(str, z_phases))
        vector = (f"P<{z_text}.{z} : {house}.{h} : {d_phase}>"
                  if house is not None and d_phase is not None else None)
        states[body] = {
            "body": body,
            "longitude": longitude,
            "sign": _SIGN_NAMES[sign_index - 1],
            "deg_in_sign": deg_in_sign,
            "dignity_zakharian": _dignity(body, sign_index),
            "ruler_by_position": ruler,
            "ruler_by_phase": "/".join(_PHASE_RULER[phase - 1] for phase in z_phases),
            "Z": z_text,
            "Z_phase_name": "/".join(_PHASE_NAME[phase - 1] for phase in z_phases),
            "z_micro": z,
            "z_micro_name": _PHASE_NAME[z - 1],
            "H_house": house,
            "H_phase_name": _PHASE_NAME[house - 1] if house is not None else None,
            "h_micro": h,
            "h_micro_name": _PHASE_NAME[h - 1] if h is not None else None,
            "D_pos_ruler_sign": ruler_sign,
            "D_pos_ruler_phase": d_phase,
            "D_pos_ruler_phasename": _PHASE_NAME[d_phase - 1] if d_phase is not None else None,
            "vector": vector,
            "house_frame": frame,
            "tier": ("Z,достоинство=grounded(book); z,D=anumita(attested); "
                     f"H,h=extrapolation({frame})"),
            "availability": {
                "Z": "computed", "z": "computed",
                "H": "computed" if house is not None else "no_house_frame",
                "h": "computed" if h is not None else "no_house_frame",
                "D": "computed" if d_phase is not None else f"missing_dispositor:{ruler}",
            },
        }
    return {
        "operator_version": OPERATOR_VERSION,
        "rulership": "modern",
        "moment_utc": moment_utc,
        "house_frame": frame,
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "input": canonical_input,
        "states": states,
    }


def main() -> int:
    """One stdin/stdout JSON batch for non-Python recipe adapters."""
    request = json.load(sys.stdin)
    if not isinstance(request, dict) or not isinstance(request.get("batch"), list):
        raise ValueError("expected a JSON object with a batch list")
    results = [compute_phase_states(**item) for item in request["batch"]]
    json.dump({"results": results}, sys.stdout, ensure_ascii=True, allow_nan=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
