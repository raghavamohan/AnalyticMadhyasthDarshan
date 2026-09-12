"""Tests for the shared Theme icon helper."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _theme_icons import (
    IDENTITY_NAMES,
    SPRITE_HREF,
    comments_loading_html,
    fill_theme_placeholders,
    load_study_visuals,
    study_icon_map,
    topic_icon_html,
    ui_icon_html,
    verify_study_visuals_assignments,
    wait_inner_html,
)


def test_study_visuals_cover_the_catalog() -> None:
    assert verify_study_visuals_assignments() == []
    mapped = study_icon_map()
    assert mapped["The-Ontology-of-Coexistence"] == "coexistence"
    assert mapped["Why-Humans-Are-Not-Just-Material"] == "jeevan"
    assert mapped["How-Undivided-Society-Is-Established"] == "akhand-samaj"
    assert set(mapped) == set(load_study_visuals())


def test_ui_icons_use_the_theme_sprite() -> None:
    html = ui_icon_html("download")
    assert SPRITE_HREF in html
    assert "#download" in html
    assert 'aria-hidden="true"' in html
    assert "amd-icon" in html


def test_topic_icons_follow_page_theme_variables() -> None:
    topic = topic_icon_html("resolution")
    identity = topic_icon_html("jeevan")
    assert "amd-topic-icon" in topic
    assert "amd-mark" in identity
    assert 'style="' not in topic
    assert 'style="' not in identity
    assert 'aria-hidden="true"' in topic
    assert "faculty" in identity
    assert IDENTITY_NAMES == {"jeevan", "akhand-samaj"}


def test_waiters_keep_identity_motion_hooks() -> None:
    wait = wait_inner_html("akhand-samaj", "Loading comments&hellip;")
    assert "amd-wait" in wait
    assert "goal" in wait
    assert "Loading comments" in wait
    loading = comments_loading_html()
    assert 'class="comments-loading"' in loading
    assert "amd-wait" in loading


def test_placeholder_fill_keeps_labels() -> None:
    filled = fill_theme_placeholders(
        '<a>@amd-ui:search@Search</a><span>@amd-stage:jeevan@</span>'
    )
    assert "@amd-ui:search@" not in filled
    assert "#search" in filled
    assert "amd-stage-mark" in filled
    assert "Search" in filled


def main() -> int:
    tests = [
        test_study_visuals_cover_the_catalog,
        test_ui_icons_use_the_theme_sprite,
        test_topic_icons_follow_page_theme_variables,
        test_waiters_keep_identity_motion_hooks,
        test_placeholder_fill_keeps_labels,
    ]
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            test()
            print(f"PASS {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
