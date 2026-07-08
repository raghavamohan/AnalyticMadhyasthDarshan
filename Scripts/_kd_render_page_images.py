"""Render Hindi KD source PDF pages to PNG images for visual translation verification.

Output: References/Madhyasth-Darshan/KD-Karm-Darshan-English/_page-images/
Naming: p{pdf:03d}_print{printed:03d}.png
  - Front matter (PDF pages 1-25): printed = pdf page number
  - Body (PDF pages 26+): printed = pdf page - 25
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

from _common import BASE

DEFAULT_PDF = BASE / "References" / "Madhyasth-Darshan" / "KD-karm darshan v5.pdf"
DEFAULT_OUT = (
    BASE
    / "References"
    / "Madhyasth-Darshan"
    / "KD-Karm-Darshan-English"
    / "_page-images"
)
DEFAULT_DPI = 150


def printed_page(pdf_page: int) -> int:
    """Map 1-based PDF page index to printed page number."""
    if pdf_page <= 25:
        return pdf_page
    return pdf_page - 25


def output_name(pdf_page: int) -> str:
    return f"p{pdf_page:03d}_print{printed_page(pdf_page):03d}.png"


def render_pages(
    pdf_path: Path,
    out_dir: Path,
    *,
    dpi: int = DEFAULT_DPI,
    force: bool = False,
) -> tuple[int, int]:
    """Render all pages; return (written, skipped) counts."""
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    written = 0
    skipped = 0
    try:
        for i in range(doc.page_count):
            pdf_page = i + 1
            dest = out_dir / output_name(pdf_page)
            if dest.is_file() and not force:
                skipped += 1
                continue
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(dest))
            written += 1
    finally:
        doc.close()

    return written, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render KD Hindi PDF pages to _page-images/ PNGs."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help=f"Hindi source PDF (default: {DEFAULT_PDF.relative_to(BASE)})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory for PNG files",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help="Render resolution (default: 150)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-render even when PNG already exists",
    )
    args = parser.parse_args()

    written, skipped = render_pages(
        args.pdf.resolve(),
        args.out_dir.resolve(),
        dpi=args.dpi,
        force=args.force,
    )
    total = written + skipped
    print(
        f"Done: {written} written, {skipped} skipped ({total} pages) "
        f"-> {args.out_dir.resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
