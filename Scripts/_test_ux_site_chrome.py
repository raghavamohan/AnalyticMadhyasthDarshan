"""UX contracts for shared theme chrome, catalog search, and the study toolbar."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _convert_to_pdf import convert_to_html, _term_tip_js
from _site_chrome import THEME_BOOTSTRAP_SCRIPT, site_home_and_tools
from _build_discussion_pages import DISCUSS_CSS
from _study_search import search_page
from _build_studies_index import INDEX_TEMPLATE


def test_shared_pages_bootstrap_and_toggle_theme() -> None:
    chrome = site_home_and_tools(home_href="index.html", studies_prefix="", current="notebook")
    assert 'id="theme-toggle"' in chrome
    assert "localStorage.setItem(\"amd-theme\"" in chrome
    assert "amd-theme" in THEME_BOOTSTRAP_SCRIPT
    page = search_page("test")
    assert THEME_BOOTSTRAP_SCRIPT in page
    assert 'id="theme-toggle"' in page


def test_discussion_css_follows_saved_theme() -> None:
    assert 'html[data-theme="dark"] .discuss-toolbar' in DISCUSS_CSS
    assert "html:not([data-theme]) .discuss-toolbar" in DISCUSS_CSS
    assert DISCUSS_CSS.index('html[data-theme="dark"] .discuss-toolbar') < DISCUSS_CSS.index(
        "html:not([data-theme]) .discuss-toolbar"
    )


def test_catalog_bridges_passage_search_and_related_chips() -> None:
    assert 'id="search-passage-hint"' in INDEX_TEMPLATE
    assert "Passage Search" in INDEX_TEMPLATE
    assert "path-related-chips" in INDEX_TEMPLATE
    assert "About these related studies" in INDEX_TEMPLATE
    assert "scrollIntoView" in INDEX_TEMPLATE
    assert "prefers-reduced-motion" in INDEX_TEMPLATE


def test_reader_toolbar_exposes_progress_offline_and_glossary_sheet() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text("# Title\n\nParagraph.\n", encoding="utf-8")
        html = convert_to_html(
            md_path, include_web_chrome=True, update_search=False
        ).read_text(encoding="utf-8")
    assert 'id="reader-progress"' in html
    assert 'id="reader-offline"' in html
    assert "term-tip-backdrop" in _term_tip_js()
    assert "is-sheet" in _term_tip_js()
    assert "pointer-events: auto" in html


def test_submit_portal_does_not_wrap_nav_in_a_paragraph() -> None:
    portal = (BASE / "Studies/submit.html").read_text(encoding="utf-8")
    assert '<div class="back-link" id="hub-back-link">' in portal
    assert '<p class="back-link" id="hub-back-link">' not in portal
    assert 'id="auth-kind-note"' in portal


def main() -> int:
    tests = [
        test_shared_pages_bootstrap_and_toggle_theme,
        test_discussion_css_follows_saved_theme,
        test_catalog_bridges_passage_search_and_related_chips,
        test_reader_toolbar_exposes_progress_offline_and_glossary_sheet,
        test_submit_portal_does_not_wrap_nav_in_a_paragraph,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
