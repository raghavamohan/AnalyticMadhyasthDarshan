import argparse
import html as html_module
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import markdown
from bs4 import BeautifulSoup

from _safe_study_html import sanitize_author_html
from _study_reader import reader_assets, reader_bootstrap, reader_controls
from _verify_study_svgs import verify_study_svgs, verify_svg_file

from _build_discussion_pages import ASSET_VERSION as DISCUSS_ASSET_VERSION
from _common import (
    APPLICATIONS,
    BASE,
    REFERENCES,
    STUDIES,
    favicon_link_tags,
    is_linkable_reference_file,
    site_base_url,
    study_md,
    write_text_lf,
)
from _glossary_tooltips import apply_glossary_tooltips, load_glossary, wrap_tables_for_scroll
from _reference_artifacts import public_delivery_url
from _study_catalog import STATUS_MD_RE, get_study_row, parse_edited_on, strip_status_for_pdf

FEEDBACK_ISSUES_URL = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new"

SCRIPTS_DIR = Path(__file__).resolve().parent
KATEX_CSS_PATH = SCRIPTS_DIR / "node_modules" / "katex" / "dist" / "katex.min.css"
# Vendored so published pages do not reference node_modules. Studies and
# applications both sit two levels below the repo root, so one relative href
# resolves for the site and for the file:// render that produces the PDF.
KATEX_WEB_FONTS = SCRIPTS_DIR.parent / "Assets" / "KaTeX" / "fonts"
KATEX_WEB_FONT_HREF = "../../Assets/KaTeX/fonts"
KATEX_RENDER_SCRIPT = SCRIPTS_DIR / "_render_katex_math.js"
_INLINE_MATH = re.compile(r"(?<!\\)\$(?!\$).+?(?<!\\)\$(?!\$)", re.DOTALL)
_DISPLAY_MATH = re.compile(r"\$\$.+?\$\$", re.DOTALL)
_INLINE_MATH_CAPTURE = re.compile(
    r"(?<!\\)\$(?!\$)((?:\\.|[^$\\])+?)(?<!\\)\$(?!\$)",
)
_DISPLAY_MATH_CAPTURE = re.compile(r"\$\$([\s\S]+?)\$\$")
_MATH_PLACEHOLDER = "\ue000MATH_{idx}\ue001"
_CODE_FENCE = re.compile(r"^```[\s\S]*?^```[^\n]*$", re.MULTILINE)
_INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_CODE_PLACEHOLDER = "\x00CODE_{idx}\x00"
_CODE_PLACEHOLDER_RE = re.compile(r"\x00CODE_(\d+)\x00")
_ORG_NAME = "AnalyticMadhyasthDarshan.org"
_CC_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
_THE_QUESTION_RE = re.compile(
    r"^\*\*The question:\*\*\s*(.+?)\s*$",
    re.MULTILINE,
)
_META_DESC_MAX = 300


def contains_latex_math(text: str) -> bool:
    """Return True when markdown or HTML still has $...$ / $$...$$ math delimiters."""
    return bool(_INLINE_MATH.search(text) or _DISPLAY_MATH.search(text))


def protect_latex_math(html_body: str) -> tuple[str, list[str]]:
    """Replace math delimiters with placeholders so later HTML passes leave them intact."""
    segments: list[str] = []

    def stash(match: re.Match[str]) -> str:
        segments.append(match.group(0))
        return _MATH_PLACEHOLDER.format(idx=len(segments) - 1)

    protected = _DISPLAY_MATH_CAPTURE.sub(stash, html_body)
    protected = _INLINE_MATH_CAPTURE.sub(stash, protected)
    return protected, segments


def protect_latex_math_in_markdown(md_text: str) -> tuple[str, list[str]]:
    """Stash math out of the markdown source before Markdown eats LaTeX backslashes.

    Python-Markdown treats ``\\{``, ``\\}``, ``\\_`` and friends as escaped
    punctuation, so set notation and subscripts silently lose their backslashes
    if math is only protected after conversion. Code spans and fences are
    stashed first so a stray ``$`` in sample code is not read as math.
    """
    code_segments: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_segments.append(match.group(0))
        return _CODE_PLACEHOLDER.format(idx=len(code_segments) - 1)

    guarded = _CODE_FENCE.sub(stash_code, md_text)
    guarded = _INLINE_CODE.sub(stash_code, guarded)
    protected, math_segments = protect_latex_math(guarded)
    protected = _CODE_PLACEHOLDER_RE.sub(
        lambda match: code_segments[int(match.group(1))],
        protected,
    )
    return protected, math_segments


def restore_latex_math(html_body: str, segments: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        return segments[int(match.group(1))]

    return re.sub(r"\ue000MATH_(\d+)\ue001", repl, html_body)


def _load_katex_css() -> str:
    """Inline KaTeX's stylesheet with font URLs that resolve in both places.

    The PDF is rendered from the published HTML through a file:// URL, so these
    references have to work on the site and on disk alike, which a page-relative
    path does. The absolute local path this used to write worked only for the
    PDF: on the site it could not resolve, so every formula fell back to a plain
    serif, and it shipped the maintainer's home directory into public HTML.
    """
    if not KATEX_CSS_PATH.is_file():
        raise FileNotFoundError(
            "KaTeX CSS not found. Run once from the repo root:\n"
            "  cd Scripts; npm install"
        )
    if not KATEX_WEB_FONTS.is_dir():
        raise FileNotFoundError(
            f"Vendored KaTeX fonts missing at {KATEX_WEB_FONTS}. Restore with:\n"
            "  cp Scripts/node_modules/katex/dist/fonts/*.woff2 Assets/KaTeX/fonts/"
        )
    css = KATEX_CSS_PATH.read_text(encoding="utf-8")
    # Only woff2 is vendored -- supported everywhere, including by the Chrome
    # that renders the PDF -- so the woff and truetype alternatives are dropped
    # rather than left pointing at files the site does not serve.
    css = re.sub(
        r',\s*url\(fonts/[^)]+\)\s*format\("(?:woff|truetype)"\)',
        "",
        css,
    )
    return css.replace("url(fonts/", f"url({KATEX_WEB_FONT_HREF}/")


def render_latex_math(html_body: str) -> str:
    """Replace LaTeX math delimiters with KaTeX HTML before glossary/tooltip passes."""
    if not contains_latex_math(html_body):
        return html_body
    if not KATEX_RENDER_SCRIPT.is_file():
        raise FileNotFoundError(f"Missing KaTeX render script: {KATEX_RENDER_SCRIPT}")

    result = subprocess.run(
        ["node", str(KATEX_RENDER_SCRIPT)],
        input=html_body,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        cwd=SCRIPTS_DIR,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise RuntimeError(f"KaTeX rendering failed: {detail}")
    return result.stdout


_OL_SPLIT_BY_PAGE_MARKER = re.compile(
    r"(<ol(?:\s[^>]*)?>)((?:(?!</ol>).)*)(</ol>\s*)"
    r'(<span class="page-marker"[^>]*>\[[^\]]+\]</span>\s*)'
    r"(<ol>)",
    re.DOTALL,
)

_KD_CHAPTER_HEADING_RE = re.compile(
    r"<p>(Chapter (?:One|Two|Three))</p>\s*<p>(.*?)</p>",
    re.DOTALL,
)


def _continue_ordered_list_numbering(html_body: str) -> str:
    """Set start= on <ol> blocks split only by page markers so numbering continues."""
    while True:
        match = _OL_SPLIT_BY_PAGE_MARKER.search(html_body)
        if not match:
            break
        open_tag, content, close_ol, separator, next_open = match.groups()
        start_match = re.search(r'\bstart="(\d+)"', open_tag)
        start = int(start_match.group(1)) if start_match else 1
        item_count = len(re.findall(r"<li\b", content))
        next_start = start + item_count
        html_body = (
            html_body[: match.start()]
            + f"{open_tag}{content}{close_ol}{separator}<ol start=\"{next_start}\">"
            + html_body[match.end() :]
        )
    return html_body


def _wrap_kd_chapter_headings(html_body: str) -> str:
    """Give the three KD chapter openings a stable, separately styled structure."""

    def repl(match: re.Match[str]) -> str:
        label, title = match.groups()
        return (
            '<header class="kd-chapter-heading">\n'
            f'  <p class="kd-chapter-label">{label}</p>\n'
            f'  <p class="kd-chapter-title">{title}</p>\n'
            "</header>"
        )

    wrapped, count = _KD_CHAPTER_HEADING_RE.subn(repl, html_body)
    if count != 3:
        raise ValueError(f"Expected 3 KD chapter headings, found {count}")
    return wrapped


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
    """Resolve a relative href to a published file under References/, Studies/, or Applications/.

    Study-folder ``.md`` companions resolve to a sibling ``.html`` or ``.pdf`` when
    one exists, so PDF output can use a site URL instead of a local ``file://`` link.
    """
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
            if candidate.is_relative_to(REFERENCES):
                if is_linkable_reference_file(candidate):
                    return candidate
                continue
            if not (
                candidate.is_relative_to(studies) or candidate.is_relative_to(applications)
            ):
                continue
            suffix = candidate.suffix.lower()
            if suffix in {".pdf", ".html"}:
                if is_linkable_reference_file(candidate):
                    return candidate
                continue
            if suffix == ".md":
                for sibling_suffix in (".html", ".pdf"):
                    sibling = candidate.with_suffix(sibling_suffix)
                    if sibling.is_file() and is_linkable_reference_file(sibling):
                        return sibling
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

        path_part = unquote(parsed.path or href.split("#", 1)[0].split("?", 1)[0])
        candidates = [(html_path.parent / path_part).resolve()]
        normalized_path = path_part.replace("\\", "/")
        if normalized_path.startswith("../References/"):
            fixed = normalized_path.replace("../References/", "../../References/", 1)
            candidates.append((html_path.parent / fixed).resolve())
        for candidate in candidates:
            try:
                if candidate.is_relative_to(REFERENCES):
                    repo_path = candidate.relative_to(BASE).as_posix()
                    reference_url = public_delivery_url(repo_path)
                    if not reference_url and candidate.suffix.lower() == ".md":
                        active_prefixes = (
                            REFERENCES / "Madhyasth-Darshan/KD-Karm-Darshan-English",
                            REFERENCES / "Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English",
                        )
                        if any(candidate.is_relative_to(prefix) for prefix in active_prefixes):
                            sibling_pdf = candidate.with_suffix(".pdf")
                            if sibling_pdf.is_file():
                                reference_url = (
                                    f"{site_root}/{sibling_pdf.relative_to(BASE).as_posix()}"
                                )
                    if reference_url:
                        if fragment:
                            reference_url = f"{reference_url}#{fragment}"
                        return f'href="{reference_url}"'
                if candidate.is_relative_to(studies) or candidate.is_relative_to(applications):
                    source_markdown = candidate.with_suffix(".md")
                    published_html = candidate.with_suffix(".html")
                    if source_markdown.is_file():
                        if not published_html.is_file():
                            raise ValueError(
                                "cross-study link has no generated HTML target: "
                                f"{published_html.relative_to(BASE).as_posix()}"
                            )
                        url = f"{site_root}/{published_html.relative_to(BASE).as_posix()}"
                        if fragment:
                            url = f"{url}#{fragment}"
                        return f'href="{url}"'
            except (OSError, ValueError):
                raise

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


_HEADING_NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)[\s.]")


def _heading_depth(inner_html: str) -> int | None:
    """Depth implied by a leading section number: "1.2" -> 2, "1.2.1" -> 3."""
    text = re.sub(r"<[^>]+>", "", inner_html)
    match = _HEADING_NUMBER_RE.match(html_module.unescape(text))
    if not match:
        return None
    return match.group(1).count(".") + 1


def add_section_ids(html_body: str) -> str:
    """Add stable fragment ids to h2 and h3 headings for in-page navigation.

    An h3 also carries data-depth -- 2 for "1.2", 3 for "1.2.1" -- so the screen
    stylesheet and the contents list can tell a subsection from a
    sub-subsection. The element stays an h3 rather than becoming an h4, because
    the PDF is rendered from this same HTML and its outline is asserted by
    _verify_pdf_outline; the distinction is presentational on screen only.
    """
    seen: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        if "id=" in attrs:
            return match.group(0)
        base = _slugify_heading(inner)
        count = seen.get(base, 0)
        seen[base] = count + 1
        slug = base if count == 0 else f"{base}-{count + 1}"
        depth = _heading_depth(inner) if tag == "h3" else None
        depth_attr = f' data-depth="{depth}"' if depth else ""
        return f'<{tag} id="{slug}"{depth_attr}{attrs}>{inner}</{tag}>'

    return re.sub(r"<(h2|h3)([^>]*)>(.*?)</\1>", repl, html_body, flags=re.DOTALL)


_TOC_MIN_ENTRIES = 6


def _study_contents_html(html_body: str) -> str:
    """Build a contents list from the ids add_section_ids has just written.

    Studies run to 34,000 words with as many as 57 headings, and the only other
    way through them is the sequential previous/next section pair. Rendered
    server-side so it works without JavaScript and is crawlable; hidden in
    print, where the PDF outline already serves this purpose.
    """
    entries: list[tuple[int, str, str]] = []
    pattern = re.compile(r'<(h2|h3) id="([^"]+)"([^>]*)>(.*?)</\1>', re.DOTALL)
    for match in pattern.finditer(html_body):
        tag, slug, attrs, inner = match.groups()
        if tag == "h2":
            level = 1
        else:
            depth_match = re.search(r'data-depth="(\d+)"', attrs)
            level = min(int(depth_match.group(1)), 3) if depth_match else 2
        text = " ".join(html_module.unescape(re.sub(r"<[^>]+>", "", inner)).split())
        if text:
            entries.append((level, slug, text))
    if len(entries) < _TOC_MIN_ENTRIES:
        return ""
    items = "\n".join(
        f'      <li class="study-toc-item study-toc-l{level}">'
        f'<a href="#{slug}">{html_module.escape(text)}</a></li>'
        for level, slug, text in entries
    )
    sections = sum(1 for level, _, _ in entries if level == 1)
    return f"""<details class="study-toc" id="study-contents">
  <summary class="study-toc-summary">
    <span class="study-toc-label">Contents</span>
    <span class="study-toc-meta">{sections} sections &middot; {len(entries)} headings</span>
  </summary>
  <nav class="study-toc-nav" aria-label="Contents">
    <ol class="study-toc-list">
{items}
    </ol>
  </nav>
</details>
"""


def insert_study_contents(html_body: str) -> str:
    """Place the contents list after the opening matter, before the first section."""
    contents = _study_contents_html(html_body)
    if not contents:
        return html_body
    first_section = re.search(r'<h2 id="', html_body)
    if not first_section:
        return html_body
    cut = first_section.start()
    return f"{html_body[:cut]}{contents}{html_body[cut:]}"


def insert_study_reading_key(html_body: str) -> str:
    """Explain the two inline affordances once, beside the study contents."""
    if 'class="term-tip"' not in html_body:
        return html_body

    key = """<p class="study-reading-key" aria-label="Reading key">
  <span class="study-reading-key-term">Dotted underline</span>: definition
  <span aria-hidden="true">&middot;</span>
  <span class="study-reading-key-link">Blue underline</span>: link
</p>
"""
    toc = re.search(
        r'(<details class="study-toc" id="study-contents">.*?</details>\n)',
        html_body,
        flags=re.DOTALL,
    )
    if toc:
        details = toc.group(1).replace(
            'class="study-toc"', 'class="study-toc study-toc--with-key"', 1
        )
        return f"{html_body[:toc.start()]}{details}{key}{html_body[toc.end():]}"

    first_section = re.search(r'<h2 id="', html_body)
    if first_section:
        cut = first_section.start()
        return f"{html_body[:cut]}{key}{html_body[cut:]}"
    title_end = re.search(r"</h1>\n?", html_body)
    if title_end:
        cut = title_end.end()
        return f"{html_body[:cut]}{key}{html_body[cut:]}"
    return f"{key}{html_body}"


def _feedback_href(title: str) -> str:
    issue_title = quote(f"Study feedback: {title}")
    return f"{FEEDBACK_ISSUES_URL}?template=study-feedback.yml&title={issue_title}"


def _study_toolbar_html(md_path: Path, *, title: str) -> str:
    md_path = md_path.resolve()
    stem = md_path.stem
    try:
        if md_path.parent.is_relative_to(APPLICATIONS):
            catalog_href = "../../Studies/index.html"
        else:
            catalog_href = "../index.html"
    except ValueError:
        catalog_href = "../index.html"
    catalog_href = f"{catalog_href}#study-{quote(stem)}"
    pdf_href = f"{stem}.pdf"
    discuss_href = f"discussion.html?dv={DISCUSS_ASSET_VERSION}" if DISCUSS_ASSET_VERSION else "discussion.html"
    feedback_href = _feedback_href(title)
    return f"""<nav class="study-toolbar" aria-label="Study navigation">
  <div class="study-toolbar-row study-toolbar-row--primary">
    <span class="reader-toolbar-start"><a class="study-toolbar-link study-toolbar-back" href="{catalog_href}" aria-label="Back to all studies">&larr; Studies</a>
      <button type="button" id="reader-open" aria-controls="reader-tools" aria-expanded="false" hidden>Contents &amp; tools</button></span>
    <span class="study-toolbar-actions">
      <a class="study-toolbar-link study-toolbar-discuss" href="{discuss_href}">Discuss</a>
      <a class="study-toolbar-link study-toolbar-download" href="{pdf_href}" download aria-label="Download PDF">PDF</a>
      <a class="study-toolbar-link study-toolbar-feedback" href="{feedback_href}" aria-label="Suggest a correction">Suggest edit</a>
      <button type="button" class="study-theme-toggle" id="study-theme-toggle" aria-label="Switch color theme">
        <span class="study-theme-toggle-label">Dark</span>
      </button>
    </span>
  </div>
  <div class="study-toolbar-row study-toolbar-row--sections">
    <a class="study-toolbar-link study-toolbar-section study-toolbar-section--prev" id="study-section-prev" href="#" aria-disabled="true">&larr; Previous section</a>
    <span id="reader-current" aria-label="Current section">Introduction</span>
    <a class="study-toolbar-link study-toolbar-section study-toolbar-section--next" id="study-section-next" href="#" aria-disabled="true">Next section &rarr;</a>
  </div>
</nav>
"""


def _term_tip_js() -> str:
    return """<script>
(() => {
  let floatPanel = document.getElementById("term-tip-float");
  if (!floatPanel) {
    floatPanel = document.createElement("div");
    floatPanel.id = "term-tip-float";
    floatPanel.className = "term-tip-panel";
    floatPanel.setAttribute("role", "tooltip");
    floatPanel.hidden = true;
    document.body.appendChild(floatPanel);
  }
  let activeButton = null;
  let pinnedButton = null;

  const hide = () => {
    if (activeButton) activeButton.setAttribute("aria-expanded", "false");
    activeButton = null;
    floatPanel.classList.remove("is-visible");
    floatPanel.hidden = true;
    floatPanel.textContent = "";
  };

  const show = (button, text) => {
    if (activeButton && activeButton !== button) {
      activeButton.setAttribute("aria-expanded", "false");
    }
    activeButton = button;
    button.setAttribute("aria-expanded", "true");
    floatPanel.textContent = text;
    floatPanel.hidden = false;
    floatPanel.classList.add("is-visible");
    const rect = button.getBoundingClientRect();
    const margin = 8;
    let top = rect.top - floatPanel.offsetHeight - margin;
    if (top < margin) top = rect.bottom + margin;
    let left = rect.left;
    const maxLeft = window.innerWidth - floatPanel.offsetWidth - margin;
    if (left > maxLeft) left = Math.max(margin, maxLeft);
    floatPanel.style.top = `${Math.max(8, top)}px`;
    floatPanel.style.left = `${Math.max(8, left)}px`;
  };

  document.querySelectorAll(".term-tip").forEach(button => {
    const definition = button.getAttribute("data-definition");
    if (!definition) return;
    button.setAttribute("aria-describedby", "term-tip-float");
    button.setAttribute("aria-expanded", "false");
    const reveal = () => show(button, definition);
    button.addEventListener("mouseenter", () => {
      if (!pinnedButton) reveal();
    });
    button.addEventListener("focus", () => {
      if (!pinnedButton || pinnedButton === button) reveal();
    });
    button.addEventListener("mouseleave", () => {
      if (!pinnedButton) hide();
    });
    button.addEventListener("blur", () => {
      if (!pinnedButton) hide();
    });
    button.addEventListener("click", event => {
      event.stopPropagation();
      if (pinnedButton === button) {
        pinnedButton = null;
        hide();
      } else {
        pinnedButton = button;
        reveal();
      }
    });
  });

  document.addEventListener("click", () => {
    pinnedButton = null;
    hide();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      pinnedButton = null;
      hide();
    }
  });
})();
</script>
"""


def _mermaid_loader_html(html_body: str) -> str:
    if 'class="mermaid"' not in html_body:
        return ""
    version = json.loads((SCRIPTS_DIR / "package.json").read_text(encoding="utf-8"))["dependencies"]["mermaid"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Pin Mermaid to an exact version shared by browser and PDF rendering")
    return """<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@__VERSION__/dist/mermaid.esm.min.mjs";
const system = window.matchMedia("(prefers-color-scheme: dark)");
const diagrams = Array.from(document.querySelectorAll(".mermaid"), node => ({ node, source: node.dataset.readerSource || (node.dataset.readerSource = node.textContent) }));
let queue = Promise.resolve();
let generation = 0;
const render = () => {
  queue = queue.then(async () => {
    const dark = document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && system.matches);
    const theme = dark ? "dark" : "neutral";
    mermaid.initialize({ startOnLoad: false, theme, securityLevel: "strict", flowchart: { htmlLabels: true, useMaxWidth: true } });
    const run = ++generation;
    for (const [index, { node, source }] of diagrams.entries()) {
      // Keep the old figure in place until its replacement is ready.
      const { svg } = await mermaid.render(`study-diagram-${run}-${index}`, source);
      node.innerHTML = svg;
      node.dataset.diagramTheme = theme;
    }
  }).catch(error => console.error("Study diagram could not render", error));
};
new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
system.addEventListener("change", render);
render();
</script>
""".replace("__VERSION__", version)


_STUDY_DARK_DECLARATIONS = """
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
    .study-toolbar-section.is-disabled { color: #6f655a; }
    .term-tip { color: inherit; border-bottom-color: #c9a66b; }
    .term-tip:hover { background: #2f2a24; }
    .term-tip-panel {
      color: #e6dfd6;
      background: #26231e;
      border-color: #423b33;
    }
    .study-toc { border-color: #423b33; }
    .study-toc-summary:hover { background: #1e1b18; }
    .study-toc-label { color: #f5f1ec; }
    .study-toc-meta { color: #aca194; }
    .study-toc-list a { color: #7ebbed; }
    .study-toc-l1 > a { color: #f5f1ec; }
    .study-reading-key { color: #aca194; }
    .study-reading-key-term { color: #e6dfd6; border-bottom-color: #c9a66b; }
    .study-reading-key-link { color: #7ebbed; }
    .study-theme-toggle {
      color: #7ebbed;
      border-color: #423b33;
      background: #1e1b18;
    }
    .study-theme-toggle:hover { border-color: #7ebbed; }
"""


def _prefix_selectors(css: str, prefix: str) -> str:
    """Scope every rule in a flat CSS block under `prefix`.

    Native CSS nesting would express this in one line but is not available to
    every reader's browser, so the selectors are rewritten instead. The block is
    flat -- no nested at-rules -- which makes the rule split safe.
    """
    rules = []
    for selectors, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        scoped = ", ".join(
            f"{prefix} {part.strip()}" for part in selectors.split(",") if part.strip()
        )
        body = " ".join(declarations.split())
        rules.append(f"    {scoped} {{ {body} }}")
    return "\n".join(rules)


def _study_screen_dark_css() -> str:
    """Dark palette for the study page, keyed to both theme signals.

    A reader who picks Dark on the studies index has "amd-theme" in
    localStorage, which the head script stamps onto data-theme. Anyone who has
    made no choice falls through to prefers-color-scheme. Both routes get the
    same declarations, and an explicit Light choice beats a dark OS.
    """
    chosen = _prefix_selectors(_STUDY_DARK_DECLARATIONS, 'html[data-theme="dark"]')
    inherited = _prefix_selectors(
        _STUDY_DARK_DECLARATIONS, 'html:not([data-theme])'
    )
    return f"""
  @media screen {{
{chosen}
  }}
  @media screen and (prefers-color-scheme: dark) {{
{inherited}
  }}
"""


def _study_canonical_url(input_path: Path) -> str:
    rel = input_path.relative_to(BASE).with_suffix(".html")
    return f"{site_base_url()}/{rel.as_posix()}"


def _truncate_description(text: str, limit: int = _META_DESC_MAX) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rsplit(" ", 1)[0]
    return f"{truncated}…"


def _study_description(md_text: str, slug: str) -> str:
    from _study_catalog import ONGOING_DESC_PREFIX_RE

    row_info = get_study_row(slug)
    if row_info:
        desc = ONGOING_DESC_PREFIX_RE.sub("", row_info[0].description.strip()).strip()
        if desc:
            return _truncate_description(desc)
    question = _THE_QUESTION_RE.search(md_text)
    if question:
        return _truncate_description(question.group(1).strip())
    for line in md_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("**"):
            continue
        return _truncate_description(stripped)
    return _truncate_description(slug.replace("-", " "))


def _social_card_url(slug: str) -> str:
    """Absolute URL of a study's share card, falling back to the site card.

    Cards are committed by Scripts/_build_social_cards.py. A study with no card
    yet -- one added since that last ran -- points at the site card rather than
    at a 404, so a shared link still renders.
    """
    base = site_base_url().rstrip("/")
    if (BASE / "Assets" / "Social" / f"{slug}.png").is_file():
        return f"{base}/Assets/Social/{quote(slug)}.png"
    return f"{base}/Assets/Social/og-default.png"


def _study_seo_head_html(
    *,
    title: str,
    description: str,
    canonical_url: str,
    date_modified_iso: str | None,
    slug: str,
) -> str:
    site_url = site_base_url().rstrip("/") + "/"
    esc_title = html_module.escape(title)
    esc_desc = html_module.escape(description)
    esc_canonical = html_module.escape(canonical_url)
    image_url = _social_card_url(slug)
    esc_image = html_module.escape(image_url)
    og_bits = f"""
<link rel="canonical" href="{esc_canonical}"/>
<meta name="description" content="{esc_desc}"/>
<meta property="og:type" content="article"/>
<meta property="og:site_name" content="{_ORG_NAME}"/>
<meta property="og:title" content="{esc_title}"/>
<meta property="og:description" content="{esc_desc}"/>
<meta property="og:url" content="{esc_canonical}"/>
<meta property="og:image" content="{esc_image}"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="{esc_title}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{esc_title}"/>
<meta name="twitter:description" content="{esc_desc}"/>
<meta name="twitter:image" content="{esc_image}"/>"""
    schema: dict = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": title,
        "description": description,
        "url": canonical_url,
        "inLanguage": "en",
        "author": {"@type": "Organization", "name": _ORG_NAME, "url": site_url},
        "publisher": {"@type": "Organization", "name": _ORG_NAME, "url": site_url},
        "license": _CC_LICENSE,
        "isPartOf": {"@type": "WebSite", "name": _ORG_NAME, "url": site_url},
        "image": image_url,
    }
    if date_modified_iso:
        schema["dateModified"] = date_modified_iso
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"""{og_bits}
<script type="application/ld+json">
{schema_json}
</script>"""


def convert_to_html(
    input_path: Path,
    *,
    is_draft: bool = False,
    include_web_chrome: bool = False,
) -> Path:
    output_path = input_path.with_suffix(".html")
    verify_study_svgs(input_path)
    md_text_raw = input_path.read_text(encoding="utf-8")
    md_text = strip_status_for_pdf(md_text_raw) if STATUS_MD_RE.search(md_text_raw) else md_text_raw

    h1 = next((line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")), None)
    title = h1 or input_path.stem

    has_latex_math = contains_latex_math(md_text)
    math_segments: list[str] = []
    md_for_html = md_text
    if has_latex_math:
        md_for_html, math_segments = protect_latex_math_in_markdown(md_text)

    html_body = markdown.markdown(
        md_for_html,
        extensions=["tables", "fenced_code", "smarty"],
    )
    html_body = sanitize_author_html(html_body)
    # Raw <img> authoring must pass the same SVG gate as Markdown images.
    for image in BeautifulSoup(html_body, "html.parser").find_all("img", src=True):
        source = urlparse(image["src"])
        if not source.scheme and not source.netloc and source.path.lower().endswith(".svg"):
            errors = verify_svg_file((input_path.parent / unquote(source.path)).resolve())
            if errors:
                raise ValueError("Unsafe study figure: " + "; ".join(errors))
    html_body = re.sub(
        r'<p>\[blank p[.\-]\s*([^\]]+)\]</p>',
        r'<div class="blank-page"><span class="blank-page-label">[p. \1]</span></div>',
        html_body,
    )
    html_body = re.sub(
        r'<p>\[p[.\-]\s*([^\]]+)\]</p>',
        r'<span class="page-marker">[p. \1]</span>',
        html_body,
    )
    if input_path.name == "KD-Karm-Darshan-English.md":
        html_body = _wrap_kd_chapter_headings(html_body)
    html_body = _continue_ordered_list_numbering(html_body)
    html_body = convert_mermaid_blocks(html_body)
    html_body = rewrite_local_links_for_site(
        html_body,
        output_path,
        study_links_as_html=include_web_chrome,
    )
    if include_web_chrome:
        html_body = add_section_ids(html_body)
        html_body = insert_study_contents(html_body)
        html_body = wrap_tables_for_scroll(html_body)
        try:
            glossary_terms = load_glossary()
            html_body = apply_glossary_tooltips(html_body, glossary_terms)
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    if has_latex_math:
        html_body = restore_latex_math(html_body, math_segments)
        html_body = render_latex_math(html_body)
    if include_web_chrome:
        html_body = insert_study_reading_key(html_body)

    toolbar = (
        _study_toolbar_html(input_path, title=title)
        if include_web_chrome
        else ""
    )
    mermaid_loader = _mermaid_loader_html(html_body) if include_web_chrome else ""
    reader_css, section_nav_js = reader_assets(input_path) if include_web_chrome else ("", "")
    reading_tools = reader_controls() if include_web_chrome else ""
    term_tip_js = _term_tip_js() if include_web_chrome else ""
    screen_dark_css = _study_screen_dark_css() if include_web_chrome else ""
    theme_bootstrap = reader_bootstrap() if include_web_chrome else ""
    katex_css = _load_katex_css() if has_latex_math else ""

    kd_document_css = ""
    kd_print_css = ""
    page_margin = "2.2cm 2cm 2.2cm 2cm"
    if input_path.name == "KD-Karm-Darshan-English.md":
        page_margin = "1.6cm 1.5cm 1.6cm 1.5cm"
        kd_document_css = """
  .kd-chapter-heading {
    margin: 20pt 0 14pt 0;
    text-align: center;
    page-break-after: avoid;
    break-after: avoid;
  }
  .kd-chapter-heading .kd-chapter-label {
    margin: 0;
    font-size: 17pt;
    line-height: 1.15;
    font-weight: 700;
    text-align: center;
  }
  .kd-chapter-heading .kd-chapter-title {
    margin: 6pt 0 0 0;
    font-size: 23pt;
    line-height: 1.18;
    font-weight: 700;
    text-align: center;
  }
  .kd-chapter-heading + p {
    margin-top: 8pt;
  }
"""
        kd_print_css = """
    body { font-size: 10pt; line-height: 1.34; }
    h2 { margin: 8pt 0 4pt 0; }
    h3 { margin: 4pt 0 1pt 0; page-break-after: avoid; break-after: avoid; }
    h3 + p { margin: 1pt 0 2pt 0; }
    p { margin: 1pt 0; }
    ul, ol { margin: 1pt 0 3pt 0; padding-left: 16pt; }
    li { margin: 0; }
"""

    seo_head = ""
    if include_web_chrome:
        slug = input_path.parent.name
        description = _study_description(md_text, slug)
        canonical_url = _study_canonical_url(input_path)
        edited_at = parse_edited_on(md_text_raw)
        date_modified_iso = edited_at.isoformat() if edited_at else None
        seo_head = _study_seo_head_html(
            title=title,
            description=description,
            canonical_url=canonical_url,
            date_modified_iso=date_modified_iso,
            slug=input_path.stem,
        )

    web_chrome_css = ""
    if include_web_chrome:
        web_chrome_css = """
  html { scroll-behavior: smooth; }
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
  }
  .skip-link {
    position: absolute;
    left: -9999px;
    top: 0;
    z-index: 100;
    padding: 8px 14px;
    background: #1a5276;
    color: #fff;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    border-radius: 0 0 8px 0;
  }
  .skip-link:focus {
    left: 0;
    outline: 2px solid #13405c;
    outline-offset: 2px;
  }
  h2[id], h3[id], h4[id], main[id] {
    scroll-margin-top: calc(var(--study-toolbar-height, 88px) + 10px);
  }
  .table-scroll {
    overflow-x: auto;
    margin: 12pt 0;
    -webkit-overflow-scrolling: touch;
  }
  .table-scroll table {
    margin: 0;
  }
  .term-tip-wrap {
    position: relative;
    display: inline;
    white-space: normal;
  }
  .term-tip {
    background: none;
    border: none;
    border-bottom: 1px dotted #8a6d3b;
    padding: 0;
    margin: 0;
    font: inherit;
    color: inherit;
    cursor: help;
    text-align: inherit;
  }
  .term-tip:hover {
    background: #f6f0e7;
    border-radius: 2px;
  }
  .term-tip:focus-visible {
    outline: 2px solid #1a5276;
    outline-offset: 2px;
    border-bottom-color: transparent;
  }
  .term-tip-panel {
    display: none;
    position: fixed;
    z-index: 40;
    min-width: 220px;
    max-width: min(320px, 90vw);
    padding: 8px 10px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 12px;
    line-height: 1.45;
    font-style: normal;
    font-weight: 400;
    color: #2a241c;
    background: #fff;
    border: 1px solid #c5d9e6;
    border-radius: 8px;
    box-shadow: 0 4px 14px rgba(42, 36, 28, 0.12);
    text-align: left;
    pointer-events: none;
  }
  .term-tip-panel.is-visible {
    display: block;
  }
  .study-toolbar {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    position: sticky;
    top: 0;
    z-index: 20;
    margin: 0 0 18px;
    padding: 6px 10px;
    border: 1px solid #d8d2c8;
    border-radius: 8px;
    background: rgba(247, 244, 239, 0.92);
    -webkit-backdrop-filter: blur(8px);
    backdrop-filter: blur(8px);
  }
  .study-toolbar-row {
    display: grid;
    align-items: center;
    gap: 10px;
  }
  .study-toolbar-row--primary {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .study-toolbar-actions {
    grid-column: 2;
    justify-self: end;
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    min-width: 0;
    white-space: nowrap;
    text-align: right;
  }
  .study-toolbar-feedback {
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
  }
  .study-toolbar-row--sections {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
  .study-toolbar-back {
    grid-column: 1;
    justify-self: start;
    min-width: 0;
  }
  .study-toolbar-download {
    min-width: 0;
    text-align: right;
  }
  .study-toolbar-link {
    color: #1a5276;
    text-decoration: none;
    font-weight: 600;
  }
  .study-toolbar-link:hover { color: #13405c; }
  .study-toolbar-link:focus-visible {
    outline: 2px solid #1a5276;
    outline-offset: 2px;
  }
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
  .study-theme-toggle {
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #1a5276;
    background: #fdfcfa;
    border: 1px solid #d9d2c7;
    border-radius: 999px;
    padding: 2px 8px;
    cursor: pointer;
    white-space: nowrap;
  }
  .study-theme-toggle:hover { border-color: #1a5276; }
  .study-theme-toggle:focus-visible {
    outline: 2px solid #1a5276;
    outline-offset: 2px;
  }

  /* Contents ---------------------------------------------------------------
     Studies run past 30,000 words, so the sequential previous/next pair is not
     enough to move around one. Closed by default so small screens never pay
     for its height; a parser-blocking script inside the element opens it
     where there is room, before the reading key is parsed. */
  .study-toc {
    max-width: 37rem;
    margin: 1.6em 0 2.2em;
    border: 1px solid #ddd6cc;
    border-radius: 10px;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }
  .study-toc-summary {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 10px 15px;
    cursor: pointer;
    list-style: none;
  }
  .study-toc-summary::-webkit-details-marker { display: none; }
  .study-toc-summary::before {
    content: "";
    flex: 0 0 auto;
    width: 6px;
    height: 6px;
    border-right: 1.5px solid currentColor;
    border-bottom: 1.5px solid currentColor;
    transform: rotate(-45deg);
    transition: transform 0.15s ease;
  }
  .study-toc[open] > .study-toc-summary::before { transform: rotate(45deg); }
  .study-toc-summary:hover { background: #faf7f2; }
  .study-toc-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #2c241c;
  }
  .study-toc-meta { font-size: 12px; color: #6b6357; }
  .study-toc-nav {
    max-height: 58vh;
    overflow-y: auto;
    padding: 2px 15px 13px;
  }
  .study-toc-list { list-style: none; margin: 0; padding: 0; }
  .study-toc-item { margin: 0; }
  .study-toc-item > a {
    display: block;
    padding: 3px 0;
    font-size: 13.5px;
    line-height: 1.35;
    color: #1a5276;
    text-decoration: none;
  }
  .study-toc-item > a:hover { text-decoration: underline; }
  .study-toc-l1 { margin-top: 9px; }
  .study-toc-l1:first-child { margin-top: 0; }
  .study-toc-l1 > a { font-weight: 700; color: #2c241c; }
  .study-toc-l2 > a { padding-left: 15px; }
  .study-toc-l3 > a { padding-left: 30px; font-size: 12.5px; color: #4d6f86; }
  .study-toc--with-key { margin-bottom: 0.55em; }
  .study-reading-key {
    margin: 0 0 2.2em;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 12px;
    line-height: 1.45;
    color: #6b6357;
  }
  .study-reading-key > span[aria-hidden="true"] { padding: 0 5px; }
  .study-reading-key-term {
    color: #2c241c;
    border-bottom: 1px dotted #8a6d3b;
  }
  .study-reading-key-link {
    color: #1a5276;
    text-decoration: underline;
  }
  @media (prefers-reduced-motion: reduce) {
    .study-toc-summary::before { transition: none; }
  }

  /* Reading measure --------------------------------------------------------
     The PDF is rendered from this same HTML, so anything that governs reading
     on screen is confined to @media screen. The bare rules and the @media
     print block above remain the print baseline and are left alone. */
  @media screen {
    html { color-scheme: light; }
    html[data-theme="dark"] { color-scheme: dark; }
    @media (prefers-color-scheme: dark) {
      html:not([data-theme]) { color-scheme: dark; }
    }
    body {
      background: #fff;
      overflow-wrap: anywhere;
      font-size: 17px;
      line-height: 1.62;
      max-width: 46rem;
      margin: 32px auto 88px;
      padding: 0 22px;
    }
    /* Add a subtle one point of breathing room above and below quotations on
       screen without changing the print/PDF layout. */
    blockquote {
      margin-top: 11pt;
      margin-bottom: 11pt;
    }
    /* Running text uses the full reading column. Tables and figures share the
       same 46rem container, so paragraphs no longer collapse into a visibly
       narrower strip inside the page. */
    p {
      margin: 0.72em 0;
      text-align: left;
      hyphens: auto;
    }
    h1 { font-size: 2.05rem; line-height: 1.16; }
    h2 { font-size: 1.5rem; margin-top: 2.3em; }
    h3 { font-size: 1.18rem; margin-top: 1.85em; }
    /* "1.2.1" is a sub-subsection but has to stay an h3 for the PDF outline,
       so the distinction from "1.2" is carried here. */
    h3[data-depth="3"] {
      font-size: 1.0rem;
      font-weight: 600;
      margin-top: 1.45em;
    }
    h4 { font-size: 1.0rem; }
    /* Long inline formulae need their own scroll region, just like display
       equations and tables; they must not widen the whole reading page. */
    .katex { display: inline-block; max-width: 100%; overflow-x: auto; vertical-align: middle; }
    .katex-display > .katex { display: block; overflow: visible; }

  }
  @media screen and (min-width: 760px) {
    .study-toc { max-width: 46rem; }
  }

  @media (max-width: 640px) {
    .study-toolbar-row--primary { grid-template-columns: minmax(0, 1fr); gap: 0; }
    .study-toolbar-actions {
      grid-column: 1;
      justify-self: stretch;
      justify-content: space-between;
      gap: 5px;
    }
    .study-toolbar-link, .study-theme-toggle { min-height: 44px; display: inline-flex; align-items: center; box-sizing: border-box; }
    .study-toolbar-section { display: block; line-height: 44px; }
    .study-toolbar-feedback { font-size: 11px; }
    .study-toolbar-section { font-size: 11px; }
    .study-toc-nav { max-height: 52vh; }
  }
  @media print {
    .reader-chrome { display: none !important; }
    .study-toolbar { display: none !important; }
    .study-theme-toggle { display: none !important; }
    .study-toc { display: none !important; }
    .study-reading-key { display: none !important; }
    .skip-link { display: none !important; }
    .term-tip {
      border-bottom: none;
      color: inherit;
      cursor: text;
    }
    .term-tip-panel { display: none !important; }
  }
"""

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta name="color-scheme" content="light dark"/>
<title>{html_module.escape(title)}</title>
{favicon_link_tags()}{seo_head}
{theme_bootstrap}<style>
  @page {{
    size: A4;
    margin: {page_margin};
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
{kd_print_css}    .page-marker {{
      page-break-before: always;
      break-before: page;
      visibility: hidden;
      height: 0;
      margin: 0;
      padding: 0;
      border: none;
    }}
    .blank-page {{
      page-break-before: always;
      break-before: page;
      min-height: 1px;
      margin: 0;
      padding: 0;
    }}
    .blank-page-label {{
      visibility: hidden;
      height: 0;
      margin: 0;
      padding: 0;
      border: none;
      display: block;
    }}
  }}
  .page-marker {{
    display: block;
    font-family: Georgia, serif;
    font-size: 9pt;
    color: #888;
    margin: 24pt 0 12pt 0;
    border-top: 1px dashed #ddd;
    padding-top: 6pt;
    text-align: right;
  }}
  body {{
    position: relative;
    z-index: 1;
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    /* Never fake an italic for a font that has no italic face. Georgia, Times
       and Consolas all ship true italics, so Latin text is unaffected. Scripts
       with no italic tradition -- Devanagari via Nirmala UI, in the Hindi
       transcripts under References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/
       -- would otherwise be slanted synthetically inside blockquotes, which
       distorts matras and makes editorial [brackets] read as vowel marks. */
    font-synthesis-style: none;
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
{kd_document_css}
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
  .katex-display {{
    margin: 8pt 0;
    overflow-x: auto;
    overflow-y: hidden;
  }}
{katex_css}{web_chrome_css}{screen_dark_css}
</style>
{reader_css}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{toolbar}{reading_tools}<main id="main">{html_body}</main>
{mermaid_loader}{section_nav_js}{term_tip_js}
</body>
</html>"""

    write_text_lf(output_path, full_html)
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

    from _study_catalog import StudyStatus, parse_status_md

    md_text = input_path.read_text(encoding="utf-8")
    status = parse_status_md(md_text)
    if status == StudyStatus.ONGOING:
        print(f"Skipping ongoing study (no HTML): {input_path}", file=sys.stderr)
        raise SystemExit(1)

    output_path = convert_to_html(
        input_path,
        is_draft=status == StudyStatus.DRAFT,
        include_web_chrome=True,
    )
    print(f"HTML written to: {output_path}")


if __name__ == "__main__":
    main()
