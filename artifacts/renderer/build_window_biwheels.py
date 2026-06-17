#!/usr/bin/env python3
"""
build_window_biwheels.py — natal+transit biwheels, one per carrier window.

GENERATIVE, chart-agnostic. Reads the carrier-window ledger of ANY chart and emits one biwheel
(natal inner ring + transit outer ring, with the window's carrying aspects as chords) per window.
Nothing about a specific chart is hardcoded — windows, dates, aspects and orbs all come from data.

PIPELINE (per window)
  1. Group rows of 03_carrier_windows.csv into windows by overlapping [window_open, window_close].
  2. Peak date = the median exact-date of the group. Snapshot transit positions there via
     run_natal_snapshot.ps1 (chart coords) → 06_core_longitudes.csv.
  3. Write outer-planets CSV (10 bodies) + outer-aspects CSV (the group's transit→natal aspects;
     is_exact = orb <= 1.0) and call render_chart.py --outer-planets/--outer-aspects.

INPUTS
  --chart-dir   charts/<id> (or .private/charts/<id>) — has outputs/ for the natal inner ring
  --carrier-csv 03_carrier_windows.csv produced by run_transits_to_natal.ps1
  --lat --lon   chart coordinates for the transit snapshot (decimal degrees)
  --out-dir     where to write per-window SVGs (e.g. a packs/ or temp dir — biwheels of a PII chart
                are PII; keep them under .private/ or a scratch dir, never in git)
  --snapshot-recipe  path to run_natal_snapshot.ps1 (default: artifacts/mcp-recipes/run_natal_snapshot.ps1)

NOTE Carrier windows are SLOW movers only (Jupiter..Pluto) by construction of the ledger; fast
     bodies are point-triggers and get no window. One SVG per carrier window.
"""
import argparse, csv, glob, subprocess, sys, statistics
from datetime import date
from pathlib import Path

BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


def parse_date(s):
    s = s.strip()
    if not s:
        return None
    # exact_dates may be "2026-07-26" or "2026-11-16; 2027-01-07"
    first = s.split(";")[0].strip()
    y, m, d = (int(x) for x in first.split("-"))
    return date(y, m, d)


def load_carrier(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "transit_body": r["transit_body"].strip().lower(),
                "aspect": r["aspect"].strip().lower(),
                "natal_target": r["natal_target"].strip().lower(),
                "open": parse_date(r["window_open"]),
                "close": parse_date(r["window_close"]),
                "exact": parse_date(r["exact_dates"]),
                "orb": float(r["tightest_orb_deg"]),
            })
    return rows


def group_windows(rows, gap_days=35):
    """Group carrier rows into windows by clustering on PEAK (exact) date.

    Slow-carrier windows are wide and overlap transitively (Neptune/Uranus/Pluto can chain across a
    whole year), so grouping by [open,close] overlap collapses everything into one. The exact passes,
    however, are spaced — so we cluster on exact date: a gap > gap_days between consecutive peaks
    starts a new window. Each cluster = one biwheel.
    """
    rows = sorted([r for r in rows if r["exact"]], key=lambda r: r["exact"])
    if not rows:
        return []
    groups, cur = [], {"rows": [rows[0]], "open": rows[0]["open"], "close": rows[0]["close"]}
    last_peak = rows[0]["exact"]
    for r in rows[1:]:
        if (r["exact"] - last_peak).days > gap_days:
            groups.append(cur)
            cur = {"rows": [r], "open": r["open"], "close": r["close"]}
        else:
            cur["rows"].append(r)
            cur["open"] = min(cur["open"], r["open"]) if cur["open"] and r["open"] else (cur["open"] or r["open"])
            cur["close"] = max(cur["close"], r["close"]) if cur["close"] and r["close"] else (cur["close"] or r["close"])
        last_peak = r["exact"]
    groups.append(cur)
    return groups


def peak_date(group):
    exacts = sorted(r["exact"] for r in group["rows"] if r["exact"])
    if not exacts:
        return group["open"]
    return exacts[len(exacts) // 2]  # median exact date


def run_snapshot(recipe, case_id, lat, lon, dt_utc, results_root):
    subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(recipe),
         "-CaseId", case_id, "-Latitude", str(lat), "-Longitude", str(lon),
         "-DateTimeUtc", dt_utc],
        capture_output=True, text=True, check=True)
    g = sorted(glob.glob(str(results_root / f"natal_{case_id}_*")))
    if not g:
        raise SystemExit(f"snapshot produced no output for {case_id}")
    lons = {}
    with open(Path(g[-1]) / "06_core_longitudes.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            lons[r["body"].strip().lower()] = float(r["longitude"].replace(",", "."))
    return lons


def main():
    ap = argparse.ArgumentParser(description="Build natal+transit biwheels, one per carrier window.")
    ap.add_argument("--chart-dir", required=True)
    ap.add_argument("--carrier-csv", required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--snapshot-recipe",
                    default=str(Path(__file__).resolve().parents[1] / "mcp-recipes" / "run_natal_snapshot.ps1"))
    ap.add_argument("--renderer", default=str(Path(__file__).resolve().parent / "render_chart.py"))
    ap.add_argument("--results-root",
                    default=str(Path(__file__).resolve().parents[1] / "results"))
    args = ap.parse_args()

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    results_root = Path(args.results_root)
    groups = group_windows(load_carrier(args.carrier_csv))
    print(f"{len(groups)} carrier windows found")

    for i, g in enumerate(groups, 1):
        pk = peak_date(g)
        tag = f"win{i:02d}_{pk:%Y%m%d}"
        carriers = sorted({r["transit_body"] for r in g["rows"]})
        label = f"транзит {pk:%d.%m.%Y}"
        lons = run_snapshot(args.snapshot_recipe, tag, args.lat, args.lon,
                            f"{pk:%Y-%m-%d}T12:00:00Z", results_root)

        op = out / f"{tag}_outer.csv"
        with open(op, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["body", "longitude"])
            for b in BODIES:
                if b in lons:
                    w.writerow([b, f"{lons[b]:.4f}"])
        oa = out / f"{tag}_asp.csv"
        with open(oa, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["transit_body", "natal_body", "aspect", "orb", "is_exact"])
            for r in g["rows"]:
                w.writerow([r["transit_body"], r["natal_target"], r["aspect"],
                            f"{r['orb']:.3f}", "TRUE" if r["orb"] <= 1.0 else "FALSE"])

        wdir = out / tag; wdir.mkdir(exist_ok=True)
        res = subprocess.run(
            [sys.executable, args.renderer, "--chart-dir", args.chart_dir,
             "--output-dir", str(wdir), "--outer-planets", str(op),
             "--outer-aspects", str(oa), "--outer-label", label],
            capture_output=True, text=True)
        svgs = list(wdir.glob("*chart_wheel*.svg")) or list(wdir.glob("*.svg"))
        status = f"OK {svgs[0].name}" if (res.returncode == 0 and svgs) else f"FAIL {res.stderr[-200:]}"
        print(f"  {tag} [{', '.join(carriers)}]: {status}")


if __name__ == "__main__":
    main()
