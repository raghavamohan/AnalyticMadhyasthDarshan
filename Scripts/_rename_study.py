"""Rename a study slug and sync all proposal-tracking metadata.

Coordinates directory rename, catalog, proposal-registry.json, .proposal-meta.json,
GitHub proposal issue body, References paths, discussion page, and PDF regeneration.

Usage:
  python Scripts/_rename_study.py --from Old-Slug --to New-Slug
  python Scripts/_rename_study.py --from Old-Slug --to New-Slug --title "New display title"
  python Scripts/_rename_study.py --from Old-Slug --to New-Slug --metadata-only
  python Scripts/_rename_study.py --from Old-Slug --to New-Slug --issue 70 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path

from _bootstrap_proposal_study import (
    REGISTRY_PATH,
    ProposalFields,
    issue_body_with_slug,
    issue_body_with_title,
)
from _common import APPLICATIONS, BASE, REFERENCES, STUDIES, validate_study_slug, write_text_lf
from _study_catalog import (
    display_title,
    get_study_row,
    load_catalog_rows,
    write_studies_catalog,
)

SCRIPTS = Path(__file__).resolve().parent


def validate_slug(slug: str) -> None:
    try:
        validate_study_slug(slug)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def study_root_for_slug(slug: str) -> Path:
    if (APPLICATIONS / slug / f"{slug}.md").is_file():
        return APPLICATIONS
    return STUDIES


def load_registry() -> dict:
    if not REGISTRY_PATH.is_file():
        return {"version": 1, "proposals": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def registry_row_for_slug(slug: str) -> dict | None:
    for row in load_registry().get("proposals", []):
        if row.get("slug") == slug:
            return row
    return None


def proposal_meta_paths(slug: str) -> tuple[Path, Path]:
    return STUDIES / slug / ".proposal-meta.json", APPLICATIONS / slug / ".proposal-meta.json"


def existing_proposal_meta_path(slug: str) -> Path | None:
    return next((path for path in proposal_meta_paths(slug) if path.is_file()), None)


def resolve_issue_number(
    old_slug: str,
    issue_number: int | None,
    new_slug: str | None = None,
) -> int | None:
    if issue_number is not None:
        return issue_number
    for slug in dict.fromkeys((old_slug, new_slug)):
        if slug is None:
            continue
        meta_path = existing_proposal_meta_path(slug)
        if meta_path is not None:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            issue = data.get("proposalIssue")
            if issue:
                return int(issue)
        row = registry_row_for_slug(slug)
        if row and row.get("issueNumber"):
            return int(row["issueNumber"])
    return None


def rename_study_files(old_slug: str, new_slug: str, *, dry_run: bool) -> None:
    root = study_root_for_slug(old_slug)
    old_dir = root / old_slug
    new_dir = root / new_slug
    if not old_dir.is_dir() and new_dir.is_dir():
        print(f"Filesystem already renamed: {old_dir.name} -> {new_dir.name}")
        return
    if not old_dir.is_dir():
        raise SystemExit(f"Missing study directory: {old_dir}")
    if new_dir.exists():
        raise SystemExit(f"Target directory already exists: {new_dir}")

    if dry_run:
        print(f"Would rename directory {old_dir} -> {new_dir}")
        return

    canonical_renames = [
        (old_dir / f"{old_slug}{suffix}", old_dir / f"{new_slug}{suffix}")
        for suffix in (".md", ".html", ".pdf")
        if (old_dir / f"{old_slug}{suffix}").is_file()
    ]
    collisions = [target for _source, target in canonical_renames if target.exists()]
    if collisions:
        raise SystemExit(
            "Cannot rename canonical files; target name(s) already exist: "
            + ", ".join(str(path) for path in collisions)
        )

    # Move the tree as one filesystem operation, then rename only the canonical
    # source/generated trio. Companion deck and note basenames remain stable.
    old_dir.rename(new_dir)
    for source, target in canonical_renames:
        (new_dir / source.name).rename(new_dir / target.name)
    print(f"Renamed {old_dir} -> {new_dir}")


def update_catalog_row(old_slug: str, new_slug: str, new_title: str | None, *, dry_run: bool) -> None:
    located = get_study_row(old_slug)
    if located is None:
        located = get_study_row(new_slug)
        if located is None:
            print(f"No catalog row for {old_slug} or {new_slug}; skipping catalog update.")
            return
        row, table = located
        if new_title and row.title != new_title:
            rows = load_catalog_rows(table)
            index = next(index for index, item in enumerate(rows) if item.slug == new_slug)
            rows[index] = replace(row, title=new_title)
            if dry_run:
                print(f"Would update {table.value} catalog title for {new_slug}")
            else:
                write_studies_catalog(rows, table, rebuild_discussion=[new_slug])
                print(f"Updated {table.value} catalog title for {new_slug}")
        else:
            print(f"Catalog already uses slug {new_slug}.")
        return

    row, table = located
    title = new_title or row.title or display_title(row)
    new_row = replace(row, slug=new_slug, title=title, pdf_href=None, html_href=None)
    rows = load_catalog_rows(table)
    index = next(index for index, item in enumerate(rows) if item.slug == old_slug)
    rows[index] = new_row
    if dry_run:
        print(f"Would update {table.value} catalog: {old_slug} -> {new_slug}")
        return
    write_studies_catalog(rows, table, rebuild_discussion=[new_slug])
    print(f"Updated {table.value} catalog: {old_slug} -> {new_slug}")


def update_registry(old_slug: str, new_slug: str, new_title: str | None, issue_number: int | None, *, dry_run: bool) -> None:
    data = load_registry()
    proposals = list(data.get("proposals", []))
    old_row = next((row for row in proposals if row.get("slug") == old_slug), None)
    new_row = next((row for row in proposals if row.get("slug") == new_slug), None)

    meta_path = existing_proposal_meta_path(new_slug if new_row else old_slug)
    meta = {}
    if meta_path is not None:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    fields = ProposalFields(
        slug=new_slug,
        title=new_title or (old_row or new_row or meta or {}).get("title") or new_slug.replace("-", " "),
        category=(old_row or new_row or meta or {}).get("category") or "Other",
        description=(old_row or new_row or meta or {}).get("description") or "",
        summary=(old_row or new_row or meta or {}).get("description") or "",
        formal=bool((old_row or new_row or meta or {}).get("formal")),
        submitter=(old_row or new_row or meta or {}).get("submitter") or "",
        issue_number=issue_number
        or (old_row or new_row or {}).get("issueNumber")
        or meta.get("proposalIssue"),
    )
    if not fields.description:
        located = get_study_row(new_slug) or get_study_row(old_slug)
        if located:
            fields = replace(fields, description=located[0].description)

    phase = (old_row or new_row or meta or {}).get("phase") or "catalog-draft"
    if dry_run:
        print(f"Would update proposal-registry.json: {old_slug} -> {new_slug} (phase={phase})")
        return

    filtered = [row for row in proposals if row.get("slug") not in {old_slug, new_slug}]
    filtered.append(
        {
            "slug": new_slug,
            "title": fields.title,
            "issueNumber": fields.issue_number,
            "submitter": fields.submitter,
            "category": fields.category,
            "description": fields.description,
            "formal": fields.formal,
            "phase": phase,
        }
    )
    filtered.sort(key=lambda row: row.get("slug", ""))
    write_text_lf(REGISTRY_PATH, json.dumps({"version": 1, "proposals": filtered}, indent=2) + "\n")
    print(f"Updated proposal-registry.json: {old_slug} -> {new_slug}")


def update_proposal_meta_file(old_slug: str, new_slug: str, new_title: str | None, issue_number: int | None, *, dry_run: bool) -> None:
    src = existing_proposal_meta_path(old_slug)
    dst = existing_proposal_meta_path(new_slug)
    if dst is None:
        if (APPLICATIONS / new_slug).is_dir():
            dst = APPLICATIONS / new_slug / ".proposal-meta.json"
        elif (STUDIES / new_slug).is_dir():
            dst = STUDIES / new_slug / ".proposal-meta.json"
        elif src is not None and src.parent.parent == APPLICATIONS:
            dst = APPLICATIONS / new_slug / ".proposal-meta.json"
        else:
            dst = STUDIES / new_slug / ".proposal-meta.json"
    if dst.is_file():
        data = json.loads(dst.read_text(encoding="utf-8"))
    elif src is not None and src.is_file():
        data = json.loads(src.read_text(encoding="utf-8"))
    else:
        row = registry_row_for_slug(new_slug) or registry_row_for_slug(old_slug)
        if not row:
            print("No .proposal-meta.json or registry row; skipping meta file.")
            return
        data = {
            "slug": new_slug,
            "title": row.get("title"),
            "category": row.get("category"),
            "description": row.get("description"),
            "formal": row.get("formal", False),
            "proposalIssue": row.get("issueNumber"),
            "submitter": row.get("submitter"),
            "phase": row.get("phase", "catalog-draft"),
        }

    data["slug"] = new_slug
    if new_title:
        data["title"] = new_title
    if issue_number is not None:
        data["proposalIssue"] = issue_number

    if dry_run:
        print(f"Would write {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(dst, json.dumps(data, indent=2) + "\n")
    if src is not None and src.is_file() and src != dst:
        src.unlink()
    print(f"Updated {dst}")


def gh_request(path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set.")
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "rename-study",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is not set.")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"GitHub API {path} failed ({exc.code}): {body}") from exc


def update_github_issue(issue_number: int, slug: str, title: str | None) -> None:
    issue = gh_request(f"/issues/{issue_number}")
    body = issue.get("body") or ""
    updated = issue_body_with_slug(body, slug)
    if title:
        updated = issue_body_with_title(updated, title)
    if updated == body and not title:
        return
    payload: dict[str, str] = {"body": updated}
    if title:
        payload["title"] = f"Study proposal: {title}"
    gh_request(f"/issues/{issue_number}", method="PATCH", payload=payload)
    print(f"Updated GitHub issue #{issue_number} slug/title.")


def update_reference_paths(old_slug: str, new_slug: str, *, dry_run: bool) -> None:
    replacements = [
        (f"[{old_slug}.pdf]", f"[{new_slug}.pdf]"),
        (f"[{old_slug}.html]", f"[{new_slug}.html]"),
        (f"Studies/{old_slug}/{old_slug}.pdf", f"Studies/{new_slug}/{new_slug}.pdf"),
        (f"Studies/{old_slug}/{old_slug}.html", f"Studies/{new_slug}/{new_slug}.html"),
        (f"../Studies/{old_slug}/{old_slug}.pdf", f"../Studies/{new_slug}/{new_slug}.pdf"),
        (f"../Studies/{old_slug}/{old_slug}.html", f"../Studies/{new_slug}/{new_slug}.html"),
        (f"Applications/{old_slug}/{old_slug}.pdf", f"Applications/{new_slug}/{new_slug}.pdf"),
        (f"Applications/{old_slug}/{old_slug}.html", f"Applications/{new_slug}/{new_slug}.html"),
    ]
    for path in (REFERENCES / "README.md", REFERENCES / "MANIFEST.md"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            if dry_run:
                print(f"Would update references in {path}")
            else:
                write_text_lf(path, updated)
                print(f"Updated references in {path}")


def regenerate_artifacts(new_slug: str, *, dry_run: bool) -> None:
    if dry_run:
        print(f"Would regenerate PDF and discussion page for {new_slug}")
        return
    subprocess.run(
        [sys.executable, str(SCRIPTS / "_regenerate_pdf.py"), new_slug],
        check=True,
        cwd=BASE,
    )


def rename_study(
    old_slug: str,
    new_slug: str,
    *,
    title: str | None = None,
    issue_number: int | None = None,
    metadata_only: bool = False,
    skip_issue: bool = False,
    skip_pdf: bool = False,
    dry_run: bool = False,
) -> None:
    old_slug = old_slug.strip().removesuffix(".md")
    new_slug = new_slug.strip().removesuffix(".md")
    if old_slug == new_slug:
        raise SystemExit("Old and new slug are the same.")

    validate_slug(old_slug)
    validate_slug(new_slug)
    resolved_issue = resolve_issue_number(old_slug, issue_number, new_slug)

    if not metadata_only:
        rename_study_files(old_slug, new_slug, dry_run=dry_run)

    update_catalog_row(old_slug, new_slug, title, dry_run=dry_run)
    update_registry(old_slug, new_slug, title, resolved_issue, dry_run=dry_run)
    update_proposal_meta_file(old_slug, new_slug, title, resolved_issue, dry_run=dry_run)
    update_reference_paths(old_slug, new_slug, dry_run=dry_run)

    if resolved_issue and not skip_issue and not dry_run:
        update_github_issue(resolved_issue, new_slug, title)

    if not skip_pdf:
        regenerate_artifacts(new_slug, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename a study slug and sync metadata.")
    parser.add_argument("--from", dest="old_slug", required=True, help="Current slug")
    parser.add_argument("--to", dest="new_slug", required=True, help="New slug")
    parser.add_argument("--title", help="New display title (optional)")
    parser.add_argument("--issue", type=int, help="Proposal issue number (optional)")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Skip filesystem rename; sync registry, issue, and references only",
    )
    parser.add_argument("--skip-issue", action="store_true", help="Do not patch GitHub issue body")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF regeneration")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rename_study(
        args.old_slug,
        args.new_slug,
        title=args.title,
        issue_number=args.issue,
        metadata_only=args.metadata_only,
        skip_issue=args.skip_issue,
        skip_pdf=args.skip_pdf,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
