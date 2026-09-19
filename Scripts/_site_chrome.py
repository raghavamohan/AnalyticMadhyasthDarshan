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
        "work",
    ),
)

THEME_BOOTSTRAP_SCRIPT = """<script>
(function(){try{var t=localStorage.getItem("amd-theme");if(t!=="light"&&t!=="dark"){t=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}document.documentElement.setAttribute("data-theme",t);}catch(e){document.documentElement.setAttribute("data-theme","light");}})();
</script>"""

THEME_TOGGLE_SCRIPT = """<script>
(function(){
  var root=document.documentElement;
  var btn=document.getElementById("theme-toggle");
  if(!btn)return;
  var system=window.matchMedia("(prefers-color-scheme: dark)");
  function active(){
    var t=root.getAttribute("data-theme");
    if(t==="dark")return "dark";
    if(t==="light"||t==="sepia")return "light";
    return system.matches?"dark":"light";
  }
  function paint(){
    var next=active()==="dark"?"Light":"Dark";
    var label=document.getElementById("theme-toggle-label");
    if(label)label.textContent=next;
    btn.setAttribute("aria-label","Switch to "+next.toLowerCase()+" theme");
  }
  btn.addEventListener("click",function(){
    var next=active()==="dark"?"light":"dark";
    root.setAttribute("data-theme",next);
    try{localStorage.setItem("amd-theme",next);}catch(e){}
    paint();
  });
  if(system.addEventListener)system.addEventListener("change",paint);
  paint();
})();
</script>"""

SITE_CHROME_CSS = """
.site-chrome-nav { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px 16px; margin:0 0 18px; }
.site-chrome-tools { display:flex; flex-wrap:wrap; align-items:center; gap:4px 14px; }
.site-chrome-link { display:inline-flex; align-items:center; gap:6px; color:inherit; text-decoration:none; font-weight:600; font-size:14px; min-height:44px; }
.site-chrome-link .amd-icon { width:18px; height:18px; }
.site-chrome-link[aria-current="page"] { text-decoration:underline; text-underline-offset:3px; }
.site-chrome-nav .amd-home { display:inline-flex; align-items:center; gap:8px; color:inherit; text-decoration:none; font-weight:600; min-height:44px; }
.site-chrome-nav .amd-home .amd-mark { width:32px; height:32px; }
.site-chrome-tools .theme-toggle {
  flex: 0 0 auto;
  font: 600 13px/1 inherit;
  color: inherit;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 999px;
  padding: 0 10px;
  cursor: pointer;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}
.site-chrome-tools .theme-toggle:hover { opacity: 0.85; }
.site-chrome-tools .theme-toggle:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.theme-toggle .amd-icon { width: 18px; height: 18px; }
.theme-toggle-icon { display: inline-flex; align-items: center; }
.theme-icon-sun { display: none; }
[data-theme="dark"] .theme-icon-sun { display: inline-flex; }
[data-theme="dark"] .theme-icon-moon { display: none; }
@media (prefers-color-scheme: dark) {
  html:not([data-theme]) .theme-icon-sun { display: inline-flex; }
  html:not([data-theme]) .theme-icon-moon { display: none; }
}
#theme-toggle-label { display: inline-block; min-width: 2.75em; text-align: left; }
@media (max-width: 640px) {
  #theme-toggle-label { display: none; }
  .site-chrome-tools .theme-toggle { min-width: 36px; padding: 0 8px; }
}
""".strip()


def site_feed_link_tags() -> str:
    return (
        '<link rel="alternate" type="application/feed+json" href="/Studies/feed.json" '
        'title="Studies change feed"/>\n'
        '<link rel="alternate" type="application/atom+xml" href="/Studies/atom.xml" '
        'title="Studies Atom feed"/>'
    )


def theme_toggle_html() -> str:
    return (
        '<button type="button" class="theme-toggle" id="theme-toggle" aria-label="Switch color theme">'
        '<span class="theme-toggle-icon" aria-hidden="true">'
        f'<span class="theme-icon-moon">{ui_icon_html("moon")}</span>'
        f'<span class="theme-icon-sun">{ui_icon_html("sun")}</span>'
        "</span>"
        '<span id="theme-toggle-label">Dark</span></button>'
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
    tools = site_tool_links(studies_prefix=studies_prefix, current=current) + theme_toggle_html()
    return (
        '<nav class="site-chrome-nav" aria-label="Study navigation">'
        f'<a class="amd-home" href="{escape(home_href)}">'
        f'{identity_mark_html("akhand-samaj")}<span>All studies</span></a>'
        f'<div class="site-chrome-tools">{tools}</div>'
        "</nav>"
        + THEME_TOGGLE_SCRIPT
    )
