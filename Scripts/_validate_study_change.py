"""Read-only lifecycle validation inferred from changed paths and PR intent."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import PurePosixPath
import re
import subprocess

from _common import BASE, study_md
from _ci_study_pr import (changed_study_slugs, changed_markdown_slugs, detect_study_renames,
    verify_removal_metadata, verify_rename_metadata, run_reference_checks, references_changed, study_references_changed,
    gh_request, parse_body_field, registry_row_for_slug)
from _study_catalog import get_study_row, StudyStatus, parse_edited_on, verify_timestamp_sync
from _study_pdf_metadata import iter_pdf_study_rows
from _study_links import cross_study_section_errors


def infer_intent(body: str, paths: list[str], base: str) -> str | None:
    if re.search(r'^Target status:', body, re.M | re.I):
        return 'status-change'
    if re.search(r'^Operation:\s*delete-study', body, re.M | re.I):
        return 'study-update'
    if re.search(r'^Proposal issue:\s*#?\d+', body, re.M | re.I):
        return 'new-study'
    if any(len(PurePosixPath(p).parts) >= 3 and p.startswith(('Studies/', 'Applications/')) for p in paths):
        return 'study-update'
    return None


def old_text(base: str, path: str) -> str | None:
    result = subprocess.run(['git', 'show', f'{base}:{path}'], cwd=BASE, capture_output=True, text=True, encoding='utf-8')
    return result.stdout if result.returncode == 0 else None


def validate(base: str, body: str = '', *, check_approval: bool = True) -> None:
    renames = {new: old for old, new in detect_study_renames(base)}
    for new, old in renames.items():
        located = get_study_row(new)
        verify_rename_metadata(old, new, located[0].title if located else None)
    canonical = set(changed_markdown_slugs(base))
    base_public = set()
    for family in ['topical','formal','applied']:
        previous = old_text(base,f'Studies/catalog-{family}.json')
        if previous:
            base_public.update(row['slug'] for row in json.loads(previous) if row['status'] in {'draft','released'})
    published = {row.slug for row in iter_pdf_study_rows() if row.status in {StudyStatus.DRAFT,StudyStatus.RELEASED}}
    errors = []
    for slug in sorted(set(changed_study_slugs(base)) | published):
        located = get_study_row(slug)
        if located is None:
            verify_removal_metadata(slug)
            continue
        row, _ = located
        md = study_md(slug)
        if row.status == StudyStatus.ONGOING:
            if slug in canonical and md.exists():
                errors.append(f'{slug}: Planned source changed; prepare its first draft before review.')
            continue
        errors.extend(verify_timestamp_sync(slug))
        if slug in canonical and md.exists():
            current = md.read_text(encoding='utf-8')
            old = old_text(base, md.relative_to(BASE).as_posix())
            if old and old != current and parse_edited_on(old) == parse_edited_on(current):
                errors.append(f'{slug}: changed canonical content requires a new Edited on timestamp.')
        if check_approval and slug not in renames and slug not in base_public:
            issue = parse_body_field(body, r'^Proposal issue:\s*#?(\d+)')
            if not issue:
                errors.append(f'{slug}: first draft requires Proposal issue: #N in the PR body.')
            else:
                registered = registry_row_for_slug(slug)
                if not registered or str(registered.get('issueNumber')) != issue:
                    errors.append(f'{slug}: linked approval does not match the registered proposal.')
                proposal = gh_request(f'/repos/{os.environ["GITHUB_REPOSITORY"]}/issues/{issue}')
                if proposal.get('state') != 'open' or 'proposal-approved' not in {label['name'] for label in proposal.get('labels', [])}:
                    errors.append(f'{slug}: proposal #{issue} must be open and approved.')
    errors.extend(cross_study_section_errors(list(canonical)))
    target = parse_body_field(body, r'^Target status:\s*(\w+)')
    if target:
        slug = parse_body_field(body, r'^Study slug:\s*([A-Za-z0-9-]+)')
        located = get_study_row(slug or '')
        if not located or target.lower() not in {'draft', 'released'} or located[0].status.value != target.lower():
            errors.append('Prepare the requested status change before review; catalog does not match Target status.')
    if errors:
        raise ValueError('\n'.join(errors))
    if references_changed(base):
        run_reference_checks(full_repo=True)
    else:
        for slug in canonical:
            if study_references_changed(base, slug):
                run_reference_checks(study=slug)
    print('Lifecycle metadata, timestamps, removals and section links verified without writes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', required=True)
    parser.add_argument('--body-file')
    args = parser.parse_args()
    event = json.loads(open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8').read()) if os.environ.get('GITHUB_EVENT_PATH') else {}
    body = open(args.body_file, encoding='utf-8').read() if args.body_file else (event.get('pull_request', {}).get('body') or '')
    validate(args.base_ref, body)
