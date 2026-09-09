"""Shared glossary registry and inline tooltip markup for study HTML."""
from __future__ import annotations

import html as html_module
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from _common import STUDIES

GLOSSARY_PATH = STUDIES / "glossary.json"

SKIP_TAGS = frozenset(
    {
        "a",
        "button",
        "code",
        "pre",
        "script",
        "style",
        "nav",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "h1",
        "h2",
        "h3",
        "h4",
        "blockquote",
    }
)
SKIP_CLASSES = frozenset(
    {
        "term-tip",
        "term-tip-float",
        "term-tip-panel",
        "study-toolbar",
        "skip-link",
        "mermaid",
        "study-reading-key",
        "katex",
        "katex-display",
    }
)
REFERENCES_HEADING_RE = re.compile(r"^(?:\d+\.\s*)?references$", re.IGNORECASE)
VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})
MAIN_RE = re.compile(
    r'(?P<open><main\b(?=[^>]*\bid="main")[^>]*>)'
    r'(?P<body>.*?)'
    r'(?P<close></main>)',
    re.IGNORECASE | re.DOTALL,
)
TOOLTIP_WRAPPER_RE = re.compile(
    r'<span\b(?=[^>]*\bclass="term-tip-wrap")[^>]*>'
    r'<button\b(?=[^>]*\bclass="term-tip")[^>]*>'
    r'(?P<text>[^<]*)</button></span>',
    re.IGNORECASE,
)


def load_glossary(path: Path | None = None) -> list[dict[str, object]]:
    glossary_path = path or GLOSSARY_PATH
    if not glossary_path.is_file():
        return []
    data = json.loads(glossary_path.read_text(encoding="utf-8"))
    terms = data.get("terms", [])
    if not isinstance(terms, list):
        raise ValueError(f"{glossary_path}: 'terms' must be a list")
    return terms


def _compile_patterns(terms: list[dict[str, object]]) -> list[tuple[re.Pattern[str], str, str]]:
    compiled: list[tuple[re.Pattern[str], str, str, int]] = []
    for entry in terms:
        term_id = str(entry.get("id", "")).strip()
        definition = str(entry.get("definition", "")).strip()
        matches = entry.get("match") or []
        if not term_id or not definition or not isinstance(matches, list):
            continue
        labels = [str(label).strip() for label in matches if str(label).strip()]
        if not labels:
            continue
        labels.sort(key=len, reverse=True)
        pattern = "|".join(re.escape(label) for label in labels)
        compiled.append(
            (
                re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE),
                term_id,
                definition,
                max(len(label) for label in labels),
            )
        )
    compiled.sort(key=lambda item: item[3], reverse=True)
    return [(pattern, term_id, definition) for pattern, term_id, definition, _ in compiled]


def _wrap_term(match: re.Match[str], term_id: str, definition: str) -> str:
    text = match.group(0)
    attr_def = (
        definition.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<span class="term-tip-wrap">'
        f'<button class="term-tip" data-definition="{attr_def}" '
        f'data-term="{term_id}" type="button">{text}</button>'
        f"</span>"
    )


def _apply_terms_to_text(
    text: str,
    patterns: list[tuple[re.Pattern[str], str, str]],
    seen_term_ids: set[str] | None = None,
) -> str:
    if not text.strip():
        return text

    seen = seen_term_ids if seen_term_ids is not None else set()
    placeholders: list[str] = []

    def repl(match: re.Match[str], term_id: str, definition: str) -> str:
        html = _wrap_term(match, term_id, definition)
        token = f"\x00GLOSS{len(placeholders)}\x00"
        placeholders.append(html)
        return token

    result = text
    for pattern, term_id, definition in patterns:
        if term_id in seen:
            continue

        matched = False

        def wrap_first(
            match: re.Match[str], i: str = term_id, d: str = definition
        ) -> str:
            nonlocal matched
            matched = True
            return repl(match, i, d)

        result = pattern.sub(
            wrap_first,
            result,
            count=1,
        )
        if matched:
            seen.add(term_id)
    for index, html in enumerate(placeholders):
        result = result.replace(f"\x00GLOSS{index}\x00", html)
    return result


class _GlossaryHTMLParser(HTMLParser):
    def __init__(self, patterns: list[tuple[re.Pattern[str], str, str]]) -> None:
        super().__init__(convert_charrefs=False)
        self.patterns = patterns
        self._skip_stack: list[tuple[str, bool]] = []
        self._seen_term_ids: set[str] = set()
        self._h2_text: list[str] | None = None
        self._tooltips_disabled = False
        self.parts: list[str] = []

    def _skip_active(self) -> bool:
        return any(skip for _tag, skip in self._skip_stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h2":
            self._seen_term_ids.clear()
            self._h2_text = []

        attr_map = {k: (v or "") for k, v in attrs}
        class_names = set(attr_map.get("class", "").split())
        skip = tag in SKIP_TAGS or bool(class_names.intersection(SKIP_CLASSES))
        if tag not in VOID_TAGS:
            self._skip_stack.append((tag, skip))

        # Preserve existing generated HTML byte-for-byte when refreshing only
        # tooltip wrappers. Reconstructing a tag from parsed attributes would
        # decode entities and reorder or normalize unrelated markup.
        self.parts.append(self.get_starttag_text() or f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")
        if tag == "h2" and self._h2_text is not None:
            heading = " ".join(
                html_module.unescape("".join(self._h2_text)).split()
            )
            self._tooltips_disabled = bool(REFERENCES_HEADING_RE.fullmatch(heading))
            self._h2_text = None
        if self._skip_stack and self._skip_stack[-1][0] == tag:
            self._skip_stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_data(self, data: str) -> None:
        if self._h2_text is not None:
            self._h2_text.append(data)
        if self._skip_active() or self._tooltips_disabled:
            self.parts.append(data)
        else:
            self.parts.append(
                _apply_terms_to_text(data, self.patterns, self._seen_term_ids)
            )

    def handle_entityref(self, name: str) -> None:
        if self._h2_text is not None:
            self._h2_text.append(f"&{name};")
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._h2_text is not None:
            self._h2_text.append(f"&#{name};")
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")


def apply_glossary_tooltips(html_body: str, terms: list[dict[str, object]]) -> str:
    patterns = _compile_patterns(terms)
    if not patterns:
        return html_body
    parser = _GlossaryHTMLParser(patterns)
    parser.feed(html_body)
    parser.close()
    return "".join(parser.parts)


def refresh_document_tooltips(
    document_html: str,
    terms: list[dict[str, object]],
) -> str:
    """Refresh shared glossary wrappers inside a generated study's main body.

    This deliberately leaves the rest of the generated reader untouched. It is
    therefore cheap enough for glossary-only changes and does not require the
    Node/KaTeX/Chrome PDF toolchain.
    """
    main = MAIN_RE.search(document_html)
    if main is None:
        return document_html
    refreshed = refresh_body_tooltips(main.group("body"), terms)
    return (
        document_html[:main.start()]
        + main.group("open")
        + refreshed
        + main.group("close")
        + document_html[main.end():]
    )


def refresh_body_tooltips(
    html_body: str,
    terms: list[dict[str, object]],
) -> str:
    """Remove generated tooltip wrappers and apply the current registry once."""
    unwrapped = TOOLTIP_WRAPPER_RE.sub(lambda match: match.group("text"), html_body)
    return apply_glossary_tooltips(unwrapped, terms)


def wrap_tables_for_scroll(html_body: str) -> str:
    return re.sub(
        r"<table(\s[^>]*)?>",
        r'<div class="table-scroll"><table\1>',
        html_body,
        flags=re.IGNORECASE,
    ).replace("</table>", "</table></div>")


def validate_glossary(path: Path | None = None) -> list[str]:
    glossary_path = path or GLOSSARY_PATH
    issues: list[str] = []
    terms = load_glossary(glossary_path)
    seen_ids: set[str] = set()
    for index, entry in enumerate(terms):
        if not isinstance(entry, dict):
            issues.append(f"term #{index + 1}: entry is not an object")
            continue
        term_id = str(entry.get("id", "")).strip()
        if not term_id:
            issues.append(f"term #{index + 1}: missing id")
            continue
        if term_id in seen_ids:
            issues.append(f"duplicate id: {term_id}")
        seen_ids.add(term_id)
        if not str(entry.get("definition", "")).strip():
            issues.append(f"{term_id}: missing definition")
        matches = entry.get("match")
        if not isinstance(matches, list) or not matches:
            issues.append(f"{term_id}: match must be a non-empty list")
    return issues
