"""Engine-free partner-portrait derivatives over an existing compute_natal JSON.

Source choices and limits: docs/research/partner-portrait-method-sources.md.
This recipe supplies evidence, never a person count or a generated interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from astro.partner_portrait import (
    VERSION, RULERS, CLASSICAL, FIRMICUS, PTOLEMY, VALENS, GREENBAUM, TERMS, DECAN_CYCLE,
    MAJOR_ASPECTS, _number, _longitude, _point, subdivisions, contact_motion, compute_partner_portrait,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--natal", type=Path, required=True)
    parser.add_argument("--partner", choices=("women", "men"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--speeds", type=Path)
    parser.add_argument("--orb", type=float, default=6.0)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output directory already exists; choose a new run directory")
    inputs = {"natal.json": args.natal.resolve()}
    if args.speeds:
        inputs["speeds.json"] = args.speeds.resolve()
    for path in inputs.values():
        for parent in path.parents:
            if parent.name.casefold() == ".private" and not output.is_relative_to(parent):
                raise ValueError("private input requires output under the same .private root")
    raw = {name: path.read_bytes() for name, path in inputs.items()}
    result = compute_partner_portrait(json.loads(raw["natal.json"]), partner=args.partner,
                                     speeds=json.loads(raw["speeds.json"]) if args.speeds else None,
                                     orb=args.orb)
    code = ("artifacts/mcp-recipes/partner_portrait.py", "astro/partner_portrait.py",
            "astro/phases.py", "astro/aspects.py",
            "astro/dignities.py", "astro/placements.py", "astro/sect.py")
    result["provenance"] = {
        "input_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()},
        "operator_sha256": {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest() for path in code},
        "source_files": {name: f"sources/{name}" for name in raw},
    }
    payload = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    output.mkdir(parents=True)
    (output / "sources").mkdir()
    for name, data in raw.items():
        (output / "sources" / name).write_bytes(data)
    (output / "01_partner_portrait.json").write_bytes(payload)
    summary = (f"RECIPE=partner-portrait\nVERSION={VERSION}\nPARTNER={args.partner}\n"
               f"SECT={result['sect']}\nPHASE_ORIGIN={result['phase_origin']}\n"
               f"MOTION={'provided' if args.speeds else 'unavailable'}\n"
               f"OUTPUT_HASH={hashlib.sha256(payload).hexdigest()}\n")
    (output / "00_summary.txt").write_text(summary, encoding="utf-8")
    print(f"Partner portrait calculation written: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f"partner-portrait: {exc}", file=sys.stderr)
        raise SystemExit(1)
