"""CI helper: route study pull requests to the correct Scripts pipeline.

Reads the pull_request event from GITHUB_EVENT_PATH, inspects PR labels and body,
runs the appropriate study script, and exits non-zero on validation failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path

from _common import BASE, STUDIES, slug_from_study_relative_path, study_md

from _pdf_cache_sync import pdfs_for_study, sync_pdf_cache  # noqa: E402
from _study_catalog import (  # noqa: E402
    StudyStatus,
    get_study_row,
    parse_edited_on,
    parse_status_md,
    regenerate_pdf,
    upsert_study_row,
    verify_timestamp_sync,
    write_studies_catalog,
)

PR_LABELS = ("new-study", "study-update", "status-change")
ISSUE_FORM_HEADINGS = {
    "category": "Category",
    "description": "One-line description",
    "formal": "Catalog table",
}


def load_event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        raise SystemExit("GITHUB_EVENT_PATH is not set.")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gh_request(path: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set.")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "study-pr-ci",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"GitHub API {path} failed ({exc.code}): {body}") from exc


def parse_body_field(body: str, *patterns: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def parse_issue_form_section(body: str, heading: str) -> str | None:
    pattern = rf"###\s*{re.escape(heading)}\s*\r?\n+(.+?)(?=\r?\n###|\Z)"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def issue_is_approved(issue_number: int) -> bool:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is not set.")
    issue = gh_request(f"/repos/{repo}/issues/{issue_number}")
    labels = {label["name"] for label in issue.get("labels", [])}
    if "proposal-approved" not in labels:
        raise SystemExit(
            f"Issue #{issue_number} is missing the `proposal-approved` label."
        )
    return True


def proposal_metadata_from_issue(issue_number: int) -> tuple[str, str, bool]:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is not set.")
    issue = gh_request(f"/repos/{repo}/issues/{issue_number}")
    body = issue.get("body") or ""

    category = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["category"])
    description = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["description"])
    formal_block = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["formal"]) or ""
    formal = "- [x]" in formal_block

    if not category:
        raise SystemExit(f"Issue #{issue_number} is missing a Category field.")
    if not description:
        raise SystemExit(f"Issue #{issue_number} is missing a One-line description field.")
    return category, description, formal


def changed_study_slugs(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
        cwd=BASE,
    )
    slugs: list[str] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        path = Path(line.strip())
        if path.parts[:1] != ("Studies",):
            continue
        rel = Path(*path.parts[1:])
        slug = slug_from_study_relative_path(rel)
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


def active_pr_label(labels: list[dict]) -> str | None:
    names = [label["name"] for label in labels if label["name"] in PR_LABELS]
    if not names:
        return None
    if len(names) > 1:
        raise SystemExit(
            f"Apply only one study PR label; found: {', '.join(names)}."
        )
    return names[0]


def sync_catalog_timestamp_from_md(slug: str) -> None:
    located = get_study_row(slug)
    if located is None:
        raise SystemExit(f"Study not found in catalog: {slug}")

    row, table = located
    md_path = study_md(slug)
    if not md_path.exists():
        raise SystemExit(f"Missing markdown file: {md_path}")

    md_text = md_path.read_text(encoding="utf-8")
    edited_at = parse_edited_on(md_text)
    if edited_at is None:
        raise SystemExit(
            f"{slug}: update `**Edited on:**` in {md_path.name} before opening the PR."
        )

    md_status = parse_status_md(md_text)
    if md_status is not None:
        row = replace(row, status=StudyStatus(md_status.lower()))

    row = replace(row, edited_at=edited_at)
    rows = upsert_study_row(load_catalog_rows(table), row)
    write_studies_catalog(rows, table)


def sync_study_reference_cache(slug: str) -> None:
    paths = pdfs_for_study(slug)
    if not paths:
        print(f"No local PDF references to cache for {slug}.")
        return
    print(f"Syncing PDF cache for {slug} ({len(paths)} file(s))...")
    sync_pdf_cache(paths, prune=False)


def handle_new_study(body: str, base_ref: str) -> None:
    issue_text = parse_body_field(
        body,
        r"Proposal issue:\s*#?(\d+)",
        r"Proposal issue:\s*(\d+)",
    )
    if not issue_text:
        raise SystemExit("PR body must include `Proposal issue: #<number>`.")

    issue_number = int(issue_text)
    issue_is_approved(issue_number)

    slug = parse_body_field(body, r"^Slug:\s*(.+)$", r"Study slug:\s*(.+)$")
    changed = changed_study_slugs(base_ref)
    if slug:
        slug = slug.strip().removesuffix(".md")
    elif len(changed) == 1:
        slug = changed[0]
    else:
        raise SystemExit(
            "Set `Slug:` in the PR body or change exactly one Studies/<Slug>/<Slug>.md file."
        )

    md_path = study_md(slug)
    if not md_path.exists():
        raise SystemExit(f"Expected study markdown at {md_path}")

    category, description, formal = proposal_metadata_from_issue(issue_number)
    tags = parse_body_field(body, r"^Tags:\s*(.+)$") or "MVD, SB, JV"

    command = [
        sys.executable,
        str(SCRIPTS / "_add_study.py"),
        str(md_path),
        "--category",
        category,
        "--description",
        description,
        "--tags",
        tags,
        "--status",
        "draft",
        "--force",
    ]
    if formal:
        command.append("--formal")

    print("Running:", " ".join(command))
    subprocess.run(command, check=True, cwd=BASE)
    sync_study_reference_cache(slug)


def handle_study_update(body: str, base_ref: str) -> None:
    slug = parse_body_field(body, r"^Study slug:\s*(.+)$", r"^Slug:\s*(.+)$")
    changed = changed_study_slugs(base_ref)
    if slug:
        slug = slug.strip().removesuffix(".md")
    elif len(changed) == 1:
        slug = changed[0]
    else:
        raise SystemExit(
            "Set `Study slug:` in the PR body or change exactly one Studies/<Slug>/<Slug>.md file."
        )

    located = get_study_row(slug)
    if located is None:
        raise SystemExit(f"Study not found in catalog: {slug}")

    row, _table = located
    if row.status == StudyStatus.ONGOING:
        raise SystemExit(f"{slug} is an Ongoing placeholder; register it with a new-study PR first.")

    sync_catalog_timestamp_from_md(slug)
    located = get_study_row(slug)
    if located is None:
        raise SystemExit(f"Study not found after catalog sync: {slug}")
    row, _table = located

    md_path = study_md(slug)
    print(f"Regenerating PDF for {slug} ({row.status.value})")
    sync_study_reference_cache(slug)
    regenerate_pdf(md_path, row.status)

    errors = verify_timestamp_sync(slug)
    if errors:
        raise SystemExit("Timestamp verification failed:\n  - " + "\n  - ".join(errors))


def handle_status_change(body: str) -> None:
    slug = parse_body_field(body, r"^Study slug:\s*(.+)$", r"^Slug:\s*(.+)$")
    target = parse_body_field(body, r"^Target status:\s*(\w+)")
    if not slug:
        raise SystemExit("PR body must include `Study slug: <Slug>`.")
    if not target:
        raise SystemExit("PR body must include `Target status: draft` or `released`.")

    slug = slug.strip().removesuffix(".md")
    target = target.strip().lower()
    if target not in {"draft", "released"}:
        raise SystemExit("Target status must be `draft` or `released`.")

    command = [
        sys.executable,
        str(SCRIPTS / "_set_study_status.py"),
        slug,
        "--status",
        target,
    ]
    print("Running:", " ".join(command))
    subprocess.run(command, check=True, cwd=BASE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run study PR CI pipeline.")
    parser.add_argument(
        "--base-ref",
        default="origin/master",
        help="Git ref to diff against (default: origin/master)",
    )
    args = parser.parse_args()

    event = load_event()
    pull_request = event.get("pull_request")
    if pull_request is None:
        raise SystemExit("Event does not include pull_request payload.")

    label = active_pr_label(pull_request.get("labels", []))
    if label is None:
        raise SystemExit(
            "Apply one PR label: `new-study`, `study-update`, or `status-change`."
        )

    body = pull_request.get("body") or ""
    print(f"Study PR type: {label}")

    if label == "new-study":
        handle_new_study(body, args.base_ref)
    elif label == "study-update":
        handle_study_update(body, args.base_ref)
    elif label == "status-change":
        handle_status_change(body)
    else:
        raise SystemExit(f"Unsupported label: {label}")

    print("Study PR pipeline completed successfully.")


if __name__ == "__main__":
    main()
