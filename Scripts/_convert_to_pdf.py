import argparse
import html as html_module
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown

from _common import APPLICATIONS, BASE, REFERENCES, STUDIES, is_linkable_reference_file, site_base_url, study_md
from _study_catalog import strip_status_for_pdf


def convert_mermaid_blocks(html_body: str) -> str:
    """Turn fenced ```mermaid code blocks into div.mermaid for browser rendering."""

    pattern = re.compile(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        re.DOTALL | re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        content = html_module.unescape(match.group(1).strip())
        return f'<div class="mermaid">\n{content}\n</div>'

    return pattern.sub(replace, html_body)


def _resolve_repo_link(href: str, source_dir: Path) -> Path | None:
    """Resolve a relative href to a downloadable file under References/ or Studies/."""
    if not href or href.startswith("#"):
        return None
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https", "mailto", "file"}:
        return None

    path_part = unquote(parsed.path or href.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return None

    candidates = [(source_dir / path_part).resolve()]
    normalized = path_part.replace("\\", "/")
    if normalized.startswith("../References/"):
        fixed = normalized.replace("../References/", "../../References/", 1)
        candidates.append((source_dir / fixed).resolve())

    studies = BASE / "Studies"
    applications = BASE / "Applications"
    for candidate in candidates:
        try:
            if not candidate.is_file() or not candidate.is_relative_to(BASE):
                continue
            if not is_linkable_reference_file(candidate):
                continue
            if candidate.is_relative_to(REFERENCES):
                return candidate
            if candidate.suffix.lower() == ".pdf" and (
                candidate.is_relative_to(studies) or candidate.is_relative_to(applications)
            ):
                return candidate
        except ValueError:
            continue
    return None


def rewrite_local_links_for_site(
    html_body: str,
    html_path: Path,
    *,
    study_links_as_html: bool = False,
) -> str:
    """Rewrite local bibliography and cross-study hrefs to the published site URL."""

    site_root = site_base_url().rstrip("/")
    studies = BASE / "Studies"
    applications = BASE / "Applications"

    def replace(match: re.Match[str]) -> str:
        href = unquote(match.group(1))
        parsed = urlparse(href)
        fragment = parsed.fragment
        if parsed.scheme in {"http", "https", "mailto"} or href.startswith("#"):
            return match.group(0)

        target = _resolve_repo_link(href, html_path.parent)
        if target is None:
            return match.group(0)

        publish_target = target
        if study_links_as_html and target.suffix.lower() == ".pdf":
            try:
                if target.is_relative_to(studies) or target.is_relative_to(applications):
                    publish_target = target.with_suffix(".html")
            except ValueError:
                pass

        url = f"{site_root}/{publish_target.relative_to(BASE).as_posix()}"
        if fragment:
            url = f"{url}#{fragment}"
        return f'href="{url}"'

    return re.sub(r'href="([^"]+)"', replace, html_body)


def _slugify_heading(text: str) -> str:
    plain = re.sub(r"<[^>]+>", "", text)
    plain = html_module.unescape(plain).strip().lower()
    slug = re.sub(r"[^\w\s-]", "", plain)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug or "section"


def add_section_ids(html_body: str) -> str:
    """Add stable fragment ids to h2 headings for in-page section navigation."""
    seen: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        if match.group(0).startswith("<h2 id="):
            return match.group(0)
        inner = match.group(1)
        base = _slugify_heading(inner)
        count = seen.get(base, 0)
        seen[base] = count + 1
        slug = base if count == 0 else f"{base}-{count + 1}"
        return f'<h2 id="{slug}">{inner}</h2>'

    return re.sub(r"<h2>(.*?)</h2>", repl, html_body, flags=re.DOTALL)


def _format_toolbar_title(title: str, *, is_draft: bool) -> str:
    escaped = html_module.escape(title)
    if is_draft:
        return f'{escaped} <span class="study-toolbar-draft">(Draft)</span>'
    return escaped


def _study_toolbar_html(md_path: Path, *, is_draft: bool, title: str) -> str:
    md_path = md_path.resolve()
    stem = md_path.stem
    try:
        if md_path.parent.is_relative_to(APPLICATIONS):
            catalog_href = "../../Studies/index.html"
        else:
            catalog_href = "../index.html"
    except ValueError:
        catalog_href = "../index.html"
    pdf_href = f"{stem}.pdf"
    title_html = _format_toolbar_title(title, is_draft=is_draft)
    return f"""<nav class="study-toolbar" aria-label="Study navigation">
  <div class="study-toolbar-row study-toolbar-row--primary">
    <a class="study-toolbar-link study-toolbar-back" href="{catalog_href}">&larr; All studies</a>
    <p class="study-toolbar-title">{title_html}</p>
    <a class="study-toolbar-link study-toolbar-download" href="{pdf_href}" download>Download PDF</a>
  </div>
  <div class="study-toolbar-row study-toolbar-row--sections">
    <a class="study-toolbar-link study-toolbar-section study-toolbar-section--prev" id="study-section-prev" href="#" aria-disabled="true">&larr; Previous section</a>
    <a class="study-toolbar-link study-toolbar-section study-toolbar-section--next" id="study-section-next" href="#" aria-disabled="true">Next section &rarr;</a>
  </div>
</nav>
"""


def _study_section_nav_js() -> str:
    return """<script>
(() => {
  const toolbar = document.querySelector(".study-toolbar");
  const prev = document.getElementById("study-section-prev");
  const next = document.getElementById("study-section-next");
  if (!toolbar || !prev || !next) return;

  const sections = Array.from(document.querySelectorAll("h2[id]"));
  const syncToolbarHeight = () => {
    document.documentElement.style.setProperty(
      "--study-toolbar-height",
      `${toolbar.offsetHeight}px`
    );
  };

  const sectionLabel = el => el.textContent.replace(/\\s+/g, " ").trim();

  const marker = () => (toolbar.offsetHeight || 0) + 16;

  const currentIndex = () => {
    const y = window.scrollY + marker();
    let idx = -1;
    for (let i = 0; i < sections.length; i++) {
      if (sections[i].offsetTop <= y) idx = i;
      else break;
    }
    return idx;
  };

  const setDisabled = (link, disabled, fallback) => {
    link.classList.toggle("is-disabled", disabled);
    if (disabled) {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
      link.textContent = fallback;
    } else {
      link.setAttribute("aria-disabled", "false");
    }
  };

  const update = () => {
    if (!sections.length) {
      setDisabled(prev, true, "\\u2190 Previous section");
      setDisabled(next, true, "Next section \\u2192");
      return;
    }

    const idx = currentIndex();

    if (idx <= 0) {
      setDisabled(prev, true, "\\u2190 Previous section");
    } else {
      prev.classList.remove("is-disabled");
      prev.href = `#${sections[idx - 1].id}`;
      prev.setAttribute("aria-disabled", "false");
      prev.textContent = `\\u2190 ${sectionLabel(sections[idx - 1])}`;
    }

    if (idx < 0 || idx >= sections.length - 1) {
      setDisabled(next, true, "Next section \\u2192");
    } else {
      next.classList.remove("is-disabled");
      next.href = `#${sections[idx + 1].id}`;
      next.setAttribute("aria-disabled", "false");
      next.textContent = `${sectionLabel(sections[idx + 1])} \\u2192`;
    }
  };

  syncToolbarHeight();
  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", () => {
    syncToolbarHeight();
    update();
  });
})();
</script>
"""


def _mermaid_loader_html(html_body: str) -> str:
    if 'class="mermaid"' not in html_body:
        return ""
    return """<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({
  startOnLoad: true,
  theme: prefersDark ? "dark" : "neutral",
  securityLevel: "loose",
  flowchart: { htmlLabels: true, useMaxWidth: true },
});
</script>
"""


def _study_screen_dark_css() -> str:
    return """
  @media screen and (prefers-color-scheme: dark) {
    body {
      color: #e6dfd6;
      background: #1a1815;
    }
    h1, h2, h3, h4 {
      color: #f5f1ec;
    }
    h1 { border-bottom-color: #6f655a; }
    h2 { border-bottom-color: #423b33; }
    a { color: #7ebbed; }
    a:visited { color: #9ec8e8; }
    blockquote {
      background: #26231e;
      border-left-color: #6f655a;
      color: #e6dfd6;
    }
    .quote-source { color: #aca194; }
    th {
      background: #2f2a24;
      border-color: #423b33;
      color: #f5f1ec;
    }
    td {
      border-color: #423b33;
      color: #e6dfd6;
    }
    tr:nth-child(even) { background: #1e1b18; }
    code {
      background: #2f2a24;
      color: #f0e8dc;
    }
    pre {
      background: #1e1b18;
      color: #e6dfd6;
    }
    .study-toolbar {
      background: rgba(26, 24, 21, 0.92);
      border-color: #423b33;
    }
    .study-toolbar-link { color: #7ebbed; }
    .study-toolbar-link:hover { color: #b8daf3; }
    .study-toolbar-title { color: #f5f1ec; }
    .study-toolbar-draft { color: #aca194; }
    .study-toolbar-section.is-disabled { color: #6f655a; }
  }
"""


def convert_to_html(
    input_path: Path,
    *,
    is_draft: bool = False,
    include_web_chrome: bool = False,
) -> Path:
    output_path = input_path.with_suffix(".html")
    md_text = input_path.read_text(encoding="utf-8")
    md_text = strip_status_for_pdf(md_text)

    h1 = next((line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")), None)
    title = h1 or input_path.stem

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "smarty"],
    )
    html_body = convert_mermaid_blocks(html_body)
    html_body = rewrite_local_links_for_site(
        html_body,
        output_path,
        study_links_as_html=include_web_chrome,
    )
    if include_web_chrome:
        html_body = add_section_ids(html_body)

    toolbar = (
        _study_toolbar_html(input_path, is_draft=is_draft, title=title)
        if include_web_chrome
        else ""
    )
    mermaid_loader = _mermaid_loader_html(html_body) if include_web_chrome else ""
    section_nav_js = _study_section_nav_js() if include_web_chrome else ""
    screen_dark_css = _study_screen_dark_css() if include_web_chrome else ""

    web_chrome_css = ""
    if include_web_chrome:
        web_chrome_css = """
  html { scroll-behavior: smooth; }
  h2[id] {
    scroll-margin-top: calc(var(--study-toolbar-height, 88px) + 10px);
  }
  .study-toolbar {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    position: sticky;
    top: 0;
    z-index: 20;
    margin: 0 0 22px;
    padding: 10px 14px;
    border: 1px solid #d8d2c8;
    border-radius: 8px;
    background: rgba(247, 244, 239, 0.92);
    -webkit-backdrop-filter: blur(8px);
    backdrop-filter: blur(8px);
  }
  .study-toolbar-row {
    display: grid;
    align-items: center;
    gap: 8px 14px;
  }
  .study-toolbar-row--primary {
    grid-template-columns: minmax(0, 1fr) minmax(0, 2fr) minmax(0, 1fr);
  }
  .study-toolbar-row--sections {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
  .study-toolbar-back {
    justify-self: start;
    min-width: 0;
  }
  .study-toolbar-download {
    justify-self: end;
    min-width: 0;
    text-align: right;
  }
  .study-toolbar-title {
    justify-self: center;
    text-align: center;
    margin: 0;
    min-width: 0;
    font-size: 14px;
    font-weight: 700;
    color: #2c241c;
    line-height: 1.35;
  }
  .study-toolbar-draft {
    font-weight: 600;
    color: #5c5348;
  }
  .study-toolbar-link {
    color: #1a5276;
    text-decoration: none;
    font-weight: 600;
  }
  .study-toolbar-link:hover { color: #13405c; }
  .study-toolbar-section {
    display: block;
    min-width: 0;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .study-toolbar-section--prev { justify-self: start; }
  .study-toolbar-section--next {
    justify-self: end;
    text-align: right;
  }
  .study-toolbar-section.is-disabled {
    opacity: 0.45;
    pointer-events: none;
    color: #6f655a;
  }
  .study-toolbar-download::after {
    content: " \\2193";
    font-weight: 700;
  }
  @media (max-width: 640px) {
    .study-toolbar-row--primary {
      grid-template-columns: 1fr 1fr;
    }
    .study-toolbar-title {
      grid-column: 1 / -1;
      white-space: normal;
    }
    .study-toolbar-section {
      white-space: normal;
    }
  }
  @media print {
    .study-toolbar { display: none !important; }
  }
"""

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="color-scheme" content="light dark"/>
<title>{html_module.escape(title)}</title>
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
    pre {{ page-break-inside: avoid; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; }}
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
    overflow-wrap: anywhere;
    word-break: break-word;
    white-space: pre-wrap;
    max-width: 100%;
    font-size: 10pt;
    line-height: 1.4;
  }}
  pre code {{
    background: none;
    padding: 0;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
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
  .mermaid {{
    display: flex;
    justify-content: center;
    margin: 12pt auto;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .mermaid svg {{
    max-width: 100%;
    height: auto;
  }}
{web_chrome_css}{screen_dark_css}
</style>
</head>
<body>
{toolbar}{html_body}
{mermaid_loader}{section_nav_js}
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
