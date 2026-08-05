"""Validate an exported tree against its exact public file manifest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import subprocess


IGNORED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}
PATTERN_CHARS = frozenset("*?[]")
ORIGINS = {"source", "overlay", "generated"}


def load_paths(root: Path) -> tuple[list[str], list[str]]:
    manifest = root / "PUBLIC_SURFACE.txt"
    raw_entries = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    errors: list[str] = []
    seen: set[str] = set()
    paths: list[str] = []
    for entry in raw_entries:
        fields = entry.split("\t")
        if len(fields) != 2 or fields[0] not in ORIGINS:
            errors.append(f"Expected '<source|overlay|generated><TAB><path>': {entry}")
            continue
        _, path = fields
        paths.append(path)
        parsed = PurePosixPath(path)
        if any(character in path for character in PATTERN_CHARS):
            errors.append(f"Patterns are not allowed: {path}")
        if (
            "\\" in path
            or parsed.is_absolute()
            or ".." in parsed.parts
            or path != parsed.as_posix()
        ):
            errors.append(f"Invalid public path: {path}")
        if path in seen:
            errors.append(f"Duplicate public path: {path}")
        seen.add(path)
    return paths, errors


def included_files(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if relative.parts[:3] == ("infra", "ephe", "files"):
            continue
        files.add(relative.as_posix())
    return files


def tracked_files(root: Path) -> set[str]:
    if not (root / ".git").exists():
        return set()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return set()
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def verify_hashes(root: Path, files: set[str]) -> list[str]:
    manifest_path = root / "EXPORT_MANIFEST.sha256"
    if "EXPORT_MANIFEST.sha256" not in files:
        return []

    expected_paths = files - {"EXPORT_MANIFEST.sha256"}
    recorded: dict[str, str] = {}
    errors: list[str] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        fields = line.split("  ", 1)
        if len(fields) != 2 or len(fields[0]) != 64:
            errors.append(f"Invalid hash line: {line}")
            continue
        digest, path = fields
        if path in recorded:
            errors.append(f"Duplicate hash path: {path}")
            continue
        recorded[path] = digest.lower()

    for path in sorted(expected_paths - recorded.keys()):
        errors.append(f"Missing SHA-256: {path}")
    for path in sorted(recorded.keys() - expected_paths):
        errors.append(f"Unexpected SHA-256: {path}")
    for path in sorted(expected_paths & recorded.keys()):
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if actual != recorded[path]:
            errors.append(f"SHA-256 mismatch: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    paths, path_errors = load_paths(root)
    files = included_files(root)
    expected = set(paths)
    tracked = tracked_files(root)

    unexpected = sorted(files - expected)
    unexpected_tracked = sorted(tracked - expected)
    missing = sorted(expected - files)
    hash_errors = verify_hashes(root, files) if not missing else []
    if path_errors or unexpected or unexpected_tracked or missing or hash_errors:
        if path_errors:
            print("Invalid PUBLIC_SURFACE.txt:")
            print("\n".join(f"  {error}" for error in path_errors))
        if unexpected:
            print("Unexpected public files:")
            print("\n".join(f"  {path}" for path in unexpected))
        if unexpected_tracked:
            print("Unexpected tracked public files:")
            print("\n".join(f"  {path}" for path in unexpected_tracked))
        if missing:
            print("Missing public files:")
            print("\n".join(f"  {path}" for path in missing))
        if hash_errors:
            print("Invalid EXPORT_MANIFEST.sha256:")
            print("\n".join(f"  {error}" for error in hash_errors))
        return 1

    print(f"PUBLIC_SURFACE_PASS files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
