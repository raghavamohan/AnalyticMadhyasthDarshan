"""Remove selected companions and their owned outputs while preserving the study.

Usage: python Scripts/_remove_study_companions.py <Slug> <Note.md> <Deck.pptx> --dry-run
Repeat with --yes to apply, then run _finalize_study_artifacts.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess

from _common import BASE, validate_study_slug, write_text_lf


def previous_manifests(base: str | None, root: Path) -> dict[str, dict]:
    if not base:
        return {}
    result = {}
    for name in ('presentation-pipeline.json', 'companion-pipeline.json'):
        output = subprocess.run(['git', 'show', f'{base}:Scripts/{name}'], cwd=root,
                                capture_output=True, check=True)
        result[name] = json.loads(output.stdout)
    return result


def remove_selected(slug: str, names: list[str], *, root: Path = BASE,
                    previous: dict[str, dict] | None = None, dry_run: bool = False) -> list[str]:
    """Plan all paths first, then unlink files only; never remove a directory."""
    validate_study_slug(slug)
    root = root.resolve()
    parents = [root / collection / slug for collection in ('Studies', 'Applications')
               if (root / collection / slug / f'{slug}.md').is_file()]
    if len(parents) != 1:
        raise ValueError(f'{slug}: companion removal requires one surviving canonical study source')
    parent = parents[0]
    if parent.is_symlink() or not parent.resolve().is_relative_to(root):
        raise ValueError('Study directory must be a real directory inside the repository')
    prefix = parent.relative_to(root).as_posix()
    protected = {f'{slug}{suffix}'.casefold() for suffix in ('.md', '.html', '.pdf')}
    files: set[str] = set()

    def include(name: str, suffixes: set[str]) -> None:
        path = PurePosixPath(name)
        target = root / name
        if (len(path.parts) != 3 or str(path.parent) != prefix or '\\' in name or ':' in name
                or path.suffix.lower() not in suffixes or path.name.casefold() in protected
                or target.is_symlink() or not target.resolve().is_relative_to(parent.resolve())
                or not parent.resolve().is_relative_to(root) or (target.exists() and not target.is_file())):
            raise ValueError(f'Companion deletion cannot touch this path: {name}')
        files.add(name)

    selected = set()
    for name in names:
        path = PurePosixPath(name)
        if len(path.parts) != 1 or path.name != name or '\\' in name or ':' in name or path.suffix.lower() not in {'.md', '.pptx'}:
            raise ValueError(f'Choose a companion Markdown/PPTX filename, not a path: {name}')
        full = f'{prefix}/{name}'
        include(full, {'.md', '.pptx'})
        selected.add(full)
    if not selected:
        raise ValueError('Select at least one companion')

    current = {}
    for name, field in (('presentation-pipeline.json', 'decks'), ('companion-pipeline.json', 'companions')):
        current[name] = json.loads((root / 'Scripts' / name).read_bytes())
        if not isinstance(current[name].get(field), list):
            raise ValueError(f'{name}: missing {field} list')
    previous = previous or {}
    decks = current['presentation-pipeline.json']['decks'] + previous.get('presentation-pipeline.json', {}).get('decks', [])
    mappings = current['companion-pipeline.json']['companions'] + previous.get('companion-pipeline.json', {}).get('companions', [])
    removed_decks = set()
    for name in selected:
        if name.lower().endswith('.pptx'):
            specs = [item for item in decks if item['source'] == name]
            if not specs:
                raise ValueError(f'{name}: deck registration is missing; use --base-ref for a partial deletion')
            for item in specs:
                removed_decks.add(item['id'])
                include(item['slidesPdf'], {'.pdf'})
                include(item['notesPdf'], {'.pdf'})
    removed_companions = set()
    for item in mappings:
        if item['deck'] in removed_decks or item['markdown'] in selected:
            name = item['markdown']
            removed_companions.add(name)
            for suffix in ('.md', '.html', '.pdf', '.docx', '.notes.json'):
                include(str(PurePosixPath(name).with_suffix(suffix)), {'.md', '.html', '.pdf', '.docx', '.json'})
    for name in selected:
        if name.lower().endswith('.md'):
            for suffix in ('.html', '.pdf'):
                include(str(PurePosixPath(name).with_suffix(suffix)), {'.html', '.pdf'})

    # No recursive delete, glob expansion, catalog/status/proposal edit or asset
    # garbage collection. Figures may still be consumed by surviving documents.
    result = sorted(files)
    for name in result:
        print(f"{'Would remove' if dry_run else 'Remove'} {name}")
    if dry_run:
        return result
    for name in result:
        (root / name).unlink(missing_ok=True)
    for manifest, field, keep in (
        ('presentation-pipeline.json', 'decks', lambda item: item['source'] not in selected),
        ('companion-pipeline.json', 'companions', lambda item: item['markdown'] not in removed_companions),
    ):
        data = current[manifest]
        kept = [item for item in data[field] if keep(item)]
        if kept != data[field]:
            data[field] = kept
            write_text_lf(root / 'Scripts' / manifest, json.dumps(data, indent=2) + '\n')
    return result


def prepare_deleted(changes: list[tuple[str, str]], base: str, *, root: Path = BASE) -> None:
    """Apply the same scoped cleanup to source deletions from portal/local PRs."""
    groups: dict[str, list[str]] = {}
    # Authored relocations keep their stable deck identity. Do not treat the
    # old path as retirement and delete the newly relocated ownership chain.
    previous = previous_manifests(base, root) if any(s == 'D' for s, _ in changes) else {}
    relocated = set()
    for manifest, field, identity, source in (
        ('presentation-pipeline.json', 'decks', 'id', 'source'),
        ('companion-pipeline.json', 'companions', 'deck', 'markdown'),
    ):
        if manifest not in previous:
            continue
        current = json.loads((root / 'Scripts' / manifest).read_bytes())
        by_id = {row[identity]: row[source] for row in current[field]}
        for old in previous[manifest][field]:
            new = by_id.get(old[identity])
            if new and new != old[source] and (root / new).is_file():
                relocated.add(old[source])
    for status, name in changes:
        path = PurePosixPath(name)
        if (status == 'D' and name not in relocated and len(path.parts) == 3 and path.parts[0] in {'Studies', 'Applications'}
                and (path.suffix == '.pptx' or (path.suffix == '.md' and path.stem != path.parts[1]))
                and (root / path.parent / f'{path.parts[1]}.md').is_file()
                and not (root / path).exists()):
            groups.setdefault(path.parts[1], []).append(path.name)
    if groups:
        for slug, names in groups.items():
            remove_selected(slug, names, root=root, previous=previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('names', nargs='+')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--yes', action='store_true')
    parser.add_argument('--base-ref', help='Recover registrations from this commit after a partial deletion')
    args = parser.parse_args()
    remove_selected(args.slug, args.names, previous=previous_manifests(args.base_ref, BASE), dry_run=args.dry_run)


if __name__ == '__main__':
    main()
