"""Restore retired study/companion sources from an ancestor of master.

Restoration preserves historical authoring bytes and metadata. Render the
restored sources with the current toolchain, then run the shared finalizer.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

from _common import BASE, validate_study_slug, write_text_lf


def git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)


def historical_row(slug: str, revision: str, base: str, *, root: Path = BASE) -> tuple[str, dict]:
    validate_study_slug(slug)
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Restore from must be a full 40-character commit SHA')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', revision, base], cwd=root, capture_output=True).returncode:
        raise ValueError('Restoration requires a commit already in the base branch history')
    matches = []
    for family in ('topical', 'formal', 'applied'):
        rows = json.loads(git_bytes(root, 'show', f'{revision}:Studies/catalog-{family}.json'))
        matches.extend((family, row) for row in rows if row.get('slug') == slug and row.get('status') in {'draft', 'released'})
    if len(matches) != 1:
        raise ValueError('Restore only a previously registered Draft/Released study')
    return matches[0]


def restoration_errors(slug: str, body: str, base: str, *, root: Path = BASE) -> list[str]:
    match = re.search(r'^Restore from:\s*([a-f0-9]{40})\s*$', body, re.M)
    if not match:
        return ['Restoration requires Restore from: <full merged commit SHA>.']
    try:
        family, old = historical_row(slug, match[1], base, root=root)
        prefix = 'Applications' if family == 'applied' else 'Studies'
        path = f'{prefix}/{slug}/{slug}.md'
        if (root / path).read_bytes() != git_bytes(root, 'show', f'{match[1]}:{path}'):
            return [f'{slug}: restore the historical canonical source unchanged; revise it in a subsequent update.']
        rows = json.loads((root / f'Studies/catalog-{family}.json').read_bytes())
        current = next((row for row in rows if row.get('slug') == slug), None)
        if current != old:
            return [f'{slug}: restored catalog metadata must match the selected historical revision.']
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        return [f'{slug}: invalid restoration: {error}']
    return []


def restore(slug: str, revision: str, *, base: str = 'origin/master', names: list[str] | None = None,
            root: Path = BASE, dry_run: bool = False) -> list[str]:
    root = root.resolve()
    family, row = historical_row(slug, revision, base, root=root)
    collection = 'Applications' if family == 'applied' else 'Studies'
    prefix = f'{collection}/{slug}'
    parent = root / prefix
    if names:
        from _relocate_study_companion import parent_path, companion_name
        if parent_path(root, slug) != parent:
            raise ValueError('Restore companions only into their original surviving parent')
        for name in names:
            companion_name(name, slug)
    elif any((root / p / slug).exists() for p in ('Studies', 'Applications')):
        raise ValueError('Study path already exists; select companions or use the update workflow')
    current_catalogs = {f: json.loads((root / f'Studies/catalog-{f}.json').read_bytes())
                        for f in ('topical', 'formal', 'applied')}
    if not names and any(r['slug'] == slug for rows in current_catalogs.values() for r in rows):
        raise ValueError('Study is already registered')
    all_files = {}
    for record in git_bytes(root, 'ls-tree', '-r', '-z', revision, '--', prefix).split(b'\0'):
        if not record:
            continue
        info, raw_name = record.split(b'\t', 1)
        name = raw_name.decode('utf-8')
        path = PurePosixPath(name)
        if info.split()[0] not in {b'100644', b'100755'} or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError(f'Unsafe historical entry: {name}')
        if not name.startswith(prefix + '/') or not (root / name).resolve().is_relative_to(parent.resolve()):
            raise ValueError(f'Historical path escapes the study: {name}')
        if path.suffix != '.pdf':
            all_files[name] = git_bytes(root, 'show', f'{revision}:{name}')
    historical = {name: json.loads(git_bytes(root, 'show', f'{revision}:Scripts/{name}'))
                  for name in ('presentation-pipeline.json', 'companion-pipeline.json')}
    selected = {f'{prefix}/{name}' for name in names} if names else set(all_files)
    if selected - all_files.keys():
        raise ValueError('One or more selected sources did not exist at that revision')
    decks = [d for d in historical['presentation-pipeline.json']['decks'] if d['source'] in selected]
    companions = [c for c in historical['companion-pipeline.json']['companions']
                  if c['markdown'] in selected or c['deck'] in {d['id'] for d in decks}]
    selected.update(c['markdown'] for c in companions)
    if names:
        for name in list(selected):
            if name.endswith('.md'):
                selected.update(str(PurePosixPath(name).with_suffix(s)) for s in ('.html', '.docx', '.notes.json')
                                if str(PurePosixPath(name).with_suffix(s)) in all_files)
        # Include locally embedded resources transitively. Shared files that
        # changed since retirement cause a conflict rather than being replaced.
        from _artifact_graph import local_path, parsed_links
        pending = list(selected)
        while pending:
            name = pending.pop()
            if not name.endswith(('.md', '.svg', '.css', '.html')):
                continue
            text = all_files.get(name, b'').decode('utf-8')
            embedded, _ = parsed_links(text)
            if name.endswith(('.svg', '.css')):
                embedded = set(embedded) | set(re.findall(r'''(?:href|src)=["']([^"']+)''', text))
            for link in embedded:
                resolved = local_path(root / name, link, root)
                if resolved is None:
                    continue
                target = resolved.relative_to(root).as_posix()
                if target in all_files and target not in selected and PurePosixPath(target).suffix in {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.css'}:
                    selected.add(target)
                    pending.append(target)
    files = {name: all_files[name] for name in selected}
    for name, content in files.items():
        target = root / name
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.read_bytes() != content)):
            raise ValueError(f'Restoration conflicts with an existing file: {name}')
        if names and name in {f'{prefix}/{selected_name}' for selected_name in names} and target.exists():
            raise ValueError(f'Companion is already present: {name}')
    manifests = {}
    for name, field, additions, key in (
        ('presentation-pipeline.json', 'decks', decks, 'id'),
        ('companion-pipeline.json', 'companions', companions, 'deck'),
    ):
        data = json.loads((root / 'Scripts' / name).read_bytes())
        for item in additions:
            old = next((r for r in data[field] if r[key] == item[key]), None)
            if old and old != item:
                raise ValueError(f'Restoration conflicts with active ownership: {item[key]}')
            if not old:
                data[field].append(item)
        manifests[name] = data
    from _companion_lifecycle import output_contract
    _, required_sources = output_contract(manifests)
    if any(name not in files and not (root / name).is_file() for name in required_sources):
        raise ValueError('Restore the owning deck together with its presenter companion')
    registry_path = root / 'Studies/proposal-registry.json'
    registry = json.loads(registry_path.read_bytes())
    reference_updates = {}
    if not names:
        old_registry = json.loads(git_bytes(root, 'show', f'{revision}:Studies/proposal-registry.json'))
        entry = next((r for r in old_registry['proposals'] if r['slug'] == slug), None)
        if entry:
            if any(r['slug'] == slug or (entry.get('issueNumber') and r.get('issueNumber') == entry['issueNumber']) for r in registry['proposals']):
                raise ValueError('Historical proposal ownership conflicts with a current study')
            registry['proposals'].append(entry)
        # Preflight reference metadata before restoring any authoring files.
        for filename, marker in (('README.md', '<!-- /studies-catalog -->'), ('MANIFEST.md', '\n## By tag')):
            path = root / 'References' / filename
            old = git_bytes(root, 'show', f'{revision}:References/{filename}').decode('utf-8')
            block = re.search(r'^\| \[' + re.escape(slug) + r'\.pdf\][^\n]*\n(?:\|\s*\|[^\n]*\n)*', old, re.M)
            current = path.read_text(encoding='utf-8')
            if block and f'[{slug}.pdf]' not in current:
                if marker not in current:
                    raise ValueError(f'Missing reference catalog marker in {filename}')
                reference_updates[path] = current.replace(marker, block[0] + marker, 1)
    for name in sorted(files):
        print(f'Restore: {name}')
    if dry_run:
        return sorted(files)
    for name, content in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for name, data in manifests.items():
        write_text_lf(root / 'Scripts' / name, json.dumps(data, indent=2) + '\n')
    if not names:
        write_text_lf(registry_path, json.dumps(registry, indent=2) + '\n')
        from _study_catalog import StudyTable, catalog_entry_to_row, load_catalog_rows, write_studies_catalog
        table = StudyTable(family)
        write_studies_catalog(load_catalog_rows(table) + [catalog_entry_to_row(row, table)], table, rebuild_discussion=[slug])
        for path, text in reference_updates.items():
            write_text_lf(path, text)
    print('Render restored sources with the current pipelines, then run _finalize_study_artifacts.py.')
    print(f'PR body: Operation: restore-study\nRestore from: {revision}' if not names else 'PR label: study-update')
    return sorted(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('--from-ref', required=True)
    parser.add_argument('--base-ref', default='origin/master')
    parser.add_argument('--companion', action='append')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    restore(args.slug, args.from_ref, base=args.base_ref, names=args.companion, dry_run=args.dry_run)
