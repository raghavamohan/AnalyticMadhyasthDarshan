#!/usr/bin/env python3
"""Build a sanitized reading HTML and deterministic PDF from reference Markdown."""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from pypdf import PdfReader

from _common import BASE, REFERENCES, configure_utf8_stdio, favicon_link_tags, write_text_lf
from _pdf_metadata import normalize_study_pdf

DEFAULT_OUTPUT_ROOT = BASE / "tmp" / "reference-build"

STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0 auto;
  max-width: 52rem;
  padding: 2rem 2.25rem 4rem;
  color: #1f2933;
  background: #fff;
  font-family: Georgia, "Noto Serif", "Times New Roman", serif;
  font-size: 16px;
  line-height: 1.62;
}
h1, h2, h3, h4 { color: #172554; line-height: 1.25; break-after: avoid; }
h1 { font-size: 2.1rem; margin: 0 0 1.4rem; }
h2 { border-bottom: 1px solid #cbd5e1; font-size: 1.45rem; margin-top: 2.2rem; padding-bottom: .25rem; }
h3 { font-size: 1.18rem; margin-top: 1.7rem; }
p { margin: .75rem 0; text-align: justify; text-justify: inter-word; hyphens: auto; }
a { color: #1d4ed8; overflow-wrap: anywhere; }
blockquote { border-left: 4px solid #94a3b8; color: #475569; margin: 1rem 0; padding: .1rem 1rem; }
li { margin: .28rem 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #cbd5e1; padding: .4rem .5rem; text-align: left; vertical-align: top; }
pre { background: #f8fafc; border: 1px solid #e2e8f0; padding: .8rem; white-space: pre-wrap; }
code { font-family: "Cascadia Mono", Consolas, monospace; font-size: .9em; }
@media print {
  body { max-width: none; padding: 0; font-size: 10.5pt; line-height: 1.48; }
  a { color: inherit; text-decoration: none; }
  h1 { font-size: 22pt; }
  h2 { font-size: 15pt; }
  h3 { font-size: 12pt; }
  p, li, blockquote, table, pre { break-inside: avoid-page; }
}
""".strip()


def _title(markdown_text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", markdown_text, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def render_html(markdown_path: Path) -> str:
    text = markdown_path.read_text(encoding="utf-8")
    title = _title(text, markdown_path.stem)
    body = markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "toc"],
        output_format="html5",
    )
    soup = BeautifulSoup(body, "html.parser")
    for forbidden in soup.find_all(["script", "iframe", "form", "object", "embed"]):
        forbidden.decompose()
    for tag in soup.find_all(True):
        for attribute in list(tag.attrs):
            if attribute.casefold().startswith("on"):
                del tag.attrs[attribute]
        href = tag.get("href")
        if isinstance(href, str) and href.strip().casefold().startswith("javascript:"):
            del tag.attrs["href"]
    safe_body = str(soup)
    if re.search(r"<(?:script|iframe|form|object|embed)\b|\son\w+=|javascript:", safe_body, re.I):
        raise ValueError("generated reference HTML contains executable content")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
{favicon_link_tags()}
<style>{STYLE}</style>
</head>
<body>
<main>
{safe_body}
</main>
</body>
</html>
"""


def build(markdown_path: Path, output_root: Path) -> tuple[Path, Path]:
    markdown_path = markdown_path.resolve()
    if not markdown_path.is_relative_to(REFERENCES) or markdown_path.suffix.lower() != ".md":
        raise ValueError("input must be normalized Markdown under References/")
    rel = markdown_path.relative_to(REFERENCES)
    html_path = (output_root.resolve() / rel).with_suffix(".html")
    pdf_path = html_path.with_suffix(".pdf")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(html_path, render_html(markdown_path))
    result = subprocess.run(
        ["node", str(BASE / "Scripts/_html_to_pdf.js"), str(html_path)],
        cwd=BASE,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "reference PDF rendering failed")
    normalize_study_pdf(markdown_path, pdf_path)
    reader = PdfReader(str(pdf_path))
    if not reader.pages:
        raise ValueError("generated reference PDF has no pages")
    if pdf_path.stat().st_size < 10_000:
        raise ValueError("generated reference PDF is unexpectedly small")
    print(f"Built {_display_path(html_path)}")
    print(f"Built {_display_path(pdf_path)} ({len(reader.pages)} pages)")
    return html_path, pdf_path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(BASE).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    try:
        build(args.markdown, args.output_root)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Reference PDF build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
