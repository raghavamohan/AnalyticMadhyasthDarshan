"""Sanitize author content before adding trusted reader UI or rendered math.

Do not run this over the finished page: its scripts and KaTeX/SVG are generated
by the repository, whereas this boundary accepts contributor Markdown/HTML.
"""
from __future__ import annotations

import nh3

_CLEANER = nh3.Cleaner(
    tags={
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
        "ul", "ol", "li", "pre", "code", "em", "strong", "b", "i", "s",
        "del", "sub", "sup", "a", "img", "table", "thead", "tbody", "tfoot",
        "tr", "th", "td", "caption", "div", "span", "dl", "dt", "dd",
    },
    clean_content_tags={"script", "style", "iframe", "object", "embed", "svg", "math", "template"},
    attributes={
        "a": {"href", "title"},
        "img": {"src", "alt", "title", "width", "height"},
        "ol": {"start"},
        "td": {"colspan", "rowspan", "style"},
        "th": {"colspan", "rowspan", "scope", "style"},
    },
    # Fenced blocks are converted into trusted diagram containers afterwards.
    attribute_filter=lambda tag, attr, value: value if attr != "src" or not value.startswith("//") else None,
    allowed_classes={"code": {"language-mermaid", "language-text", "language-python", "language-json", "language-javascript", "language-bash"}},
    url_schemes={"http", "https", "mailto"},
    filter_style_properties={"text-align"},
    link_rel="noopener noreferrer",
)


def sanitize_author_html(fragment: str) -> str:
    return _CLEANER.clean(fragment)
