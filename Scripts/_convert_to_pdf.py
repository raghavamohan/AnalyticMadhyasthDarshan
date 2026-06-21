import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown

from _common import STUDIES, study_md
from _study_catalog import strip_status_for_pdf


def absolutize_local_links(html_body: str, html_path: Path) -> str:
    """Rewrite relative local hrefs to file:// URLs so PDF renderers can open them."""

    def replace(match: re.Match[str]) -> str:
        href = unquote(match.group(1))
        parsed = urlparse(href)
        if parsed.scheme in {"http", "https", "mailto", "file"} or href.startswith("#"):
            return match.group(0)
        target = (html_path.parent / href).resolve()
        if target.exists():
            return f'href="{target.as_uri()}"'
        return match.group(0)

    return re.sub(r'href="([^"]+)"', replace, html_body)


def convert_to_html(input_path: Path) -> Path:
    output_path = input_path.with_suffix(".html")
    md_text = input_path.read_text(encoding="utf-8")
    md_text = strip_status_for_pdf(md_text)

    h1 = next((line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")), None)
    title = h1 or input_path.stem

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "smarty"],
    )
    html_body = absolutize_local_links(html_body, output_path)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  @page {{
    size: A4;
    margin: 2.2cm 2cm 2.2cm 2cm;
  }}
  @media print {{
    body {{
      font-size: 11pt;
      margin: 0;
      padding: 0;
      max-width: none;
    }}
    h1 ~ p {{
      margin: 3pt 0;
    }}
    h2 {{
      page-break-after: auto;
      break-after: auto;
    }}
    h2:first-of-type {{
      margin-top: 10pt;
    }}
    h2, h3, h4 {{ page-break-after: avoid; break-after: avoid; }}
    h3, h4 {{ page-break-inside: avoid; break-inside: avoid; }}
    p {{ text-align: justify; text-justify: inter-word; hyphens: auto; }}
    li {{ text-align: left; }}
    table {{
      page-break-inside: auto;
      break-inside: auto;
    }}
    thead {{
      display: table-header-group;
    }}
    tr {{
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    pre {{ page-break-inside: avoid; }}
    blockquote {{ page-break-inside: avoid; }}
  }}
  body {{
    position: relative;
    z-index: 1;
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    max-width: 750px;
    margin: 30px auto;
    padding: 0 20px;
  }}
  h1 {{
    font-size: 20pt;
    margin-top: 0;
    margin-bottom: 4pt;
    color: #111;
    border-bottom: 2px solid #333;
    padding-bottom: 6pt;
  }}
  h1 + p {{
    margin-top: 4pt;
  }}
  h2 {{
    font-size: 15pt;
    margin-top: 18pt;
    margin-bottom: 6pt;
    color: #222;
    border-bottom: 1px solid #bbb;
    padding-bottom: 4pt;
  }}
  h3 {{
    font-size: 12.5pt;
    margin-top: 16pt;
    margin-bottom: 4pt;
    color: #333;
  }}
  h4 {{
    font-size: 11.5pt;
    margin-top: 14pt;
    margin-bottom: 4pt;
    color: #333;
    font-weight: bold;
  }}
  p {{
    margin: 6pt 0;
    text-align: justify;
    text-justify: inter-word;
    hyphens: auto;
  }}
  a {{
    color: #1a5276;
    text-decoration: underline;
  }}
  blockquote {{
    margin: 10pt 0 10pt 16pt;
    padding: 6pt 12pt;
    border-left: 3pt solid #888;
    background: #f7f7f5;
    font-style: italic;
    color: #333;
  }}
  blockquote p {{
    margin: 0;
    white-space: pre-line;
  }}
  blockquote p + p {{
    margin-top: 6pt;
  }}
  blockquote strong {{
    font-style: normal;
  }}
  .quote-source {{
    font-style: normal;
    font-size: 10pt;
    color: #555;
    margin-top: 4pt;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
    page-break-inside: auto;
    break-inside: auto;
  }}
  thead {{
    display: table-header-group;
  }}
  tr {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  th {{
    background: #e8e8e4;
    border: 1px solid #aaa;
    padding: 5pt 7pt;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    border: 1px solid #ccc;
    padding: 5pt 7pt;
    vertical-align: top;
  }}
  tr:nth-child(even) {{
    background: #fafaf8;
  }}
  code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10pt;
    background: #f0f0ec;
    padding: 1pt 3pt;
    border-radius: 2pt;
  }}
  pre {{
    background: #f5f5f1;
    padding: 10pt 14pt;
    border-radius: 4pt;
    overflow-x: auto;
    font-size: 10pt;
    line-height: 1.4;
  }}
  pre code {{
    background: none;
    padding: 0;
  }}
  ul, ol {{
    margin: 6pt 0;
    padding-left: 24pt;
  }}
  li {{
    margin: 3pt 0;
  }}
  img {{
    display: block;
    max-width: 100%;
    height: auto;
    margin: 12pt auto;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  p:has(> img:only-child) {{
    text-align: center;
    margin: 12pt 0;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    output_path.write_text(full_html, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a study markdown file to styled HTML.")
    parser.add_argument("input", nargs="?", default=None, help="Path to the study .md file")
    parser.add_argument(
        "--watermark",
        default=None,
        help='Deprecated: watermark is applied in _html_to_pdf.js after PDF generation.',
    )
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input).resolve()
    else:
        input_path = study_md("How-To-Form-Self-Sustaining-Organizations")

    if args.watermark:
        print("Note: --watermark on _convert_to_pdf.py is ignored; use _html_to_pdf.js instead.")

    output_path = convert_to_html(input_path)
    print(f"HTML written to: {output_path}")


if __name__ == "__main__":
    main()
