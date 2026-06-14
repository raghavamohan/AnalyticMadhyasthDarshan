import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown

from _common import STUDIES

if len(sys.argv) > 1:
    INPUT = Path(sys.argv[1]).resolve()
else:
    INPUT = STUDIES / "How-To-Form-Self-Sustaining-Organizations.md"

OUTPUT = INPUT.with_suffix(".html")


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


md_text = INPUT.read_text(encoding="utf-8")

# Use the document's first H1 as the HTML title, falling back to the filename.
h1 = next((line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")), None)
TITLE = h1 or INPUT.stem

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "smarty"],
)
html_body = absolutize_local_links(html_body, OUTPUT)

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{TITLE}</title>
<style>
  @page {{
    size: A4;
    margin: 2.2cm 2cm 2.2cm 2cm;
  }}
  @media print {{
    body {{ font-size: 11pt; }}
    h2 {{ page-break-after: avoid; }}
    h3 {{ page-break-after: avoid; }}
    table {{ page-break-inside: avoid; }}
    pre {{ page-break-inside: avoid; }}
    blockquote {{ page-break-inside: avoid; }}
  }}
  body {{
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
  h2 {{
    font-size: 15pt;
    margin-top: 22pt;
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
  p {{
    margin: 6pt 0;
    text-align: justify;
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
  blockquote strong {{
    font-style: normal;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
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
  em {{
    color: #444;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

OUTPUT.write_text(full_html, encoding="utf-8")

print(f"HTML written to: {OUTPUT}")
