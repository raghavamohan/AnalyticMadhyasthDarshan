"""Tests for PDF-to-markdown conversion (maintainer import pipeline)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _pdf_to_md import convert_pdf_to_markdown

# A round-trip test used to live here, converting the Restfulness-And-Least-Action
# PDF and asserting on its headings, page count, and extraction quality. That study
# was removed in 8c5b4dc and the test was left behind asserting on a fixture that no
# longer exists, so it had been failing ever since. This file is not wired into any
# workflow, which is why nobody noticed. Restoring that coverage needs a fixture PDF
# the repo actually owns -- not another study's, which would break the same way the
# next time a study is retired.


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
