#!/usr/bin/env python3
"""Unit tests for Scripts/_sync_reference_translation.py."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import write_text_lf  # noqa: E402
from _sync_reference_translation import (  # noqa: E402
    clean_page_text,
    extract_google_doc_id,
    extract_pages_for_sigil,
    map_pages_by_shingles,
    scan_repository_citations,
)


class SyncReferenceTranslationTests(unittest.TestCase):
    def test_extract_google_doc_id(self) -> None:
        url = "https://docs.google.com/document/d/1FFYmzzxdaEiru52oPmUU5Xu-jgQlfNl6VdoFXDATmLw/edit?usp=sharing"
        self.assertEqual(
            extract_google_doc_id(url),
            "1FFYmzzxdaEiru52oPmUU5Xu-jgQlfNl6VdoFXDATmLw",
        )
        self.assertEqual(
            extract_google_doc_id("1FFYmzzxdaEiru52oPmUU5Xu-jgQlfNl6VdoFXDATmLw"),
            "1FFYmzzxdaEiru52oPmUU5Xu-jgQlfNl6VdoFXDATmLw",
        )
        with self.assertRaises(ValueError):
            extract_google_doc_id("https://example.com/not-a-doc")

    def test_clean_page_text_dewraps_skia_lines(self) -> None:
        raw = "मानव\nपरम्परा\nमें\n\nHuman\ntradition\nis\none\n\nSecond\nparagraph."
        cleaned = clean_page_text(raw)
        self.assertIn("मानव परम्परा में", cleaned)
        self.assertIn("Human tradition is one", cleaned)
        self.assertIn("Second paragraph.", cleaned)

    def test_extract_pages_for_sigil(self) -> None:
        self.assertEqual(
            extract_pages_for_sigil("As shown earlier (AA, p. 73; JVD, pp. 168–169).", "JVD"),
            (168, 169),
        )
        self.assertEqual(
            extract_pages_for_sigil(
                "- **JVD** — Nagraj, A. *Janvad*. Cited: (pp. 32, 35, 168–169; §3.1).",
                "JVD",
            ),
            (32, 35, 168, 169),
        )

    def test_map_pages_by_shingles_tracks_shifted_pages(self) -> None:
        old_pages = [
            "Title page status as on 12 June 2026 peer review till page 92",
            "Chapter one unchanged text with five or more words matching exactly",
            "Draft version one\nDraft version two\nश्रम ही मूलपूंजी है Human labour is the fundamental form of capital in cyclical economics",
        ]
        new_pages = [
            "Title page status as on 21 Oct 2026 peer review till page 120",
            "श्रम ही मूलपूंजी है Human labour is the fundamental form of capital in cyclical economics",
            "Chapter one unchanged text with five or more words matching exactly",
        ]
        mapping = map_pages_by_shingles(old_pages, new_pages, [2, 3], shingle_size=5)
        self.assertEqual(mapping[2][0][0], 3)
        self.assertEqual(mapping[3][0][0], 2)

    def test_scan_repository_citations_reads_md_and_pptx(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md_file = root / "Studies" / "Demo" / "Demo.md"
            md_file.parent.mkdir(parents=True, exist_ok=True)
            write_text_lf(
                md_file,
                "Labour is primary capital (JVD, p. 168) and exchange is free of profit (JVD, pp. 187–188).\n",
            )
            pptx_file = root / "Studies" / "Demo" / "Deck.pptx"
            slide_xml = (
                '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                "<a:t>Public dialogue on the economy (JVD, pp. 168-169)</a:t>"
                "</p:sld>"
            )
            with zipfile.ZipFile(pptx_file, "w") as zf:
                zf.writestr("ppt/slides/slide1.xml", slide_xml)

            md_cites, pptx_cites, pages = scan_repository_citations(
                "JVD", ("JVD", "Janvad"), root=root
            )
            self.assertEqual(len(md_cites), 1)
            self.assertEqual(len(pptx_cites), 1)
            self.assertEqual(pages, [168, 169, 187, 188])


if __name__ == "__main__":
    unittest.main()
