"""Render MSM Hindi source pages to PNGs for translation verification.

The page map is tied to the official 2008 OCR edition registered as the MSM
reference. Output names retain both the 1-based PDF page and the logical printed
page so translators can move between the source PDF, images, and page markers.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import fitz

from _common import BASE

DEFAULT_PDF = (
    BASE
    / "References"
    / "Madhyasth-Darshan"
    / "MSM-manav-sanchetnavaadi-manovigyan.pdf"
)
DEFAULT_OUT = (
    BASE
    / "References"
    / "Madhyasth-Darshan"
    / "MSM-Manav-Sanchetnavadi-Manovigyan-English"
    / "_page-images"
)
DEFAULT_DPI = 150
EXPECTED_PAGE_COUNT = 268
FRONT_MATTER_PAGES = 12
EXPECTED_SOURCE_SHA256 = (
    "d71ff870a3fdaffd99cc0e3e4a3c52444c817b7f02c41f8b09ecd904a45cff87"
)


def logical_printed_page(pdf_page: int) -> int:
    """Return the filename's printed-page key for a 1-based PDF page.

    Front matter uses its PDF page as a stable logical key. PDF pages 13-266
    map to the book's printed pages 1-254. The two trailing pages continue the
    logical sequence as 255-256 even though they are not numbered in print.
    """
    if pdf_page <= FRONT_MATTER_PAGES:
        return pdf_page
    return pdf_page - FRONT_MATTER_PAGES


def output_name(pdf_page: int) -> str:
    return f"p{pdf_page:03d}_print{logical_printed_page(pdf_page):03d}.png"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(pdf_path: Path, *, allow_source_mismatch: bool) -> int:
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    actual_hash = sha256(pdf_path)
    if actual_hash != EXPECTED_SOURCE_SHA256 and not allow_source_mismatch:
        raise ValueError(
            "MSM source SHA-256 does not match the mapped 2008 OCR edition. "
            "Review its pagination before rendering, or pass "
            "--allow-source-mismatch for an intentional diagnostic render."
        )

    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
    if page_count != EXPECTED_PAGE_COUNT and not allow_source_mismatch:
        raise ValueError(
            f"Expected {EXPECTED_PAGE_COUNT} pages, found {page_count}. "
            "Review and update the page map before rendering another edition."
        )
    return page_count


def render_pages(
    pdf_path: Path,
    out_dir: Path,
    *,
    dpi: int = DEFAULT_DPI,
    force: bool = False,
    allow_source_mismatch: bool = False,
) -> tuple[int, int, int]:
    """Render all source pages; return (written, skipped, page_count)."""
    page_count = validate_source(
        pdf_path, allow_source_mismatch=allow_source_mismatch
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    written = 0
    skipped = 0
    with fitz.open(str(pdf_path)) as doc:
        for index in range(doc.page_count):
            pdf_page = index + 1
            dest = out_dir / output_name(pdf_page)
            if dest.is_file() and not force:
                skipped += 1
                continue
            pix = doc.load_page(index).get_pixmap(
                matrix=matrix, colorspace=fitz.csGRAY, alpha=False
            )
            pix.save(str(dest))
            written += 1

    return written, skipped, page_count


def check_outputs(out_dir: Path, page_count: int = EXPECTED_PAGE_COUNT) -> list[str]:
    """Return problems with the expected page-image set."""
    expected = {output_name(page) for page in range(1, page_count + 1)}
    actual = {path.name for path in out_dir.glob("*.png")} if out_dir.is_dir() else set()
    issues: list[str] = []

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    empty = sorted(
        path.name for path in out_dir.glob("*.png") if path.stat().st_size == 0
    ) if out_dir.is_dir() else []
    if missing:
        issues.append(f"missing {len(missing)} image(s): {', '.join(missing[:5])}")
    if unexpected:
        issues.append(
            f"unexpected {len(unexpected)} image(s): {', '.join(unexpected[:5])}"
        )
    if empty:
        issues.append(f"empty {len(empty)} image(s): {', '.join(empty[:5])}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render MSM Hindi PDF pages to the English workspace."
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
        help="Re-render even when a PNG already exists",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the source and existing image set without rendering",
    )
    parser.add_argument(
        "--allow-source-mismatch",
        action="store_true",
        help="Allow a different source hash/page count for diagnostic rendering only",
    )
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    out_dir = args.out_dir.resolve()
    if args.check:
        page_count = validate_source(
            pdf_path, allow_source_mismatch=args.allow_source_mismatch
        )
        issues = check_outputs(out_dir, page_count)
        if issues:
            print("MSM page-image check failed:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        print(f"MSM page-image check passed: {page_count} PNGs in {out_dir}")
        return 0

    written, skipped, page_count = render_pages(
        pdf_path,
        out_dir,
        dpi=args.dpi,
        force=args.force,
        allow_source_mismatch=args.allow_source_mismatch,
    )
    issues = check_outputs(out_dir, page_count)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1
    print(
        f"Done: {written} written, {skipped} skipped ({page_count} pages) "
        f"-> {out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
