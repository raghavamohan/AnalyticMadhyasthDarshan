"""Tests for the markdown-to-HTML converter's output correctness.

LaTeX math survival, plus the two other places the converter can silently
corrupt what it emits: line endings, and local links rewritten for the site.

Everything here fails only when the *converter* is wrong. Assertions about how
the reader is styled — column width, spacing, toolbar structure, reading-key
copy — live in `_test_study_html_layout.py`, because those fail whenever the
design changes, including deliberately, and need a different judgement call
when they do.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import markdown

from _common import BASE, site_base_url
from _convert_to_pdf import (
    convert_to_html,
    protect_latex_math_in_markdown,
    restore_latex_math,
    rewrite_local_links_for_site,
)


def _round_trip(md_text: str) -> str:
    protected, segments = protect_latex_math_in_markdown(md_text)
    html = markdown.markdown(protected, extensions=["tables", "fenced_code", "smarty"])
    return restore_latex_math(html, segments)


def test_set_braces_survive() -> None:
    html = _round_trip(r"Let $\mathcal{F}=\{a,b,c\}$ be the faculties.")
    assert r"\{a,b,c\}" in html, html


def test_asterisks_and_underscores_survive() -> None:
    html = _round_trip(r"$$\operatorname{Sh}(C^*_{MD},J^*) \simeq \mathcal{W}(T_{MD})$$")
    assert "<em>" not in html, html
    assert r"C^*_{MD},J^*" in html, html


def test_display_math_becomes_its_own_paragraph() -> None:
    html = _round_trip("Before.\n\n$$\nx\\in\\{\\top,\\bot\\}\n$$\n\nAfter.")
    assert "<p>$$\nx\\in\\{\\top,\\bot\\}\n$$</p>" in html, html


def test_dollars_in_code_are_not_math() -> None:
    md_text = "Run `$env:PATH` then `$LASTEXITCODE`, and note $x\\_1$ is math."
    html = _round_trip(md_text)
    assert "<code>$env:PATH</code>" in html, html
    assert "<code>$LASTEXITCODE</code>" in html, html
    assert r"$x\_1$" in html, html


def test_generated_html_uses_lf_line_endings() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_bytes(b"# Title\r\n\r\nParagraph.\r\n")
        html_path = convert_to_html(md_path)
        assert b"\r\n" not in html_path.read_bytes()


def test_study_folder_md_companion_rewrites_to_site_html() -> None:
    html_path = (
        BASE
        / "Studies"
        / "The-Ontology-of-Coexistence"
        / "The-Ontology-of-Coexistence.html"
    )
    body = (
        '<p><a href="Technical-Note-Roop-Guna-Svabhava-Dharma.md">'
        "tetrad note</a></p>"
    )
    rewritten = rewrite_local_links_for_site(body, html_path)
    expected = (
        f"{site_base_url().rstrip('/')}/Studies/The-Ontology-of-Coexistence/"
        "Technical-Note-Roop-Guna-Svabhava-Dharma.html"
    )
    assert expected in rewritten, rewritten


def main() -> int:
    tests = [
        test_set_braces_survive,
        test_asterisks_and_underscores_survive,
        test_display_math_becomes_its_own_paragraph,
        test_dollars_in_code_are_not_math,
        test_generated_html_uses_lf_line_endings,
        test_study_folder_md_companion_rewrites_to_site_html,
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
