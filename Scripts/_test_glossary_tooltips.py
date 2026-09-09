"""Tests for restrained, distinguishable glossary tooltip placement."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _glossary_tooltips import apply_glossary_tooltips, refresh_document_tooltips


TERMS = [
    {
        "id": "jeevan",
        "match": ["jeevan"],
        "definition": "The sentient self.",
    },
    {
        "id": "satta",
        "match": ["satta"],
        "definition": "Omnipresence.",
    },
]


class GlossaryTooltipPlacementTests(unittest.TestCase):
    def test_wraps_only_first_occurrence_per_major_section(self) -> None:
        source = (
            "<p>Jeevan meets jeevan and satta meets satta.</p>"
            "<h2>Next section</h2>"
            "<p>Jeevan meets jeevan and satta meets satta.</p>"
        )

        rendered = apply_glossary_tooltips(source, TERMS)

        self.assertEqual(rendered.count('data-term="jeevan"'), 2)
        self.assertEqual(rendered.count('data-term="satta"'), 2)

    def test_heading_does_not_consume_first_body_occurrence(self) -> None:
        source = "<h2>Jeevan and satta</h2><p>Jeevan rests in satta.</p>"

        rendered = apply_glossary_tooltips(source, TERMS)

        self.assertEqual(rendered.count('data-term="jeevan"'), 1)
        self.assertEqual(rendered.count('data-term="satta"'), 1)
        self.assertNotIn('<h2><span class="term-tip-wrap">', rendered)

    def test_html_void_tag_does_not_disable_later_tooltips(self) -> None:
        source = "<p>Jeevan<br>satta.</p><h2>Next</h2><p>Jeevan and satta.</p>"

        rendered = apply_glossary_tooltips(source, TERMS)

        self.assertEqual(rendered.count('data-term="jeevan"'), 2)
        self.assertEqual(rendered.count('data-term="satta"'), 2)

    def test_skips_blockquotes_without_consuming_the_term(self) -> None:
        source = "<blockquote><p>Jeevan and satta.</p></blockquote><p>Jeevan in satta.</p>"

        rendered = apply_glossary_tooltips(source, TERMS)

        quote = rendered.split("</blockquote>", 1)[0]
        self.assertNotIn('class="term-tip"', quote)
        self.assertEqual(rendered.count('data-term="jeevan"'), 1)
        self.assertEqual(rendered.count('data-term="satta"'), 1)

    def test_disables_tooltips_in_references_and_resumes_afterward(self) -> None:
        source = (
            "<p>Jeevan.</p>"
            "<h2>References</h2><p>Jeevan and satta.</p>"
            "<h2>Appendix</h2><p>Jeevan and satta.</p>"
        )

        rendered = apply_glossary_tooltips(source, TERMS)

        references = rendered.split("<h2>References</h2>", 1)[1].split(
            "<h2>Appendix</h2>", 1
        )[0]
        self.assertNotIn('class="term-tip"', references)
        self.assertEqual(rendered.count('data-term="jeevan"'), 2)
        self.assertEqual(rendered.count('data-term="satta"'), 1)

    def test_refresh_updates_definitions_without_reformatting_document(self) -> None:
        original = (
            '<!doctype html>\n<main id="main"><p data-reader-passage="">'
            '<span class="term-tip-wrap"><button class="term-tip" '
            'data-definition="Old." data-term="jeevan" type="button">Jeevan'
            '</button></span> rests in satta.</p></main>\n<footer>Untouched.</footer>\n'
        )

        refreshed = refresh_document_tooltips(original, TERMS)

        self.assertIn('data-definition="The sentient self."', refreshed)
        self.assertIn('data-definition="Omnipresence."', refreshed)
        self.assertIn('<p data-reader-passage="">', refreshed)
        self.assertTrue(refreshed.endswith('<footer>Untouched.</footer>\n'))

    def test_refresh_replaces_obsolete_match_placement(self) -> None:
        original = (
            '<main id="main"><p><span class="term-tip-wrap"><button '
            'class="term-tip" data-definition="Old." data-term="jeevan" '
            'type="button">Jeevan</button></span> meets satta.</p></main>'
        )
        satta_only = [TERMS[1]]

        refreshed = refresh_document_tooltips(original, satta_only)

        self.assertNotIn('data-term="jeevan"', refreshed)
        self.assertIn('data-term="satta"', refreshed)


if __name__ == "__main__":
    unittest.main()
