"""Verify diagram sources (Mermaid) rendered in study PDFs.

Raw ```mermaid`` source in a PDF means the HTML→PDF step did not render diagrams.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

from _common import SCRIPTS

MERMAID_BLOCK = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Syntax lines that should never appear as visible PDF text when Mermaid rendered.
RAW_MERMAID_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("flowchart TD/LR/BT/RL", re.compile(r"\bflowchart\s+(TD|LR|BT|RL|TB)\b", re.I)),
    ("graph TD/LR", re.compile(r"\bgraph\s+(TD|LR|BT|RL|TB)\b", re.I)),
    ("sequenceDiagram", re.compile(r"\bsequenceDiagram\b")),
    ("classDiagram", re.compile(r"\bclassDiagram\b")),
    ("stateDiagram", re.compile(r"\bstateDiagram(-v2)?\b")),
    ("erDiagram", re.compile(r"\berDiagram\b")),
)

MERMAID_JS = SCRIPTS / "node_modules" / "mermaid" / "dist" / "mermaid.min.js"


def count_mermaid_blocks(md_text: str) -> int:
    return len(MERMAID_BLOCK.findall(md_text))


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def find_raw_mermaid_leaks(pdf_text: str) -> list[str]:
    return [label for label, pattern in RAW_MERMAID_PATTERNS if pattern.search(pdf_text)]


def verify_study_pdf_diagrams(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    block_count = count_mermaid_blocks(md_text)
    if block_count == 0:
        return

    if not MERMAID_JS.exists():
        raise SystemExit(
            "Study markdown contains Mermaid diagrams but mermaid is not installed.\n"
            "Run once from the repo root:\n"
            "  cd Scripts\n"
            "  npm install"
        )

    if not pdf_path.exists():
        raise SystemExit(f"PDF missing after regeneration: {pdf_path}")

    leaks = find_raw_mermaid_leaks(extract_pdf_text(pdf_path))
    if leaks:
        raise SystemExit(
            f"Mermaid diagram(s) did not render in {pdf_path.name} "
            f"({block_count} ```mermaid block(s) in {md_path.name}).\n"
            f"Raw diagram syntax found in PDF: {', '.join(leaks)}.\n"
            "Ensure Scripts/npm dependencies are installed and _html_to_pdf.js renders "
            "`.mermaid` divs before PDF export."
        )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python Scripts/_verify_pdf_diagrams.py <study.md> <study.pdf>")

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()
    verify_study_pdf_diagrams(md_path, pdf_path)
    print(f"OK: diagram check passed for {pdf_path.name}")


if __name__ == "__main__":
    main()
