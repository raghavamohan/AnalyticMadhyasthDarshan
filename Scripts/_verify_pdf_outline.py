"""Verify PDF document outline (sidebar bookmarks) in study PDFs.

Chromium generates the outline from h1–h3 when _html_to_pdf.js passes outline: true.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import Destination

MIN_H2_FOR_OUTLINE = 2


def count_h2_headings(md_text: str) -> int:
    return sum(1 for line in md_text.splitlines() if line.startswith("## ") and not line.startswith("### "))


def count_outline_entries(outline: list | None) -> int:
    if not outline:
        return 0

    total = 0
    for item in outline:
        total += 1
        if isinstance(item, Destination):
            continue
        if isinstance(item, list):
            total += count_outline_entries(item)
    return total


def verify_study_pdf_outline(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    h2_count = count_h2_headings(md_text)
    if h2_count < MIN_H2_FOR_OUTLINE:
        return

    if not pdf_path.exists():
        raise SystemExit(f"PDF missing after regeneration: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    outline_count = count_outline_entries(reader.outline)
    if outline_count == 0:
        raise SystemExit(
            f"PDF document outline missing in {pdf_path.name} "
            f"({h2_count} ## headings in {md_path.name}).\n"
            "Ensure _html_to_pdf.js passes outline: true and Chrome/Chromium is 126+."
        )

    expected_min = h2_count
    if outline_count < expected_min:
        print(
            f"Warning: {pdf_path.name} outline has {outline_count} entries "
            f"but markdown has {h2_count} ## headings (Chromium may omit some headings)."
        )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python Scripts/_verify_pdf_outline.py <study.md> <study.pdf>")

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()
    verify_study_pdf_outline(md_path, pdf_path)
    print(f"OK: outline check passed for {pdf_path.name}")


if __name__ == "__main__":
    main()
