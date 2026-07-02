"""Tests for PDF-to-markdown conversion (maintainer import pipeline)."""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import STUDIES
from _pdf_to_md import convert_pdf_to_markdown

FIXTURE_SLUG = "Restfulness-And-Least-Action"
FIXTURE_PDF = STUDIES / FIXTURE_SLUG / f"{FIXTURE_SLUG}.pdf"


def _assert_no_word_per_line_artifacts(md: str) -> None:
    lines = [line for line in md.splitlines() if line.strip()]
    short_lines = [line for line in lines if len(line.split()) <= 2 and len(line) < 30]
    ratio = len(short_lines) / max(len(lines), 1)
    assert ratio < 0.35, (
        f"Too many short lines ({len(short_lines)}/{len(lines)}); "
        "possible word-per-line extraction artifacts"
    )


def test_round_trip_restfulness_pdf() -> None:
    assert FIXTURE_PDF.is_file(), f"Missing fixture PDF: {FIXTURE_PDF}"
    md, report = convert_pdf_to_markdown(FIXTURE_PDF, min_chars=1000)

    assert report.pages_processed >= 5
    assert report.headings_found >= 5
    assert report.total_chars >= 5000
    assert report.empty_pages == 0

    assert re.search(r"^#\s+", md, re.MULTILINE), "Expected an H1 heading"
    assert re.search(r"^##\s+References\b", md, re.MULTILINE | re.IGNORECASE)
    assert re.search(r"^##\s+", md, re.MULTILINE), "Expected section headings"
    assert "Least Action" in md or "Restfulness" in md

    _assert_no_word_per_line_artifacts(md)


def test_empty_pdf_fails() -> None:
    import fitz

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        temp_path = Path(handle.name)

    try:
        doc = fitz.open()
        doc.new_page()
        doc.save(str(temp_path))
        doc.close()

        try:
            convert_pdf_to_markdown(temp_path, min_chars=50)
            raise AssertionError("Expected ValueError for empty PDF")
        except ValueError as exc:
            assert "characters" in str(exc).lower() or "extractable" in str(exc).lower()
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> int:
    tests = [
        test_round_trip_restfulness_pdf,
        test_empty_pdf_fails,
    ]
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            test()
            print(f"PASS {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
