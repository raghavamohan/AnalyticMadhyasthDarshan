"""Build the side-by-side Hindi-English review PDF for the AA working translation.

Each sheet pairs one page of the Hindi source PDF (left, at full size) with the
English for that page (right), split from the canonical manuscript at its page
markers. Only translated pages are included, so the PDF grows with the
translation. The English for every page is fitted to a single column so that
page alignment never drifts; the build fails if a page cannot fit.

Run from the repository root after any manuscript change:

    python Scripts/_aa_build_hindi_english_pdf.py

Writing the default output also refreshes its size and SHA-256 in
References/r2-artifacts.json, where it is a Git-retained active-translation
output.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import markdown
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from _aa_render_page_images import (
    DEFAULT_PDF as HINDI_PDF,
    EXPECTED_SOURCE_SHA256,
    FRONT_MATTER_PAGES,
    output_name,
    sha256,
)
from _common import BASE, SCRIPTS, configure_utf8_stdio, write_text_lf
from _reference_artifacts import MANIFEST_PATH, _canonical_json, load_manifest

AA_DIR = BASE / "References" / "Madhyasth-Darshan" / "AA-Avartansheel-Arthshastra-English"
MANUSCRIPT = AA_DIR / "AA-Avartansheel-Arthshastra-English.md"
DEFAULT_OUTPUT = AA_DIR / "AA-Avartansheel-Arthshastra-Hindi-English.pdf"
FONT_DIR = BASE / "Assets" / "KaTeX" / "fonts"

FRONT_MARKER_RE = re.compile(r"^\[PDF p\. (\d+) - front matter\]$")
BODY_MARKER_RE = re.compile(r"^\[p\. (\d+)\]$")
SOURCE_RE = re.compile(r"^<!-- source: _page-images/(\S+) -->$")
CHAPTER_RE = re.compile(r"^## (Chapter \d+: .+)$", re.MULTILINE)

MAX_FONT_PT = 10.5
MIN_FONT_PT = 7.5


@dataclass
class SourcePage:
    pdf_page: int
    label: str
    markdown: str
    chapter: str | None


def parse_manuscript(text: str) -> tuple[str, list[SourcePage]]:
    """Split the manuscript into its header and one chunk per source page."""
    lines = text.split("\n")
    header: list[str] = []
    pages: list[SourcePage] = []
    current: list[str] | None = None
    pdf_page = 0
    label = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        front = FRONT_MARKER_RE.match(line)
        body = BODY_MARKER_RE.match(line)
        if front or body:
            if current is not None:
                pages.append(SourcePage(pdf_page, label, "\n".join(current).strip(), None))
            if front:
                pdf_page = int(front.group(1))
                label = f"Front matter, PDF p. {pdf_page}"
            else:
                printed = int(body.group(1))
                pdf_page = printed + FRONT_MATTER_PAGES
                label = f"p. {printed} (PDF p. {pdf_page})"
            expected_pdf = len(pages) + 1
            if pdf_page != expected_pdf:
                raise ValueError(f"{line}: expected PDF page {expected_pdf}, found {pdf_page}")
            source = SOURCE_RE.match(lines[index + 1]) if index + 1 < len(lines) else None
            if not source or source.group(1) != output_name(pdf_page):
                raise ValueError(f"{line}: next line must cite _page-images/{output_name(pdf_page)}")
            current = []
            index += 2
            continue
        (header if current is None else current).append(line)
        index += 1
    if current is not None:
        pages.append(SourcePage(pdf_page, label, "\n".join(current).strip(), None))
    if not pages:
        raise ValueError("no page markers found in the manuscript")
    for page in pages:
        match = CHAPTER_RE.search(page.markdown)
        page.chapter = match.group(1) if match else None
    return "\n".join(header).strip(), pages


def render_markdown(text: str) -> str:
    # sane_lists keeps a list's printed start number (a list resumed after a
    # page break starts at 3, not 1).
    rendered = markdown.markdown(text, extensions=["tables", "smarty", "sane_lists"])
    # Relative links would resolve against the build's scratch directory.
    return re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", rendered, flags=re.DOTALL)


def _font_faces() -> str:
    faces = (
        ("KaTeX_Main-Regular.woff2", "400", "normal"),
        ("KaTeX_Main-Bold.woff2", "700", "normal"),
        ("KaTeX_Main-Italic.woff2", "400", "italic"),
        ("KaTeX_Main-BoldItalic.woff2", "700", "italic"),
    )
    return "\n".join(
        "@font-face { font-family: 'AA Review Serif'; "
        f"src: url('{(FONT_DIR / name).as_uri()}') format('woff2'); "
        f"font-weight: {weight}; font-style: {style}; }}"
        for name, weight, style in faces
    )


def build_html(header_md: str, pages: list[SourcePage], width: float, height: float) -> str:
    """Return one fixed-size English sheet per source page, after a cover sheet."""
    sheets = [
        '<section class="sheet cover"><div class="body">'
        + render_markdown(header_md)
        + "<h2>How to read this file</h2>"
        "<p>Each sheet shows one page of the Hindi source on the left and the English "
        "first-pass translation of that page on the right. Sentences are split where "
        "the Hindi page breaks. Bold passages follow the source. Terms still marked "
        "<em>proposed</em> in <code>AA-Glossary-Additions.md</code> are not settled.</p>"
        "</div></section>"
    ]
    for page in pages:
        sheets.append(
            '<section class="sheet">'
            f'<div class="head"><span>{html.escape(page.label)}</span>'
            "<span>English working translation, first pass</span></div>"
            f'<div class="body">{render_markdown(page.markdown)}</div>'
            "</section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Avartansheel Arthshastra: Hindi-English review</title>
<style>
{_font_faces()}
@page {{ size: {width}pt {height}pt; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{
  color: #1a1a1a;
  font-family: 'AA Review Serif', 'FreeSerif', 'Noto Serif Devanagari', serif;
  -webkit-print-color-adjust: exact;
}}
.sheet {{
  width: {width}pt;
  height: {height}pt;
  padding: 26pt 30pt 28pt 32pt;
  border-left: 0.75pt solid #b8b8b8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  break-after: page;
  page-break-after: always;
}}
.sheet.cover {{ border-left: none; padding: 48pt 46pt; }}
.head {{
  display: flex;
  justify-content: space-between;
  font-size: 7.5pt;
  color: #6b6b6b;
  border-bottom: 0.5pt solid #d0d0d0;
  padding-bottom: 3pt;
  margin-bottom: 8pt;
}}
.body {{ flex: 1 1 auto; min-height: 0; overflow: hidden; font-size: {MAX_FONT_PT}pt; line-height: 1.38; }}
.body p {{ margin: 0 0 0.45em 0; text-align: justify; hyphens: auto; }}
.body h1 {{ font-size: 1.45em; margin: 0 0 0.6em 0; }}
.body h2 {{ font-size: 1.22em; margin: 0.35em 0 0.45em 0; }}
.body h3 {{ font-size: 1.08em; margin: 0.3em 0 0.35em 0; }}
.body ol, .body ul {{ margin: 0 0 0.45em 0; padding-left: 1.5em; }}
.body li {{ margin: 0 0 0.25em 0; }}
.body li > p {{ margin: 0 0 0.25em 0; }}
.body blockquote {{ margin: 0.3em 0 0.5em 0; padding-left: 0.8em; border-left: 2pt solid #c8c8c8; color: #444; }}
.body table {{ border-collapse: collapse; width: 100%; margin: 0.3em 0 0.6em 0; font-size: 0.92em; }}
.body th, .body td {{ border: 0.5pt solid #bbb; padding: 2pt 4pt; text-align: left; vertical-align: top; }}
.body hr {{ border: none; border-top: 0.5pt solid #ccc; margin: 0.6em 0; }}
.body code {{ font-family: monospace; font-size: 0.9em; }}
</style>
<script>
window.__layoutPages = function () {{
  const report = {{ sheets: 0, sizes: [], overflow: [] }};
  document.querySelectorAll('.sheet').forEach(function (sheet, index) {{
    const body = sheet.querySelector('.body');
    let size = {MAX_FONT_PT};
    body.style.fontSize = size + 'pt';
    while (body.scrollHeight > body.clientHeight + 0.5 && size > {MIN_FONT_PT}) {{
      size = Math.round((size - 0.25) * 100) / 100;
      body.style.fontSize = size + 'pt';
    }}
    report.sheets += 1;
    report.sizes.push(size);
    if (body.scrollHeight > body.clientHeight + 0.5) report.overflow.push(index);
  }});
  return report;
}};
</script>
</head>
<body>
{"".join(sheets)}
</body>
</html>
"""


def _fit(page: PageObject, width: float, height: float) -> Transformation:
    """Scale to fit and centre within a width x height box."""
    src_w, src_h = float(page.mediabox.width), float(page.mediabox.height)
    scale = min(width / src_w, height / src_h)
    return Transformation().scale(scale, scale).translate(
        (width - src_w * scale) / 2, (height - src_h * scale) / 2
    )


def compose(hindi: PdfReader, english: PdfReader, pages: list[SourcePage],
            width: float, height: float) -> PdfWriter:
    writer = PdfWriter()
    sheet_w = width * 2

    cover = writer.add_blank_page(width=sheet_w, height=height)
    cover.merge_transformed_page(
        english.pages[0], Transformation().translate((sheet_w - width) / 2, 0)
    )
    writer.add_outline_item("About this file", 0)

    parent = writer.add_outline_item("Front matter", 1)
    for number, page in enumerate(pages, start=1):
        sheet = writer.add_blank_page(width=sheet_w, height=height)
        sheet.merge_transformed_page(hindi.pages[page.pdf_page - 1], _fit(
            hindi.pages[page.pdf_page - 1], width, height))
        sheet.merge_transformed_page(english.pages[number], Transformation().translate(width, 0))
        if page.chapter:
            parent = writer.add_outline_item(page.chapter, number)
        writer.add_outline_item(page.label, number, parent=parent)

    writer.add_metadata({
        "/Title": "Avartansheel Arthshastra: Hindi-English review (working translation)",
        "/Author": "A. Nagraj (Hindi); working English translation, Analytic Madhyasth Darshan",
    })
    writer.page_layout = "/SinglePage"
    return writer


def build(manuscript: Path, hindi_pdf: Path, output: Path, *, keep: Path | None = None) -> int:
    if sha256(hindi_pdf) != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"{hindi_pdf} is not the mapped 2024 printing")
    header_md, pages = parse_manuscript(manuscript.read_text(encoding="utf-8"))
    hindi = PdfReader(str(hindi_pdf))
    width = float(hindi.pages[0].mediabox.width)
    height = float(hindi.pages[0].mediabox.height)

    with tempfile.TemporaryDirectory(prefix="aa-hindi-english-") as scratch:
        work = keep or Path(scratch)
        work.mkdir(parents=True, exist_ok=True)
        html_path = work / "aa-english-columns.html"
        english_path = work / "aa-english-columns.pdf"
        write_text_lf(html_path, build_html(header_md, pages, width, height))
        result = subprocess.run(
            ["node", str(SCRIPTS / "_html_to_paged_pdf.js"), str(html_path), str(english_path)],
            cwd=str(SCRIPTS), capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"English column render failed:\n{result.stdout}{result.stderr}")
        report_line = next(
            (line for line in reversed(result.stdout.splitlines()) if line.startswith("REPORT ")),
            None,
        )
        if report_line is None:
            raise RuntimeError("English column render returned no layout report")
        report = json.loads(report_line.removeprefix("REPORT "))
        if report["overflow"]:
            labels = [pages[i - 1].label if i else "cover" for i in report["overflow"]]
            raise ValueError(
                f"English does not fit one column at {MIN_FONT_PT}pt on: {', '.join(labels)}"
            )
        english = PdfReader(str(english_path))
        if len(english.pages) != len(pages) + 1:
            raise ValueError(
                f"English column PDF has {len(english.pages)} pages; expected {len(pages) + 1}"
            )
        writer = compose(hindi, english, pages, width, height)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("wb") as handle:
            writer.write(handle)

    shrunk = [
        f"{pages[i - 1].label} ({size}pt)"
        for i, size in enumerate(report["sizes"]) if i and size < MAX_FONT_PT
    ]
    if shrunk:
        print("Reduced type to fit: " + "; ".join(shrunk))
    return len(pages)


def refresh_manifest_row(output: Path) -> bool:
    """Record the rebuilt PDF's size and hash in its existing manifest row."""
    repo_path = output.resolve().relative_to(BASE).as_posix()
    data = load_manifest()
    row = next((item for item in data["artifacts"] if item["repo_path"] == repo_path), None)
    if row is None:
        raise ValueError(f"{repo_path} has no row in {MANIFEST_PATH.relative_to(BASE)}")
    row["source"]["bytes"] = output.stat().st_size
    row["source"]["sha256"] = sha256(output)
    return write_text_lf(MANIFEST_PATH, _canonical_json(data))


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--manuscript", type=Path, default=MANUSCRIPT)
    parser.add_argument("--hindi", type=Path, default=HINDI_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--keep-intermediate", type=Path, metavar="DIR",
        help="Write the English column HTML and PDF to DIR for inspection.",
    )
    args = parser.parse_args()
    try:
        count = build(args.manuscript, args.hindi, args.output, keep=args.keep_intermediate)
        if args.output.resolve() == DEFAULT_OUTPUT.resolve() and refresh_manifest_row(args.output):
            print(f"Updated {MANIFEST_PATH.relative_to(BASE)}")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output} ({count} source pages, {count + 1} sheets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
