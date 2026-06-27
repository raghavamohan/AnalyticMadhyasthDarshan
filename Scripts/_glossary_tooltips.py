"""Shared glossary registry and inline tooltip markup for study HTML."""
from __future__ import annotations

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
    }
)
SKIP_CLASSES = frozenset({"term-tip", "term-tip-float", "term-tip-panel", "study-toolbar", "skip-link"})


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
        f'<button type="button" class="term-tip" data-term="{term_id}" '
        f'data-definition="{attr_def}">{text}</button>'
        f"</span>"
    )


def _apply_terms_to_text(text: str, patterns: list[tuple[re.Pattern[str], str, str]]) -> str:
    if not text.strip():
        return text

    placeholders: list[str] = []

    def repl(match: re.Match[str], term_id: str, definition: str) -> str:
        html = _wrap_term(match, term_id, definition)
        token = f"\x00GLOSS{len(placeholders)}\x00"
        placeholders.append(html)
        return token

    result = text
    for pattern, term_id, definition in patterns:
        result = pattern.sub(
            lambda m, i=term_id, d=definition: repl(m, i, d),
            result,
        )
    for index, html in enumerate(placeholders):
        result = result.replace(f"\x00GLOSS{index}\x00", html)
    return result


class _GlossaryHTMLParser(HTMLParser):
    def __init__(self, patterns: list[tuple[re.Pattern[str], str, str]]) -> None:
        super().__init__(convert_charrefs=False)
        self.patterns = patterns
        self._skip_stack: list[bool] = []
        self.parts: list[str] = []

    def _skip_active(self) -> bool:
        return any(self._skip_stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        class_names = set(attr_map.get("class", "").split())
        skip = tag in SKIP_TAGS or bool(class_names.intersection(SKIP_CLASSES))
        self._skip_stack.append(skip)

        attr_text = "".join(
            f' {name}="{attr_map[name].replace(chr(34), "&quot;")}"' for name in attr_map
        )
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")
        if self._skip_stack:
            self._skip_stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        class_names = set(attr_map.get("class", "").split())
        skip = tag in SKIP_TAGS or bool(class_names.intersection(SKIP_CLASSES))
        self._skip_stack.append(skip)
        attr_text = "".join(
            f' {name}="{attr_map[name].replace(chr(34), "&quot;")}"' for name in attr_map
        )
        self.parts.append(f"<{tag}{attr_text}/>")
        if self._skip_stack:
            self._skip_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_active():
            self.parts.append(data)
        else:
            self.parts.append(_apply_terms_to_text(data, self.patterns))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")


def apply_glossary_tooltips(html_body: str, terms: list[dict[str, object]]) -> str:
    patterns = _compile_patterns(terms)
    if not patterns:
        return html_body
    parser = _GlossaryHTMLParser(patterns)
    parser.feed(html_body)
    parser.close()
    return "".join(parser.parts)


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
