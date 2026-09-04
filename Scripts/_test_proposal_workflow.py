#!/usr/bin/env python3
"""Regression tests for proposal readiness, collision safety, and portal revision flow."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _bootstrap_proposal_study as bootstrap
import _study_catalog as catalog
from _common import BASE
from _study_catalog import StudyRow, StudyStatus, StudyTable


WORKER = BASE / "infra" / "worker" / "src" / "index.js"
PORTAL = BASE / "Studies" / "submit.html"
APPROVAL_WORKFLOW = BASE / ".github" / "workflows" / "proposal-approved.yml"


def proposal(issue: int = 123, slug: str = "Example-Proposal") -> bootstrap.ProposalFields:
    return bootstrap.ProposalFields(
        slug=slug,
        title=slug.replace("-", " "),
        category="Ontology",
        description="Example proposal",
        summary="Example scope",
        formal=False,
        submitter="example",
        issue_number=issue,
    )


class ProposalBootstrapSafetyTests(unittest.TestCase):
    def test_bootstrap_rejects_slug_owned_by_another_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "proposal-registry.json"
            registry.write_text(
                json.dumps({
                    "version": 1,
                    "proposals": [{
                        "slug": "Example-Proposal",
                        "issueNumber": 99,
                        "phase": "pre-catalog",
                    }],
                }),
                encoding="utf-8",
            )
            with (
                patch.object(bootstrap, "REGISTRY_PATH", registry),
                patch.object(bootstrap, "study_md", lambda slug: root / slug / f"{slug}.md"),
                patch.object(bootstrap, "get_study_row", return_value=None),
            ):
                with self.assertRaisesRegex(SystemExit, "already belongs to proposal issue #99"):
                    bootstrap.bootstrap_target_state(proposal())

    def test_bootstrap_allows_only_the_same_pre_catalog_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "proposal-registry.json"
            registry.write_text(
                json.dumps({
                    "version": 1,
                    "proposals": [{
                        "slug": "Example-Proposal",
                        "issueNumber": 123,
                        "phase": "pre-catalog",
                    }],
                }),
                encoding="utf-8",
            )
            md_path = root / "Example-Proposal" / "Example-Proposal.md"
            md_path.parent.mkdir()
            md_path.write_text("# Example\n\n## Study proposal\n", encoding="utf-8")
            row = StudyRow(
                slug="Example-Proposal",
                category="Ontology",
                description="Example",
                status=StudyStatus.ONGOING,
            )
            with (
                patch.object(bootstrap, "REGISTRY_PATH", registry),
                patch.object(bootstrap, "study_md", lambda _slug: md_path),
                patch.object(
                    bootstrap,
                    "get_study_row",
                    return_value=(row, StudyTable.TOPICAL),
                ),
            ):
                self.assertEqual(bootstrap.bootstrap_target_state(proposal()), "pre-catalog")

    def test_bootstrap_never_replaces_a_full_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "proposal-registry.json"
            registry.write_text(
                json.dumps({
                    "version": 1,
                    "proposals": [{
                        "slug": "Example-Proposal",
                        "issueNumber": 123,
                        "phase": "pre-catalog",
                    }],
                }),
                encoding="utf-8",
            )
            md_path = root / "Example-Proposal" / "Example-Proposal.md"
            md_path.parent.mkdir()
            md_path.write_text("# Example\n\n**Status:** Draft\n", encoding="utf-8")
            row = StudyRow(
                slug="Example-Proposal",
                category="Ontology",
                description="Example",
                status=StudyStatus.ONGOING,
            )
            with (
                patch.object(bootstrap, "REGISTRY_PATH", registry),
                patch.object(bootstrap, "study_md", lambda _slug: md_path),
                patch.object(
                    bootstrap,
                    "get_study_row",
                    return_value=(row, StudyTable.TOPICAL),
                ),
            ):
                with self.assertRaisesRegex(SystemExit, "Refusing to replace a full study"):
                    bootstrap.bootstrap_target_state(proposal())

    def test_formal_and_topical_pre_catalog_proposals_are_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            registry = Path(temp) / "proposal-registry.json"
            registry.write_text(
                json.dumps({
                    "version": 1,
                    "proposals": [
                        {"slug": "Topical", "phase": "pre-catalog", "formal": False},
                        {"slug": "Formal", "phase": "pre-catalog", "formal": True},
                        {"slug": "Applied", "phase": "pre-catalog", "applied": True},
                        {"slug": "Published", "phase": "published", "formal": False},
                    ],
                }),
                encoding="utf-8",
            )
            with patch.object(catalog, "PROPOSAL_REGISTRY_PATH", registry):
                topical = catalog.load_pre_catalog_proposals(StudyTable.TOPICAL)
                formal = catalog.load_pre_catalog_proposals(StudyTable.FORMAL)
            self.assertEqual([row["slug"] for row in topical], ["Topical"])
            self.assertEqual([row["slug"] for row in formal], ["Formal"])

    def test_sync_writes_planned_rows_to_both_catalogs(self) -> None:
        proposals = {
            StudyTable.TOPICAL: [{
                "slug": "Topical",
                "title": "Topical",
                "category": "Ontology",
                "description": "Topical proposal",
            }],
            StudyTable.FORMAL: [{
                "slug": "Formal",
                "title": "Formal",
                "category": "Formal",
                "description": "Formal proposal",
            }],
        }
        writes: list[tuple[StudyTable, list[StudyRow], bool]] = []

        def capture(rows: list[StudyRow], table: StudyTable, *, rebuild_index: bool) -> None:
            writes.append((table, rows, rebuild_index))

        with (
            patch.object(
                catalog,
                "load_pre_catalog_proposals",
                side_effect=lambda table: proposals[table],
            ),
            patch.object(catalog, "load_catalog_rows", return_value=[]),
            patch.object(catalog, "proposal_stub_hrefs", return_value=(None, None)),
            patch.object(catalog, "write_studies_catalog", side_effect=capture),
        ):
            catalog.sync_pre_catalog_proposals_to_catalog()

        self.assertEqual([table for table, _rows, _rebuild in writes], [
            StudyTable.TOPICAL,
            StudyTable.FORMAL,
        ])
        self.assertFalse(writes[0][2])
        self.assertTrue(writes[1][2])
        self.assertEqual(writes[1][1][0].status, StudyStatus.ONGOING)
        self.assertEqual(writes[1][1][0].table, StudyTable.FORMAL)


class ProposalPortalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.worker = WORKER.read_text(encoding="utf-8")
        cls.portal = PORTAL.read_text(encoding="utf-8")
        cls.workflow = APPROVAL_WORKFLOW.read_text(encoding="utf-8")

    def test_proposal_submission_validates_fields_and_slug_uniqueness(self) -> None:
        self.assertIn("requiredProposalText(data.title", self.worker)
        self.assertIn("await assertProposalSlugAvailable(", self.worker)
        self.assertIn("Open proposal #${duplicate.number} already uses", self.worker)

    def test_draft_submission_requires_verified_workspace(self) -> None:
        self.assertIn("function proposalWorkspaceReady(", self.worker)
        self.assertIn("assertProposalWorkspaceReady(proposal, slug", self.worker)
        self.assertIn("preparing: 'Preparing workspace'", self.portal)
        self.assertIn("item.catalogStatus === 'ongoing'", self.portal)
        self.assertIn("Planned workspace is ready", self.portal)

    def test_requested_changes_update_the_existing_pull_request(self) -> None:
        self.assertIn("label: 'Revise draft'", self.worker)
        self.assertIn("router.get('/api/revision-source'", self.worker)
        self.assertIn("router.post('/api/revise'", self.worker)
        self.assertIn("branch: target.branch", self.worker)
        self.assertIn("mode === 'revise'", self.portal)
        self.assertIn("Draft pull request updated.", self.portal)

    def test_every_existing_study_write_is_owner_guarded(self) -> None:
        self.assertGreaterEqual(
            self.worker.count("await assertStudyOwnedBySession(session, slug, env);"),
            3,
        )
        self.assertIn("repo:${REPO} is:pr is:open label:status-change", self.worker)

    def test_dashboard_limit_and_bootstrap_feedback_are_explicit(self) -> None:
        self.assertNotIn("per_page=20", self.worker)
        self.assertIn("per_page=100", self.worker)
        self.assertIn("Report workspace preparation failure", self.workflow)
        self.assertIn("Confirm that the proposal workspace is ready", self.workflow)

    def test_review_state_uses_each_reviewers_latest_decision(self) -> None:
        self.assertIn("const latestByReviewer = new Map();", self.worker)
        self.assertIn("latestByReviewer.set(reviewer, review);", self.worker)

    def test_closed_removed_proposals_are_terminal(self) -> None:
        self.assertIn("function proposalIsRetired(", self.worker)
        self.assertIn("if (retired) stage = 'retired';", self.worker)
        self.assertIn("proposal?.state === 'open'", self.worker)
        self.assertIn("proposal?.state === 'closed'", self.worker)
        self.assertIn("item.state === 'open' && existing.state !== 'open'", self.worker)
        self.assertIn("retired: 'Retired'", self.portal)
        self.assertIn("if (data.closed)", self.portal)

    def test_dashboard_can_filter_by_workflow_state_and_category(self) -> None:
        self.assertIn("async function fetchCatalogMaps(", self.worker)
        self.assertIn("categoryMap: new Map(", self.worker)
        self.assertIn("function proposalCategories(", self.worker)
        self.assertGreaterEqual(self.worker.count("categories: proposalCategories("), 2)
        self.assertIn('id="dashboard-state-filter"', self.portal)
        self.assertIn('id="dashboard-category-filter"', self.portal)
        self.assertIn("function filterDashboardSubmissions(", self.portal)
        self.assertIn("categories.includes(selectedCategory)", self.portal)
        self.assertIn("No submissions match these filters.", self.portal)


if __name__ == "__main__":
    unittest.main()
