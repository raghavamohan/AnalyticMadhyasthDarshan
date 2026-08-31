"""Tests for LaTeX math survival through the markdown-to-HTML conversion."""
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
    insert_study_reading_key,
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


def test_study_screen_text_uses_the_full_reading_column() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text("# Title\n\nParagraph.\n", encoding="utf-8")
        html = convert_to_html(md_path, include_web_chrome=True).read_text(
            encoding="utf-8"
        )
        narrowed_text_rule = """p, ul, ol, blockquote, .quote-source, dl {
      max-width: 37rem;
    }"""
        assert narrowed_text_rule not in html
        assert "max-width: 46rem;" in html


def test_study_screen_blockquotes_gain_one_point_spacing() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text("# Title\n\n> Quotation.\n", encoding="utf-8")
        html = convert_to_html(md_path, include_web_chrome=True).read_text(
            encoding="utf-8"
        )
        screen_spacing_rule = """blockquote {
      margin-top: 11pt;
      margin-bottom: 11pt;
    }"""
        assert screen_spacing_rule in html
        assert "margin: 10pt 0 10pt 16pt;" in html


def test_study_html_explains_tooltip_and_link_affordances() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text("# Title\n\nJeevan is sentient.\n", encoding="utf-8")
        html = convert_to_html(md_path, include_web_chrome=True).read_text(
            encoding="utf-8"
        )
        assert 'class="study-reading-key"' in html
        assert "Dotted underline</span>: definition" in html
        assert "Blue underline</span>: link" in html
        assert ".study-reading-key { display: none !important; }" in html


def test_study_reading_key_follows_contents() -> None:
    body = (
        '<details class="study-toc" id="study-contents"></details>\n'
        '<p><button class="term-tip">Jeevan</button></p>'
        '<h2 id="first">First section</h2>'
    )

    rendered = insert_study_reading_key(body)

    assert 'class="study-toc study-toc--with-key"' in rendered
    assert rendered.index("</details>") < rendered.index('class="study-reading-key"')
    assert rendered.index('class="study-reading-key"') < rendered.index(
        '<h2 id="first">'
    )


def test_study_toolbar_is_two_rows_without_the_study_title() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text("# A Very Long Study Title\n\nParagraph.\n", encoding="utf-8")
        html = convert_to_html(md_path, include_web_chrome=True).read_text(
            encoding="utf-8"
        )
        toolbar = html.split('<nav class="study-toolbar"', 1)[1].split("</nav>", 1)[0]

        assert "A Very Long Study Title" not in toolbar
        assert toolbar.count('class="study-toolbar-row ') == 2
        assert 'aria-label="Back to all studies">&larr; Studies</a>' in toolbar
        assert 'aria-label="Download PDF">PDF</a>' in toolbar
        assert 'aria-label="Suggest a correction">Suggest edit</a>' in toolbar
        assert "flex-wrap: nowrap;" in html


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
        test_study_screen_text_uses_the_full_reading_column,
        test_study_screen_blockquotes_gain_one_point_spacing,
        test_study_html_explains_tooltip_and_link_affordances,
        test_study_reading_key_follows_contents,
        test_study_toolbar_is_two_rows_without_the_study_title,
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
