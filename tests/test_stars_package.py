"""Portable STARS documentation checks; run with Python's standard library."""

from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "docs/stars/README.md",
    "docs/stars/READ2PLAY.md",
    "docs/stars/EXAMPLE.md",
    "docs/stars-supplier-metacontract.md",
    "docs/stars-consumer-metacontract.md",
)


class StarsPackageTests(unittest.TestCase):
    def test_all_entry_points_ship(self):
        surface = ROOT / "PUBLIC_SURFACE.txt"
        if not surface.exists():
            surface = ROOT / "distribution/public/PUBLIC_SURFACE.txt"
        paths = {line.split("\t", 1)[1] for line in surface.read_text().splitlines()
                 if line and not line.startswith("#")}
        for name in (*DOCS, "tests/test_stars_package.py"):
            self.assertIn(name, paths)
            self.assertTrue((ROOT / name).is_file(), name)

    def test_relative_document_links_resolve(self):
        for name in DOCS:
            for target in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text(encoding="utf-8")):
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                path = ((ROOT / name).parent / unquote(parsed.path)).resolve()
                self.assertTrue(path.is_relative_to(ROOT), f"{name}: link escapes package")
                if not path.exists() and (ROOT / "distribution/public/PUBLIC_SURFACE.txt").exists():
                    path = ROOT / "distribution/public" / path.relative_to(ROOT)
                self.assertTrue(path.exists(), f"{name}: {target}")

    def test_no_workbench_dependencies_in_public_docs(self):
        for name in DOCS:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("TaskLogs" + "/", text, name)
            self.assertIsNone(re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text), name)
            self.assertNotIn("127.0.0.1:64927", text, name)

    def test_human_entry_names_agent_entry(self):
        text = (ROOT / "docs/stars/README.md").read_text(encoding="utf-8")
        self.assertIn("READ2PLAY.md", text)
        self.assertIn("STARS.full.md", text)


if __name__ == "__main__":
    unittest.main()
