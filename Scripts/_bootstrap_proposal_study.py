"""Bootstrap a pre-catalog study directory after proposal approval.

Creates Studies/<Slug>/<Slug>.md (proposal stub), .proposal-meta.json, HTML, and PDF.
Does not register the study in the public catalog.

Usage:
  python Scripts/_bootstrap_proposal_study.py --issue 42
  python Scripts/_bootstrap_proposal_study.py --slug My-Study --title "My Study" \\
      --category Ontology --description "One line" --summary "Scope..." \\
      --issue 42 --submitter raghavamohan
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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from _common import STUDIES, study_dir, study_md
from _study_catalog import format_edited_on_md, now_ist, slug_to_title, title_to_slug

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
REGISTRY_PATH = STUDIES / "proposal-registry.json"
IST = ZoneInfo("Asia/Kolkata")

GITHUB_REPO = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan"
AUTHOR_BLOCK = (
    f"**Author:** [AnalyticMadhyasthDarshan.org]({GITHUB_REPO}) — a group of people "
    f"studying Madhyasth Darshan philosophy. Source repository: "
    f"[raghavamohan/AnalyticMadhyasthDarshan]({GITHUB_REPO})."
)

ISSUE_FORM_HEADINGS = {
    "slug": "Slug",
    "title": "Proposed title",
    "category": "Category",
    "description": "One-line description",
    "summary": "Study summary",
    "formal": "Catalog table",
    "submitter": "Portal submitter",
}


@dataclass
class ProposalFields:
    slug: str
    title: str
    category: str
    description: str
    summary: str
    formal: bool
    submitter: str
    issue_number: int | None = None


def gh_request(path: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set.")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "bootstrap-proposal-study",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"GitHub API {path} failed ({exc.code}): {body}") from exc


def parse_issue_form_section(body: str, heading: str) -> str | None:
    pattern = rf"###\s*{re.escape(heading)}\s*\r?\n+(.+?)(?=\r?\n###|\Z)"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def proposed_title_from_issue_title(title: str) -> str | None:
    match = re.match(r"^Study proposal:\s*(.+)$", title.strip(), re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_submitter_login(body: str) -> str | None:
    section = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["submitter"]) or ""
    match = re.search(r"@([A-Za-z0-9-]+)", section)
    return match.group(1) if match else None


def fields_from_issue(issue_number: int) -> ProposalFields:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is not set.")
    issue = gh_request(f"/repos/{repo}/issues/{issue_number}")
    body = issue.get("body") or ""
    title = proposed_title_from_issue_title(issue.get("title") or "")
    if not title:
        title = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["title"])
    if not title:
        raise SystemExit(f"Issue #{issue_number} is missing a proposed title.")

    slug = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["slug"])
    if slug:
        slug = slug.strip().removesuffix(".md")
    else:
        slug = title_to_slug(title)

    category = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["category"])
    description = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["description"])
    summary = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["summary"])
    formal_block = parse_issue_form_section(body, ISSUE_FORM_HEADINGS["formal"]) or ""
    formal = "- [x]" in formal_block
    submitter = parse_submitter_login(body) or issue.get("user", {}).get("login") or ""

    if not category:
        raise SystemExit(f"Issue #{issue_number} is missing a Category field.")
    if not description:
        raise SystemExit(f"Issue #{issue_number} is missing a One-line description field.")
    if not summary:
        summary = description

    return ProposalFields(
        slug=slug,
        title=title,
        category=category,
        description=description,
        summary=summary,
        formal=formal,
        submitter=submitter,
        issue_number=issue_number,
    )


def build_proposal_stub_markdown(fields: ProposalFields, edited_at: datetime) -> str:
    return f"""# {fields.title}

{AUTHOR_BLOCK}

{format_edited_on_md(edited_at)}

{fields.description}

## Study proposal

{fields.summary}

> This directory holds an **approved study proposal** (pre-catalog). It is not listed on
> the public studies index until a maintainer merges your first **draft** pull request.
> Submit the full study via [My Submissions](https://analyticmadhyasthdarshan.org/Studies/submit.html).

## References

- *(Add references when you submit the full draft — link to files under `../References/` where available.)*
"""


def proposal_meta_path(slug: str) -> Path:
    return study_dir(slug) / ".proposal-meta.json"


def write_proposal_meta(fields: ProposalFields, edited_at: datetime) -> None:
    meta = {
        "slug": fields.slug,
        "title": fields.title,
        "category": fields.category,
        "description": fields.description,
        "formal": fields.formal,
        "proposalIssue": fields.issue_number,
        "submitter": fields.submitter,
        "phase": "pre-catalog",
        "approvedAt": format_edited_on_md(edited_at).replace("**Edited on:** ", ""),
    }
    path = proposal_meta_path(fields.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def regenerate_proposal_artifacts(md_path: Path) -> None:
    from _convert_to_pdf import convert_to_html
    from _verify_study_svgs import verify_study_svgs

    md_path = md_path.resolve()
    verify_study_svgs(md_path)
    html_path = md_path.with_suffix(".html")
    build_pdf_path = md_path.with_name(f"{md_path.stem}.build.pdf")
    convert_to_html(md_path, is_draft=True, include_web_chrome=True)
    subprocess.run(
        [
            "node",
            str(SCRIPTS / "_html_to_pdf.js"),
            str(html_path),
            "Draft",
            str(build_pdf_path),
        ],
        check=True,
        cwd=BASE,
    )
    pdf_path = md_path.with_suffix(".pdf")
    build_pdf_path.replace(pdf_path)


def upsert_registry_entry(fields: ProposalFields) -> None:
    entries: list[dict] = []
    if REGISTRY_PATH.is_file():
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        entries = list(data.get("proposals") or [])
    filtered = [row for row in entries if row.get("slug") != fields.slug]
    filtered.append(
        {
            "slug": fields.slug,
            "title": fields.title,
            "issueNumber": fields.issue_number,
            "submitter": fields.submitter,
            "category": fields.category,
            "description": fields.description,
            "formal": fields.formal,
            "phase": "pre-catalog",
        }
    )
    filtered.sort(key=lambda row: row.get("slug", ""))
    REGISTRY_PATH.write_text(
        json.dumps({"version": 1, "proposals": filtered}, indent=2) + "\n",
        encoding="utf-8",
    )


def issue_body_with_slug(body: str, slug: str) -> str:
    if parse_issue_form_section(body, ISSUE_FORM_HEADINGS["slug"]):
        return body
    slug_block = f"### Slug\n\n{slug}\n\n"
    marker = "### Proposed title"
    if marker in body:
        return body.replace(marker, slug_block + marker, 1)
    return slug_block + body


def bootstrap_proposal(
    fields: ProposalFields,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    dest_dir = study_dir(fields.slug)
    dest_md = study_md(fields.slug)
    if dest_md.exists() and not force:
        existing = dest_md.read_text(encoding="utf-8")
        if "**Status:**" in existing and "Study proposal" not in existing:
            print(f"{fields.slug} already has a full study markdown; skipping bootstrap.")
            return

    edited_at = now_ist()
    stub = build_proposal_stub_markdown(fields, edited_at)
    if dry_run:
        print(f"Would write {dest_md}")
        print(stub[:400], "...")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_md.write_text(stub, encoding="utf-8")
    write_proposal_meta(fields, edited_at)
    regenerate_proposal_artifacts(dest_md)
    upsert_registry_entry(fields)
    print(f"Bootstrapped pre-catalog proposal at {dest_dir}")


def update_issue_slug(issue_number: int, slug: str) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return
    issue = gh_request(f"/repos/{repo}/issues/{issue_number}")
    body = issue.get("body") or ""
    if parse_issue_form_section(body, ISSUE_FORM_HEADINGS["slug"]) == slug:
        return
    updated = issue_body_with_slug(body, slug)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return
    payload = json.dumps({"body": updated}).encode()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "bootstrap-proposal-study",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request):
        pass
    print(f"Updated issue #{issue_number} with Slug: {slug}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a pre-catalog approved proposal study.")
    parser.add_argument("--issue", type=int, help="GitHub proposal issue number")
    parser.add_argument("--slug")
    parser.add_argument("--title")
    parser.add_argument("--category")
    parser.add_argument("--description")
    parser.add_argument("--summary")
    parser.add_argument("--submitter", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-issue-update", action="store_true")
    args = parser.parse_args()

    if args.issue:
        fields = fields_from_issue(args.issue)
    else:
        if not all([args.slug, args.title, args.category, args.description]):
            raise SystemExit("Provide --issue or --slug, --title, --category, and --description.")
        fields = ProposalFields(
            slug=args.slug.strip().removesuffix(".md"),
            title=args.title.strip(),
            category=args.category.strip(),
            description=args.description.strip(),
            summary=(args.summary or args.description).strip(),
            formal=args.formal,
            submitter=args.submitter.strip(),
            issue_number=None,
        )

    if args.issue and not args.skip_issue_update:
        update_issue_slug(args.issue, fields.slug)

    bootstrap_proposal(fields, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
