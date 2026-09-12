"""Shared Theme icon markup for website chrome.

Assignment source: Assets/Theme/study-visuals.json. Do not add icon fields to
catalog-*.json; the index verifier requires the catalog island to match those
files exactly.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from _common import BASE

THEME_DIR = BASE / "Assets" / "Theme"
THEME_ICONS = THEME_DIR / "icons"
STUDY_VISUALS_PATH = THEME_DIR / "study-visuals.json"
SPRITE_HREF = "/Assets/Theme/icons/sprite.svg"

IDENTITY_NAMES = frozenset({"jeevan", "akhand-samaj"})
UI_ICON_NAMES = frozenset(
    {
        "search",
        "download",
        "slides",
        "discussion",
        "audio",
        "pause",
        "close",
        "menu",
        "external",
        "saved",
        "moon",
        "sun",
        "notes",
        "learning",
    }
)

STUDY_VISUALS_PLACEHOLDER = "@study-visuals@"
THEME_ICON_HTML_PLACEHOLDER = "@theme-icon-html@"
THEME_MOTION_CSS_PLACEHOLDER = "@theme-motion-css@"
PDF_DOWNLOAD_ICON_PLACEHOLDER = "@pdf-download-icon-json@"
PRESENTATION_ICON_PLACEHOLDER = "@presentation-icon-json@"
DISCUSSION_ICON_PLACEHOLDER = "@discussion-icon-json@"

_PLACEHOLDER_RE = re.compile(r"@amd-(ui|topic|mark|stage):([a-z0-9-]+)@")
_OPEN_SVG_RE = re.compile(r"<svg\b([^>]*)>")
_STYLE_ATTR_RE = re.compile(r'\sstyle="[^"]*"')
_CLASS_ATTR_RE = re.compile(r'\sclass="[^"]*"')
_ROLE_ATTR_RE = re.compile(r'\srole="[^"]*"')
_LABEL_ATTR_RE = re.compile(r'\saria-label="[^"]*"')

# The approved token sheet owns palette and motion; website geometry lives here.
THEME_MOTION_CSS = (THEME_DIR / "tokens.css").read_text(encoding="utf-8") + """
  .amd-icon { width: 20px; height: 20px; display: block; }
  .amd-topic-icon, .amd-mark { width: 40px; height: 40px; flex: 0 0 auto; display: block; }
  .amd-stage-mark { width: 24px; height: 24px; flex: 0 0 auto; display: block; }
  .amd-home { display: inline-flex; align-items: center; gap: 8px; color: inherit; }
  .amd-home .amd-mark { width: 32px; height: 32px; }
  .amd-action { display: inline-flex; align-items: center; gap: 6px; }
  .amd-action .amd-icon { width: 18px; height: 18px; }
"""



def json_for_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


@lru_cache(maxsize=1)
def topic_icon_names() -> frozenset[str]:
    names = set()
    for path in THEME_ICONS.glob("*-light.svg"):
        name = path.name.removesuffix("-light.svg")
        if name not in IDENTITY_NAMES:
            names.add(name)
    return frozenset(names)


def card_icon_names() -> frozenset[str]:
    return topic_icon_names() | IDENTITY_NAMES


@lru_cache(maxsize=1)
def load_study_visuals() -> dict[str, dict[str, str]]:
    data = json.loads(STUDY_VISUALS_PATH.read_text(encoding="utf-8"))
    studies = data.get("studies")
    if not isinstance(studies, list):
        raise ValueError(f"{STUDY_VISUALS_PATH.name}: missing studies array")
    by_slug: dict[str, dict[str, str]] = {}
    for row in studies:
        if not isinstance(row, dict) or not row.get("slug") or not row.get("icon"):
            raise ValueError(f"{STUDY_VISUALS_PATH.name}: each study needs slug and icon")
        slug = str(row["slug"])
        if slug in by_slug:
            raise ValueError(f"{STUDY_VISUALS_PATH.name}: duplicate slug {slug}")
        by_slug[slug] = {
            "icon": str(row["icon"]),
            "theme": str(row.get("theme") or ""),
            "illustration": str(row.get("illustration") or ""),
        }
    return by_slug


def study_icon_map() -> dict[str, str]:
    return {slug: row["icon"] for slug, row in load_study_visuals().items()}


def study_icon_name(slug: str) -> str:
    row = load_study_visuals().get(slug)
    return row["icon"] if row else ""


def serialize_study_visuals_json() -> str:
    return json_for_script(study_icon_map())


def serialize_theme_icon_html_js() -> str:
    return json_for_script({name: topic_icon_html(name) for name in sorted(card_icon_names())})


def ui_icon_html(name: str) -> str:
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError(f"invalid icon name: {name}")
    return (
        f'<svg class="amd-icon" aria-hidden="true" focusable="false">'
        f'<use href="{SPRITE_HREF}#{name}"></use></svg>'
    )


def topic_icon_html(name: str) -> str:
    if name in IDENTITY_NAMES:
        return _identity_svg(name, css_class="amd-mark")
    return _topic_svg(name, css_class="amd-topic-icon")


def identity_mark_html(name: str) -> str:
    return _identity_svg(name, css_class="amd-mark")


def stage_icon_html(name: str) -> str:
    if name in IDENTITY_NAMES:
        return _identity_svg(name, css_class="amd-stage-mark")
    return _topic_svg(name, css_class="amd-stage-mark")


def wait_inner_html(name: str, label: str) -> str:
    if name not in IDENTITY_NAMES:
        raise ValueError(f"waiting marks are identity-only: {name}")
    svg = _identity_svg(name, css_class="")
    return (
        f'<span class="amd-wait">{svg}'
        f'<span class="amd-wait-label">{label}</span></span>'
    )


def comments_loading_html() -> str:
    return (
        '<li class="comments-loading">'
        f'{wait_inner_html("akhand-samaj", "Loading comments&hellip;")}'
        "</li>"
    )


def search_wait_html() -> str:
    svg = _identity_svg("jeevan", css_class="")
    return f'<span class="amd-wait" id="search-wait" hidden>{svg}</span>'


def fill_theme_placeholders(html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        kind, name = match.groups()
        if kind == "ui":
            return ui_icon_html(name)
        if kind == "topic":
            return topic_icon_html(name)
        if kind == "mark":
            return identity_mark_html(name)
        return stage_icon_html(name)

    html = _PLACEHOLDER_RE.sub(replace, html)
    html = html.replace(THEME_MOTION_CSS_PLACEHOLDER, THEME_MOTION_CSS)
    html = html.replace(THEME_ICON_HTML_PLACEHOLDER, serialize_theme_icon_html_js())
    html = html.replace(PDF_DOWNLOAD_ICON_PLACEHOLDER, json_for_script(ui_icon_html("download")))
    html = html.replace(PRESENTATION_ICON_PLACEHOLDER, json_for_script(ui_icon_html("slides")))
    html = html.replace(DISCUSSION_ICON_PLACEHOLDER, json_for_script(ui_icon_html("discussion")))
    return html


def verify_study_visuals_assignments() -> list[str]:
    errors: list[str] = []
    try:
        visuals = load_study_visuals()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"Assets/Theme/study-visuals.json: {exc}"]

    allowed = card_icon_names()
    catalog = _catalog_slugs()
    for slug in sorted(catalog - visuals.keys()):
        errors.append(
            f"Assets/Theme/study-visuals.json: missing assignment for catalog slug {slug}."
        )
    for slug in sorted(visuals.keys() - catalog):
        errors.append(
            f"Assets/Theme/study-visuals.json: {slug} is not in the study catalog."
        )
    for slug, row in visuals.items():
        icon = row["icon"]
        if icon not in allowed:
            errors.append(
                f"Assets/Theme/study-visuals.json: {slug} uses unknown icon {icon!r}."
            )
    return errors


def verify_study_visuals_sync() -> list[str]:
    return verify_study_visuals_assignments() + verify_study_visuals_index_sync()


def verify_study_visuals_index_sync() -> list[str]:
    index_path = BASE / "Studies" / "index.html"
    if not index_path.is_file():
        return []
    match = re.search(
        r"const STUDY_VISUALS = (\{.*?\});",
        index_path.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    if match is None:
        return ["Studies/index.html: STUDY_VISUALS map is missing."]
    try:
        actual = json.loads(match.group(1).replace("<\\/", "</"))
    except json.JSONDecodeError:
        return ["Studies/index.html: STUDY_VISUALS map is not valid JSON."]
    if actual != study_icon_map():
        return [
            "Studies/index.html: STUDY_VISUALS does not match "
            "Assets/Theme/study-visuals.json. Run python Scripts/_build_studies_index.py."
        ]
    return []


def _catalog_slugs() -> set[str]:
    from _study_catalog import CATALOG_TABLES, load_catalog_rows

    slugs: set[str] = set()
    for table in CATALOG_TABLES:
        for row in load_catalog_rows(table):
            slugs.add(row.slug)
    return slugs


@lru_cache(maxsize=64)
def _read_svg(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()


def _topic_svg(name: str, *, css_class: str) -> str:
    if name not in topic_icon_names():
        raise ValueError(f"unknown topic icon: {name}")
    return _prepare_svg(_read_svg(THEME_ICONS / f"{name}-light.svg"), css_class=css_class)


def _identity_svg(name: str, *, css_class: str) -> str:
    if name not in IDENTITY_NAMES:
        raise ValueError(f"unknown identity mark: {name}")
    return _prepare_svg(_read_svg(THEME_ICONS / f"{name}-compact.svg"), css_class=css_class)


def _prepare_svg(raw: str, *, css_class: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        attrs = _STYLE_ATTR_RE.sub("", attrs)
        attrs = _CLASS_ATTR_RE.sub("", attrs)
        attrs = _ROLE_ATTR_RE.sub("", attrs)
        attrs = _LABEL_ATTR_RE.sub("", attrs)
        extra = ' aria-hidden="true" focusable="false"'
        if css_class:
            extra = f' class="{css_class}"{extra}'
        return f"<svg{attrs}{extra}>"

    prepared, count = _OPEN_SVG_RE.subn(repl, raw.strip(), count=1)
    if count != 1:
        raise ValueError("Theme SVG is missing a root <svg> tag")
    return prepared
