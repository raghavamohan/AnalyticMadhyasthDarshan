"""Tests for ordered-list continuation across rendered KD page markers."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _convert_to_pdf import _continue_ordered_list_numbering


class OrderedListContinuationTests(unittest.TestCase):
    def test_continues_numbering_across_page_marker(self) -> None:
        html = (
            "<ol><li>First</li></ol>\n"
            '<span class="page-marker">[p. 120]</span>\n'
            "<ol><li>Second</li></ol>"
        )

        converted = _continue_ordered_list_numbering(html)

        self.assertIn('<ol start="2"><li>Second</li></ol>', converted)

    def test_does_not_count_items_from_an_unrelated_earlier_list(self) -> None:
        html = (
            "<ol><li>Unrelated</li></ol>\n"
            "<p>Separate material</p>\n"
            "<ol><li>First</li></ol>\n"
            '<span class="page-marker">[p. 120]</span>\n'
            "<ol><li>Second</li></ol>"
        )

        converted = _continue_ordered_list_numbering(html)

        self.assertIn('<ol start="2"><li>Second</li></ol>', converted)
        self.assertNotIn('<ol start="3"><li>Second</li></ol>', converted)

    def test_respects_an_existing_start_value(self) -> None:
        html = (
            '<ol start="4"><li>Fourth</li><li>Fifth</li></ol>\n'
            '<span class="page-marker">[p. 6]</span>\n'
            "<ol><li>Sixth</li></ol>"
        )

        converted = _continue_ordered_list_numbering(html)

        self.assertIn('<ol start="6"><li>Sixth</li></ol>', converted)


if __name__ == "__main__":
    unittest.main()
