"""Keep companion slide headings with their scripts without restyling studies."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _convert_to_pdf import convert_to_html


COMPANION_H1_RULE = (
    "    h1 { page-break-after: avoid; break-after: avoid; "
    "page-break-inside: avoid; break-inside: avoid; }\n"
)
SLIDE_SCRIPT = """# PRESENTER'S COMPANION

# Slide 7

# Nature Is Complementary

## Delivering the slide

Each unit participates in definite mutuality with other units.
"""


class CompanionHeadingPaginationTests(unittest.TestCase):
    def _render(self, directory: Path, name: str) -> str:
        source = directory / name
        source.write_bytes(SLIDE_SCRIPT.encode("utf-8"))
        return convert_to_html(source, update_search=False).read_text(encoding="utf-8")

    def test_companion_h1_rule_is_inside_print_styles(self) -> None:
        with tempfile.TemporaryDirectory(dir=BASE) as temporary:
            html = self._render(Path(temporary), "Presenters-Companion-Example.md")

        print_start = html.index("@media print {")
        page_marker = html.index("    .page-marker {", print_start)
        self.assertIn(COMPANION_H1_RULE, html[print_start:page_marker])
        self.assertEqual(html.count(COMPANION_H1_RULE), 1)
        self.assertIn("h2, h3, h4 { page-break-after: avoid; break-after: avoid; }", html)

    def test_non_companion_output_has_no_other_change(self) -> None:
        with tempfile.TemporaryDirectory(dir=BASE) as temporary:
            directory = Path(temporary)
            companion = self._render(directory, "Presenters-Companion-Example.md")
            for name in ("Example.md", "Technical-Note-Example.md", "Other-Presenters-Companion.md"):
                with self.subTest(name=name):
                    ordinary = self._render(directory, name)
                    self.assertNotIn(COMPANION_H1_RULE, ordinary)
                    self.assertEqual(companion.replace(COMPANION_H1_RULE, ""), ordinary)


if __name__ == "__main__":
    unittest.main()
