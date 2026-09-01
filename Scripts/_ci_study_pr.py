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
from collections.abc import Callable
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from _common import BASE, STUDIES, slug_from_repo_relative_path, study_md, write_text_lf

from _verify_studies_index import collect_index_errors  # noqa: E402
from _check_references import run_checks, print_report  # noqa: E402
from _study_catalog import (  # noqa: E402
    StudyStatus,
    get_study_row,
    load_catalog_rows,
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


def normalize_pr_slug(value: str) -> str:
    """Return a bare catalog slug from a PR body field.

    Accepts optional ``.md`` suffix. Strips trailing notes that authors sometimes
    append on the same line (parentheticals, em dashes, commas), which otherwise
    break catalog lookup — e.g. ``The-Ontology-of-Coexistence (companion deck)``.
    """
    cleaned = value.strip().removesuffix(".md").strip()
    # Cut at the first space that begins a note, or at punctuation used as a note separator.
    cleaned = re.split(r"\s+[\(\[—–\-]|[;,]", cleaned, maxsplit=1)[0].strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", cleaned)
    if match:
        return match.group(1)
    return cleaned


def resolve_pr_body(pull_request: dict) -> str:
    """Prefer the live PR body from the API so body edits apply without a new commit.

    ``GITHUB_EVENT_PATH`` freezes the body from the triggering event; ``gh pr edit``
    alone does not re-run this workflow (``edited`` is intentionally omitted), and
    ``gh run rerun`` reuses the stale event payload. Fetching the current body makes
    a corrected ``Study slug:`` line take effect on the next pipeline run.
    """
    number = pull_request.get("number")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if number and repo and os.environ.get("GITHUB_TOKEN"):
        try:
            data = gh_request(f"/repos/{repo}/pulls/{number}")
            body = data.get("body")
            if body is not None:
                return body
        except SystemExit:
            pass
    return pull_request.get("body") or ""


def parse_issue_form_section(body: str, heading: str) -> str | None:
    pattern = rf"###\s*{re.escape(heading)}\s*\r?\n+(.+?)(?=\r?\n###|\Z)"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


SCRIPTS = Path(__file__).resolve().parent


def run_reference_checks(*, study: str | None = None, full_repo: bool = False) -> None:
    """Run Scripts/_check_references.py; fail CI when references are broken."""
    target = None if full_repo else study
    report = run_checks(study=target, skip_pdf=False)
    if print_report(report, study=target) != 0:
        raise SystemExit("Reference checks failed. Run: python Scripts/_check_references.py")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=BASE,
        check=False,
    )
    return result.stdout


@lru_cache(maxsize=None)
def changed_paths(base_ref: str) -> tuple[tuple[str, str], ...]:
    """``((status, path), ...)`` for the PR range, read once per base ref.

    Renames are flattened to a ``D`` for the old path and an ``A`` for the new
    one so callers can treat every entry uniformly; ``detect_study_rename`` reads
    the raw ``R`` records separately.
    """
    entries: list[tuple[str, str]] = []
    for line in _git("diff", "--name-status", f"{base_ref}...HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            entries.append(("D", parts[1]))
            entries.append(("A", parts[2]))
        else:
            entries.append((status, parts[1]))
    return tuple(entries)


def references_changed(base_ref: str) -> bool:
    return any(path.startswith("References/") for _status, path in changed_paths(base_ref))


# Touching any of these changes how every PDF is rendered, so the study PDF has to
# be rebuilt even when the markdown itself is untouched.
PDF_PIPELINE_PATHS = (
    "Scripts/_convert_to_pdf.py",
    "Scripts/_html_to_pdf.js",
    "Scripts/_pdf_metadata.py",
    "Scripts/_regenerate_pdf.py",
    "Scripts/_study_catalog.py",
    "Scripts/package.json",
    "Scripts/package-lock.json",
)


def pdf_regeneration_reason(base_ref: str, slug: str) -> str | None:
    """Why ``slug``'s PDF needs rebuilding, or None when it can be skipped.

    A study-update PR often touches only companion files — a deck, research
    notes, figures that the study does not embed — and rebuilding the PDF then
    costs a full Puppeteer render and (before the output was made reproducible)
    pushed a fresh multi-megabyte blob for no change in content.
    """
    md_path = study_md(slug)
    if not md_path.with_suffix(".pdf").is_file():
        return "the PDF is missing"

    changed = changed_paths(base_ref)
    md_rel = md_path.relative_to(BASE).as_posix()
    study_dir = md_path.parent.relative_to(BASE).as_posix()

    for _status, path in changed:
        if path == md_rel:
            return "the study markdown changed"
        # Only figures inside the study's own directory can appear in its PDF.
        if path.startswith(f"{study_dir}/") and path.lower().endswith((".svg", ".png", ".jpg", ".jpeg")):
            return f"a figure changed ({path})"
        if path in PDF_PIPELINE_PATHS:
            return f"the PDF pipeline changed ({path})"
    return None


def only_generated_html_changed(base_ref: str, slug: str) -> bool:
    """Allow shared HTML regeneration to pass through ongoing placeholders.

    Ongoing studies are intentionally blocked for source or companion edits, but
    a shared reader/generator change may regenerate their tracked HTML alongside
    cataloged studies. Those HTML-only artifacts are not published by the
    catalog and do not represent a new study submission.
    """
    prefixes = (f"Studies/{slug}/", f"Applications/{slug}/")
    paths = [
        path
        for _status, path in changed_paths(base_ref)
        if path.startswith(prefixes)
    ]
    return bool(paths) and all(path.lower().endswith(".html") for path in paths)


def study_references_changed(base_ref: str, slug: str) -> bool:
    md_path = study_md(slug).relative_to(BASE).as_posix()
    diff = _git("diff", base_ref, "HEAD", "--", md_path)
    if not diff:
        return False
    return "../References/" in diff or "## References" in diff


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
    slugs: list[str] = []
    seen: set[str] = set()
    for _status, path in changed_paths(base_ref):
        slug = slug_from_repo_relative_path(Path(path))
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


STUDY_ROOTS = ("Studies", "Applications")


def slug_from_path_lexical(path: Path) -> str | None:
    """Slug from a repo-relative study path *without* requiring it on disk.

    ``_common.slug_from_repo_relative_path`` only resolves paths that still exist,
    which is right for "which studies did this PR touch" but wrong for rename
    detection: the old side of a rename has by definition been moved away, so it
    always resolved to None and no rename was ever detected.
    """
    parts = path.parts
    if len(parts) < 2 or parts[0] not in STUDY_ROOTS:
        return None
    return parts[1] or None


def detect_study_rename(base_ref: str) -> tuple[str, str] | None:
    # A git-detected rename is authoritative, so check the raw R records first.
    for line in _git("diff", "--name-status", f"{base_ref}...HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].startswith("R"):
            old_slug = slug_from_path_lexical(Path(parts[1]))
            new_slug = slug_from_path_lexical(Path(parts[2]))
            if old_slug and new_slug and old_slug != new_slug:
                return old_slug, new_slug

    # Otherwise infer it from exactly one slug disappearing and one appearing.
    removed_slugs: set[str] = set()
    added_slugs: set[str] = set()
    for status, path in changed_paths(base_ref):
        slug = slug_from_path_lexical(Path(path))
        if not slug:
            continue
        if status == "D":
            removed_slugs.add(slug)
        elif status.startswith("A"):
            added_slugs.add(slug)
    # Only a clean one-out/one-in pair is unambiguous; ignore slugs that appear on
    # both sides, which just means files were added and removed within one study.
    removed_only = removed_slugs - added_slugs
    added_only = added_slugs - removed_slugs
    if len(removed_only) == 1 and len(added_only) == 1:
        return removed_only.pop(), added_only.pop()
    return None


def registry_row_for_slug(slug: str) -> dict | None:
    registry_path = STUDIES / "proposal-registry.json"
    if not registry_path.is_file():
        return None
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    for row in data.get("proposals", []):
        if row.get("slug") == slug:
            return row
    return None


def study_was_removed(base_ref: str, slug: str) -> bool:
    """Whether the PR completely deletes one study tree.

    A removed study no longer resolves through ``get_study_row`` or
    ``slug_from_repo_relative_path``.  Recognize it lexically, but only when every
    changed path for that slug is a deletion and neither possible study directory
    remains on disk.  This keeps a misspelled PR-body slug from being accepted as
    a removal.
    """
    touched = [
        status
        for status, path in changed_paths(base_ref)
        if slug_from_path_lexical(Path(path)) == slug
    ]
    if not touched or any(status != "D" for status in touched):
        return False
    return not (STUDIES / slug).exists() and not (BASE / "Applications" / slug).exists()


def verify_removal_metadata(slug: str) -> None:
    """Reject a removal that leaves proposal metadata capable of recreating it."""
    errors: list[str] = []
    if registry_row_for_slug(slug):
        errors.append(
            f"proposal-registry.json still lists removed slug {slug}; remove its proposal entry."
        )
    if errors:
        raise SystemExit("Study removal verification failed:\n  - " + "\n  - ".join(errors))


def verify_rename_metadata(old_slug: str, new_slug: str) -> None:
    errors: list[str] = []
    if registry_row_for_slug(old_slug):
        errors.append(
            f"proposal-registry.json still lists old slug {old_slug}; run _rename_study.py metadata sync."
        )
    if not registry_row_for_slug(new_slug):
        errors.append(
            f"proposal-registry.json is missing new slug {new_slug}; run _rename_study.py metadata sync."
        )
    meta_path = STUDIES / new_slug / ".proposal-meta.json"
    applied_meta = BASE / "Applications" / new_slug / ".proposal-meta.json"
    if not meta_path.is_file() and not applied_meta.is_file():
        errors.append(f"Missing .proposal-meta.json under {new_slug}.")
    if errors:
        raise SystemExit("Rename metadata verification failed:\n  - " + "\n  - ".join(errors))


SLUG_PATTERNS = (r"^Study slug:\s*(.+)$", r"^Slug:\s*(.+)$")


def resolve_slug(
    body: str,
    base_ref: str | None = None,
    *,
    rename: tuple[str, str] | None = None,
    allow_changed: bool = False,
) -> str:
    """Resolve the target slug from the PR body, with optional fallbacks.

    All three PR types accept the same two body keys; they differ only in which
    fallbacks apply when the body omits them.
    """
    raw = parse_body_field(body, *SLUG_PATTERNS)
    if raw:
        return normalize_pr_slug(raw)
    if rename:
        return rename[1]
    if allow_changed and base_ref is not None:
        changed = changed_study_slugs(base_ref)
        if len(changed) == 1:
            return changed[0]
    hint = (
        " or change exactly one Studies/<Slug>/<Slug>.md "
        "(or Applications/<Slug>/<Slug>.md) file"
        if allow_changed
        else ""
    )
    raise SystemExit(
        "Set `Study slug: <Slug>` on its own line (bare catalog slug only — "
        f"no parenthetical notes){hint}."
    )


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
    write_studies_catalog(rows, table, rebuild_discussion=False, rebuild_feedback_template=False)


# No PDF text cache is built here. Extracting the page text of a study's cited
# references took roughly ten of every twelve minutes of this job, and nothing in
# the run ever read the result: the cache feeds quote verification, which CI does
# not run, while _check_references.py only resolves link targets. Scripts/_pdf_cache/
# is gitignored and outside the commit-artifacts paths, so the runner discarded it.
# Authors still build it locally, on demand, through the tool that needs it:
# `python Scripts/_quote_tool.py verify --study <Slug>`, which AGENTS.md §7 already
# requires before pushing.


def mark_registry_in_catalog(slug: str) -> None:
    """After first draft merge, stop treating the slug as pre-catalog in proposal-registry.json."""
    registry_path = STUDIES / "proposal-registry.json"
    if not registry_path.is_file():
        return
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    changed = False
    for row in data.get("proposals", []):
        if row.get("slug") == slug and row.get("phase") == "pre-catalog":
            row["phase"] = "catalog-draft"
            changed = True
    if changed:
        write_text_lf(registry_path, json.dumps(data, indent=2) + "\n")
        print(f"Updated proposal-registry.json: {slug} is now catalog-draft.")


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

    slug = resolve_slug(body, base_ref, allow_changed=True)
    md_path = study_md(slug)
    if not md_path.exists():
        raise SystemExit(f"Expected study markdown at {md_path}")

    located = get_study_row(slug)
    if located is not None:
        row, _table = located
        if row.status != StudyStatus.ONGOING:
            print(f"{slug} is already registered; running study-update pipeline.")
            handle_study_update(body, base_ref)
            return

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
    mark_registry_in_catalog(slug)
    # A brand-new study gets a full audit regardless of what the diff touched;
    # study-update only re-checks when references actually changed.
    if references_changed(base_ref):
        run_reference_checks(full_repo=True)
    else:
        run_reference_checks(study=slug)


def handle_study_update(body: str, base_ref: str) -> None:
    rename = detect_study_rename(base_ref)
    if rename:
        old_slug, new_slug = rename
        primary_slug = resolve_slug(body, base_ref, rename=rename, allow_changed=True)
        if primary_slug != new_slug:
            raise SystemExit(
                f"Directory rename {old_slug} -> {new_slug} requires "
                f"`Study slug: {new_slug}` in the PR body."
            )
        print(f"Detected study rename: {old_slug} -> {new_slug}")
        command = [
            sys.executable,
            str(SCRIPTS / "_rename_study.py"),
            "--from",
            old_slug,
            "--to",
            new_slug,
            "--metadata-only",
            "--skip-pdf",
        ]
        print("Running:", " ".join(command))
        subprocess.run(command, check=True, cwd=BASE)
        verify_rename_metadata(old_slug, new_slug)

    changed_slugs = changed_study_slugs(base_ref) if base_ref else []
    body_slug = None
    raw = parse_body_field(body, *SLUG_PATTERNS)
    if raw:
        body_slug = normalize_pr_slug(raw)

    target_slugs: list[str] = []
    if changed_slugs:
        target_slugs = list(changed_slugs)
        if body_slug and body_slug not in target_slugs:
            target_slugs.append(body_slug)
    elif body_slug:
        target_slugs = [body_slug]
    elif rename:
        target_slugs = [rename[1]]
    else:
        target_slugs = [resolve_slug(body, base_ref, rename=rename, allow_changed=True)]

    print(f"Processing study update for {len(target_slugs)} study slug(s): {', '.join(target_slugs)}")

    for slug in target_slugs:
        located = get_study_row(slug)
        if located is None:
            if study_was_removed(base_ref, slug):
                verify_removal_metadata(slug)
                print(f"Validated complete study removal: {slug}")
                continue
            raise SystemExit(f"Study not found in catalog: {slug}")

        row, _table = located
        if row.status == StudyStatus.ONGOING:
            if base_ref and only_generated_html_changed(base_ref, slug):
                print(
                    f"Skipping {slug}: only shared/generated HTML artifacts changed; "
                    "ongoing source remains protected."
                )
                continue
            raise SystemExit(
                f"{slug} is a pre-catalog proposal placeholder. Submit a new-study PR to register the draft."
            )

        sync_catalog_timestamp_from_md(slug)
        located = get_study_row(slug)
        if located is None:
            raise SystemExit(f"Study not found after catalog sync: {slug}")
        row, _table = located

        md_path = study_md(slug)
        reason = pdf_regeneration_reason(base_ref, slug)
        if reason:
            print(f"Regenerating PDF for {slug} ({row.status.value}): {reason}")
            regenerate_pdf(md_path, row.status)
        else:
            print(
                f"Skipping PDF regeneration for {slug}: no change to the markdown, "
                "its figures, or the PDF pipeline."
            )

        errors = verify_timestamp_sync(slug)
        if errors:
            raise SystemExit(f"Timestamp verification failed for {slug}:\n  - " + "\n  - ".join(errors))

    if references_changed(base_ref):
        run_reference_checks(full_repo=True)
    else:
        for slug in target_slugs:
            if study_references_changed(base_ref, slug):
                run_reference_checks(study=slug)


def handle_status_change(body: str, base_ref: str) -> None:  # noqa: ARG001 - uniform signature
    slug = resolve_slug(body)
    target = parse_body_field(body, r"^Target status:\s*(\w+)")
    if not target:
        raise SystemExit("PR body must include `Target status: draft` or `released`.")

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


def verify_studies_index() -> None:
    # collect_index_errors() is shared with _verify_studies_index.py, which the
    # master-push check runs. Calling a hand-picked subset of the verifiers here
    # is exactly what let a stale Studies/index.html pass a study PR and turn
    # master red only after the merge (#343).
    errors = collect_index_errors()
    if errors:
        raise SystemExit(
            "Studies index verification failed:\n  - " + "\n  - ".join(errors)
        )


# Label → handler. active_pr_label() guarantees the key exists, and adding a
# fourth PR type means one entry here plus a body template.
HANDLERS: dict[str, Callable[[str, str], None]] = {
    "new-study": handle_new_study,
    "study-update": handle_study_update,
    "status-change": handle_status_change,
}
assert set(HANDLERS) == set(PR_LABELS), "HANDLERS must cover exactly PR_LABELS"


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

    body = resolve_pr_body(pull_request)
    print(f"Study PR type: {label}")

    HANDLERS[label](body, args.base_ref)

    verify_studies_index()
    print("Study PR pipeline completed successfully.")


if __name__ == "__main__":
    main()
