"""Verify companion Markdown -> DOCX / delivery JSON -> PPTX note ownership."""
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

from _common import BASE


def load_companions() -> list[dict]:
    """Validate ownership before any preparation write or freshness check."""
    from _presentation_pipeline import load_manifest
    data = json.loads((BASE / 'Scripts/companion-pipeline.json').read_bytes())
    if not isinstance(data, dict) or data.get('schema') != 1 or not isinstance(data.get('companions'), list):
        raise ValueError('companion-pipeline.json requires schema 1 and a companions array')
    decks = {deck.id: deck for deck in load_manifest().decks}
    declared, used_decks = set(), set()
    for item in data['companions']:
        if not isinstance(item, dict) or not isinstance(item.get('markdown'), str) or not isinstance(item.get('deck'), str):
            raise ValueError('Each companion requires markdown and deck strings')
        name = item.get('markdown', '')
        path = PurePosixPath(name)
        if (len(path.parts) != 3 or path.parts[0] not in {'Studies', 'Applications'}
                or '..' in path.parts or '\\' in name or path.suffix != '.md'
                or not path.name.startswith('Presenters-Companion-')):
            raise ValueError(f'Invalid presenter-companion source path: {name}')
        source = BASE / name
        if not source.resolve().is_relative_to(BASE.resolve()) or not source.is_file():
            raise ValueError(f'Presenter-companion source is missing or outside the repository: {name}')
        deck = decks.get(item.get('deck'))
        if deck is None or deck.source.parent.resolve() != source.parent.resolve():
            raise ValueError(f'{name}: deck must be registered under the same study')
        if name in declared or deck.id in used_decks:
            raise ValueError(f'Duplicate presenter-companion ownership: {name}')
        declared.add(name)
        used_decks.add(deck.id)
    discovered = {p.relative_to(BASE).as_posix() for root in ('Studies', 'Applications')
                  for p in (BASE / root).glob('*/Presenters-Companion-*.md')}
    if discovered - declared:
        raise ValueError('Unregistered presenter companion(s): ' + ', '.join(sorted(discovered - declared)))
    return data['companions']


def normalize(text: str) -> str:
    return ' '.join(text.split())


def delivery_notes(source: Path) -> dict[int, str]:
    text = source.read_text(encoding='utf-8')
    sections = re.split(r'^# Slide (\d+)\s*$', text, flags=re.M)
    notes = {}
    for index in range(1, len(sections), 2):
        number = int(sections[index])
        match = re.search(r'^## Delivering the slide\s*\n([\s\S]*?)(?=^## |\Z)', sections[index + 1], re.M)
        if number in notes or not match:
            raise ValueError(f'Duplicate slide or missing delivery script: {source.name}, slide {number}')
        # Notes preserve the authored emphasis cues, as the existing deck does.
        notes[number] = match[1].strip()
    if not notes or set(notes) != set(range(1, len(notes) + 1)):
        raise ValueError(f'Companion slide numbers are not contiguous: {source}')
    return notes


def office_parts(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as package:
        return {name: package.read(name) for name in package.namelist()}


def prepare(sources: set[str]) -> None:
    """Generate the declared companion chain during read-only preparation."""
    from _build_presenters_companion import build_docx
    from _presentation_pipeline import load_manifest
    from _sync_pptx_speaker_notes import sync_speaker_notes
    from _common import write_text_lf
    manifest = load_manifest()
    for item in load_companions():
        if item['markdown'] not in sources:
            continue
        source = BASE / item['markdown']
        notes = delivery_notes(source)
        build_docx(source, source.with_suffix('.docx'))
        write_text_lf(source.with_suffix('.notes.json'), json.dumps(notes, ensure_ascii=False, indent=2) + '\n')
        sync_speaker_notes(manifest.deck(item['deck']).source, notes)


def verify() -> list[str]:
    from _build_presenters_companion import build_docx
    from _presentation_pipeline import load_manifest
    from _sync_pptx_speaker_notes import load_notes
    from pptx import Presentation
    errors = []
    try:
        manifest = load_manifest()
        companions = load_companions()
    except (ValueError, KeyError, OSError) as error:
        return [str(error)]
    for item in companions:
        source = BASE / item['markdown']
        expected = delivery_notes(source)
        notes_path = source.with_suffix('.notes.json')
        actual = load_notes(notes_path) if notes_path.is_file() else {}
        if {k: normalize(v) for k, v in actual.items()} != {k: normalize(v) for k, v in expected.items()}:
            errors.append(f'{notes_path.relative_to(BASE)} differs from the companion delivery scripts')
        deck = manifest.deck(item['deck'])
        slides = Presentation(deck.source).slides
        if len(slides) != len(expected):
            errors.append(f'{deck.id}: companion slide count differs from deck')
        for number, slide in enumerate(slides, 1):
            actual_note = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ''
            if normalize(actual_note) != normalize(expected.get(number, '')):
                errors.append(f'{deck.id}: slide {number} speaker notes differ from companion')
        target = source.with_suffix('.docx')
        with tempfile.TemporaryDirectory() as directory:
            rendered = Path(directory) / target.name
            build_docx(source, rendered)
            if not target.is_file() or office_parts(target) != office_parts(rendered):
                errors.append(f'{target.relative_to(BASE)} differs from its Markdown source or generator')
    return errors


if __name__ == '__main__':
    errors = verify()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Companion DOCX, delivery JSON, slide counts and PPTX notes are current.')
