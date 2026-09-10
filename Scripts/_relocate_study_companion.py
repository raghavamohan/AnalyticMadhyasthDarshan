"""Rename or move a companion and its owned outputs, preserving both studies."""
from __future__ import annotations

import argparse
import json
import posixpath
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit

from _common import BASE, validate_study_slug, write_text_lf


def parent_path(root: Path, slug: str) -> Path:
    validate_study_slug(slug)
    matches = [root / family / slug for family in ('Studies', 'Applications')
               if (root / family / slug / f'{slug}.md').is_file()]
    if len(matches) != 1 or matches[0].is_symlink() or not matches[0].resolve().is_relative_to(root.resolve()):
        raise ValueError(f'{slug}: expected one canonical parent inside the repository')
    return matches[0]


def companion_name(name: str, slug: str) -> None:
    if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*\.(md|pptx)', name)
            or name.casefold() == f'{slug}.md'.casefold()):
        raise ValueError('Choose a companion filename, never the canonical study or a path')
    if name.endswith('.md') and not name.startswith(('Technical-Note-', 'Research-Note-', 'Presenters-Companion-')):
        raise ValueError('Use a technical/research note or presenter-companion filename')


def rewrite_links(text: str, source: PurePosixPath, destination: PurePosixPath,
                  mapping: dict[str, str]) -> str:
    def url(value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme or parts.netloc or not parts.path:
            return value
        resolved = posixpath.normpath(posixpath.join(str(source.parent), unquote(parts.path)))
        if parts.path.startswith('/'):
            resolved = unquote(parts.path).lstrip('/')
        moved = mapping.get(resolved, resolved)
        if moved == resolved and source.parent == destination.parent:
            return value
        path = '/' + moved if parts.path.startswith('/') else posixpath.relpath(moved, str(destination.parent))
        return urlunsplit(('', '', path, parts.query, parts.fragment))
    # Inline Markdown links/images, reference definitions, and authored HTML.
    patterns = (r'(?P<pre>!?\[[^\]\n]*\]\(<?)(?P<url>[^\s)>]+)',
                r'(?P<pre>^\s*\[[^\]\n]+\]:\s*<?)(?P<url>[^\s>]+)',
                r'''(?P<pre>\b(?:href|src)=["'])(?P<url>[^"']+)''')
    for pattern in patterns:
        text = re.sub(pattern, lambda m: m['pre'] + url(m['url']), text, flags=re.M)
    return text


def relocate(slug: str, name: str, to_slug: str, to_name: str, *, root: Path = BASE,
             dry_run: bool = False) -> dict[str, str]:
    root = root.resolve()
    old_parent, new_parent = parent_path(root, slug), parent_path(root, to_slug)
    companion_name(name, slug)
    companion_name(to_name, to_slug)
    if Path(name).suffix != Path(to_name).suffix or name.startswith('Presenters-Companion-') != to_name.startswith('Presenters-Companion-'):
        raise ValueError('A relocation cannot change the companion type')
    old, new = old_parent / name, new_parent / to_name
    if old == new:
        return {}
    if not old.is_file():
        raise ValueError(f'Companion source is missing: {old}')
    manifests = {n: json.loads((root / 'Scripts' / n).read_bytes())
                 for n in ('presentation-pipeline.json', 'companion-pipeline.json')}
    mapping: dict[str, str] = {}

    def plan(source: Path, target: Path):
        if (source.is_symlink() or target.is_symlink() or target.exists()
                or not source.resolve().is_relative_to(old_parent.resolve())
                or not target.resolve().is_relative_to(new_parent.resolve())
                or source.name.casefold() in {f'{slug}{s}'.casefold() for s in ('.md', '.html', '.pdf')}
                or target.name.casefold() in {f'{to_slug}{s}'.casefold() for s in ('.md', '.html', '.pdf')}):
            raise ValueError(f'Unsafe or occupied relocation target: {target}')
        mapping[source.relative_to(root).as_posix()] = target.relative_to(root).as_posix()

    plan(old, new)
    if old.suffix == '.pptx':
        spec = next((d for d in manifests['presentation-pipeline.json']['decks']
                     if d['source'] == old.relative_to(root).as_posix()), None)
        if spec is None:
            raise ValueError('Register the deck before moving it')
        for field in ('slidesPdf', 'notesPdf'):
            src = root / spec[field]
            if src.suffix != '.pdf':
                raise ValueError('Deck outputs must be PDFs')
            target_name = src.name.replace(old.stem, new.stem, 1) if src.name.startswith(old.stem) else src.name
            plan(src, new_parent / target_name)
        owner = next((c for c in manifests['companion-pipeline.json']['companions'] if c['deck'] == spec['id']), None)
        if owner and old_parent != new_parent:
            src = root / owner['markdown']
            if not src.is_file():
                raise ValueError('The owning presenter source is missing; repair ownership before moving the deck')
            for suffix in ('.md', '.html', '.pdf', '.docx', '.notes.json'):
                plan(src.with_suffix(suffix), new_parent / src.with_suffix(suffix).name)
    else:
        for suffix in ('.html', '.pdf'):
            plan(old.with_suffix(suffix), new.with_suffix(suffix))
        if name.startswith('Presenters-Companion-'):
            if old_parent != new_parent:
                raise ValueError('Move the owning deck to move a Presenter’s Companion between studies')
            for suffix in ('.docx', '.notes.json'):
                plan(old.with_suffix(suffix), new.with_suffix(suffix))

    # Validate the whole move, including missing ignored outputs, before writing.
    destinations = [v.casefold() for v in mapping.values()]
    if len(destinations) != len(set(destinations)):
        raise ValueError('Relocation would collide with another owned output')
    updates = {}
    for family in ('Studies', 'Applications'):
        for path in (root / family).glob('*/*.md'):
            rel = path.relative_to(root).as_posix()
            dest = mapping.get(rel, rel)
            before = path.read_text(encoding='utf-8')
            after = rewrite_links(before, PurePosixPath(rel), PurePosixPath(dest), mapping)
            if before != after:
                if path.stem == path.parent.name:
                    from _study_catalog import set_edited_on, now_ist
                    after = set_edited_on(after, now_ist())
                updates[dest] = after
    for manifest, fields, rows in (
        ('presentation-pipeline.json', ('source', 'slidesPdf', 'notesPdf'), 'decks'),
        ('companion-pipeline.json', ('markdown',), 'companions'),
    ):
        for row in manifests[manifest][rows]:
            for field in fields:
                row[field] = mapping.get(row[field], row[field])
    for source, target in mapping.items():
        print(f'{source} -> {target}')
    if not dry_run:
        # Read all sources before modifying any file. Moves are individually
        # confined to the already validated study directories.
        content = {dst: (root / src).read_bytes() for src, dst in mapping.items() if (root / src).is_file()}
        for target, body in content.items():
            (root / target).write_bytes(body)
        for source in mapping:
            (root / source).unlink(missing_ok=True)
        for target, text in updates.items():
            write_text_lf(root / target, text)
        for name, data in manifests.items():
            write_text_lf(root / 'Scripts' / name, json.dumps(data, indent=2) + '\n')
    for path in sorted(set(updates) | {dst for dst in mapping.values() if dst.endswith(('.md', '.pptx'))}):
        print(f'Render and verify: {path}')
    return mapping


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('name')
    parser.add_argument('--to-study')
    parser.add_argument('--to-name')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    relocate(args.slug, args.name, args.to_study or args.slug, args.to_name or args.name, dry_run=args.dry_run)
