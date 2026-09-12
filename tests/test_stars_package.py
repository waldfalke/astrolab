"""Portable STARS documentation checks; run with Python's standard library."""

from pathlib import Path
import re
import base64
import xml.etree.ElementTree as ET
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "docs/recipes.md",
    "docs/stars/README.md",
    "docs/stars/READ2PLAY.md",
    "docs/stars/EXAMPLE.md",
    "docs/stars-supplier-metacontract.md",
    "docs/stars-consumer-metacontract.md",
)


class StarsPackageTests(unittest.TestCase):
    def test_all_entry_points_ship(self):
        surface = ROOT / "distribution/public/PUBLIC_SURFACE.txt"
        if not surface.exists():
            surface = ROOT / "PUBLIC_SURFACE.txt"
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

    def test_landing_images_and_recipe_links_resolve(self):
        overlay = ROOT / "distribution/public"
        landing = overlay / "README.md" if overlay.exists() else ROOT / "README.md"
        text = landing.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'<img\s', text)), 6)
        tables = re.findall(r'<table>(.*?)</table>', text, re.DOTALL)
        self.assertEqual(len(tables), 0, 'Recipe cards must not inherit GitHub table borders')
        self.assertRegex(text, r'<img src="assets/stars-dialogue.png"[^>]+width="100%"')
        self.assertNotIn('Пока не входит в публичный пакет.', text)
        for name in ('natal', 'solar', 'transits', 'day-forecast'):
            tag = re.search(r'<img src="assets/' + name + r'-card.svg"[^>]+>', text)
            self.assertIsNotNone(tag, name)
            self.assertIn('width="360"', tag.group())
            self.assertGreater(len(re.search(r'alt="([^"]+)"', tag.group())[1]), 70)
            assets = overlay / 'assets' if overlay.exists() else ROOT / 'assets'
            svg = ET.parse(assets / (name + '-card.svg')).getroot()
            self.assertNotIn('Пока не входит в публичный пакет.', ''.join(svg.itertext()))
            self.assertEqual(svg.attrib['viewBox'], '0 0 360 390')
            image = svg.find('{http://www.w3.org/2000/svg}image')
            encoded = image.attrib['href']
            self.assertTrue(encoded.startswith('data:image/png;base64,'))
            self.assertEqual(base64.b64decode(encoded.split(',', 1)[1]),
                             (assets / (name + '.png')).read_bytes())
            self.assertIsNone(svg.find('{http://www.w3.org/2000/svg}script'))
        recipes = (ROOT / "docs/recipes.md").read_text(encoding="utf-8")
        for anchor in ("natal", "solar", "transits", "day"):
            self.assertIn(f'docs/recipes.md#{anchor}', text)
            self.assertIn(f'<a id="{anchor}"></a>', recipes)
        targets = re.findall(r'(?:src|href)="([^"]+)"', text)
        targets += re.findall(r"\]\(([^)]+)\)", text)
        for target in targets:
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            relative = unquote(parsed.path)
            self.assertTrue((ROOT / relative).is_file() or (overlay / relative).is_file(), target)


if __name__ == "__main__":
    unittest.main()
