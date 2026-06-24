"""Verify fenced code blocks from markdown appear intact in study PDFs.

Long ```text`` lines in `<pre>` blocks overflow the page when CSS uses `pre` without
wrap; PDF export clips the right edge, leaving truncated tokens such as `[c` instead
of `[compound]`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

# Require a language tag (e.g. ```text) so closing ``` after ```mermaid is not
# parsed as the start of a fenced block.
FENCED_BLOCK = re.compile(
    r"```(?!mermaid)(\w+)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

# Bracketed annotations in formal spec blocks — common truncation victims.
BRACKET_TAG = re.compile(r"\[[^\]]+\]")


def extract_fenced_blocks(md_text: str) -> list[str]:
    return [match.group(2) for match in FENCED_BLOCK.finditer(md_text)]


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def find_truncation_signatures(pdf_text: str) -> list[str]:
    """Detect clipped bracket tags and Petri-style spec lines cut mid-token."""
    issues: list[str] = []
    if re.search(r"\[c\n", pdf_text):
        issues.append("[c (truncated [compound...])")
    for match in re.finditer(r"(?m)(bond|complete|awaken|evidence)\s*:.*?(\[[^\]\n]{0,4})\n", pdf_text):
        tail = match.group(2)
        if tail != "[]" and not tail.endswith("]"):
            issues.append(f"{match.group(1)} line ends with {tail!r}")
    return issues


def extract_spec_bracket_tags(block: str) -> list[str]:
    """Bracket annotations on formal spec lines (Petri, type rules), not prose links."""
    tags: list[str] = []
    for line in block.splitlines():
        if "->" not in line and " admissible" not in line.lower():
            continue
        for match in BRACKET_TAG.finditer(line):
            tag = match.group(0)
            if "?" in tag or "http" in tag.lower():
                continue
            if re.match(r"\[\*?.+\*\?\]", tag):
                continue
            # Markdown links [title](url) are not Petri/spec annotations.
            if match.end() < len(line) and line[match.end()] == "(":
                continue
            tags.append(tag)
    return tags


def find_missing_bracket_tags(md_text: str, pdf_text: str) -> list[str]:
    missing: list[str] = []
    pdf_norm = normalize_ws(pdf_text)
    for block in extract_fenced_blocks(md_text):
        for tag in extract_spec_bracket_tags(block):
            if tag not in pdf_text and normalize_ws(tag) not in pdf_norm:
                missing.append(tag)
    return missing


def verify_study_pdf_fenced_code(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    if not extract_fenced_blocks(md_text):
        return

    if not pdf_path.exists():
        raise SystemExit(f"PDF missing after regeneration: {pdf_path}")

    pdf_text = extract_pdf_text(pdf_path)
    issues = find_truncation_signatures(pdf_text)
    issues.extend(find_missing_bracket_tags(md_text, pdf_text))

    if issues:
        sample = ", ".join(list(dict.fromkeys(issues))[:5])
        extra = f" (+{len(issues) - 5} more)" if len(issues) > 5 else ""
        raise SystemExit(
            f"Fenced code block content missing or truncated in {pdf_path.name}.\n"
            f"Examples: {sample}{extra}.\n"
            "Ensure `_convert_to_pdf.py` uses `white-space: pre-wrap` on `<pre>` "
            "for print/PDF, or use a table for wide specs."
        )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python Scripts/_verify_pdf_fenced_code.py <study.md> <study.pdf>"
        )

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()
    verify_study_pdf_fenced_code(md_path, pdf_path)
    print(f"OK: fenced-code check passed for {pdf_path.name}")


if __name__ == "__main__":
    main()
