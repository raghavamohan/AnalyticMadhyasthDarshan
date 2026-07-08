"""Interleave Hindi KD PDF with page-aligned English translation PDF."""
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from _common import BASE

KD_DIR = BASE / "References" / "Madhyasth-Darshan"
HINDI_PDF = KD_DIR / "KD-karm darshan v5.pdf"
ENGLISH_PDF = KD_DIR / "KD-Karm-Darshan-English" / "KD-Karm-Darshan-English.pdf"
DEFAULT_OUTPUT = KD_DIR / "KD-Karm-Darshan-English" / "KD-Karm-Darshan-Hindi-English.pdf"


def _fit_page_to_size(page, target_width: float, target_height: float) -> PageObject:
    """Scale and center a source page onto a blank page of the target dimensions."""
    src_width = float(page.mediabox.width)
    src_height = float(page.mediabox.height)
    scale = min(target_width / src_width, target_height / src_height)
    offset_x = (target_width - src_width * scale) / 2
    offset_y = (target_height - src_height * scale) / 2
    fitted = PageObject.create_blank_page(width=target_width, height=target_height)
    fitted.merge_transformed_page(
        page,
        Transformation().scale(scale, scale).translate(offset_x, offset_y),
    )
    return fitted


def build_interleaved_pdf(
    hindi_path: Path = HINDI_PDF,
    english_path: Path = ENGLISH_PDF,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    scale_hindi_to_english: bool = True,
) -> int:
    hindi = PdfReader(str(hindi_path))
    english = PdfReader(str(english_path))
    n_h, n_e = len(hindi.pages), len(english.pages)
    if n_h != n_e:
        raise SystemExit(f"Page count mismatch: Hindi {n_h}, English {n_e}")

    target_width = float(english.pages[0].mediabox.width)
    target_height = float(english.pages[0].mediabox.height)

    writer = PdfWriter()
    for i in range(n_h):
        hindi_page = hindi.pages[i]
        if scale_hindi_to_english:
            hindi_page = _fit_page_to_size(hindi_page, target_width, target_height)
        writer.add_page(hindi_page)
        writer.add_page(english.pages[i])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        writer.write(handle)
    return len(writer.pages)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Hindi-then-English interleaved KD PDF (364 pages when both sources are 182)."
    )
    parser.add_argument("--hindi", type=Path, default=HINDI_PDF)
    parser.add_argument("--english", type=Path, default=ENGLISH_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--no-scale-hindi",
        action="store_true",
        help="Keep original Hindi page dimensions instead of scaling to English page size.",
    )
    args = parser.parse_args()

    page_count = build_interleaved_pdf(
        args.hindi,
        args.english,
        args.output,
        scale_hindi_to_english=not args.no_scale_hindi,
    )
    print(f"Wrote {args.output} ({page_count} pages)")


if __name__ == "__main__":
    main()
