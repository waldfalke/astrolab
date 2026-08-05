"""Tests for the transits-to-natal composite (recipe = run_transits_to_natal.ps1 range-scan).

Layers: pure carrier-window merge on synthetic events; self-validating property (transiting Sun
conjunct natal Sun peaks on the solar-return date); recipe golden (witnessed run, values below).
"""
from datetime import datetime, timezone
import pytest

from astro.transits import (
    compute_carrier_windows,
    compute_transit_events,
    compute_transits_to_natal,
)

NATAL_MOMENT = datetime(1946, 6, 14, 14, 54, 0, tzinfo=timezone.utc)
LAT, LON = 40.7, -73.8164


@pytest.mark.parametrize("step_days", [0, -1])
def test_transit_events_reject_nonpositive_step_before_engine_call(step_days):
    with pytest.raises(ValueError, match="step_days must be greater than zero"):
        compute_transit_events(
            NATAL_MOMENT,
            LAT,
            LON,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
            step_days=step_days,
        )


def _ev(body, target, aspect, exact, orb, start, end):
    return {"transit_body": body, "natal_target": target, "aspect": aspect,
            "exact_date": exact, "min_orb_deg": orb, "window_start": start, "window_end": end}


def test_carrier_windows_merge_retro_passes_pure():
    """Three retro passes of one theme = ONE window (earliest open -> latest close), peak = the
    tightest pass; fast movers stay out; pre-anchor windows are dropped; zones classify."""
    events = [
        _ev("jupiter", "IC", "trine", "2025-11-10", 0.4, "2025-11-01", "2025-11-20"),
        _ev("jupiter", "IC", "trine", "2026-01-15", 0.1, "2026-01-05", "2026-01-25"),
        _ev("jupiter", "IC", "trine", "2026-07-02", 0.3, "2026-06-20", "2026-07-10"),
        _ev("mars", "sun", "square", "2025-12-01", 0.2, "2025-11-28", "2025-12-03"),  # fast
        _ev("saturn", "moon", "square", "2025-03-01", 0.2, "2025-02-20", "2025-03-10"),  # old
    ]
    anchor = datetime(2025, 6, 13, tzinfo=timezone.utc)
    wins = compute_carrier_windows(events, solar_year_start_utc=anchor)
    assert len(wins) == 1  # mars = fast trigger, saturn window closed before the anchor
    w = wins[0]
    assert (w["window_open"], w["window_close"]) == ("2025-11-01", "2026-07-10")
    assert w["passes"] == 3
    assert w["tightest_orb_deg"] == 0.1
    assert w["zone"] == "core"  # peak 2026-01-15 inside [2025-06-13, +365.25d]
    # no anchor -> nothing dropped, zone empty
    wins_free = compute_carrier_windows(events)
    assert {w["transit_body"] for w in wins_free} == {"jupiter", "saturn"}
    assert all(w["zone"] == "" for w in wins_free)


def test_sun_conjunct_natal_sun_peaks_on_solar_return_date():
    """Self-validating: the transiting-Sun-conjunct-natal-Sun event IS the solar return —
    its exact date must equal the witnessed SR instant date (2025-06-13, recipe-confirmed)."""
    events = compute_transit_events(
        NATAL_MOMENT, LAT, LON,
        datetime(2025, 6, 1, tzinfo=timezone.utc), datetime(2025, 6, 28, tzinfo=timezone.utc),
        step_days=2.0, transit_bodies=["sun"],
    )
    hits = [e for e in events
            if e["natal_target"] == "sun" and e["aspect"] == "conjunction"]
    assert len(hits) == 1
    assert hits[0]["exact_date"] == "2025-06-13"
    # min_orb is the recipe's parabolic ESTIMATE on a V-shaped series — coarse for fast bodies at
    # 2-day steps (the DATE is the refined quantity); the recipe-golden test checks exact equality.
    assert hits[0]["min_orb_deg"] <= 1.0


def test_matches_recipe_golden_witnessed_run():
    """Witnessed golden (run_transits_to_natal.ps1, Trump fixture, 2025-06-01..09-01, step 2d,
    anchor = SR instant; run transit_timeline_trump_tl2025_20260703_231634): the port matched the
    recipe on ALL 108 timeline events (orbs to 2e-3, window dates exact) and ALL 11 carrier
    windows (zones, passes, exact dates). Compact spot-set embedded here."""
    out = compute_transits_to_natal(
        NATAL_MOMENT, LAT, LON,
        datetime(2025, 6, 1, tzinfo=timezone.utc), datetime(2025, 9, 1, tzinfo=timezone.utc),
        step_days=2.0,
        solar_year_start_utc=datetime(2025, 6, 13, 16, 57, 23, tzinfo=timezone.utc),
    )
    assert len(out["timeline"]) == 108
    assert len(out["carrier_windows"]) == 11

    by_key = {(e["transit_body"], e["natal_target"], e["aspect"], e["exact_date"]): e
              for e in out["timeline"]}
    e = by_key[("venus", "mars", "trine", "2025-06-02")]
    assert (e["min_orb_deg"], e["window_start"], e["window_end"]) == (0.083, "2025-06-01", "2025-06-03")
    e = by_key[("north_node", "saturn", "trine", "2025-06-06")]
    assert e["min_orb_deg"] == 0.018

    cw = {(w["transit_body"], w["natal_target"], w["aspect"]): w for w in out["carrier_windows"]}
    # retro double-pass merged into ONE theme with two exact dates
    w = cw[("north_node", "moon", "square")]
    assert (w["passes"], w["exact_dates"]) == (2, "2025-06-28; 2025-07-02")
    assert (w["window_open"], w["window_close"], w["zone"]) == ("2025-06-21", "2025-07-10", "core")
    # tail zone: peaked before the SR anchor, still in orb at the year open
    w = cw[("jupiter", "ASC", "sextile")]
    assert (w["zone"], w["tightest_orb_deg"]) == ("tail", 0.137)
    w = cw[("uranus", "ASC", "square")]
    assert (w["zone"], w["exact_dates"]) == ("core", "2025-07-06")


def test_composite_shape():
    out = compute_transits_to_natal(
        NATAL_MOMENT, LAT, LON,
        datetime(2025, 6, 1, tzinfo=timezone.utc), datetime(2025, 7, 15, tzinfo=timezone.utc),
        step_days=3.0, transit_bodies=["jupiter", "sun"],
        solar_year_start_utc=datetime(2025, 6, 13, 16, 57, 23, tzinfo=timezone.utc),
    )
    assert set(out) == {"timeline", "carrier_windows"}
    for w in out["carrier_windows"]:
        assert w["transit_body"] == "jupiter"  # sun is a fast trigger, never a carrier
