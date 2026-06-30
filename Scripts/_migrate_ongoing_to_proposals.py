"""Migrate catalog Ongoing rows to pre-catalog approved proposals.

Bootstraps proposal stubs under Studies/<Slug>/, optionally creates GitHub issues,
updates proposal-registry.json, and syncs Planned (ongoing) rows on the public index.

Usage:
  python Scripts/_migrate_ongoing_to_proposals.py --dry-run
  python Scripts/_migrate_ongoing_to_proposals.py --create-issues --submitter raghavamohan
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _bootstrap_proposal_study import ProposalFields, bootstrap_proposal, upsert_registry_entry
from _study_catalog import (
    StudyStatus,
    StudyTable,
    load_catalog_rows,
    slug_to_title,
    sync_pre_catalog_proposals_to_catalog,
)

REPO = "raghavamohan/AnalyticMadhyasthDarshan"
DEFAULT_SUBMITTER = "raghavamohan"


def build_issue_body(fields: ProposalFields) -> str:
    formal_line = "- [x]" if fields.formal else "- [ ]"
    issue_ref = f"#{fields.issue_number}" if fields.issue_number else "(pending)"
    return f"""Propose a new analytic study before writing the full paper.
Maintainers will review and label approved proposals `proposal-approved`.

### Slug

{fields.slug}

### Proposed title

{fields.title}

### Category

{fields.category}

### One-line description

{fields.description}

### Study summary

{fields.description}

(Migrated from catalog **Ongoing** placeholder — proposal pre-approved.)

### Catalog table

{formal_line} Register in the Formal Studies table (instead of Topical Studies)

### Prior familiarity with Madhyasth Darshan

Maintainer migration from catalog Ongoing status.

### Portal submitter

@{fields.submitter}
"""


def create_github_issue(fields: ProposalFields) -> int:
    title = f"Study proposal: {fields.title}"
    body = build_issue_body(fields)
    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        REPO,
        "--title",
        title,
        "--body",
        body,
        "--label",
        "study-proposal",
        "--label",
        "proposal-approved",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"gh issue create failed: {result.stderr or result.stdout}")
    url = (result.stdout or "").strip()
    number_text = url.rstrip("/").split("/")[-1]
    return int(number_text)


def migrate(*, dry_run: bool, create_issues: bool, submitter: str) -> None:
    rows = load_catalog_rows(StudyTable.TOPICAL)
    ongoing = [row for row in rows if row.status == StudyStatus.ONGOING]
    if not ongoing:
        print("No Ongoing topical studies in catalog.")
        return

    print(f"Found {len(ongoing)} Ongoing study(ies) to migrate.")
    for row in ongoing:
        title = slug_to_title(row.slug)
        fields = ProposalFields(
            slug=row.slug,
            title=title,
            category=row.category,
            description=row.description,
            summary=row.description,
            formal=False,
            submitter=submitter,
            issue_number=None,
        )
        if dry_run:
            print(f"  [dry-run] {row.slug}: bootstrap stub and sync Planned index row")
            continue

        if create_issues:
            issue_number = create_github_issue(fields)
            fields.issue_number = issue_number
            print(f"  Created issue #{issue_number} for {row.slug}")

        bootstrap_proposal(fields, force=True)

    if dry_run:
        return

    sync_pre_catalog_proposals_to_catalog()
    print(f"Synced {len(ongoing)} pre-catalog proposal(s) to the public index as Planned.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Ongoing catalog rows to pre-catalog proposals.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-issues", action="store_true", help="Create GitHub issues via gh CLI")
    parser.add_argument("--submitter", default=DEFAULT_SUBMITTER)
    args = parser.parse_args()
    migrate(dry_run=args.dry_run, create_issues=args.create_issues, submitter=args.submitter)


if __name__ == "__main__":
    main()
