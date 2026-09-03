#!/usr/bin/env python3
"""Tests for changed-source selection in the Markdown PDF builder."""
from __future__ import annotations

import unittest

from _build_markdown_pdfs import markdown_specs, select_specs
from _build_studies_index import _presentation_source_paths, catalog_build_id
from _presentation_pipeline import repo_relative


class GeneratedPdfBuildSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs = markdown_specs()

    def test_exact_companion_markdown_selects_one_output(self) -> None:
        source = next(spec.source for spec in self.specs if spec.source.name.startswith("Technical-Note-"))
        rel = repo_relative(source)
        selected = select_specs((rel,), self.specs)
        self.assertEqual([spec.source for spec in selected], [source])

    def test_study_figure_selects_markdown_outputs_in_that_directory(self) -> None:
        directory = "Studies/The-Ontology-of-Coexistence/"
        selected = select_specs((directory + "figure.svg",), self.specs)
        self.assertTrue(selected)
        self.assertTrue(all(spec.key.startswith(directory) for spec in selected))

    def test_shared_pipeline_change_selects_every_markdown_output(self) -> None:
        self.assertEqual(select_specs(("Scripts/_html_to_pdf.js",), self.specs), self.specs)

    def test_presentation_only_change_selects_no_markdown_output(self) -> None:
        selected = select_specs((
            "Studies/The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pptx",
        ), self.specs)
        self.assertEqual(selected, ())

    def test_catalog_cache_buster_uses_present_pptx_sources(self) -> None:
        sources = _presentation_source_paths()
        self.assertTrue(sources)
        self.assertTrue(all(path.is_file() and path.suffix.lower() == ".pptx" for path in sources))
        self.assertEqual(catalog_build_id(), catalog_build_id())


if __name__ == "__main__":
    unittest.main()
