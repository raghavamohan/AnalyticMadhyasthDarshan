"""Backfill approved-study proposals for existing published studies.

Studies that were written before the proposal workflow existed have no
`study-proposal` issue, so they never appear in a contributor's My Submissions
dashboard. This script creates one GitHub issue per published (`draft`/`released`)
study under `Studies/` (topical + formal catalogs) and registers it in
`proposal-registry.json`, attributing it to the given submitter.

Only the `study-proposal` label is applied. The `proposal-approved` label is
intentionally NOT applied: adding it fires `.github/workflows/proposal-approved.yml`,
whose bootstrap step runs `_bootstrap_proposal_study.py --issue N --force` and
would overwrite the existing full study with a proposal stub. The submissions
worker already treats any proposal whose slug is `draft`/`released` in the catalog
as published, so the approved label is not needed for the dashboard.

The applied catalog (`catalog-applied.json`) is skipped: those studies live under
`Applications/`, but the portal update/status endpoints only handle
`Studies/<slug>/<slug>.md`.

Usage:
  python Scripts/_backfill_published_proposals.py --dry-run
  python Scripts/_backfill_published_proposals.py --submitter raghavamohan
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
STUDIES = BASE / "Studies"
REGISTRY_PATH = STUDIES / "proposal-registry.json"
REPO = "raghavamohan/AnalyticMadhyasthDarshan"

PUBLISHED_STATUSES = {"draft", "released"}
# (catalog file, formal flag). catalog-applied.json is intentionally excluded.
CATALOG_SOURCES = [
    ("catalog-topical.json", False),
    ("catalog-formal.json", True),
]


def title_to_slug(title: str) -> str:
    words = re.findall(r"[\w']+", title)
    return "-".join(w[0].upper() + w[1:] for w in words if w)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def gh_json(args: list[str]):
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        cwd=BASE,
    )
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def existing_proposal_slugs() -> set[str]:
    """Slugs that already have a study-proposal issue (open or closed)."""
    issues = gh_json(
        [
            "api",
            f"repos/{REPO}/issues?labels=study-proposal&state=all&per_page=100",
        ]
    ) or []
    slugs: set[str] = set()
    for issue in issues:
        body = issue.get("body") or ""
        match = re.search(r"###\s*Slug\s*\r?\n+(.+)", body)
        if match:
            slug = match.group(1).splitlines()[0].strip().removesuffix(".md")
            if slug:
                slugs.add(slug)
                continue
        title = issue.get("title") or ""
        proposed = re.match(r"^Study proposal:\s*(.+)$", title.strip(), re.IGNORECASE)
        if proposed:
            slugs.add(title_to_slug(proposed.group(1).strip()))
    return slugs


def registry_slugs(registry: dict) -> set[str]:
    return {row.get("slug") for row in registry.get("proposals", []) if row.get("slug")}


def collect_published_studies() -> list[dict]:
    studies: list[dict] = []
    seen: set[str] = set()
    for filename, formal in CATALOG_SOURCES:
        path = STUDIES / filename
        if not path.is_file():
            continue
        for row in load_json(path):
            slug = row.get("slug")
            status = row.get("status")
            if not slug or status not in PUBLISHED_STATUSES or slug in seen:
                continue
            seen.add(slug)
            studies.append(
                {
                    "slug": slug,
                    "title": row.get("title") or slug.replace("-", " "),
                    "category": row.get("category") or "Other",
                    "description": row.get("description") or "",
                    "formal": formal,
                    "status": status,
                }
            )
    return studies


def build_issue_body(study: dict, submitter: str) -> str:
    formal_mark = "x" if study["formal"] else " "
    return (
        "Backfilled proposal for an existing published study "
        "(streamlining studies written before the proposal workflow).\n\n"
        f"### Proposed title\n\n{study['title']}\n\n"
        f"### Category\n\n{study['category']}\n\n"
        f"### One-line description\n\n{study['description']}\n\n"
        f"### Slug\n\n{study['slug']}\n\n"
        "### Catalog table\n\n"
        f"- [{formal_mark}] Register in the Formal Studies table (instead of Topical Studies)\n\n"
        f"### Portal submitter\n\n@{submitter}\n"
    )


def create_issue(study: dict, submitter: str) -> int:
    body = build_issue_body(study, submitter)
    issue = gh_json(
        [
            "api",
            f"repos/{REPO}/issues",
            "-f",
            f"title=Study proposal: {study['title']}",
            "-f",
            f"body={body}",
            "-f",
            "labels[]=study-proposal",
        ]
    )
    return int(issue["number"])


def write_registry(registry: dict, new_entries: list[dict]) -> None:
    proposals = list(registry.get("proposals", []))
    proposals.extend(new_entries)
    proposals.sort(key=lambda row: row.get("slug", ""))
    REGISTRY_PATH.write_text(
        json.dumps({"version": registry.get("version", 1), "proposals": proposals}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submitter", default="raghavamohan", help="GitHub login of the proposer")
    parser.add_argument("--dry-run", action="store_true", help="List what would be created without creating")
    args = parser.parse_args()

    registry = load_json(REGISTRY_PATH) if REGISTRY_PATH.is_file() else {"version": 1, "proposals": []}
    already = registry_slugs(registry) | existing_proposal_slugs()

    published = collect_published_studies()
    targets = [s for s in published if s["slug"] not in already]

    if not targets:
        print("Nothing to backfill; every published study already has a proposal.")
        return

    print(f"{len(targets)} published studies to backfill:")
    for study in targets:
        print(f"  - {study['slug']} ({study['status']})")

    if args.dry_run:
        print("\nDry run: no issues created.")
        return

    new_entries: list[dict] = []
    for study in targets:
        number = create_issue(study, args.submitter)
        print(f"Created issue #{number} for {study['slug']}")
        new_entries.append(
            {
                "slug": study["slug"],
                "title": study["title"],
                "issueNumber": number,
                "submitter": args.submitter,
                "category": study["category"],
                "description": study["description"],
                "formal": study["formal"],
                "phase": "published",
            }
        )

    write_registry(registry, new_entries)
    print(f"\nRegistered {len(new_entries)} proposals in {REGISTRY_PATH.relative_to(BASE)}")


if __name__ == "__main__":
    main()
