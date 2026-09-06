"""Tests that pin the reader HTML's layout, copy, and toolbar structure.

Split out of `_test_convert_to_pdf_math.py`, which had accumulated six design
assertions under a name that promised only math. The distinction is worth
keeping: the tests left there fail when the *converter* is wrong, while these
fail when the *design* changes — including when it changes on purpose.

That makes them change-detectors rather than correctness tests, and they are
deliberately written that way. Each one exists because a restyle silently
regressed the reading experience: the text column was narrowed to 37rem, the
blockquote spacing collapsed, the reading key drifted away from the contents
block, the toolbar wrapped onto a third row and swallowed the study title.
Asserting the exact rule is what catches that.

So when one of these fails, first decide which happened:

* the design changed **by accident** — fix the generator; or
* the design changed **on purpose** — update the assertion in the same commit,
  so the new rule is the one under guard.

Never delete an assertion to make a run green.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _convert_to_pdf import convert_to_html, insert_study_reading_key


def _study_html(markdown_text: str) -> str:
    """Render `markdown_text` with the web chrome the study reader ships with.

    The temporary directory sits inside BASE because the generator resolves site
    paths relative to the repository root.
    """
    with tempfile.TemporaryDirectory(dir=BASE) as temp_dir:
        md_path = Path(temp_dir) / "note.md"
        md_path.write_text(markdown_text, encoding="utf-8")
        return convert_to_html(md_path, include_web_chrome=True).read_text(
            encoding="utf-8"
        )


def test_study_screen_text_uses_the_full_reading_column() -> None:
    html = _study_html("# Title\n\nParagraph.\n")
    narrowed_text_rule = """p, ul, ol, blockquote, .quote-source, dl {
      max-width: 37rem;
    }"""
    assert narrowed_text_rule not in html
    assert "max-width: 46rem;" in html


def test_study_screen_blockquotes_gain_one_point_spacing() -> None:
    html = _study_html("# Title\n\n> Quotation.\n")
    screen_spacing_rule = """blockquote {
      margin-top: 11pt;
      margin-bottom: 11pt;
    }"""
    assert screen_spacing_rule in html
    assert "margin: 10pt 0 10pt 16pt;" in html


def test_study_html_explains_tooltip_and_link_affordances() -> None:
    html = _study_html("# Title\n\nJeevan is sentient.\n")
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


def test_study_contents_remains_a_native_fallback_before_the_reading_key() -> None:
    sections = "\n".join(f"## Section {i}\n\nParagraph {i}.\n" for i in range(1, 7))
    html = _study_html(f"# Title\n\nJeevan is sentient.\n\n{sections}")
    details_end = html.index("</details>",html.index('id="study-contents"'))
    assert 'class="study-toc study-toc--with-key" id="study-contents"' in html
    assert 'toc.open = true' not in html
    assert 'reader.js?v=' in html
    assert details_end < html.index('class="study-reading-key"')


def test_study_toolbar_is_two_rows_without_the_study_title() -> None:
    html = _study_html("# A Very Long Study Title\n\nParagraph.\n")
    toolbar = html.split('<nav class="study-toolbar"', 1)[1].split("</nav>", 1)[0]

    assert "A Very Long Study Title" not in toolbar
    assert toolbar.count('class="study-toolbar-row ') == 2
    assert 'class="study-toolbar-more"' in toolbar
    assert 'aria-label="Back to all studies">&larr; Studies</a>' in toolbar
    assert 'aria-label="Download PDF">PDF</a>' in toolbar
    assert 'aria-label="Suggest a correction">Suggest edit</a>' in toolbar
    assert "flex-wrap: nowrap;" in html


def main() -> int:
    tests = [
        test_study_screen_text_uses_the_full_reading_column,
        test_study_screen_blockquotes_gain_one_point_spacing,
        test_study_html_explains_tooltip_and_link_affordances,
        test_study_reading_key_follows_contents,
        test_study_contents_remains_a_native_fallback_before_the_reading_key,
        test_study_toolbar_is_two_rows_without_the_study_title,
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
