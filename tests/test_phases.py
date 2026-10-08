"""Synthetic numeric contracts for the Zakharian phase operator."""

import csv
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE_RUNNER = ROOT / "artifacts/mcp-recipes/run_phase_vectors.ps1"


def compute_phase_states(*args, **kwargs):
    from astro.phases import compute_phase_states as calculate

    return calculate(*args, **kwargs)


def test_book_table_22_all_sign_phases():
    # Literal Table 2.2 rows carried by the original recipe, independent of the Python constants.
    expected = {
        "sun": [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8],
        "moon": [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        "mercury": ["11/8", "12/9", "1/10", "2/11", "3/12", "4/1",
                    "5/2", "6/3", "7/4", "8/5", "9/6", "10/7"],
        "venus": ["12/7", "1/8", "2/9", "3/10", "4/11", "5/12",
                  "6/1", "7/2", "8/3", "9/4", "10/5", "11/6"],
        "mars": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "jupiter": [5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4],
        "saturn": [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3],
        "uranus": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2],
        "neptune": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1],
        "pluto": [6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
    }
    for sign_index in range(12):
        positions = {body: float(sign_index * 30) for body in expected}
        states = compute_phase_states(positions)["states"]
        for body, row in expected.items():
            assert states[body]["Z"] == str(row[sign_index]), (body, sign_index)


@pytest.mark.parametrize("asc", [1.0, 10.0, 100.0])
def test_equal_house_just_before_asc_is_final_microphase(asc):
    import math

    states = compute_phase_states(
        {"mars": math.nextafter(asc, -math.inf)}, asc_longitude=asc
    )["states"]
    assert (states["mars"]["H_house"], states["mars"]["h_micro"]) == (12, 12)
    at_asc = compute_phase_states({"mars": asc}, asc_longitude=asc)["states"]
    assert (at_asc["mars"]["H_house"], at_asc["mars"]["h_micro"]) == (1, 1)


def test_micro_boundaries_real_wrap_house_and_dual_cycles():
    cusps = [350, 10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310]
    phases = compute_phase_states(
        {"mars": 2.5, "mercury": 150.0, "venus": 180.0, "sun": 300.0,
         "uranus": 300.0},
        cusps=cusps, moment_utc="2000-01-01T00:00:00Z",
    )
    states = phases["states"]
    assert phases["house_frame"] == "placidus"
    assert states["mars"]["z_micro"] == 2  # exact 2.5° belongs to microphase 2
    assert (states["mars"]["H_house"], states["mars"]["h_micro"]) == (1, 8)
    assert states["mercury"]["Z"] == "4/1"
    assert states["venus"]["Z"] == "6/1"
    assert states["sun"]["Z"] == "7"
    assert states["sun"]["D_pos_ruler_phase"] == 1
    assert states["sun"]["dignity_zakharian"] == "изгнание"
    assert states["mercury"]["D_pos_ruler_phase"] == 1


def test_missing_house_frame_and_dispositor_are_explicit():
    phases = compute_phase_states({"sun": 60.0, "chiron": 90.0})
    sun = phases["states"]["sun"]
    assert phases["house_frame"] == "unavailable"
    assert sun["Z"] == "11"
    assert sun["H_house"] is None and sun["h_micro"] is None
    assert sun["D_pos_ruler_phase"] is None
    assert sun["availability"]["D"] == "missing_dispositor:mercury"
    assert phases["states"]["chiron"]["availability"]["Z"] == "unsupported_body"
    assert phases["states"]["chiron"]["Z"] is None


def test_equal_house_requires_explicit_asc_and_provenance_tracks_actual_inputs():
    positions = {"mars": 2.5}
    fallback = compute_phase_states(positions, asc_longitude=350.0,
                                    moment_utc="2000-01-01T00:00:00Z")
    assert fallback["house_frame"] == "equal_asc"
    assert (fallback["states"]["mars"]["H_house"],
            fallback["states"]["mars"]["h_micro"]) == (1, 6)
    assert fallback["input_sha256"] != compute_phase_states(
        {"mars": 2.6}, asc_longitude=350.0,
        moment_utc="2000-01-01T00:00:00Z")["input_sha256"]
    assert fallback["input_sha256"] != compute_phase_states(
        positions, asc_longitude=350.0,
        moment_utc="2000-01-02T00:00:00Z")["input_sha256"]
    assert fallback["input_sha256"] != compute_phase_states(positions)["input_sha256"]
    assert fallback["input"]["positions"] == positions
    assert fallback["input"]["asc_longitude"] == 350.0
    assert fallback["input"]["moment_utc"] == "2000-01-01T00:00:00Z"
    assert fallback["input"]["operator_version"] == fallback["operator_version"]


def test_nextafter_sign_and_micro_boundaries():
    before_zero = math.nextafter(0.0, -math.inf)
    before_2_5 = math.nextafter(2.5, 0.0)
    after_2_5 = math.nextafter(2.5, math.inf)
    before_30 = math.nextafter(30.0, 0.0)
    after_30 = math.nextafter(30.0, math.inf)
    rows = [compute_phase_states({"mars": value})["states"]["mars"] for value in
            (before_zero, 0.0, before_2_5, 2.5, after_2_5,
             before_30, 30.0, after_30)]
    assert [(row["sign"], row["z_micro"]) for row in rows] == [
        ("Рыбы", 12), ("Овен", 1), ("Овен", 1), ("Овен", 2),
        ("Овен", 2), ("Овен", 12), ("Телец", 1), ("Телец", 1),
    ]


@pytest.mark.parametrize(
    ("body", "raw", "sign"),
    [
        ("sun", 29.99999, "Овен"),
        ("sun", 30.00001, "Телец"),
        ("sun", 359.99999, "Рыбы"),
        ("sun", math.nextafter(360.0, 0.0), "Рыбы"),
        ("sun", 360.0, "Овен"),
        ("sun", -0.00001, "Рыбы"),
        ("chiron", 359.99999, "Рыбы"),
    ],
)
def test_machine_degrees_retain_normalized_precision_at_sign_boundaries(body, raw, sign):
    result = compute_phase_states({body: raw})
    row = result["states"][body]
    normalized = result["input"]["positions"][body]
    sign_start = {"Овен": 0.0, "Телец": 30.0, "Рыбы": 330.0}[sign]
    assert row["sign"] == sign
    assert row["longitude"] == normalized
    assert row["deg_in_sign"] == normalized - sign_start
    assert 0.0 <= row["deg_in_sign"] < 30.0


def test_nextafter_house_cusp_and_microhouse_boundaries():
    cusps = [350, 5, 35, 65, 95, 125, 155, 185, 215, 245, 275, 305]
    positions = {"mars": math.nextafter(5.0, 0.0),
                 "sun": 5.0,
                 "moon": math.nextafter(5.0, math.inf),
                 "venus": math.nextafter(351.25, 350.0),
                 "mercury": 351.25,
                 "jupiter": math.nextafter(351.25, math.inf)}
    states = compute_phase_states(positions, cusps=cusps)["states"]
    assert [(states[name]["H_house"], states[name]["h_micro"])
            for name in ("mars", "sun", "moon", "venus", "mercury", "jupiter")] == [
        (1, 12), (2, 1), (2, 1), (1, 1), (1, 2), (1, 2),
    ]


@pytest.mark.parametrize("bad", [True, math.nan, math.inf, "12.5"])
def test_invalid_position_is_rejected(bad):
    with pytest.raises(ValueError, match="position sun"):
        compute_phase_states({"sun": bad})


@pytest.mark.parametrize("cusps", [
    [0] * 12,
    [i * 30 for i in range(11)],
    [0, 30, 90, 60, 120, 150, 180, 210, 240, 270, 300, 330],
    [0, 30, 60, 90, 120, math.nan, 180, 210, 240, 270, 300, 330],
])
def test_invalid_cusp_frame_is_rejected(cusps):
    with pytest.raises(ValueError):
        compute_phase_states({"sun": 60.0}, cusps=cusps)


def test_conflicting_frames_and_invalid_moment_are_rejected():
    with pytest.raises(ValueError, match="either"):
        compute_phase_states({"sun": 60.0}, cusps=[i * 30 for i in range(12)],
                             asc_longitude=0.0)
    with pytest.raises(ValueError, match="moment_utc"):
        compute_phase_states({"sun": 60.0}, moment_utc="not-an-instant")


def test_unsupported_body_has_uniform_row_keys():
    states = compute_phase_states({"sun": 60.0, "chiron": 90.0})["states"]
    assert set(states["chiron"]) == set(states["sun"])


def test_batch_cli_reads_json_and_emits_only_json():
    batch = {"batch": [
        {"positions": {"mars": 0.0}, "moment_utc": "2000-01-01T00:00:00Z"},
        {"positions": {"mars": 30.0}, "asc_longitude": 0.0,
         "moment_utc": "2000-01-02T00:00:00Z"},
    ]}
    result = subprocess.run([sys.executable, "-m", "astro.phases"],
                            input=json.dumps(batch), capture_output=True,
                            text=True, encoding="utf-8", timeout=15, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert len(output["results"]) == 2
    assert output["results"][0]["states"]["mars"]["Z"] == "1"
    assert output["results"][1]["states"]["mars"]["Z"] == "2"
    assert output["results"][0]["house_frame"] == "unavailable"
    assert output["results"][1]["house_frame"] == "equal_asc"


def test_ps_adapter_serializes_shared_operator_on_synthetic_real_house_frame(tmp_path):
    if not PHASE_RUNNER.is_file():
        pytest.skip("PowerShell phase adapter is not shipped in this source tree")
    if shutil.which("pwsh") is None:
        pytest.skip("PowerShell 7 is unavailable")
    chart = tmp_path / "charts" / "synthetic" / "outputs"
    chart.mkdir(parents=True)
    positions = {"sun": 300.0, "moon": 2.5, "mercury": 150.0, "venus": 180.0,
                 "mars": 2.5, "jupiter": 270.0, "saturn": 90.0, "uranus": 300.0,
                 "neptune": 330.0, "pluto": 210.0}
    cusps = [350, 10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310]
    with (chart / "natal_longitudes.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("body", "longitude"))
        writer.writerows((body, lon) for body, lon in positions.items())
    with (chart / "houses_placidus.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("house", "longitude"))
        writer.writerows((i, lon) for i, lon in enumerate(cusps, 1))
    (chart.parent / "chart.yaml").write_text(
        "chart_id: synthetic\nbirth:\n  utc_datetime: 2000-01-01T00:00:00Z\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(PHASE_RUNNER), "-ChartId", "synthetic",
         "-ChartsRoot", str(tmp_path / "charts"), "-OutputBase", str(tmp_path / "runs"),
         "-PythonExe", sys.executable],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    run_dirs = list((tmp_path / "runs").glob("phase_vectors_synthetic*"))
    assert len(run_dirs) == 1
    with (run_dirs[0] / "01_phase_vectors.csv").open(encoding="utf-8-sig", newline="") as stream:
        serialized = {row["body"]: row for row in csv.DictReader(stream)}
    current = compute_phase_states(
        positions, cusps=cusps, moment_utc="2000-01-01T00:00:00Z")["states"]
    assert set(serialized) == set(positions)
    assert not (chart / "phase_vectors.csv").exists()
    for body, old in serialized.items():
        for key in ("Z", "z_micro", "H_house", "h_micro", "D_pos_ruler_phase",
                    "dignity_zakharian", "ruler_by_phase", "ruler_by_position"):
            assert str(current[body][key]) == old[key], (body, key)
