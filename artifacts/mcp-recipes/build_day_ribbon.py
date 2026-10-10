"""Build one complete local-day event/state ribbon through Astrolab's MCP API."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import collect_mcp_day_frames
import collect_mcp_boundary_context
import clock_event_state_probe


async def build(
    *, mcp_target: Any, mcp_label: str, engine: str | None, date: str,
    lat: float, lon: float, tz: float, aspect_orb: float, output: Path,
    include_boundary_context: bool = True,
) -> dict:
    """Compose the accepted collector and transformer without changing either contract."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    source = output / "source"
    previous_engine = None
    if engine is not None:
        import astro.engine as astro_engine
        previous_engine = astro_engine.DEFAULT_ENGINE
        astro_engine.DEFAULT_ENGINE = engine
    try:
        await collect_mcp_day_frames.run(SimpleNamespace(
            mcp_url=mcp_label,
            mcp_target=mcp_target,
            mcp_label=mcp_label,
            mcp_transport="in_process" if not isinstance(mcp_target, str) else "http",
            engine=engine,
            date=date,
            lat=lat,
            lon=lon,
            tz=tz,
            output=source,
        ))
        manifest = clock_event_state_probe.run_probe(
            source / "minute-frames.json",
            source / "metadata.json",
            output / "ribbon",
            aspect_orb=aspect_orb,
            house_system="placidus",
        )
        boundary_context = None
        if include_boundary_context:
            boundary_context = await collect_mcp_boundary_context.run(SimpleNamespace(
                mcp_url=mcp_label,
                mcp_target=mcp_target,
                source=source,
                output=output / "boundary",
            ))
    finally:
        if previous_engine is not None:
            astro_engine.DEFAULT_ENGINE = previous_engine
    author_manifest = {key: value for key, value in manifest.items()
                       if key not in {"input_paths", "source_paths"}}
    if boundary_context is not None:
        boundary_raw = (output / "boundary/boundary-context.json").read_bytes()
        (output / "ribbon/boundary-context.json").write_bytes(boundary_raw)
        author_manifest["boundary_context"] = {
            "schema_version": boundary_context["schema_version"],
            "sha256": hashlib.sha256(boundary_raw).hexdigest(),
        }
    (output / "ribbon/author-manifest.json").write_text(
        json.dumps(author_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-url")
    parser.add_argument("--engine", choices=["a"], default="a")
    parser.add_argument("--date", required=True)
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--tz", required=True, type=float)
    parser.add_argument("--aspect-orb", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--no-boundary-context", action="store_true")
    args = parser.parse_args()
    try:
        if args.mcp_url:
            target, label, engine = args.mcp_url, args.mcp_url, None
        else:
            from astro.server import mcp
            target, label, engine = mcp, "in-process:astro.server", args.engine
        manifest = asyncio.run(build(
            mcp_target=target,
            mcp_label=label,
            engine=engine,
            date=args.date,
            lat=args.lat,
            lon=args.lon,
            tz=args.tz,
            aspect_orb=args.aspect_orb,
            output=args.output,
            include_boundary_context=not args.no_boundary_context,
        ))
    except (FileExistsError, KeyError, OSError, TypeError, ValueError) as error:
        parser.exit(2, f"Day ribbon rejected: {error}\n")
    print(json.dumps(manifest["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

