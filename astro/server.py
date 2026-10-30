"""Headless MCP server exposing astrology calculation tools.

FastMCP derives input schemas from the annotated function signatures and returns tool dictionaries
as structured content. The server is stateless and does not write files.
"""
from datetime import date as date_type, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import StrictFloat

from astro import engine
from astro.carrier_states import compute_carrier_states
from astro.engine import DEFAULT_BODIES, compute_body_states_series
from astro.horary import CLASSICAL, compute_facts as compute_horary_facts, render_wheel as render_horary_wheel
from astro.natal import compute_natal
from astro.partner_portrait import compute_partner_portrait
from astro.phases import compute_phase_states
from astro.profection import compute_profection_for_year
from astro.rising_hands import rising_hands
from astro.solar import compute_solar_return
from astro.transits import compute_transits_to_natal

mcp = FastMCP("Astrolab", instructions=(
    "For Портрет партнёра / partner portrait, discover partner_portrait_kit and read its manifest "
    "and all five documents before interpreting partner_portrait calculations or choosing images. "
    "The product fixes its calculation profile; ask the user for birth data/time quality and women/men, "
    "not an astrological technique list. Unknown time does not support the full house/DSC reading. "
    "body_states is an independent Engine A physical API; partner_portrait requires whole UTC seconds. "
    "The user's model composes the reading; calculated states alone are not interpretations. "
    "For хорар / horary, discover horary_kit and read its manifest and all five documents before "
    "calling horary or judging. Accept one question and fix its real asked/received date, time and "
    "place; clarify missing data instead of inventing it. Review radicality before outcome. "
    "Horary returns facts and SVG, while the client model writes the twin and reading."
))

_KIT_ROOT = Path(__file__).resolve().parents[1]
_KIT_DOCUMENTS = {
    "recipe": ("docs/partner-portrait-reading-recipe.md", "text/markdown", "reading_recipe"),
    "sources": ("docs/research/partner-portrait-method-sources.md", "text/markdown", "method_sources"),
    "twin": ("artifacts/report-templates/partner-portrait-astrology.md", "text/markdown", "working_twin"),
    "html": ("artifacts/report-templates/partner-portrait-reading.html", "text/html", "reference_html"),
    "boundary": ("docs/report-system.md", "text/markdown", "report_boundary"),
}
_HORARY_KIT_DOCUMENTS = {
    "recipe": ("docs/horary-reading-recipe.md", "text/markdown", "reading_recipe"),
    "sources": ("docs/research/horary-method-sources.md", "text/markdown", "method_sources"),
    "twin": ("artifacts/report-templates/horary-astrology.md", "text/markdown", "working_twin"),
    "html": ("artifacts/report-templates/horary-reading.html", "text/html", "reference_html"),
    "boundary": ("docs/report-system.md", "text/markdown", "report_boundary"),
}


def _canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _read_kit_documents(paths: dict, error_message: str) -> dict:
    documents = {}
    try:
        for identity, (source, mime, role) in paths.items():
            path = _KIT_ROOT / source
            if path.resolve(strict=True) != path:
                raise ValueError("kit document must be the exact allowed file")
            raw = path.read_bytes()
            documents[identity] = {
                "id": identity, "source_path": source, "role": role, "mime_type": mime,
                "byte_length": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                "required": True, "content": raw.decode("utf-8"),
            }
            if not documents[identity]["content"]:
                raise ValueError("empty kit document")
    except (OSError, UnicodeError, ValueError):
        raise ToolError(error_message) from None
    return documents


def _partner_materials() -> tuple[dict, dict]:
    documents = _read_kit_documents(_KIT_DOCUMENTS, "Partner portrait materials are unavailable or invalid")
    manifest = {
        "kit_id": "partner-portrait", "kit_version": "0.2.0",
        "documents": [{k: v for k, v in document.items() if k != "content"}
                      for document in documents.values()],
        "profile": {"id": "selected-classical-v1", "engine": "a", "zodiac": "tropical",
                    "center": "geocentric", "house_system": "Placidus", "bodies": list(DEFAULT_BODIES),
                    "rulership": "traditional", "phase_rulership": "modern",
                    "aspects": "five_major", "default_orb_deg": 6.0, "orb_range_deg": [0.0, 15.0]},
        "available_layers": ["natal", "phase_states", "motion_local", "solar_geometry",
            "declination_oob", "declination_aspects", "compatible_essential_states",
            "dignity_holdings", "lots", "subdivisions"],
        "unavailable_layers": ["station_events", "future_perfection", "heliacal_visibility",
            "acceleration", "historical_relative_speed", "fixed_stars", "antiscia", "marriage_paulus"],
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest)
    return manifest, documents


def _horary_materials() -> tuple[dict, dict]:
    documents = _read_kit_documents(_HORARY_KIT_DOCUMENTS, "Horary materials are unavailable or invalid")
    manifest = {
        "kit_id": "horary", "kit_version": "0.1.0", "method": "horary-v1",
        "documents": [{k: v for k, v in document.items() if k != "content"}
                      for document in documents.values()],
        "profile": {"id": "selected-classical-v1", "engine": "a", "zodiac": "tropical",
                    "center": "geocentric", "house_system": "Regiomontanus", "rulership": "traditional",
                    "phase_rulership": "modern", "bodies": list(DEFAULT_BODIES), "event_bodies": list(CLASSICAL),
                    "aspects": "five_major", "default_past_days": 3, "scan_range_days": [3, 366]},
        "available_layers": ["chart", "body_states", "carrier_states", "phase_states", "phase_samples",
                             "planetary_hour", "classical_aspect_events", "ingress_events", "station_events"],
        "unavailable_layers": ["Regiomontanus H/h", "automatic_radicality", "automatic_perfection_judgment",
                               "life_event_timing", "prose", "report_html"],
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest)
    return manifest, documents


def _state_utc(value: str) -> datetime:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value) is None:
        raise ToolError("datetime_utc must be a UTC ISO datetime with seconds and Z or +00:00")
    try:
        return _parse_utc(value, "datetime_utc")
    except ValueError:
        raise ToolError("datetime_utc must be a valid UTC ISO datetime") from None


def _require_state_engine() -> None:
    if engine.DEFAULT_ENGINE != "a":
        raise ToolError("These calculations require the selected Engine A; B1 full states are unsupported")


def _parse_utc(value: str, label: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO 8601 datetime") from exc
    if moment.tzinfo is None:
        raise ValueError(f"{label} must include an explicit UTC offset")
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC")
    return moment.astimezone(timezone.utc)


def _validate_location(lat: float, lon: float, *, prefix: str = "") -> None:
    lat_label = f"{prefix}lat"
    lon_label = f"{prefix}lon"
    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"{lat_label} must be between -90 and 90")
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"{lon_label} must be between -180 and 180")


def _validate_orb(orb: float) -> None:
    if orb < 0:
        raise ValueError("orb must not be negative")


@mcp.tool(name="rising_hands")
def rising_hands_tool(date: str, lat: float, lon: float, tz: int) -> dict:
    """Compute the day's rising-sign watches (the floating rising-sign clock, minute hand).

    Args:
        date: day to scan, "yyyy-MM-dd".
        lat: observation latitude (degrees).
        lon: observation longitude (degrees).
        tz: local-time DISPLAY offset in whole hours (e.g. 3 for Krasnodar).

    Returns:
        {"watches": [{"start_local": "HH:MM", "asc_sign": "<Russian sign>"}, ...]} — 12 watches.
    """
    try:
        date_type.fromisoformat(date)
    except ValueError as exc:
        raise ValueError("date must use yyyy-MM-dd") from exc
    _validate_location(lat, lon)
    if not -12 <= tz <= 14:
        raise ValueError("tz must be between -12 and 14")
    return rising_hands(date=date, lat=lat, lon=lon, tz=tz)


@mcp.tool(name="natal")
def natal_tool(
    datetime_utc: str,
    lat: float,
    lon: float,
    orb: float = 6.0,
    scheme: str = "modern",
) -> dict:
    """Assemble the natal chart structure for a UTC birth instant.

    Args:
        datetime_utc: birth instant in UTC, "yyyy-MM-ddTHH:MM:SSZ" (ISO 8601).
        lat: birth latitude (degrees).
        lon: birth longitude (degrees).
        orb: major-aspect orb in degrees.
        scheme: essential-dignity scheme, "modern" or "traditional".

    Returns:
        {"moment_utc", "location", "positions", "houses": {"cusps", "angles"}, "aspects",
        "dignities", "phases", "sect", "points": {"part_of_fortune"}, "placements"} — positions/angles in
        ecliptic degrees, bodies keyed by normalized lowercase names, placements as house numbers.
    """
    moment = _parse_utc(datetime_utc, "datetime_utc")
    _validate_location(lat, lon)
    _validate_orb(orb)
    return compute_natal(moment, lat, lon, orb=orb, scheme=scheme)


@mcp.tool(name="phase_states")
def phase_states_tool(
    positions: dict[str, StrictFloat], moment_utc: str,
    cusps: list[StrictFloat] | None = None, asc_longitude: StrictFloat | None = None,
) -> dict:
    """Transform supplied body longitudes into phase states; no ephemeris is calculated.

    The caller supplies positions for one UTC instant and may supply either twelve real
    house cusps or an explicit ASC for the equal-house special case. With neither, H/h
    remain unavailable. The input hash identifies the supplied values, not their source.
    """
    if any(re.fullmatch(r"[a-z][a-z0-9_]*", body) is None for body in positions):
        raise ValueError("positions keys must be lowercase ASCII body names")
    return compute_phase_states(
        positions, cusps=cusps, asc_longitude=asc_longitude, moment_utc=moment_utc,
    )


@mcp.tool(name="profection")
def profection_tool(
    natal_datetime_utc: str,
    lat: float,
    lon: float,
    return_year: int,
) -> dict:
    """Annual profection (whole-sign timelord) of a solar year, straight from birth data.

    Args:
        natal_datetime_utc: birth instant in UTC, "yyyy-MM-ddTHH:MM:SSZ" (ISO 8601).
        lat: birth latitude (degrees).
        lon: birth longitude (degrees).
        return_year: calendar year of the solar return (age = return_year - birth year).

    Returns:
        {"age_years", "profection_step", "asc_sign", "profected_house", "profected_sign",
        "lord_of_year", "lord_natal": {"sign", "wholesign_house"}, "house_frame"} — whole-sign
        frame; house numbers are NOT Placidus houses.
    """
    moment = _parse_utc(natal_datetime_utc, "natal_datetime_utc")
    _validate_location(lat, lon)
    return compute_profection_for_year(moment, lat, lon, return_year)


@mcp.tool(name="solar_return")
def solar_return_tool(
    natal_datetime_utc: str,
    birth_lat: float,
    birth_lon: float,
    return_year: int,
    sr_lat: float | None = None,
    sr_lon: float | None = None,
    orb: float = 2.0,
    scheme: str = "modern",
) -> dict:
    """Solar-return chart for a solar year: TRUE Sun-return instant (bisection, not the naive
    birthday chart) + the SR chart cast at that instant for the return location.

    Args:
        natal_datetime_utc: birth instant in UTC, "yyyy-MM-ddTHH:MM:SSZ" (ISO 8601).
        birth_lat, birth_lon: birth location (degrees).
        return_year: calendar year of the return.
        sr_lat, sr_lon: OPTIONAL relocation — where the return is lived; omit for birth location.
        orb: cross-aspect orb in degrees (return->natal, classical 10 bodies).
        scheme: essential-dignity scheme, "modern" or "traditional".

    Returns:
        {"return_instant_utc", "location", "natal": {"positions", "phases"}, "return": {"positions",
        "houses", "phases", "dignities", "sect", "placements"}, "sr_to_natal_aspects" (directed),
        "profection"} — degrees ecliptic, normalized lowercase body names.
    """
    moment = _parse_utc(natal_datetime_utc, "natal_datetime_utc")
    _validate_location(birth_lat, birth_lon, prefix="birth_")
    if (sr_lat is None) != (sr_lon is None):
        raise ValueError("sr_lat and sr_lon must be provided together")
    if sr_lat is not None and sr_lon is not None:
        _validate_location(sr_lat, sr_lon, prefix="sr_")
    _validate_orb(orb)
    return compute_solar_return(
        moment, birth_lat, birth_lon, return_year,
        sr_lat=sr_lat, sr_lon=sr_lon, orb=orb, scheme=scheme,
    )


@mcp.tool(name="transits")
def transits_tool(
    natal_datetime_utc: str,
    lat: float,
    lon: float,
    range_start_utc: str,
    range_end_utc: str,
    step_days: float = 7.0,
    orb: float = 1.0,
    solar_year_start_utc: str | None = None,
) -> dict:
    """Transit timeline over a period: dated exact-pass EVENTS of transiting bodies (sun..pluto +
    north node; no Moon — daily steps can't resolve it) over natal planets and angles, plus
    CARRIER WINDOWS — slow movers' retro passes merged into one open->exact(s)->close theme.
    Event and peak instants are estimates from the configured sampling step, not separately
    refined astronomical roots.

    Args:
        natal_datetime_utc: birth instant in UTC, "yyyy-MM-ddTHH:MM:SSZ".
        lat, lon: birth location (degrees) — natal angles are computed here.
        range_start_utc, range_end_utc: scan period, UTC ISO 8601.
        step_days: sampling step (use 2-3 for clean carrier windows; default 7).
        orb: event orb in degrees (default 1.0).
        solar_year_start_utc: OPTIONAL solar-return instant — adds zone (tail/core/horizon) to
            each carrier window and drops themes that closed before the year opened.

    Returns:
        {"timeline": [{transit_body, natal_target, aspect, exact_date, min_orb_deg,
        window_start, window_end}], "carrier_windows": [{window_open, window_close, transit_body,
        aspect, natal_target, zone, passes, exact_dates, tightest_orb_deg}]}.
    """
    natal_moment = _parse_utc(natal_datetime_utc, "natal_datetime_utc")
    range_start = _parse_utc(range_start_utc, "range_start_utc")
    range_end = _parse_utc(range_end_utc, "range_end_utc")
    _validate_location(lat, lon)
    if range_end <= range_start:
        raise ValueError("range_end_utc must be later than range_start_utc")
    if step_days <= 0:
        raise ValueError("step_days must be greater than zero")
    _validate_orb(orb)

    return compute_transits_to_natal(
        natal_moment, lat, lon,
        range_start, range_end,
        step_days=step_days, orb=orb,
        solar_year_start_utc=(
            _parse_utc(solar_year_start_utc, "solar_year_start_utc")
            if solar_year_start_utc else None
        ),
    )


@mcp.tool(name="body_states")
def body_states_tool(datetime_utc: str, bodies: list[str] | None = None) -> dict:
    """Calculate named physical states and provenance with Engine A; fractional UTC seconds are retained.

    Geocentric tropical apparent coordinates of date include real latitude, numerical longitude
    speed and equatorial declination. Default: ten planets. Also supports true north node,
    mean-apogee Lilith and Chiron. This is independent of partner portraits and calculates no prose.
    """
    moment = _state_utc(datetime_utc)
    allowed = set(DEFAULT_BODIES) | {"north_node", "lilith", "chiron"}
    if bodies is not None and (not bodies or len(set(bodies)) != len(bodies)
                               or any(body not in allowed for body in bodies)):
        raise ToolError("bodies must contain unique supported lowercase body IDs")
    _require_state_engine()
    try:
        return compute_body_states_series([moment], bodies=bodies)[0]
    except Exception:
        raise ToolError("Body-state calculation failed; Engine A needs verified ephemeris files, "
                        "SWISS_EPHE_PATH and no SE_EPHE_PATH override") from None


@mcp.tool(name="partner_portrait_kit")
def partner_portrait_kit_tool(
    document: Literal["manifest", "recipe", "sources", "twin", "html", "boundary"] = "manifest",
) -> dict:
    """Read the partner portrait manifest or one of its five complete UTF-8 documents by fixed ID.

    No checkout or resource support is required. Hashes and byte lengths identify the exact
    delivered texts. HTML is returned as source data; this tool accepts no filesystem path.
    """
    manifest, documents = _partner_materials()
    return manifest if document == "manifest" else documents[document]


@mcp.tool(name="partner_portrait")
def partner_portrait_tool(
    datetime_utc: str, lat: StrictFloat, lon: StrictFloat,
    partner: Literal["women", "men"], orb: StrictFloat = 6.0,
) -> dict:
    """Build partner portrait calculations; read partner_portrait_kit before interpreting or choosing images.

    Requires known birth time at whole UTC seconds and selected Engine A. Fixed tropical,
    geocentric, Placidus, ten-planet selected-classical-v1 profile; women uses Moon/Venus/VII,
    men Sun/Mars/VII. Returns the natal, common phases, physical/carrier states, existing
    derivatives and exact readable-kit manifest. The user's model writes the interpretation.
    """
    moment = _state_utc(datetime_utc)
    if moment.microsecond:
        raise ToolError("partner_portrait requires whole seconds; body_states retains fractional seconds")
    _validate_location(lat, lon)
    if not math.isfinite(orb) or not 0.0 <= orb <= 15.0:
        raise ToolError("orb must be finite and in [0,15]")
    _require_state_engine()
    manifest, _ = _partner_materials()
    try:
        natal = compute_natal(moment, lat, lon, bodies=list(DEFAULT_BODIES),
                              orb=orb, scheme="traditional", engine="a")
        physical = compute_body_states_series([moment])[0]
        carriers = compute_carrier_states(natal, physical)
        speeds = {"moment_utc": physical["moment_utc"], "units": "deg/day",
                  "source": "body_states.provenance sha256:" + _canonical_hash(physical["provenance"]),
                  "values": {body: row["longitude_speed_deg_per_day"]
                             for body, row in physical["bodies"].items()}}
        result = compute_partner_portrait(natal, partner=partner, speeds=speeds, orb=orb)
        result.update(body_states=physical, carrier_states=carriers, kit=manifest)
        result["settings"].update(state_profile="selected-classical-v1", engine="a", house_frame="placidus")
        operators = ("server.py", "engine.py", "natal.py", "partner_portrait.py", "carrier_states.py",
                     "phases.py", "aspects.py", "dignities.py", "placements.py", "sect.py")
        result["provenance"] = {
            "kit_manifest_sha256": manifest["manifest_sha256"],
            "operator_sha256": {"astro/" + name: hashlib.sha256(
                (Path(__file__).resolve().parent / name).read_bytes()).hexdigest() for name in operators},
        }
        return result
    except Exception:
        raise ToolError("Partner portrait calculation failed; check Engine A ephemeris configuration "
                        "and a valid Placidus birth input") from None


@mcp.tool(name="horary_kit")
def horary_kit_tool(
    document: Literal["manifest", "recipe", "sources", "twin", "html", "boundary"] = "manifest",
) -> dict:
    """Read the horary manifest or one of five complete UTF-8 documents by fixed ID.

    Read the manifest and all five before horary calculations or judgment. The recipe includes
    the full input contract; no checkout or hidden reference is needed. Hashes identify exact
    delivered bytes. HTML is source data; no filesystem path is accepted.
    """
    manifest, documents = _horary_materials()
    return manifest if document == "manifest" else documents[document]


@mcp.tool(name="horary")
def horary_tool(input: dict) -> dict:
    """Compute reviewed horary facts and wheel SVG; read horary_kit and all five documents first.

    input follows astrolab.horary.input.v1 in the recipe: one accepted question and a fixed,
    explicit asked/received moment/place. Engine A only, tropical/geocentric Regiomontanus,
    traditional rulership; seven event planets, ten common physical/carrier/phase states.
    past_days defaults to 3; past_days and scan_days accept integers 3..366. H/h unavailable.
    Returns facts, wheel_svg, kit and provenance; no files, prose or automatic radicality.
    The client model judges the chart before its outcome and writes the twin and reading.
    """
    _require_state_engine()
    manifest, _ = _horary_materials()
    try:
        facts = compute_horary_facts(input)
        svg = render_horary_wheel(facts)
        paths = ["astro/" + name for name in ("server.py", "horary.py", "engine.py", "carrier_states.py",
                 "phases.py", "dignities.py", "placements.py", "sect.py", "aspects.py")]
        paths.append("artifacts/renderer/render_chart.py")
        provenance = {"kit_manifest_sha256": manifest["manifest_sha256"],
                      "input_sha256": _canonical_hash(input), "facts_sha256": _canonical_hash(facts),
                      "payload_hash_serialization": "JSON UTF-8; sort_keys=true; ensure_ascii=false; compact separators; allow_nan=false",
                      "operator_sha256": {path: hashlib.sha256((_KIT_ROOT / path).read_bytes()).hexdigest()
                                          for path in paths}}
        return {"facts": facts, "wheel_svg": svg, "kit": manifest, "provenance": provenance}
    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc).startswith("unsupported Regiomontanus geometry"):
            raise ToolError("Horary adapter: unsupported Regiomontanus geometry; no houses, sect or SVG returned") from None
        raise ToolError("Horary calculation failed; use an accepted complete fixed-moment input and "
                        "Engine A with verified ephemeris files, SWISS_EPHE_PATH and no SE_EPHE_PATH override") from None


if __name__ == "__main__":
    import os

    # HTTP defaults to loopback for source runs. The container overrides the host to 0.0.0.0 so
    # Docker can forward a loopback-bound host port; authentication and TLS belong at ingress.
    if os.environ.get("ASTRO_MCP_TRANSPORT", "stdio").lower() == "http":
        mcp.run(
            transport="http",
            host=os.environ.get("ASTRO_MCP_HOST", "127.0.0.1"),
            port=int(os.environ.get("ASTRO_MCP_PORT", "8400")),
        )
    else:
        mcp.run()
