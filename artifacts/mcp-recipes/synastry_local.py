"""Private exact-time synastry calculation bundle using the local Swiss engine.

This is a pilot recipe, not a chart-project or report-kit implementation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from astro.aspects import compute_cross_aspects
from astro.dignities import sign_of
from astro.engine import DEFAULT_BODIES, _SWE_RUNTIME_FILES, _swe_body_consts, _init_swe
from astro.natal import compute_natal
from astro.placements import house_of
from astro.phases import compute_phase_states

ANGLES = ("asc", "mc", "ic", "dsc")
PRIVATE_ROOT = REPO / ".private"
UTC_EXACT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CODE_FILES = ("astro/natal.py", "astro/phases.py", "astro/engine.py", "astro/aspects.py",
              "astro/placements.py", "astro/dignities.py", "astro/sect.py",
              "artifacts/mcp-recipes/synastry_local.py")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_longitude(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a numeric longitude")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number < 360:
        raise ValueError(f"{label} must be finite in [0,360)")
    return number


def validate_input(data: dict) -> dict[str, dict]:
    """Require exactly two distinct identities, exact UTC instants and valid coordinates."""
    if not isinstance(data, dict) or set(data) != {"participants"}:
        raise ValueError("input must contain only participants")
    people = data["participants"]
    if not isinstance(people, dict) or set(people) != {"A", "B"}:
        raise ValueError("participants must contain exactly A and B")
    result = {}
    for slot in ("A", "B"):
        person = people[slot]
        if not isinstance(person, dict) or set(person) != {
                "id", "datetime_utc", "latitude", "longitude"}:
            raise ValueError(f"{slot} requires id, datetime_utc, latitude, longitude")
        identity = person["id"]
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", identity):
            raise ValueError(f"{slot} id must use letters, digits, underscore or hyphen")
        instant = person["datetime_utc"]
        if not isinstance(instant, str) or not UTC_EXACT.fullmatch(instant):
            raise ValueError(f"{slot} datetime_utc must have seconds and a Z suffix")
        try:
            moment = datetime.fromisoformat(instant.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{slot} datetime_utc is invalid") from exc
        if moment.tzinfo != timezone.utc:
            raise ValueError(f"{slot} datetime_utc must be UTC")
        for field, limit in (("latitude", 90), ("longitude", 180)):
            number = person[field]
            if isinstance(number, bool) or not isinstance(number, (int, float)) or (
                    not math.isfinite(number)) or not -limit <= number <= limit:
                raise ValueError(f"{slot} {field} must be finite in [-{limit},{limit}]")
        result[slot] = {**person, "moment": moment}
    if result["A"]["id"] == result["B"]["id"]:
        raise ValueError("participant IDs must be distinct")
    return result


def validate_paths(source: Path, target: Path, private_root: Path | None = None) -> None:
    root = (private_root or PRIVATE_ROOT).resolve()
    input_path, output_path = source.resolve(), target.resolve()
    if not input_path.is_relative_to(root) or not input_path.is_file():
        raise ValueError("input must be an existing file beneath .private")
    if not output_path.is_relative_to(root) or output_path == root:
        raise ValueError("output must be a new directory beneath .private")
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"output already exists: {target}")


def validate_natal(natal: dict) -> None:
    """Reject incomplete or invalid frames before accepting any report input."""
    try:
        positions = natal["positions"]
        houses = natal["houses"]
        cusps = houses["cusps"]
        angles = houses["angles"]
    except (KeyError, TypeError) as exc:
        raise ValueError("natal requires positions, cusps and angles") from exc
    if not isinstance(positions, dict) or set(positions) != set(DEFAULT_BODIES):
        raise ValueError("natal must have exactly the ten default bodies")
    for name, longitude in positions.items():
        _finite_longitude(longitude, f"position {name}")
    if not isinstance(cusps, (list, tuple)) or len(cusps) != 12:
        raise ValueError("natal must have 12 cusps")
    for index, longitude in enumerate(cusps, start=1):
        _finite_longitude(longitude, f"cusp {index}")
    spans = [(cusps[(i + 1) % 12] - cusps[i]) % 360 for i in range(12)]
    if any(span == 0 for span in spans) or not math.isclose(sum(spans), 360, abs_tol=1e-6):
        raise ValueError("12 cusps must occur in zodiacal order and cover 360 degrees")
    if not isinstance(angles, dict) or not set(ANGLES).issubset(angles):
        raise ValueError("natal requires asc, mc, ic and dsc")
    for name, longitude in angles.items():
        _finite_longitude(longitude, f"angle {name}")
    for name, index in (("asc", 0), ("ic", 3), ("dsc", 6), ("mc", 9)):
        distance = abs((angles[name] - cusps[index] + 180) % 360 - 180)
        if distance > 1e-6:
            raise ValueError(f"angle {name} disagrees with cusp {index + 1}")


def cross_contacts(natals: dict[str, dict]) -> list[dict]:
    """Owned, stable planet/planet and planet/angle major contacts across two charts."""
    if len(natals) != 2:
        raise ValueError("cross contacts require two natals")
    first, second = sorted(natals)
    charts = {first: natals[first], second: natals[second]}
    groups = [
        (first, "planet", second, "planet", 6.0),
        (first, "planet", second, "angle", 3.0),
        (second, "planet", first, "angle", 3.0),
        (first, "angle", second, "angle", 3.0),
    ]
    hits = []
    for from_owner, from_kind, to_owner, to_kind, orb in groups:
        def points(owner, kind):
            snapshot = charts[owner]
            return (snapshot["positions"] if kind == "planet" else
                    {name: snapshot["houses"]["angles"][name] for name in ANGLES})
        for contact in compute_cross_aspects(points(from_owner, from_kind),
                                             points(to_owner, to_kind), orb=orb):
            from_point, to_point = contact["from_body"], contact["to_body"]
            ends = sorted((f"{from_owner}:{from_kind}:{from_point}",
                           f"{to_owner}:{to_kind}:{to_point}"))
            hits.append({
                "key": "|".join((*ends, contact["aspect"])),
                "from_owner": from_owner, "from_kind": from_kind,
                "from_point": from_point, "to_owner": to_owner,
                "to_kind": to_kind, "to_point": to_point,
                "aspect": contact["aspect"], "separation": contact["angle"],
                "orb": contact["orb"], "orb_limit": orb,
            })
    return sorted(hits, key=lambda h: (h["orb"], h["key"]))


def directed_overlays(natals: dict[str, dict]) -> list[dict]:
    """Each person's ten planets placed in the other person's twelve houses."""
    if len(natals) != 2:
        raise ValueError("overlays require two natals")
    result = []
    for from_owner in sorted(natals):
        to_owner = next(owner for owner in natals if owner != from_owner)
        cusps = natals[to_owner]["houses"]["cusps"]
        for body, longitude in sorted(natals[from_owner]["positions"].items()):
            result.append({"from_owner": from_owner, "body": body,
                           "to_owner": to_owner, "house": house_of(longitude, cusps),
                           "longitude": longitude})
    return result


def _json_bytes(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_bundle(source: Path, target: Path, natals: dict[str, dict],
                 motions: dict[str, dict[str, float]] | None, provenance: dict,
                 private_root: Path | None = None) -> Path:
    """Publish a private bundle; manifest is the final file and hashes all outputs."""
    validate_paths(source, target, private_root)
    people = validate_input(json.loads(source.read_text(encoding="utf-8")))
    for slot in ("A", "B"):
        identity = people[slot]["id"]
        if identity not in natals:
            raise ValueError(f"natal missing for {slot} ({identity})")
        snapshot = natals[identity]
        if snapshot.get("moment_utc") != people[slot]["datetime_utc"]:
            raise ValueError(f"natal moment disagrees with input for {slot}")
        location = snapshot.get("location", {})
        if (location.get("lat") != people[slot]["latitude"] or
                location.get("lon") != people[slot]["longitude"]):
            raise ValueError(f"natal location disagrees with input for {slot}")
        validate_natal(natals[identity])
    if set(natals) != {people["A"]["id"], people["B"]["id"]}:
        raise ValueError("natal owners disagree with input")
    if motions is not None:
        if set(motions) != set(natals):
            raise ValueError("motion must cover both natal owners")
        for identity, speeds in motions.items():
            if set(speeds) != set(DEFAULT_BODIES) or not all(
                    isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                    for v in speeds.values()):
                raise ValueError(f"invalid motion speeds for {identity}")
    contacts = cross_contacts(natals)
    overlays = directed_overlays(natals)
    target.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}

    def save_json(relative: str, payload: object):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_json_bytes(payload))
        files[relative] = _sha(path)

    def save_csv(relative: str, fields: tuple[str, ...], rows: list[dict]):
        path = target / relative
        _write_csv(path, fields, rows)
        files[relative] = _sha(path)

    for slot in ("A", "B"):
        owner = people[slot]["id"]
        natal = natals[owner]
        speeds = (motions or {}).get(owner)
        phases = compute_phase_states(natal["positions"], cusps=natal["houses"]["cusps"],
                                      moment_utc=natal["moment_utc"])
        save_json(f"natals/{slot}.json", {"owner": owner, **natal, "phases": phases,
                                          "motion": {"status": "computed" if speeds is not None
                                                     else "not_computed",
                                                     "speed_longitude_deg_day": speeds}})
        base = f"adapters/charts/{slot}/outputs"
        save_csv(f"{base}/natal_longitudes.csv", ("body", "longitude"),
                 [{"body": body, "longitude": natal["positions"][body]}
                  for body in DEFAULT_BODIES])
        save_csv(f"{base}/houses_placidus.csv", ("house", "longitude"),
                 [{"house": i, "longitude": value}
                  for i, value in enumerate(natal["houses"]["cusps"], 1)])
        save_csv(f"{base}/chart_points.csv", ("point", "longitude"),
                 [{"point": point, "longitude": natal["houses"]["angles"][point]}
                  for point in ANGLES])
        save_csv(f"{base}/planets_primary.csv",
                 ("body", "longitude", "sign", "house", "dignity", "sect_role",
                  "speed_longitude_deg_day", "motion"),
                 [{"body": body, "longitude": natal["positions"][body],
                   "sign": sign_of(natal["positions"][body]),
                   "house": natal.get("placements", {}).get(body, house_of(
                       natal["positions"][body], natal["houses"]["cusps"])),
                   "dignity": natal.get("dignities", {}).get(body, {}).get("dignity", "not_computed"),
                   "sect_role": natal.get("sect", {}).get("bodies", {}).get(body, {}).get(
                       "role", "not_computed"),
                   "speed_longitude_deg_day": "" if speeds is None else speeds[body],
                   "motion": "not_computed" if speeds is None else (
                       "retrograde" if speeds[body] < 0 else "direct")}
                  for body in DEFAULT_BODIES])
        save_csv(f"natals/{slot}_aspects.csv",
                 ("body1", "body2", "aspect", "angle", "orb"),
                 natal.get("aspects", []))
    save_csv("cross_aspects.csv", ("key", "from_owner", "from_kind", "from_point",
                                    "to_owner", "to_kind", "to_point", "aspect",
                                    "separation", "orb", "orb_limit"), contacts)
    save_csv("overlays.csv", ("from_owner", "body", "to_owner", "house", "longitude"),
             overlays)
    manifest = {
        "recipe": "synastry_local", "version": "0.1.0", "scope": "private_exact_time_pilot",
        "participants": {slot: people[slot]["id"] for slot in ("A", "B")},
        "input_sha256": _sha(source), "files": dict(sorted(files.items())),
        "settings": {"engine": "a", "zodiac": "tropical", "houses": "Placidus",
                     "dignities": "traditional", "bodies": list(DEFAULT_BODIES),
                     "aspects": ["conjunction", "sextile", "square", "trine", "opposition"],
                     "natal_and_cross_planet_orb": 6.0, "cross_angle_orb": 3.0,
                     "cross_applying_separating": "not_computed"},
        "motion_status": "computed" if motions is not None else "not_computed",
        "provenance": provenance,
    }
    (target / "manifest.json").write_bytes(_json_bytes(manifest))
    return target


def _motion(moment: datetime, positions: dict[str, float]) -> dict[str, float]:
    """Read speed from the same Swiss ephemeris files and flag as used by engine A."""
    swe = _init_swe()
    consts = _swe_body_consts()
    utc = moment.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    jd = swe.julday(utc.year, utc.month, utc.day, hour)
    speeds = {}
    for body in DEFAULT_BODIES:
        xx, flag = swe.calc_ut(jd, consts[body], swe.FLG_SWIEPH | swe.FLG_SPEED)
        if not flag & swe.FLG_SWIEPH:
            raise ValueError(f"Swiss ephemeris unavailable for {body}; refusing fallback")
        longitude, speed = float(xx[0]) % 360, float(xx[3])
        delta = abs((longitude - positions[body] + 180) % 360 - 180)
        if not math.isfinite(speed) or delta > 1e-5:
            raise RuntimeError(f"motion mismatch or invalid speed for {body}")
        speeds[body] = speed
    return speeds


def _provenance() -> dict:
    import astro.engine as engine
    swe = _init_swe()
    ephe_dir = Path(engine._SWE_EPHE_PATH).resolve()
    ephemeris = {}
    for name in _SWE_RUNTIME_FILES:
        path = ephe_dir / name
        if not path.is_file():
            raise RuntimeError(f"missing required ephemeris file {path}")
        ephemeris[str(path)] = _sha(path)
    return {
        "pyswisseph_package": importlib.metadata.version("pyswisseph"),
        "swiss_ephemeris_version": swe.version,
        "ephemeris_files_sha256": ephemeris,
        "code_sha256": {name: _sha(REPO / name) for name in CODE_FILES},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="existing .private JSON")
    parser.add_argument("--output", required=True, type=Path, help="new .private directory")
    args = parser.parse_args(argv)
    validate_paths(args.input, args.output)
    people = validate_input(json.loads(args.input.read_text(encoding="utf-8")))
    natals, motions = {}, {}
    motion_error = None
    for slot in ("A", "B"):
        person = people[slot]
        identity = person["id"]
        natal = compute_natal(person["moment"], person["latitude"], person["longitude"],
                              bodies=list(DEFAULT_BODIES), orb=6.0,
                              scheme="traditional", engine="a")
        validate_natal(natal)
        natals[identity] = natal
        try:
            motions[identity] = _motion(person["moment"], natal["positions"])
        except RuntimeError as exc:
            motion_error = str(exc)
    provenance = _provenance()
    if motion_error:
        provenance["motion_unavailable_reason"] = motion_error
    output = write_bundle(args.input, args.output, natals, None if motion_error else motions,
                          provenance)
    print(f"private synastry bundle: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
