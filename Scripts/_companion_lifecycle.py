"""Keep authored deck and presenter-companion manifests with study lifecycle moves."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from _common import BASE, validate_study_slug, write_text_lf


def in_study(value: str, slug: str) -> bool:
    parts = PurePosixPath(value.replace('\\', '/')).parts
    return len(parts) >= 3 and parts[0] in {'Studies', 'Applications'} and parts[1].casefold() == slug.casefold()


def remove_companions(slug: str, *, root: Path = BASE, dry_run: bool = False) -> int:
    validate_study_slug(slug)
    path = root / 'Scripts/companion-pipeline.json'
    if not path.is_file():
        return 0
    data = json.loads(path.read_bytes())
    rows = data['companions']
    kept = [row for row in rows if not in_study(row['markdown'], slug)]
    removed = len(rows) - len(kept)
    if removed and not dry_run:
        data['companions'] = kept
        write_text_lf(path, json.dumps(data, indent=2) + '\n')
    return removed


def rename_paths(old: str, new: str, *, root: Path = BASE, dry_run: bool = False) -> int:
    validate_study_slug(old)
    validate_study_slug(new)
    changed = 0
    for name, collection, fields in (
        ('presentation-pipeline.json', 'decks', ('source', 'slidesPdf', 'notesPdf')),
        ('companion-pipeline.json', 'companions', ('markdown',)),
    ):
        path = root / 'Scripts' / name
        if not path.is_file():
            continue
        data = json.loads(path.read_bytes())
        dirty = False
        for row in data[collection]:
            for field in fields:
                if in_study(row[field], old):
                    parts = PurePosixPath(row[field].replace('\\', '/')).parts
                    row[field] = str(PurePosixPath(parts[0], new, *parts[2:]))
                    dirty = True
                    changed += 1
        if dirty and not dry_run:
            write_text_lf(path, json.dumps(data, indent=2) + '\n')
    return changed


def validate_prepared_manifest(raw: bytes | None, *, root: Path = BASE) -> None:
    """Accept retirement/relocation, never new ownership from a build payload.

    The trusted writer reads its own manifest, not a manifest supplied by the
    build, when authorizing binary outputs. New declarations belong in the
    contributor's reviewed source commit. A preparation result may only drop
    existing rows or move their same-named Markdown to another study directory.
    """
    if raw is None:
        raise ValueError('Preparation cannot delete the companion ownership manifest')
    before = json.loads((root / 'Scripts/companion-pipeline.json').read_bytes())
    after = json.loads(raw)
    if (not isinstance(after, dict) or not isinstance(after.get('companions'), list)
            or {k: v for k, v in before.items() if k != 'companions'}
            != {k: v for k, v in after.items() if k != 'companions'}):
        raise ValueError('Preparation cannot redefine the companion manifest contract')
    by_deck = {item['deck']: item for item in before['companions']}
    used = set()
    for item in after['companions']:
        if not isinstance(item, dict) or not isinstance(item.get('deck'), str):
            raise ValueError('Invalid prepared companion ownership')
        old = by_deck.get(item['deck'])
        if (old is None or item['deck'] in used
                or {k: v for k, v in old.items() if k != 'markdown'}
                != {k: v for k, v in item.items() if k != 'markdown'}):
            raise ValueError('Preparation cannot add or redefine companion ownership')
        used.add(item['deck'])
        name = item.get('markdown')
        if not isinstance(name, str):
            raise ValueError('Prepared companion source must be a path')
        src, dst = PurePosixPath(old['markdown']), PurePosixPath(name)
        if (len(dst.parts) != 3 or dst.parts[0] != src.parts[0]
                or dst.name != src.name or '\\' in name or '..' in dst.parts):
            raise ValueError('Preparation may only relocate a companion within its collection')
        validate_study_slug(dst.parts[1])
