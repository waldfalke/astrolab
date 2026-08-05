"""Headless MCP server exposing astrology calculation tools.

FastMCP derives input schemas from the annotated function signatures and returns tool dictionaries
as structured content. The server is stateless and does not write files.
"""
from datetime import date as date_type, datetime, timedelta, timezone

from fastmcp import FastMCP

from astro.natal import compute_natal
from astro.profection import compute_profection_for_year
from astro.rising_hands import rising_hands
from astro.solar import compute_solar_return
from astro.transits import compute_transits_to_natal

mcp = FastMCP("Astrolab")


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
        "dignities", "sect", "points": {"part_of_fortune"}, "placements"} — positions/angles in
        ecliptic degrees, bodies keyed by normalized lowercase names, placements as house numbers.
    """
    moment = _parse_utc(datetime_utc, "datetime_utc")
    _validate_location(lat, lon)
    _validate_orb(orb)
    return compute_natal(moment, lat, lon, orb=orb, scheme=scheme)


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
        {"return_instant_utc", "location", "natal": {"positions"}, "return": {"positions",
        "houses", "dignities", "sect", "placements"}, "sr_to_natal_aspects" (directed),
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
