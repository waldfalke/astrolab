"""Local astronomical facts for a reviewed horary; never an automatic judgment."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo
from artifacts.renderer.render_chart import draw_wheel

ROOT = Path(__file__).resolve().parents[1]
from astro import engine
from astro.aspects import compute_aspects
from astro.carrier_states import compute_carrier_states
from astro.dignities import compute_essential_states, sign_of
from astro.engine import compute_body_states_series
from astro.phases import compute_phase_states
from astro.placements import house_of
from astro.sect import compute_sect

CLASSICAL = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
RULERS = ("mars", "venus", "mercury", "moon", "sun", "mercury", "venus", "mars", "jupiter", "saturn", "saturn", "jupiter")
CHALDEAN = ("saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon")
DAY_LORDS = ("moon", "mars", "mercury", "jupiter", "venus", "saturn", "sun")
TRIPLICITY = (("sun", "jupiter"), ("venus", "moon"), ("saturn", "mercury"), ("mars", "mars"))
NATURE = {"sun": "hot_dry", "mars": "hot_dry", "jupiter": "hot_moist", "venus": "cold_moist", "moon": "cold_moist", "saturn": "cold_dry", "mercury": "cold_dry"}
ORBS = dict(sun=15, moon=12, mercury=7, venus=7, mars=7, jupiter=9, saturn=9)
RAYS = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition", 240: "trine", 270: "square", 300: "sextile"}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: nonempty text required")
    return value


def utc(value):
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.microsecond:
        raise ValueError("timestamp requires an explicit offset and whole seconds")
    return t.astimezone(timezone.utc)


def validate_input(cfg: dict) -> datetime:
    if cfg.get("schema") != "astrolab.horary.input.v1":
        raise ValueError("unsupported horary input schema")
    try:
        q, intake, m = cfg["question"], cfg["intake"], cfg["moment"]
        for key in ("original", "settled", "outcome_test", "horizon"):
            text(q[key], "question." + key)
        if q["domain"] not in ("relationship", "work", "money", "property", "travel", "study", "lost_property", "family"):
            raise ValueError("question domain outside horary-v1 product scope")
        if intake["status"] != "accepted":
            raise ValueError("intake must be reviewed before computation")
        for key in ("reviewer", "single_question_basis", "answerability_basis"):
            text(intake[key], "intake." + key)
        previous = intake["previous_question"]
        if previous["status"] != "none":
            if previous["status"] not in ("reverify", "new_circumstances"):
                raise ValueError("previous question needs clarification")
            text(previous.get("reference"), "previous.reference")
            text(previous.get("basis"), "previous.basis")
        if m["kind"] not in ("asked", "received"):
            raise ValueError("moment kind must be asked or received")
        for key in ("source", "place_source"):
            text(m[key], "moment." + key)
        moment = utc(m["local"])
        local = datetime.fromisoformat(m["local"].replace("Z", "+00:00"))
        if moment.astimezone(ZoneInfo(m["timezone"])).isoformat() != local.isoformat():
            raise ValueError("local timestamp conflicts with timezone or nonexistent civil time")
        for key, limit in (("latitude", 90), ("longitude", 180)):
            n = m[key]
            if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or abs(n) > limit:
                raise ValueError("invalid " + key)
        precision = m["precision_seconds"]
        if isinstance(precision, bool) or not isinstance(precision, (int, float)) or not math.isfinite(precision) or precision <= 0:
            raise ValueError("positive moment precision required")
        days = cfg["scan_days"]
        # shortcut: one scan is bounded to one year; extend by a new explicit run if a path needs more.
        if type(days) is not int or not 3 <= days <= 366:
            raise ValueError("scan_days must be 3..366 (execution bound, not a prediction horizon)")
        past = cfg.get("past_days", 3)
        if type(past) is not int or not 3 <= past <= 366:
            raise ValueError("past_days must be 3..366 (execution bound, not a prediction horizon)")
        samples = cfg.get("phase_samples_utc", [])
        if not isinstance(samples, list) or len(samples) > 100:
            raise ValueError("phase_samples_utc must be a list with at most 100 explicit instants")
        for sample in samples:
            utc(sample)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"incomplete horary input: {exc}") from exc
    return moment


def signed(value):
    return (value + 180) % 360 - 180


def roots(function, knots, angular=False):
    """Bracketed zeros; callers insert derivative roots so reversals are not skipped."""
    found = []
    for left, right in zip(knots, knots[1:]):
        a, b = function(left), function(right)
        if abs(a) < 1e-10:
            found.append(left)
        if abs(b) < 1e-10:
            found.append(right)
        if a * b >= 0 or (angular and abs(b-a) >= 180):
            continue
        for _ in range(45):
            mid = (left+right)/2
            if mid in (left, right):
                break
            value = function(mid)
            if a*value <= 0:
                right = mid
            else:
                left, a = mid, value
        found.append((left+right)/2)
    unique = []
    for t in sorted(found):
        if not unique or t - unique[-1] > 1e-8:
            unique.append(t)
    return unique


def planetary_hour(now, rise, setting, next_rise, day_lord):
    if not rise <= now < next_rise or not rise < setting < next_rise:
        return None
    daytime = now < setting
    base, end = (rise, setting) if daytime else (setting, next_rise)
    length = (end-base)/12
    index = min(11, int((now-base)/length)) + (0 if daytime else 12)
    return {"number": index+1, "ruler": CHALDEAN[(CHALDEAN.index(day_lord)+index) % 7],
            "day_lord": day_lord, "start_jd": base+(index % 12)*length,
            "end_jd": base+(index % 12+1)*length,
            "boundary_distance_seconds": min(now-(base+(index % 12)*length), base+(index % 12+1)*length-now)*86400}


def hour_agreement(hour_lord, asc, sect):
    lord = RULERS[int(asc // 30)]
    return {"asc_lord": lord, "same_ruler": hour_lord == lord,
            "triplicity": hour_lord == TRIPLICITY[int(asc // 30) % 4][sect == "night"],
            "same_nature": NATURE[hour_lord] == NATURE[lord], "nature_profile": "declared-general-natures-v1"}


def geometric_house(longitude, cusps):
    for cusp in cusps:
        if abs(signed(longitude-cusp)) < 1e-8:
            longitude = cusp
            break
    return house_of(longitude, cusps)


def compute_facts(cfg: dict, step_minutes: int = 30) -> dict:
    moment = validate_input(cfg)
    if step_minutes not in (15, 30):
        raise ValueError("supported audit grids: 15 or 30 minutes")
    sample_moments = [utc(value) for value in cfg.get("phase_samples_utc", [])]
    snapshots = compute_body_states_series([moment, *sample_moments], engine="a")
    physical = snapshots[0]
    swe = engine._init_swe()
    constants = engine._swe_body_consts()
    m = cfg["moment"]
    tz = ZoneInfo(m["timezone"])
    jd0 = swe.julday(moment.year, moment.month, moment.day, moment.hour+moment.minute/60+moment.second/3600)
    jd_start, jd_end = jd0-cfg.get("past_days", 3), jd0+cfg["scan_days"]
    at_datetime = lambda jd: moment + timedelta(days=jd-jd0)
    def stamp(jd):
        t = at_datetime(jd)
        return {"jd": jd, "utc": t.isoformat(), "local": t.astimezone(tz).isoformat()}

    @lru_cache(maxsize=100000)
    def state(jd, body):
        requested = swe.FLG_SWIEPH | swe.FLG_SPEED
        values, flag = swe.calc_ut(jd, constants[body], requested)
        if ((flag & (swe.FLG_SWIEPH | swe.FLG_MOSEPH | swe.FLG_JPLEPH)) != swe.FLG_SWIEPH
                or flag & requested != requested or flag & swe.FLG_EQUATORIAL):
            raise RuntimeError(f"unexpected Swiss flags or ephemeris fallback for {body}")
        if len(values) != 6 or not all(math.isfinite(value) for value in values):
            raise RuntimeError(f"invalid Swiss vector for {body}")
        return values[0], values[3], flag

    cusps, angles = swe.houses_ex(jd0, m["latitude"], m["longitude"], b"R")
    if (len(cusps) != 12 or len(angles) < 2
            or not all(math.isfinite(x) for x in (*cusps, *angles))):
        raise RuntimeError("unsupported Regiomontanus geometry in this adapter; no substituted system")
    arcs = [(cusps[(i+1) % 12]-cusp) % 360 for i, cusp in enumerate(cusps)]
    if any(arc <= 0 for arc in arcs) or not math.isclose(sum(arcs), 360, rel_tol=0, abs_tol=1e-7):
        raise RuntimeError("unsupported Regiomontanus geometry in this adapter; no substituted system")
    positions = {b: row["longitude_deg"] for b, row in physical["bodies"].items()}
    speeds = {b: row["longitude_speed_deg_per_day"] for b, row in physical["bodies"].items()}
    sect = compute_sect(positions, angles[0])["chart_sect"]
    rows = [{"body": b, "longitude": positions[b], "sign": sign_of(positions[b]), "degree": positions[b] % 30,
             "speed_deg_day": speeds[b],
             "swiss_flag": physical["provenance"]["returned_flags"][b]["ecliptic"],
             "house": geometric_house(positions[b], cusps),
             "solar_distance": abs(signed(positions[b]-positions["sun"])),
             "same_sign_as_sun": int(positions[b]//30) == int(positions["sun"]//30)}
            for b in positions]
    applications = []
    for a, b in itertools.combinations(CLASSICAL, 2):
        ray = min(RAYS, key=lambda r: abs(signed(positions[a]-positions[b]-r)))
        error = signed(positions[a]-positions[b]-ray)
        applications.append({"bodies": [a, b], "aspect": RAYS[ray], "error_degrees": error,
                             "moiety_orb": (ORBS[a]+ORBS[b])/2,
                             "within_orb": abs(error) <= (ORBS[a]+ORBS[b])/2,
                             "closing_now": error*(speeds[a]-speeds[b]) < 0})

    step = step_minutes/1440
    knots = [jd_start+i*step for i in range(math.ceil((jd_end-jd_start)/step))] + [jd_end]
    events = []
    def record(kind, bodies, function, event_knots, angular=False, **extra):
        for jd in roots(function, event_knots, angular=angular):
            residual = abs(function(jd))
            if residual > 1e-6:
                raise RuntimeError("event root failed residual check")
            before = {b: {"longitude": state(jd-1/86400, b)[0], "speed_deg_day": state(jd-1/86400, b)[1]} for b in bodies}
            after = {b: {"longitude": state(jd+1/86400, b)[0], "speed_deg_day": state(jd+1/86400, b)[1]} for b in bodies}
            if kind == "ingress" and all(int(before[b]["longitude"]//30) == int(after[b]["longitude"]//30) for b in bodies):
                continue
            events.append({**stamp(jd), "kind": kind, "bodies": list(bodies), "residual": residual,
                           "one_second_before": before, "one_second_after": after, **extra})

    for body in CLASSICAL:
        turning = roots(lambda t: state(t, body)[1], knots)
        body_knots = sorted(set(knots+turning))
        for sign in range(12):
            record("ingress", [body], lambda t, b=body, s=sign: signed(state(t, b)[0]-s*30),
                   body_knots, True, boundary_longitude=sign*30)
        record("station", [body], lambda t, b=body: state(t, b)[1], knots)
    for a, b in itertools.combinations(CLASSICAL, 2):
        turning = roots(lambda t: state(t, a)[1]-state(t, b)[1], knots)
        pair_knots = sorted(set(knots+turning))
        for ray, aspect in RAYS.items():
            record("aspect", [a, b], lambda t, a=a, b=b, r=ray: signed(state(t, a)[0]-state(t, b)[0]-r),
                   pair_knots, True, aspect=aspect, ray=ray)
    events.sort(key=lambda e: (e["jd"], e["kind"], e["bodies"]))
    future_moon_ingress = next((e for e in events if e["kind"] == "ingress" and e["bodies"] == ["moon"] and e["jd"] > jd0), None)
    moon_contacts = [e for e in events if e["kind"] == "aspect" and "moon" in e["bodies"] and
                     jd0 < e["jd"] < (future_moon_ingress["jd"] if future_moon_ingress else jd_end)]

    def solar_event(start, event):
        result, data = swe.rise_trans(start, swe.SUN, event | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION,
                                      (m["longitude"], m["latitude"], 0), flags=swe.FLG_SWIEPH)
        return data[0] if result == 0 else None
    rises = [solar_event(jd0-2+i, swe.CALC_RISE) for i in range(4)]
    previous_rise = max((r for r in rises if r is not None and r <= jd0), default=None)
    hour = {"status": "unavailable", "reason": "no complete sunrise/sunset bracket"}
    if previous_rise is not None:
        setting = solar_event(previous_rise+1e-7, swe.CALC_SET)
        next_rise = solar_event(previous_rise+1e-7, swe.CALC_RISE)
        if setting is not None and next_rise is not None:
            lord = DAY_LORDS[at_datetime(previous_rise).astimezone(tz).weekday()]
            value = planetary_hour(jd0, previous_rise, setting, next_rise, lord)
            if value:
                hour = {"status": "available", **value, "sunrise": stamp(previous_rise),
                        "sunset": stamp(setting), "next_sunrise": stamp(next_rise),
                        "agreement": hour_agreement(value["ruler"], angles[0], sect)}
    phase_samples = []
    for t, snapshot in zip(sample_moments, snapshots[1:]):
        pos = {b: row["longitude_deg"] for b, row in snapshot["bodies"].items()}
        phase_samples.append({"utc": t.isoformat(), "positions": pos, "body_states": snapshot,
                              "phases": compute_phase_states(pos, moment_utc=snapshot["moment_utc"])})
    source_files = [Path(__file__)] + [ROOT/"astro"/f for f in ("engine.py", "carrier_states.py", "phases.py", "dignities.py", "placements.py", "sect.py", "aspects.py")]
    chart = {"positions": positions, "bodies": rows, "cusps": cusps,
             "angles": {"asc": angles[0], "mc": angles[1]}, "house_system": "Regiomontanus", "sect": sect,
             "essential_states": compute_essential_states(positions, sect), "major_aspects": applications}
    context = {"moment_utc": physical["moment_utc"], "positions": positions,
               "houses": {"angles": chart["angles"]}, "sect": {"chart_sect": sect}}
    return {"method": "horary-v1", "input": cfg, "moment_utc": moment.isoformat(),
            "chart": chart, "body_states": physical, "carrier_states": compute_carrier_states(context, physical),
            "planetary_hour": hour,
            "consideration_facts": {"asc_early": angles[0] % 30 < 3, "asc_late": angles[0] % 30 >= 27,
                                     "moon_via_combusta": 195 <= positions["moon"] < 225,
                                     "moon_next_ingress": future_moon_ingress,
                                     "moon_exact_contacts_before_ingress": moon_contacts,
                                     "moon_void_exact_in_sign": not moon_contacts if future_moon_ingress else None,
                                     "moon_current_in_orb_applications": [a for a in applications if "moon" in a["bodies"] and a["within_orb"] and a["closing_now"]]},
            "events": events, "radicality_verdict": None,
            "phases": compute_phase_states(positions, moment_utc=physical["moment_utc"]), "phase_samples": phase_samples,
            "coverage": {"start": stamp(jd_start), "end": stamp(jd_end), "step_minutes": step_minutes,
                         "moon_to_ingress_complete": future_moon_ingress is not None,
                         "event_bodies": CLASSICAL, "past_days": cfg.get("past_days", 3),
                         "not_provided": ["automatic radicality or perfection judgment", "medical or factual personality diagnosis", "Regiomontanus H/h"]},
            "provenance": {"engine": "Astrolab a / local Swiss Ephemeris", "swisseph_version": swe.version,
                           "hour_sunrise_model": "solar center, no refraction, altitude 0m",
                           "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
                           "ephemerides_sha256": dict(physical["provenance"]["ephemeris_files"])}}


def render_wheel(facts: dict) -> str:
    chart = facts["chart"]
    planets = [{**row, "retrograde": row["speed_deg_day"] < 0} for row in chart["bodies"]]
    cusps = chart["cusps"]
    points = [{"point": name, "longitude": value} for name, value in zip(
        ("asc", "ic", "dsc", "mc"), (cusps[0], cusps[3], cusps[6], cusps[9]))]
    return draw_wheel(planets, [{"house": i+1, "longitude": value} for i, value in enumerate(cusps)],
                      points, compute_aspects(chart["positions"]))


