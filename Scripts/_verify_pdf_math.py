"""Verify LaTeX maths actually rendered in study PDFs.

The analogue of `_verify_pdf_diagrams.py` for maths. A study whose HTML holds
KaTeX output must produce a PDF that embeds KaTeX font faces: KaTeX draws every
glyph from its own faces, so their absence means the browser could not load them
and substituted a text font instead.

That is not hypothetical. `_convert_to_pdf.py` used to inline katex.min.css with
its font URLs rewritten to an absolute path under `Scripts/node_modules`, which
resolved on the maintainer's machine and on no other. Four committed companion
notes were rendered where it did not resolve — almost certainly CI — and their
formulae came out in TimesNewRoman and CambriaMath, with the symbol faces
(KaTeX_AMS, KaTeX_Size1) simply missing. Nothing in the pipeline noticed. This
check is what would have.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader

# KaTeX wraps each formula in .katex; the mathml/html split inside it means the
# class appears several times per formula, so this is a presence test, not a count.
KATEX_MARKER = 'class="katex'


def html_katex_occurrences(html_path: Path) -> int:
    if not html_path.exists():
        return 0
    return html_path.read_text(encoding="utf-8", errors="replace").count(KATEX_MARKER)


def pdf_font_faces(pdf_path: Path) -> set[str]:
    faces: set[str] = set()
    reader = PdfReader(str(pdf_path))
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        fonts = resources.get("/Font") or {}
        for key in fonts:
            try:
                base = fonts[key].get_object().get("/BaseFont")
            except Exception:
                continue
            if base:
                faces.add(str(base))
    return faces


def katex_faces(faces: set[str]) -> set[str]:
    return {face for face in faces if "KaTeX" in face}


def verify_study_pdf_math(md_path: Path, pdf_path: Path) -> None:
    """Fail when the HTML rendered maths but the PDF embeds no KaTeX face.

    Keyed on the generated HTML rather than the markdown: a bare ``$`` in prose
    matches a naive markdown scan, whereas KaTeX output in the HTML means maths
    was genuinely rendered and must survive into the PDF.
    """
    html_path = md_path.with_suffix(".html")
    occurrences = html_katex_occurrences(html_path)
    if occurrences == 0:
        return

    if not pdf_path.exists():
        raise SystemExit(f"PDF missing after regeneration: {pdf_path}")

    embedded = katex_faces(pdf_font_faces(pdf_path))
    if embedded:
        return

    raise SystemExit(
        f"Maths did not render in {pdf_path.name}.\n"
        f"{html_path.name} contains {occurrences} KaTeX element(s), but the PDF "
        "embeds no KaTeX font face, so every formula fell back to a text font.\n"
        "This is what a broken KaTeX font path looks like: the fonts must resolve "
        "for the file:// render that produces the PDF as well as for the site. "
        "See Scripts/_convert_to_pdf.py (_load_katex_css) and AGENTS.md §3."
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python Scripts/_verify_pdf_math.py <study.md> <study.pdf>")

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()
    verify_study_pdf_math(md_path, pdf_path)
    print(f"OK: maths check passed for {pdf_path.name}")


if __name__ == "__main__":
    main()
