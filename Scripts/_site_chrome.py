"""Shared catalog chrome: feed discovery links and Search / Notes / Submissions."""
from __future__ import annotations

from html import escape

from _theme_icons import identity_mark_html, ui_icon_html

SITE_TOOL_ITEMS = (
    (
        "search",
        "search.html",
        "Search",
        "Find words and phrases inside studies and companion notes.",
        "search",
    ),
    (
        "notebook",
        "notebook.html",
        "My Notes",
        "Open your highlights, notes and offline studies saved in this browser.",
        "notes",
    ),
    (
        "submit",
        "submit.html",
        "My Submissions",
        "Use GitHub sign-in to propose studies, submit drafts and follow reviews.",
        "",
    ),
)

SITE_CHROME_CSS = """
.site-chrome-nav { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px 16px; margin:0 0 18px; }
.site-chrome-tools { display:flex; flex-wrap:wrap; align-items:center; gap:4px 14px; }
.site-chrome-link { display:inline-flex; align-items:center; gap:6px; color:inherit; text-decoration:none; font-weight:600; font-size:14px; min-height:44px; }
.site-chrome-link .amd-icon { width:18px; height:18px; }
.site-chrome-link[aria-current="page"] { text-decoration:underline; text-underline-offset:3px; }
.site-chrome-nav .amd-home { display:inline-flex; align-items:center; gap:8px; color:inherit; text-decoration:none; font-weight:600; min-height:44px; }
.site-chrome-nav .amd-home .amd-mark { width:32px; height:32px; }
""".strip()


def site_feed_link_tags() -> str:
    return (
        '<link rel="alternate" type="application/feed+json" href="/Studies/feed.json" '
        'title="Studies change feed"/>\n'
        '<link rel="alternate" type="application/atom+xml" href="/Studies/atom.xml" '
        'title="Studies Atom feed"/>'
    )


def site_tool_links(*, studies_prefix: str, current: str = "") -> str:
    parts = []
    for key, href, label, tip, icon in SITE_TOOL_ITEMS:
        url = f"{studies_prefix}{href}"
        current_attr = ' aria-current="page"' if current == key else ""
        icon_html = ui_icon_html(icon) if icon else ""
        label_html = (
            f'<span class="nav-link-label">{escape(label)}</span>'
            if icon
            else escape(label)
        )
        extra_class = " site-chrome-text" if not icon else ""
        parts.append(
            f'<a class="site-chrome-link{extra_class}" href="{escape(url)}"{current_attr} '
            f'title="{escape(tip)}">{icon_html}{label_html}</a>'
        )
    return "".join(parts)


def site_home_and_tools(*, home_href: str, studies_prefix: str, current: str = "") -> str:
    return (
        '<nav class="site-chrome-nav" aria-label="Study navigation">'
        f'<a class="amd-home" href="{escape(home_href)}">'
        f'{identity_mark_html("akhand-samaj")}<span>All studies</span></a>'
        f'<div class="site-chrome-tools">{site_tool_links(studies_prefix=studies_prefix, current=current)}</div>'
        "</nav>"
    )
