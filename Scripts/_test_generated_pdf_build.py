#!/usr/bin/env python3
"""Tests for changed-source selection in the Markdown PDF builder."""
from __future__ import annotations

import unittest

import yaml

from _build_markdown_pdfs import markdown_specs, select_specs
from _build_studies_index import _presentation_source_paths, catalog_build_id
from _common import BASE
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

    def test_publish_workflow_reuses_one_linux_pdf_setup(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "generated-pdf-publish.yml"
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        jobs = workflow["jobs"]
        self.assertIn("pdfs", jobs)
        self.assertNotIn("markdown", jobs)
        self.assertNotIn("reference-pdfs", jobs)
        setup_steps = [
            step
            for step in jobs["pdfs"]["steps"]
            if step.get("uses") == "./.github/actions/setup-study-env"
        ]
        self.assertEqual(len(setup_steps), 1)
        self.assertEqual(jobs["publish-and-deploy"]["needs"], ["pdfs", "presentations"])


if __name__ == "__main__":
    unittest.main()
