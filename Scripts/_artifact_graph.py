"""Publication dependencies, independent of generated files and runner cache state.

Nodes are keyed by public output path. Fingerprints describe consumed source
bytes, selected metadata and the explicit rendering contract. A protected build
receipt supplies output checksums; a Git diff is never proof of publication.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

from _build_inputs import file_hash, script_dependencies

BASE = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif'}
# These helpers affect screen markup only; the printer removes their chrome.
# Keep mixed print/screen modules (converter, sanitizer and glossary table
# wrapper) in the contract until their print functions are split out.
WEB_ONLY = {
    'Scripts/_study_reader.py', 'Scripts/_study_passages.py',
    'Scripts/_discussion_assets.py', 'Scripts/_study_search.py',
    'Scripts/_build_reader_offline.py', 'Scripts/_build_studies_index.py',
    'Scripts/_study_catalog.py', 'Scripts/_build_social_cards.py',
}
PRINT_ROOTS = ('_study_pdf_pipeline.py',)
PRINT_EXTRA = {
    'CNAME', 'requirements.txt', 'Scripts/package.json', 'Scripts/package-lock.json',
    'Scripts/_chrome.js', 'Scripts/_html_to_pdf.js', 'Scripts/_pdf_resource_policy.cjs',
    'Scripts/_render_katex_math.js', 'Scripts/render-contract.json',
}


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read_json(path: Path, default):
    return json.loads(path.read_bytes()) if path.is_file() else default


def catalogs(root: Path) -> dict[tuple[str, str], dict]:
    return {(collection, row['slug']): row
            for family, collection in [('topical', 'Studies'), ('formal', 'Studies'), ('applied', 'Applications')]
            for row in read_json(root / f'Studies/catalog-{family}.json', [])}


def local_path(source: Path, url: str, root: Path) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    name = unquote(parsed.path).replace('\\', '/')
    if name.startswith('../References/') and source.parent.parent.name in {'Studies', 'Applications'}:
        name = '../' + name
    target = (root / name.lstrip('/') if name.startswith('/') else source.parent / name).resolve()
    return target if target.is_relative_to(root.resolve()) else None


def source_links(source: Path) -> tuple[set[str], set[str]]:
    return parsed_links(source.read_text(encoding='utf-8'))


@lru_cache(maxsize=128)
def parsed_links(text: str) -> tuple[frozenset[str], frozenset[str]]:
    # Pure parsing can be shared by the graph, PDF selector and receipt checks.
    # Filesystem existence/catalog state is deliberately resolved outside this cache.
    import markdown
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(markdown.markdown(text,
                         extensions=['tables', 'fenced_code']), 'html.parser')
    images = {str(tag['src']) for tag in soup.find_all(['img', 'source'], src=True)}
    for tag in soup.find_all(['img', 'source'], srcset=True):
        images.update(part.strip().split()[0] for part in str(tag['srcset']).split(',') if part.strip())
    # Include CSS-embedded images in author HTML, including background figures.
    images.update(re.findall(r'url\([\s\"\x27]*([^\s)\"\x27]+)', str(soup)))
    return frozenset(images), frozenset(str(tag['href']) for tag in soup.find_all('a', href=True))


def embedded_inputs(source: Path, root: Path = BASE) -> set[str]:
    """Follow embedded resources, including SVG image/use and CSS references."""
    pending = [(source, value) for value in source_links(source)[0]]
    found: set[str] = set()
    while pending:
        parent, value = pending.pop()
        target = local_path(parent, value, root)
        if target is None:
            continue
        name = target.relative_to(root).as_posix()
        if name in found:
            continue
        found.add(name)
        if target.is_file() and target.suffix.lower() in {'.svg', '.css'}:
            text = target.read_text(encoding='utf-8')
            urls = re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)', text)
            urls += re.findall(r'url\([\s\"\x27]*([^\s)\"\x27]+)', text)
            pending.extend((target, url) for url in urls)
    return found


def declared_outputs(root: Path) -> dict[str, str]:
    outputs = {p.with_suffix('.pdf').relative_to(root).as_posix(): p.relative_to(root).as_posix()
               for collection in ('Studies', 'Applications') for p in (root / collection).glob('*/*.md')}
    for deck in read_json(root / 'Scripts/presentation-pipeline.json', {}).get('decks', []):
        outputs.update({deck[key]: deck['source'] for key in ('slidesPdf', 'notesPdf')})
    return outputs


def link_inputs(source: Path, root: Path = BASE) -> dict:
    """Generated PDF presence is never an input, even after cache restoration."""
    rows, outputs = catalogs(root), declared_outputs(root)
    refs = read_json(root / 'References/r2-artifacts.json', {}).get('artifacts', [])
    records = {}
    for href in sorted(source_links(source)[1]):
        target = local_path(source, href, root)
        if target is None:
            continue
        name = target.relative_to(root).as_posix()
        parts = Path(name).parts
        if len(parts) >= 3 and parts[0] in {'Studies', 'Applications'}:
            canonical = outputs.get(name, target.with_suffix('.md').relative_to(root).as_posix())
            status = rows.get((parts[0], parts[1]), {}).get('status')
            if status == 'ongoing':
                records[name] = {'status': 'ongoing'}
            else:
                records[name] = {'source': canonical, 'exists': (root / canonical).is_file(),
                                 'status': 'published' if status else None}
                if Path(canonical).suffix.lower() == '.md':
                    records[name]['html'] = target.with_suffix('.html').is_file()
        elif parts and parts[0] == 'References':
            # The printed URL consumes delivery policy, not the referenced
            # document's body/checksum, rights-review notes or other row fields.
            from _reference_artifacts import public_delivery_url
            delivery = public_delivery_url(name, {'artifacts': refs})
            records[name] = {'publicUrl': delivery} if delivery else {'exists': target.is_file()}
            if not delivery and target.suffix.lower() == '.md' and name.startswith((
                'References/Madhyasth-Darshan/KD-Karm-Darshan-English/',
                'References/Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/',
            )):
                sibling = target.with_suffix('.pdf')
                records[name].update(siblingPdf=sibling.relative_to(root).as_posix(), pdfExists=sibling.is_file())
    return records


def print_inputs(root: Path = BASE) -> set[str]:
    inputs = (script_dependencies(root, PRINT_ROOTS) - WEB_ONLY) | PRINT_EXTRA
    inputs.update(p.relative_to(root).as_posix() for p in (root / 'Assets/KaTeX').rglob('*') if p.is_file())
    return inputs


def presentation_inputs(root: Path = BASE) -> set[str]:
    # Selection imports do not render decks. Traversing them would pull the
    # entire publication graph (including Markdown and web builders) back into
    # every deck's rendering contract. Follow actual renderer helpers instead.
    selection = frozenset({'_artifact_graph.py', '_publication_plan.py', '_pdf_build_cache.py'})
    return script_dependencies(root, ('_build_presentations.py',), stop=selection) | {
        'requirements.txt', 'Scripts/_install_presentation_renderer.ps1', 'Scripts/render-contract.json'}


def node(output: str, family: str, producer: str, inputs: set[str], metadata: dict,
         root: Path, **extra) -> dict:
    records = {name: file_hash(root / name) if (root / name).is_file() else 'missing' for name in sorted(inputs)}
    contract = {'schema': 1, 'producer': producer, 'inputs': records, 'metadata': metadata}
    return {'output': output, 'family': family, 'fingerprint': fingerprint(contract), **contract, **extra}


def document_node(source: Path, root: Path = BASE, *, shared_inputs: set[str] | None = None) -> dict:
    inputs = (print_inputs(root) if shared_inputs is None else shared_inputs) | embedded_inputs(source, root) | {source.relative_to(root).as_posix()}
    return node(source.with_suffix('.pdf').relative_to(root).as_posix(), 'markdown',
                '_study_pdf_pipeline.py', inputs, {'links': link_inputs(source, root)}, root,
                source=source.relative_to(root).as_posix())


def build_graph(root: Path = BASE) -> dict[str, dict]:
    root = root.resolve()
    public = {key for key, row in catalogs(root).items() if row['status'] in {'draft', 'released'}}
    nodes = {}
    shared_inputs = print_inputs(root)
    for collection, slug in sorted(public):
        for source in sorted((root / collection / slug).glob('*.md')):
            if source.stem.startswith('Research-Template-'):
                continue
            item = document_node(source, root, shared_inputs=shared_inputs)
            nodes[item['output']] = item
    manifest = read_json(root / 'Scripts/presentation-pipeline.json', {})
    profile = manifest.get('productionProfile')
    renderer = manifest.get('rendererProfiles', {}).get(profile)
    deck_inputs = presentation_inputs(root)
    for deck in manifest.get('decks', []):
        if tuple(Path(deck['source']).parts[:2]) not in public:
            continue
        for output in (deck['slidesPdf'], deck['notesPdf']):
            nodes[output] = node(output, 'presentations', '_build_presentations.py',
                                 deck_inputs | {deck['source']}, {'deck': deck, 'renderer': renderer}, root,
                                 source=deck['source'], deck=deck['id'])
    for ref in read_json(root / 'References/r2-artifacts.json', {}).get('artifacts', []):
        target = ref.get('target', {})
        output = target.get('r2_key', '')
        storage = target.get('storage')
        if (storage not in {'r2-public', 'r2-private-original'} or not output
                or ref.get('state') not in {'git-source', 'generated-local', 'r2-published'}
                or storage == 'r2-public' and ref.get('rights', {}).get('status') == 'review-required'):
            continue
        source = ref.get('generation', {}).get('source_markdown')
        inputs = {'Scripts/_build_reference_pdfs.py', 'Scripts/_reference_artifacts.py'}
        if source:
            inputs |= {source} | embedded_inputs(root / source, root)
        nodes[output] = node(output, 'references', '_build_reference_pdfs.py', inputs, {'reference': ref}, root,
                             source=source)
    return nodes


def select_changed(current: dict[str, dict], previous: dict[str, dict]) -> list[str]:
    return sorted(key for key, item in current.items()
                  if item['fingerprint'] != previous.get(key, {}).get('fingerprint'))


def affected_outputs(changed: set[str], *, root: Path = BASE, base: str | None = None,
                     nodes: dict[str, dict] | None = None) -> set[str]:
    """PR selection uses the same graph as durable publication receipts."""
    nodes = build_graph(root) if nodes is None else nodes
    result = {key for key, item in nodes.items() if changed.intersection(item['inputs'])}
    changed_catalog = any(name.startswith('Studies/catalog-') and name.endswith('.json') for name in changed)
    old_rows = {}
    if changed_catalog and base:
        for family, collection in [('topical', 'Studies'), ('formal', 'Studies'), ('applied', 'Applications')]:
            proc = subprocess.run(['git', 'show', f'{base}:Studies/catalog-{family}.json'], cwd=root,
                                  capture_output=True, check=True)
            old_rows.update({(collection, row['slug']): row for row in json.loads(proc.stdout)})
    current_rows = catalogs(root)
    ref_manifest_changed = 'References/r2-artifacts.json' in changed
    old_references = None
    if ref_manifest_changed and base:
        proc = subprocess.run(['git', 'show', f'{base}:References/r2-artifacts.json'], cwd=root,
                              capture_output=True, check=True)
        old_references = json.loads(proc.stdout)
    for key, item in nodes.items():
        parts = Path(key).parts
        if changed_catalog and len(parts) >= 3:
            prior = old_rows.get(tuple(parts[:2]), {}).get('status')
            if base is None or prior not in {'draft', 'released'}:
                result.add(key)
        for target, record in item['metadata'].get('links', {}).items():
            target_parts = Path(target).parts
            if ref_manifest_changed and target.startswith('References/'):
                from _reference_artifacts import public_delivery_url
                if old_references is None or public_delivery_url(target, old_references) != record.get('publicUrl'):
                    result.add(key)
            witnesses = {record['source']} if record.get('source') else set()
            if 'html' in record:
                witnesses.add(Path(target).with_suffix('.html').as_posix())
            if target.startswith('References/') and 'exists' in record:
                witnesses.add(target)
                if record.get('siblingPdf'):
                    witnesses.add(record['siblingPdf'])
            if changed.intersection(witnesses):
                # Source body changes do not alter the href. Only creation or
                # deletion affects the declared target, checked against base.
                if not base:
                    result.add(key)
                else:
                    for source in changed.intersection(witnesses):
                        old = subprocess.run(['git', 'cat-file', '-e', f'{base}:{source}'], cwd=root, capture_output=True)
                        if (old.returncode == 0) != (root / source).is_file():
                            result.add(key)
            if changed_catalog and len(target_parts) >= 3:
                pair = tuple(target_parts[:2])
                if not base or (old_rows.get(pair, {}).get('status') == 'ongoing') != (current_rows.get(pair, {}).get('status') == 'ongoing'):
                    result.add(key)
    if ref_manifest_changed:
        result.update(key for key, item in nodes.items() if item['family'] == 'references')
    return result


def explain(current: dict, previous: dict | None) -> list[str]:
    if not previous:
        return ['No verified published build receipt']
    reasons = [path for path in sorted(set(current['inputs']) | set(previous.get('inputs', {})))
               if current['inputs'].get(path) != previous.get('inputs', {}).get(path)]
    if current['metadata'] != previous.get('metadata'):
        reasons.append('Consumed metadata or referenced target changed')
    if current['producer'] != previous.get('producer') or current['schema'] != previous.get('schema'):
        reasons.append('Producer contract changed')
    return reasons


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--changed-print-since')
    selection.add_argument('--changed-presentation-tools-since')
    args = parser.parse_args()
    base = args.changed_print_since or args.changed_presentation_tools_since
    changed = subprocess.check_output(['git', 'diff', '--name-only', base, 'HEAD'],
                                      cwd=BASE, text=True).splitlines()
    # This cheap smoke selector needs only stdlib: it inspects print tooling,
    # not source documents, and shares the graph's exact print dependency set.
    if args.changed_print_since:
        selected = bool(set(changed).intersection(print_inputs() | {
            'Scripts/_verify_pdf_reproducible.py', '.github/workflows/pdf-pipeline-smoke.yml'}))
    else:
        selected = bool(set(changed).intersection(presentation_inputs() | {
            'Scripts/_verify_presentation_reproducible.py', '.github/workflows/presentation-pipeline-smoke.yml'}))
        if 'Scripts/presentation-pipeline.json' in changed:
            old = json.loads(subprocess.check_output(['git', 'show', f'{base}:Scripts/presentation-pipeline.json'], cwd=BASE))
            current = read_json(BASE / 'Scripts/presentation-pipeline.json', {})
            selected |= any(old.get(key) != current.get(key) for key in ('productionProfile', 'rendererProfiles'))
    print('true' if selected else 'false')
