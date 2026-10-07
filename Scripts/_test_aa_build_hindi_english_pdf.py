"""Tests for splitting the AA manuscript into page-aligned review sheets."""
from __future__ import annotations

import unittest

from _aa_build_hindi_english_pdf import MANUSCRIPT, parse_manuscript, render_markdown

SAMPLE = """# Title

**Edited on:** today

---

[PDF p. 1 - front matter]
<!-- source: _page-images/p001_print001.png -->

Title page

[PDF p. 2 - front matter]
<!-- source: _page-images/p002_print002.png -->

*(blank page)*
"""


def _body(pages: int) -> str:
    front = "".join(
        f"[PDF p. {n} - front matter]\n<!-- source: _page-images/p{n:03d}_print{n:03d}.png -->\n\nx\n\n"
        for n in range(1, 11)
    )
    body = "".join(
        f"[p. {n}]\n<!-- source: _page-images/p{n + 10:03d}_print{n:03d}.png -->\n\n"
        + ("## Chapter 1: First\n\n" if n == 1 else "")
        + "text\n\n"
        for n in range(1, pages + 1)
    )
    return "# Title\n\n" + front + body


class AaHindiEnglishTests(unittest.TestCase):
    def test_header_and_pages_split_at_markers(self) -> None:
        header, pages = parse_manuscript(SAMPLE)
        self.assertIn("Edited on", header)
        self.assertEqual([page.pdf_page for page in pages], [1, 2])
        self.assertEqual(pages[0].label, "Front matter, PDF p. 1")
        self.assertEqual(pages[0].markdown, "Title page")
        self.assertNotIn("source:", pages[1].markdown)

    def test_body_pages_map_to_pdf_pages_and_chapters(self) -> None:
        _, pages = parse_manuscript(_body(2))
        self.assertEqual(pages[10].pdf_page, 11)
        self.assertEqual(pages[10].label, "p. 1 (PDF p. 11)")
        self.assertEqual(pages[10].chapter, "Chapter 1: First")
        self.assertIsNone(pages[11].chapter)

    def test_rejects_skipped_page(self) -> None:
        text = _body(3).replace("[p. 2]\n<!-- source: _page-images/p012_print002.png -->\n\ntext\n\n", "")
        with self.assertRaisesRegex(ValueError, "expected PDF page 12"):
            parse_manuscript(text)

    def test_rejects_wrong_source_image(self) -> None:
        text = SAMPLE.replace("p002_print002.png", "p003_print003.png")
        with self.assertRaisesRegex(ValueError, "p002_print002.png"):
            parse_manuscript(text)

    def test_resumed_list_keeps_number_and_links_are_unwrapped(self) -> None:
        self.assertIn('<ol start="3">', render_markdown("3. three\n4. four"))
        self.assertEqual(render_markdown("[ledger](x.md)"), "<p>ledger</p>")

    def test_canonical_manuscript_parses(self) -> None:
        _, pages = parse_manuscript(MANUSCRIPT.read_text(encoding="utf-8"))
        self.assertEqual([page.pdf_page for page in pages], list(range(1, len(pages) + 1)))


if __name__ == "__main__":
    unittest.main()
