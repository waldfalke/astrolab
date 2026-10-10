"""Explicit experimental transformation of a recorded complete Engine-A day."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astro.aspects import MAJOR_ASPECTS, compute_aspects, compute_cross_aspects
from astro.dignities import SIGNS, compute_dignities, sign_of
from astro.phases import OPERATOR_VERSION, compute_phase_states

METHOD_VERSION = "clock-event-state-v2-draft1"
TRANSFORMER_VERSION = "0.1.0"
BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")


def angular_step(start, end):
    """Shortest sampled arc; sub-step reversals cannot be recovered."""
    return (end - start + 180.0) % 360.0 - 180.0


def contacts_in_step(a0, a1, b0, b1, *, targets):
    """Linear relative contacts, including sampled boundaries for later dedup."""
    start = a0 - b0
    end = start + angular_step(a0, a1) - angular_step(b0, b1)
    if start == end:
        return []
    low, high = sorted((start, end))
    hits = []
    for target in targets:
        for turn in range(math.ceil((low-target)/360), math.floor((high-target)/360)+1):
            level = target + 360 * turn
            fraction = (level-start)/(end-start)
            hits.append({"fraction": fraction, "target_deg": target,
                         "relative_start_deg": start, "relative_end_deg": end,
                         "side_before_deg": start-level, "side_after_deg": end-level,
                         "direction": "increasing" if end > start else "decreasing"})
    return hits


def utc_time(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)", value
    ):
        raise ValueError("UTC instant must include seconds and Z or +00:00")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def utc_text(moment):
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def load_inputs(frames_path, metadata_path, *, house_system):
    if house_system != "placidus":
        raise ValueError("This probe requires explicitly asserted Placidus")
    raw = Path(frames_path).read_bytes()
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    raw_hash = hashlib.sha256(raw).hexdigest()
    if metadata.get("raw_sha256") != raw_hash:
        raise ValueError("Raw frames SHA-256 does not match metadata")
    frames = json.loads(raw.decode("utf-8"))
    if not isinstance(frames, list) or len(frames) != 1441 or metadata.get("samples") != 1441:
        raise ValueError("Full one-minute day requires 1441 samples")
    if metadata.get("house_system", "placidus") != "placidus":
        raise ValueError("Metadata conflicts with explicitly asserted Placidus")
    offset = metadata.get("timezone", "")
    match = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", offset)
    if not match or int(match[2]) > 23 or int(match[3]) > 59:
        raise ValueError("Metadata requires a fixed UTC offset")
    minutes = (int(match[2])*60+int(match[3])) * (1 if match[1] == "+" else -1)
    local_zone = timezone(timedelta(minutes=minutes))
    interval = metadata.get("interval_utc")
    if not isinstance(interval, list) or len(interval) != 2:
        raise ValueError("Metadata requires a UTC interval")
    start, end = map(utc_time, interval)
    if end-start != timedelta(days=1):
        raise ValueError("UTC interval must span one full day")
    local_start = start.astimezone(local_zone)
    if local_start.strftime("%Y-%m-%d") != metadata.get("date") or local_start.time().isoformat() != "00:00:00":
        raise ValueError("UTC interval must match declared local date and midnight")
    for label, limit in (("latitude", 90), ("longitude", 180)):
        if abs(finite_number(metadata.get(label), label)) > limit:
            raise ValueError(f"{label} is out of range")
    for index, frame in enumerate(frames):
        if utc_time(frame.get("utc")) != start+timedelta(minutes=index):
            raise ValueError(f"UTC order/step must be exactly 60 seconds at frame {index}")
        if frame.get("local_minute") != index:
            raise ValueError("local_minute must match one-minute step")
        positions = frame.get("positions")
        if not isinstance(positions, dict) or set(positions) != set(BODIES):
            raise ValueError("Each frame must have the same ten bodies")
        for body, longitude in positions.items():
            if not 0 <= finite_number(longitude, body) < 360:
                raise ValueError(f"{body} longitude must be in [0, 360)")
        cusps = frame.get("cusps")
        if not isinstance(cusps, list) or len(cusps) != 12:
            raise ValueError("House frame requires 12 cusps")
        for cusp in cusps:
            if not 0 <= finite_number(cusp, "cusps") < 360:
                raise ValueError("cusps must be in [0, 360)")
        widths = [(cusps[(i+1)%12]-cusps[i])%360 for i in range(12)]
        if min(widths) <= 0 or not math.isclose(sum(widths), 360, abs_tol=1e-6):
            raise ValueError("cusps must be distinct, ordered and cover 360 degrees")
        angles = frame.get("angles")
        if not isinstance(angles, dict) or not {"asc", "mc"} <= set(angles):
            raise ValueError("ASC and MC are required")
        for label, angle in angles.items():
            if not 0 <= finite_number(angle, label) < 360:
                raise ValueError("angle must be in [0, 360)")
        if abs(angular_step(cusps[0], angles["asc"])) > 1e-6 or abs(angular_step(cusps[9], angles["mc"])) > 1e-6:
            raise ValueError("Placidus cusps must agree with ASC/MC")
    return frames, metadata


def build_states(frames, *, aspect_orb):
    rows = []
    times = [utc_time(frame["utc"]) for frame in frames]
    for index, frame in enumerate(frames):
        moment = utc_text(times[index])
        positions, cusps = frame["positions"], frame["cusps"]
        phases = compute_phase_states(positions, cusps=cusps, moment_utc=moment)
        dignities = compute_dignities({b: positions[b] for b in BODIES[:7]}, scheme="traditional")
        houses = [{"house": i+1, "start_deg": cusps[i], "end_deg": cusps[(i+1)%12],
                   "width_deg": (cusps[(i+1)%12]-cusps[i])%360} for i in range(12)]
        bodies = {}
        lo, hi = max(0, index-1), min(len(frames)-1, index+1)
        for body, longitude in positions.items():
            phase = phases["states"][body]
            house = houses[phase["H_house"]-1]
            speed = (angular_step(frames[lo]["positions"][body], frames[hi]["positions"][body])
                     / (times[hi]-times[lo]).total_seconds()*86400)
            bodies[body] = {
                "longitude": longitude, "sign": sign_of(longitude), "H_house": phase["H_house"],
                "house_fraction": (longitude-house["start_deg"])%360/house["width_deg"],
                "traditional_dignity": ({"availability": "computed", **dignities[body]} if body in dignities
                                        else {"availability": "unavailable", "reason": "outside_seven_classical_bodies"}),
                "secant_motion": {"deg_per_day": speed,
                                  "direction": "direct" if speed > 0 else "retrograde" if speed < 0 else "station_or_inconclusive",
                                  "interval_utc": [utc_text(times[lo]), utc_text(times[hi])],
                                  "state_indices": [lo, hi], "kind": "neighbor_secant_not_instantaneous"},
            }
        pairs = [{**hit, "orb_limit_deg": aspect_orb} for hit in compute_aspects(positions, orb=aspect_orb)]
        asc = [{**hit, "orb_limit_deg": aspect_orb} for hit in compute_cross_aspects(
            {"ASC": frame["angles"]["asc"]}, positions, orb=aspect_orb)]
        rows.append({"index": index, "utc": moment, "raw_frame": frame, "angles": frame["angles"],
                     "positions": positions, "cusps": cusps, "houses": houses, "bodies": bodies,
                     "phase_states": phases, "interplanetary_aspects": pairs, "asc_aspects": asc})
    return rows


def build_events(frames):
    events, seen = [], set()
    times = [utc_time(frame["utc"]) for frame in frames]
    signed_aspects = {0: "conjunction", 60: "sextile", -60: "sextile", 90: "square", -90: "square",
                      120: "trine", -120: "trine", 180: "opposition"}
    for index, (left, right) in enumerate(zip(frames, frames[1:])):
        p0, p1 = left["positions"], right["positions"]
        a0, a1 = left["angles"], right["angles"]
        specs = []
        for body in BODIES:
            specs.append(("asc_body_aspect", "ASC", body, a0["asc"], a1["asc"], p0[body], p1[body], signed_aspects))
            specs.append(("mc_body_conjunction", "MC", body, a0["mc"], a1["mc"], p0[body], p1[body], {0: "conjunction"}))
            for cusp in range(12):
                specs.append(("body_cusp_crossing", body, f"cusp_{cusp+1}", p0[body], p1[body], left["cusps"][cusp], right["cusps"][cusp], {0: None}))
        for first, second in combinations(sorted(BODIES), 2):
            specs.append(("interplanetary_aspect", first, second, p0[first], p1[first], p0[second], p1[second], signed_aspects))
        specs.append(("asc_sign_ingress", "ASC", "zodiac_boundary", a0["asc"], a1["asc"], 0, 0, {i*30: None for i in range(12)}))
        for kind, first, second, x0, x1, y0, y1, targets in specs:
            for hit in contacts_in_step(x0, x1, y0, y1, targets=targets):
                moment = times[index]+(times[index+1]-times[index])*hit["fraction"]
                if moment >= times[-1]:
                    continue
                stamp = utc_text(moment)
                key = kind, first, second, hit["target_deg"], stamp
                if key in seen:
                    continue
                seen.add(key)
                event = {"kind": kind, "participant1": first, "participant2": second,
                         "aspect": targets[hit["target_deg"]], **hit, "linear_estimate_utc": stamp,
                         "bracket_utc": [utc_text(times[index]), utc_text(times[index+1])],
                         "bracket_start_index": index, "bracket_end_index": index+1,
                         "state_before_index": index, "state_after_index": index+1,
                         "state_before_relation": "at_estimate" if hit["fraction"] == 0 else "before_estimate",
                         "state_after_relation": "at_estimate" if hit["fraction"] == 1 else "after_estimate",
                         "time_method": "linear_relative_longitude_in_sample_bracket"}
                if kind == "asc_sign_ingress":
                    boundary = hit["target_deg"]//30
                    increasing = hit["direction"] == "increasing"
                    event.update(sign_before=SIGNS[(boundary-1 if increasing else boundary)%12],
                                 sign_after=SIGNS[(boundary if increasing else boundary-1)%12])
                if kind == "body_cusp_crossing":
                    cusp = int(second.split("_")[1])
                    previous = (cusp-2)%12+1
                    increasing = hit["direction"] == "increasing"
                    event.update(house_before=previous if increasing else cusp,
                                 house_after=cusp if increasing else previous)
                events.append(event)
    events.sort(key=lambda e: (datetime.fromisoformat(e["linear_estimate_utc"].replace("Z", "+00:00")),
                               e["kind"], e["participant1"], e["participant2"], e["target_deg"]))
    for index, event in enumerate(events):
        event["event_id"] = f"event-{index:04d}"
    return events


def run_probe(frames_path, metadata_path, output, *, aspect_orb, house_system):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    if not 0 <= finite_number(aspect_orb, "aspect orb") <= 15:
        raise ValueError("Aspect orb must be in [0, 15] degrees")
    frames, metadata = load_inputs(frames_path, metadata_path, house_system=house_system)
    states = build_states(frames, aspect_orb=aspect_orb)
    events = build_events(frames)
    sources = {"transformer": Path(__file__), **{name: ROOT/f"astro/{name}.py" for name in ("phases", "dignities", "aspects")}}
    manifest = {
        "method_version": METHOD_VERSION, "transformer_version": TRANSFORMER_VERSION,
        "phase_operator_version": OPERATOR_VERSION, "status": "experimental",
        "parameters": {"aspect_orb_deg": aspect_orb, "house_system": house_system,
                       "house_system_basis": "explicit_cli_assertion; linked recorded input producer uses P",
                       "sample_step_seconds": 60, "timezone": metadata["timezone"]},
        "input_paths": {"frames": str(Path(frames_path).resolve()), "metadata": str(Path(metadata_path).resolve())},
        "input_sha256": {"frames": hashlib.sha256(Path(frames_path).read_bytes()).hexdigest(),
                         "metadata": hashlib.sha256(Path(metadata_path).read_bytes()).hexdigest()},
        "source_paths": {name: str(path.resolve()) for name, path in sources.items()},
        "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()},
        "provenance": metadata,
        "counts": {"states": len(states), "intervals": len(states)-1, "events": len(events),
                   "events_by_kind": dict(sorted(Counter(e["kind"] for e in events).items()))},
        "absent_layers": ["natal planets/cusps", "nodes", "additional points in event coverage",
                          "sect", "terms", "faces", "triplicity", "full traditional condition"],
        "limitations": ["Linear estimates are not Swiss roots or physical horizon rise times.",
                        "Sampling can miss tangencies without endpoint sign change and reversals within a step.",
                        "Shortest-arc unwrap assumes endpoint movement below 180 degrees per step.",
                        "Secant motion is not instantaneous speed; zero is station_or_inconclusive.",
                        "State orb is an explicit research parameter, not a useful-window boundary.",
                        "No forecast skill, ranking, score, favorable window or semantic weight is established."],
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (("states", states), ("events", events), ("manifest", manifest)):
        (output/f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    fields = ["event_id", "linear_estimate_utc", "kind", "participant1", "participant2", "aspect", "target_deg",
              "direction", "fraction", "state_before_index", "state_after_index", "state_before_relation", "state_after_relation",
              "side_before_deg", "side_after_deg", "bracket_start_index", "bracket_end_index", "sign_before", "sign_after", "house_before", "house_after"]
    with (output/"events.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(events)
    brief = f"""# Experimental event and state ribbon

Method `{METHOD_VERSION}`; experimental. This package describes sampled geometry
of a common day, without a forecast or automatic semantic weighting.

Start with [events.csv](events.csv) for the complete chronology ({len(events)} events).
[events.json](events.json) retains source minute brackets and linear estimates.
[states.json](states.json) contains all {len(states)} frames; list indices are stable.
[manifest.json](manifest.json) records parameters, input and source hashes, provenance,
versions, counts and absent layers. Its input_paths and source_paths are absolute.

To reconstruct an event, select its event_id, then open states.json at
bracket_start_index and bracket_end_index. state_before_index/state_after_index
are aliases of these bracket indices, not promises of strictly earlier/later states:
the corresponding relation is at_estimate, before_estimate or after_estimate.
At the day start the left state is at_estimate and there is no earlier supplied state.
The final sample is retained for the final interval; events at the right day boundary
are excluded. Shared sample contacts occur once, with the earlier available bracket.

participant1 minus participant2 is the signed relative longitude. target_deg is
the signed exact aspect branch (opposition +180 also represents -180 modulo 360).
side_before_deg/side_after_deg are signed endpoint residuals from that unwrapped
target; direction describes their relative change. fraction locates the linear
estimate in bracket_utc. These are sampled contacts, not exact Swiss roots.
body_cusp_crossing uses body minus moving cusp; house_before/house_after record
the local direction across that boundary, without assigning interpretive weight.
asc_sign_ingress records both sign sides. Cusp 1 = ASC is an identity and generates
no independent ASC-to-cusp event. ASC-to-body contact is ecliptic geometry;
body latitude is not used, so it does not establish physical horizon rise.

Each state preserves raw_frame in full, including original UTC text and all raw
angles (even angles outside this probe's event coverage). positions, cusps and
angles repeat the geometry for navigation. houses contains start_deg, end_deg
and positive width_deg for each of the 12 moving Placidus house arcs.
bodies contains sign, computed H_house, house_fraction in that actual arc,
traditional_dignity for the seven classical bodies and secant_motion with its
neighbor interval and direction. Outer traditional dignity is unavailable.
phase_states is the complete shared compute_phase_states result (modern rulership,
both Z cycles for Mercury/Venus, z/H/h/D, availability, tier and phase dignity).
Phase dignity and traditional dignity remain separate. H/h are the declared
project extrapolation onto Placidus, not a full classical condition layer.
interplanetary_aspects and asc_aspects expose both participants, actual separation,
actual orb and orb_limit_deg={aspect_orb}. This state limit does not constrain
the exact-contact event search and does not define useful windows.

Only the declared ten bodies, ASC/MC contacts, major interplanetary aspects,
ASC sign ingresses and body crossings of all moving cusps are covered.
Natal points, nodes and added event points are absent. Sect, terms, faces,
triplicity and a full traditional condition layer are absent. No score,
ranking, recommendation, principal window or favorable label is computed.
One-minute endpoint sampling can miss non-crossing contacts and sub-step reversals.
Zero secant speed is station_or_inconclusive; other speed directions describe
the sampled interval, not proven instantaneous motion.

Method sources: [method/version map]({(ROOT/'docs/rising-clock-method-versions.md').as_posix()}),
[bounded probe plan]({(ROOT/'docs/superpowers/plans/2026-10-04-clock-event-state-probe.md').as_posix()}),
[shared phases]({(ROOT/'astro/phases.py').as_posix()}),
[traditional dignities]({(ROOT/'astro/dignities.py').as_posix()}),
[aspect operator]({(ROOT/'astro/aspects.py').as_posix()}).
For interpretation, follow the [phase reading reference]({(ROOT/'.agents/skills/chart-analyst/references/phase-analysis-reference.md').as_posix()})
and [semantic operators and reservoirs]({(ROOT/'docs/semantic-base.md').as_posix()}).
These provide composition meanings; they do not establish predictive validity.
Concrete reference conflicts remain visible: the phase reference's older formula
blocks say ceil while its corrected introduction and this operator use floor+1;
its older inferred Z ceiling differs from the current operator's book-grounded Z.
semantic-base's legacy H-grounded wording differs from the current explicitly
extrapolated H/h tier. Its old intraday scoring statement does not apply here.
The recorded operator result and this probe plan define this packet's numerical
conventions and epistemic labels. Older midpoint/ceiling/scoring rules do not
override them. Participant order is the signed geometric equation, not an
assertion of interpretive faster-to-slower direction; secant speeds are supplied
separately and no directed semantic aspect is manufactured.
Input frames: [{Path(frames_path).name}]({Path(frames_path).resolve().as_posix()});
input metadata: [{Path(metadata_path).name}]({Path(metadata_path).resolve().as_posix()}).
"""
    (output/"BRIEF.md").write_text(brief, encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--aspect-orb", required=True, type=float)
    parser.add_argument("--house-system", required=True, choices=["placidus"])
    args = parser.parse_args()
    try:
        manifest = run_probe(args.frames, args.metadata, args.output,
                             aspect_orb=args.aspect_orb, house_system=args.house_system)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Input/output rejected: {error}\n")
    print(json.dumps(manifest["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

