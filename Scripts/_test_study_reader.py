"""Enforce reader data contracts and synchronized, screen-only generated assets."""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse
from pathlib import Path

from bs4 import BeautifulSoup

from _common import BASE
from _convert_to_pdf import convert_to_html, _study_toolbar_html
from _study_reader import reader_assets


class StudyReaderTests(unittest.TestCase):
    def test_feedback_prefills_and_companion_returns_to_parent_study(self):
        source = BASE / 'Studies/Nature-Of-Time/Research-Note-Time.md'
        title = 'Time: "duration" & change / काल'
        soup = BeautifulSoup(_study_toolbar_html(source,title=title),'html.parser')
        self.assertEqual(soup.select_one('.study-toolbar-back')['href'],'../index.html#study-Nature-Of-Time')
        fields = parse_qs(urlparse(soup.select_one('.study-toolbar-feedback')['href']).query)
        self.assertEqual(fields['study'],[title])
        self.assertEqual(fields['title'],['Study feedback: '+title])
        self.assertEqual(fields['template'],['study-feedback.yml'])
        self.assertEqual(len(soup.select('.study-toolbar-feedback')),1)
        form = (BASE / '.github/ISSUE_TEMPLATE/study-feedback.yml').read_text(encoding='utf-8')
        # The link's custom query keys must name text fields in the generated
        # GitHub form. This contract check needs no separate YAML dependency.
        inputs = {identifier: kind for kind, identifier in re.findall(r'^  - type: (input|textarea)\n    id: (\w+)\n',form,re.M)}
        self.assertEqual(inputs['study'],'input')
        self.assertEqual(inputs['location'],'input')
        self.assertEqual(inputs['description'],'textarea')
        self.assertIn('required: true',form.split('    id: description\n',1)[1])

    def test_reader_data_and_recovery(self):
        result = subprocess.run(["node", str(BASE / "Scripts/_test_study_reader.mjs")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generated_controls_preserve_content_and_print_boundary(self):
        with tempfile.TemporaryDirectory(dir=BASE) as directory:
            source = Path(directory) / "reader.md"
            source.write_bytes(b"# Reader\n\nFirst passage.\n\n## Argument\n\nSecond passage.\n\n### Detail\n\nThird passage.\n")
            html = convert_to_html(source, include_web_chrome=True).read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            identifiers = [node["id"] for node in soup.select("[id]")]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            self.assertIsNone(soup.select_one("main .reader-chrome"))
            self.assertEqual(soup.select_one("main h2").text, "Argument")
            self.assertIn('.reader-chrome { display: none !important; }', html)
            self.assertEqual(soup.select_one('link[href*="reader.css"]')["media"], "screen")
            self.assertIn("defer", soup.select_one('script[src*="reader.js"]').attrs)
            self.assertTrue(soup.select_one("#reader-resume").has_attr("hidden"))
            self.assertFalse(soup.select_one("#reader-tools").has_attr("open"))
            for node in soup.select("[aria-controls]"):
                self.assertIsNotNone(soup.find(id=node["aria-controls"]))
            plain = convert_to_html(source, include_web_chrome=False).read_text(encoding="utf-8")
            self.assertNotIn('id="reader-tools"', plain)
            self.assertNotIn('src="../Assets/reader/', plain)

    def test_every_tracked_reader_uses_current_assets(self):
        result = subprocess.run(["git", "ls-files", "-z", "Studies/**/*.html", "Applications/**/*.html"], cwd=BASE, capture_output=True, check=True)
        checked = 0
        for name in result.stdout.decode("utf-8").split("\0"):
            if not name:
                continue
            path = BASE / name
            if not path.with_suffix(".md").is_file():
                continue
            html = path.read_text(encoding="utf-8")
            if 'class="study-toolbar"' not in html:
                continue
            with self.subTest(reader=name):
                for asset in reader_assets(path.with_suffix(".md")):
                    self.assertTrue(asset in html, "Regenerate this reader with _convert_to_pdf.py")
                self.assertIn('id="reader-tools"', html)
                self.assertEqual(len(re.findall(r'id="reader-tools"', html)), 1)
            checked += 1
        self.assertGreater(checked, 30, "Reader discovery missed the published corpus")


if __name__ == "__main__":
    unittest.main()
