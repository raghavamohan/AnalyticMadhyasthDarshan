#!/usr/bin/env python3
"""Tests for changed-source selection in the Markdown PDF builder."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import Path
from unittest.mock import patch

import _generated_pdf_inventory as generated_inventory
from _bootstrap_proposal_study import ProposalFields, build_proposal_stub_markdown
from _build_markdown_pdfs import markdown_specs, select_specs
from _build_studies_index import _presentation_source_paths, catalog_build_id
from _common import BASE
from _presentation_pipeline import repo_relative
from _study_pdf_metadata import PdfStudyRow, StudyStatus


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
        for source in (
            "Scripts/_html_to_pdf.js",
            "Scripts/_safe_study_html.py",
            "Scripts/_pdf_resource_policy.cjs",
            "Scripts/_study_pdf_metadata.py",
            "Scripts/_study_pdf_pipeline.py",
            "Studies/catalog-topical.json",
        ):
            self.assertEqual(select_specs((source,), self.specs), self.specs)

    def test_catalog_publication_code_selects_no_pdf(self) -> None:
        self.assertEqual(select_specs(("Scripts/_study_catalog.py",), self.specs), ())

    def test_approval_only_catalog_change_does_not_render_existing_studies(self) -> None:
        import _build_markdown_pdfs as builder
        source = BASE / 'Studies/catalog-topical.json'
        current = source.read_text(encoding='utf-8')
        import json
        before = [row for row in json.loads(current) if row['status'] != 'ongoing']
        with patch.object(builder.subprocess,'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(before)
            selected = select_specs(('Studies/catalog-topical.json',),self.specs,base='base')
        self.assertEqual(selected,())

    def test_shared_glossary_change_selects_no_pdf(self) -> None:
        self.assertEqual(select_specs(("Studies/glossary.json",), self.specs), ())

        workflow = (BASE / ".github/workflows/generated-pdf-publish.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('- "Studies/glossary.json"', workflow)

        renderer = (BASE / "Scripts/_html_to_pdf.js").read_text(encoding="utf-8")
        self.assertLess(
            renderer.index("await removeWebOnlyGlossaryTooltips(page);"),
            renderer.index("await page.pdf({"),
        )

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

    def test_pre_catalog_proposal_stub_has_no_document_status(self) -> None:
        fields = ProposalFields(
            slug="Example-Proposal",
            title="Example Proposal",
            category="Ontology",
            description="A proposed study.",
            summary="Study scope.",
            formal=False,
            submitter="example",
            issue_number=123,
        )
        markdown = build_proposal_stub_markdown(fields, datetime(2026, 9, 4, 12, 30))
        self.assertNotIn("**Status:**", markdown)
        self.assertIn("approved study proposal", markdown)

    def test_canonical_pdf_inventory_follows_catalog_status(self) -> None:
        from _publication_inventory import public_markdown
        source = BASE / "Studies/Example/Example.md"
        self.assertFalse(public_markdown(source, studies=set()))
        self.assertTrue(public_markdown(source, studies={("Studies", "Example")}))
        self.assertFalse(public_markdown(source.with_name("Research-Template-Example.md"), studies={("Studies", "Example")}))

    def test_publish_workflow_reuses_one_linux_pdf_setup(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "generated-pdf-publish.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("\n  pdfs:\n", workflow)
        self.assertNotIn("\n  markdown:\n", workflow)
        self.assertNotIn("\n  reference-pdfs:\n", workflow)

        pdf_job = workflow.split("\n  pdfs:\n", 1)[1].split("\n  presentations:\n", 1)[0]
        self.assertEqual(pdf_job.count("uses: ./.github/actions/setup-study-env"), 1)
        self.assertIn("github.event_name != 'pull_request'", pdf_job)
        self.assertNotIn("Portal-GitHub: @", pdf_job)
        self.assertIn("--changed-since \"$BASE_SHA\"", pdf_job)
        self.assertIn("steps.pdf-inputs.outputs.references_changed == 'true'", pdf_job)

        deploy_job = workflow.split("\n  publish-and-deploy:\n", 1)[1]
        self.assertIn("needs: [pdfs, presentations]", deploy_job)

    def test_every_master_merge_queues_one_publication(self) -> None:
        workflow = (BASE / ".github/workflows/publish-site.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [master]", workflow)
        self.assertNotIn("paths:", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("source_sha:", workflow)
        self.assertIn("uses: ./.github/workflows/generated-pdf-publish.yml", workflow)

    def test_proposal_bootstrap_syncs_allowlist_and_verifies_before_merge(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "proposal-approved.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("actions: write", workflow)
        self.assertIn(
            "python Scripts/_publish_generated_pdf_worker.py --sync-keys",
            workflow,
        )
        self.assertIn("contract: 'true'", workflow)
        source = (BASE / "Scripts/_bootstrap_ci.py").read_text(encoding="utf-8")
        self.assertIn('f"report_sha={sha}"', source)
        self.assertIn('f"repos/{repo}/commits/{sha}/statuses"', source)
        self.assertIn('"--match-head-commit", sha', source)
        self.assertIn('"publish-site.yml"', source)



if __name__ == "__main__":
    unittest.main()
