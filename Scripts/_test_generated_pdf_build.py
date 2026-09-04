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
from _study_catalog import StudyRow, StudyStatus, StudyTable


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
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "Example-Proposal"
            directory.mkdir()
            source = directory / "Example-Proposal.md"
            source.write_text("**Status:** Draft\n", encoding="utf-8")

            with patch.object(generated_inventory, "get_study_row", return_value=None):
                self.assertFalse(generated_inventory._publishable_markdown(source))

            for status, expected in (
                (StudyStatus.ONGOING, False),
                (StudyStatus.DRAFT, True),
                (StudyStatus.RELEASED, True),
            ):
                row = StudyRow(
                    slug=source.stem,
                    category="Ontology",
                    description="Example",
                    status=status,
                )
                with self.subTest(status=status), patch.object(
                    generated_inventory,
                    "get_study_row",
                    return_value=(row, StudyTable.TOPICAL),
                ):
                    self.assertEqual(generated_inventory._publishable_markdown(source), expected)

    def test_publish_workflow_reuses_one_linux_pdf_setup(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "generated-pdf-publish.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("\n  pdfs:\n", workflow)
        self.assertNotIn("\n  markdown:\n", workflow)
        self.assertNotIn("\n  reference-pdfs:\n", workflow)

        pdf_job = workflow.split("\n  pdfs:\n", 1)[1].split("\n  presentations:\n", 1)[0]
        self.assertEqual(pdf_job.count("uses: ./.github/actions/setup-study-env"), 1)
        self.assertIn("github.event_name != 'pull_request'", pdf_job)
        self.assertIn(
            "!contains(github.event.pull_request.body, 'Portal-GitHub: @')",
            pdf_job,
        )

        deploy_job = workflow.split("\n  publish-and-deploy:\n", 1)[1]
        self.assertIn("needs: [pdfs, presentations]", deploy_job)

    def test_protected_branch_publish_paths_are_source_specific(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "generated-pdf-publish.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        push_paths = workflow.split("\n  push:\n", 1)[1].split("\npermissions:\n", 1)[0]
        configured_paths = {
            line.strip()[2:].strip('"')
            for line in push_paths.splitlines()
            if line.strip().startswith('- "')
        }

        for broad_root in ("Studies/**", "Applications/**", "References/**"):
            self.assertNotIn(broad_root, configured_paths)

        for source_pattern in (
            "Studies/**/*.md",
            "Studies/**/*.pptx",
            "Applications/**/*.md",
            "Applications/**/*.pptx",
            "References/**/*.md",
            "References/**/*.html",
            "References/**/*.pdf",
            "References/r2-artifacts.json",
        ):
            self.assertIn(source_pattern, configured_paths)

        for portal_path in ("Studies/submit.html", "Studies/companion-artifacts.json"):
            self.assertFalse(
                any(fnmatchcase(portal_path, pattern) for pattern in configured_paths),
                f"portal-only path unexpectedly triggers PDF publication: {portal_path}",
            )

    def test_proposal_bootstrap_syncs_allowlist_and_verifies_before_merge(self) -> None:
        workflow_path = BASE / ".github" / "workflows" / "proposal-approved.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("actions: write", workflow)
        self.assertIn(
            "python Scripts/_publish_generated_pdf_worker.py --sync-keys",
            workflow,
        )
        self.assertIn(
            "paths: Studies infra/generated-pdf-worker/src/generated-pdf-keys.js",
            workflow,
        )
        dispatch = 'gh workflow run studies-index-check.yml --ref "$BRANCH"'
        watch = 'gh run watch "$run_id" --exit-status'
        merge = 'gh pr merge "$BRANCH" --merge --delete-branch'
        self.assertIn(dispatch, workflow)
        self.assertIn('--commit="$head_sha"', workflow)
        self.assertIn(watch, workflow)
        self.assertIn(merge, workflow)
        self.assertLess(workflow.index(dispatch), workflow.index(watch))
        self.assertLess(workflow.index(watch), workflow.index(merge))


if __name__ == "__main__":
    unittest.main()
