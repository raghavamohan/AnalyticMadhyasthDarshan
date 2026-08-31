"""Tests for restrained, distinguishable glossary tooltip placement."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _glossary_tooltips import apply_glossary_tooltips


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


if __name__ == "__main__":
    unittest.main()
