#!/usr/bin/env python3
"""Convert a Word document (.docx) to PDF via Microsoft Word COM (Windows).

Examples (from repo root):

  python Scripts/_docx_to_pdf.py Studies/The-Ontology-of-Coexistence/Presenters-Companion-Ontology-of-Existence.docx
  python Scripts/_docx_to_pdf.py path/to/notes.docx --output path/to/notes.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import win32com.client as win32com_client  # type: ignore
except ImportError:  # pragma: no cover
    win32com_client = None  # type: ignore

# wdFormatPDF
WD_FORMAT_PDF = 17


def convert_docx_to_pdf(docx: Path, pdf: Path) -> None:
    if win32com_client is None:
        raise SystemExit(
            "pywin32 is required for Word COM conversion. "
            "Install with: pip install pywin32"
        )
    docx = docx.expanduser().resolve()
    pdf = pdf.expanduser().resolve()
    if not docx.is_file():
        raise SystemExit(f"DOCX not found: {docx}")
    if docx.suffix.lower() != ".docx":
        raise SystemExit(f"Expected a .docx file: {docx}")

    pdf.parent.mkdir(parents=True, exist_ok=True)
    word = win32com_client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(docx))
        try:
            doc.SaveAs(str(pdf), FileFormat=WD_FORMAT_PDF)
        finally:
            doc.Close(False)
    finally:
        word.Quit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a .docx file to PDF using Microsoft Word COM."
    )
    parser.add_argument("docx", type=Path, help="Path to the .docx file")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output .pdf path (default: same directory and stem as the .docx)",
    )
    args = parser.parse_args(argv)

    docx = args.docx
    pdf = args.output if args.output is not None else docx.with_suffix(".pdf")
    convert_docx_to_pdf(docx, pdf)
    print(f"Wrote {pdf.resolve()} ({pdf.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
