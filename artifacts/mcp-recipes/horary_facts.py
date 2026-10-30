"""Local astronomical facts for a reviewed horary; never an automatic judgment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from astro.horary import (compute_facts, geometric_house, hour_agreement, planetary_hour,
                          render_wheel, roots, signed, utc, validate_input)


def output_path(path):
    path = Path(path).resolve()
    if ".private" not in [p.lower() for p in path.parts]:
        raise ValueError("filled horary output must stay under .private")
    if path.exists():
        raise FileExistsError(f"preserve existing output: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = output_path(args.out)
    source = args.input.read_bytes()
    cfg = json.loads(source.decode("utf-8-sig"))
    facts = compute_facts(cfg)
    out.mkdir(parents=True, exist_ok=False)
    (out/"facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (out/"wheel.svg").write_text(render_wheel(facts), encoding="utf-8")
    manifest = {"method": "horary-v1", "input_sha256": hashlib.sha256(source).hexdigest(),
                "artifacts": {name: hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ("facts.json", "wheel.svg")},
                "scope": "astronomical facts; not a chart-project or a horary judgment",
                "provenance": facts["provenance"]}
    (out/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "events": len(facts["events"]), "radicality_verdict": None}, ensure_ascii=True))


if __name__ == "__main__":
    main()
