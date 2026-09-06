"""Build verified public offline bundles and the device-local notebook shell."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs, unquote

from bs4 import BeautifulSoup

from _common import BASE, favicon_link_tags, site_base_url, write_text_lf
from _study_reader import reader_assets, reader_bootstrap, reader_controls
from _study_search import eligible_documents, serialize

MANIFEST = BASE / 'Studies/offline-manifest.json'
NOTEBOOK = BASE / 'Studies/notebook.html'
VENDOR = BASE / 'Assets/Mermaid'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def vendor_mermaid() -> None:
    source = BASE / 'Scripts/node_modules/mermaid'
    package = json.loads((BASE / 'Scripts/package.json').read_text(encoding='utf-8'))
    installed = json.loads((source / 'package.json').read_text(encoding='utf-8'))
    if installed['version'] != package['dependencies']['mermaid']:
        raise ValueError('Run npm ci in Scripts before vendoring Mermaid')
    VENDOR.mkdir(parents=True, exist_ok=True)
    body = (source / 'dist/mermaid.min.js').read_bytes().replace(b'\r\n', b'\n')
    (VENDOR / 'mermaid.min.js').write_bytes(body)
    write_text_lf(VENDOR / 'LICENSE', (source / 'LICENSE').read_text(encoding='utf-8'))
    write_text_lf(VENDOR / 'vendor.json', serialize({'version': installed['version'], 'sha256': sha(body)}))


def verify_vendor() -> list[str]:
    try:
        manifest = json.loads((VENDOR / 'vendor.json').read_text(encoding='utf-8'))
        version = json.loads((BASE / 'Scripts/package.json').read_text(encoding='utf-8'))['dependencies']['mermaid']
        if manifest['version'] != version or manifest['sha256'] != sha((VENDOR / 'mermaid.min.js').read_bytes()):
            return ['Vendored browser Mermaid differs from its pinned version/checksum; run _build_reader_offline.py --vendor-mermaid']
        if not (VENDOR / 'LICENSE').is_file():
            return ['The vendored Mermaid license is missing']
    except (OSError, ValueError, KeyError):
        return ['Vendored Mermaid is missing; run _build_reader_offline.py --vendor-mermaid']
    return []


def notebook_html() -> str:
    controls = BeautifulSoup(reader_controls(), 'html.parser')
    notes = controls.find(id='reader-notes')
    notes.attrs = {'id': 'notebook-notes'}
    notes.find('p').string = 'Private highlights and notes from your study readers, stored in this browser profile. Open a source title to return to the study.'
    css, scripts = reader_assets(NOTEBOOK.with_suffix('.md'))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>My notes &amp; saved studies</title><meta name="robots" content="noindex"/>
{favicon_link_tags()}{reader_bootstrap()}{css}{scripts}</head>
<body class="notebook-page reader-chrome"><a href="index.html">← All studies</a>
<main id="notebook"><h1>My notes &amp; saved studies</h1>
<nav class="notebook-nav" aria-label="Notebook sections"><a href="#notebook-notes">Private notes</a><a href="#saved-studies">Saved studies</a></nav>
<h2>Private notes</h2>{notes}
<section id="saved-studies"><h2>Saved studies</h2><p id="offline-library-status" role="status" aria-live="polite">Checking saved copies…</p><ol id="offline-library" class="study-note-list"></ol>
<p>Saved copies include the study and its reading assets. Linked source PDFs, discussions and collection search require a connection. Browser storage can be evicted; keep exported backups of your notes.</p></section>
<noscript>JavaScript is needed to open your device’s notes and saved-study list. Your downloaded Markdown and JSON backups remain readable independently.</noscript>
</main></body></html>
'''


def allowed_resource(url: str, document: str) -> bool:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or parts.fragment or set(parse_qs(parts.query)) - {'v'}:
        return False
    path = parts.path
    if path in {document, '/Studies/notebook.html'}:
        return True
    if re.fullmatch(r'/Assets/(reader/[a-z-]+\.(js|css)|Mermaid/mermaid\.min\.js|KaTeX/fonts/[A-Za-z0-9_-]+\.woff2|Icons/[A-Za-z0-9_.-]+\.(svg|png|ico))', path):
        return True
    parent = document.rsplit('/', 1)[0] + '/'
    return path.startswith(parent) and bool(re.fullmatch(r'[A-Za-z0-9_.-]+\.(svg|png|jpg|jpeg|webp)', path[len(parent):]))


def artifacts(*, reuse: bool = True) -> tuple[str, str]:
    notebook = notebook_html()
    old = {}
    if reuse and MANIFEST.is_file():
        try:
            old = {doc['path']: doc for doc in json.loads(MANIFEST.read_text(encoding='utf-8'))['documents']}
        except (ValueError, KeyError, TypeError):
            pass
    origin = site_base_url().rstrip('/')
    memo: dict[str, bytes] = {'/Studies/notebook.html': notebook.encode('utf-8')}
    hashes = {}

    def read(url: str) -> bytes:
        path = unquote(urlsplit(url).path)
        if path not in memo:
            file = (BASE / path.lstrip('/')).resolve()
            if not file.is_relative_to(BASE.resolve()) or file.is_symlink():
                raise ValueError(f'Unsafe offline resource: {path}')
            memo[path] = file.read_bytes()
        return memo[path]

    def digest(url: str) -> str:
        path = urlsplit(url).path
        if path not in hashes:
            hashes[path] = sha(read(url))
        return hashes[path]

    def href(value: str, base: str) -> str:
        absolute = urlsplit(urljoin(origin + base, value))
        if absolute.scheme + '://' + absolute.netloc != origin:
            raise ValueError(f'External reading resource cannot be saved offline: {value}')
        return absolute.path + ('?' + absolute.query if absolute.query else '')

    def resources(page: str, base: str, document: str) -> list[dict]:
        soup = BeautifulSoup(page, 'html.parser')
        urls = {base}
        for node in soup.select('script[src],link[href],img[src],[data-offline-client]'):
            if node.name == 'link' and not set(node.get('rel', [])) & {'stylesheet','icon','apple-touch-icon'}:
                continue
            value = node.get('data-offline-client') or node.get('src') or node.get('href')
            urls.add(href(value, base))
        for node in soup.select('style'):
            for value in re.findall(r'url\([\s\'"]*([^\)\'"\s]+)', node.get_text()):
                if not value.startswith(('data:', '#')):
                    urls.add(href(value, base))
        if soup.select_one('.mermaid'):
            urls.add('/Assets/Mermaid/mermaid.min.js?v=' + digest('/Assets/Mermaid/mermaid.min.js')[:16])
        pending = list(urls)
        while pending:
            url = pending.pop()
            if not allowed_resource(url, document):
                raise ValueError(f'Unexpected offline resource in {document}: {url}')
            if urlsplit(url).path.endswith('.css'):
                for value in re.findall(r'url\([\s\'"]*([^\)\'"\s]+)', read(url).decode('utf-8')):
                    if value.startswith(('data:', '#')):
                        continue
                    child = href(value, url)
                    if child not in urls:
                        urls.add(child); pending.append(child)
        return [{'url': url, 'sha256': digest(url), 'bytes': len(read(url))} for url in sorted(urls)]

    common = resources(notebook, '/Studies/notebook.html', '/Studies/notebook.html')
    records = []
    for source, meta in eligible_documents().items():
        reader = source.with_suffix('.html')
        if not reader.is_file():
            continue
        raw = reader.read_bytes(); page = raw.decode('utf-8')
        # A catalog write may precede regeneration. Omit stale readers until the
        # converter updates them; the final verifier requires the full inventory.
        if any(asset not in page for asset in reader_assets(source)):
            continue
        old_doc = old.get(meta['url'])
        if old_doc and old_doc.get('htmlSha') == sha(raw) and old_doc.get('librarySha') == sha(notebook.encode()) \
                and all(digest(r['url']) == r['sha256'] for r in old_doc['resources']):
            records.append(old_doc); continue
        assets = {r['url']: r for r in common + resources(page, meta['url'], meta['url'])}
        soup = BeautifulSoup(page, 'html.parser')
        version = soup.find('meta', attrs={'name': 'amd-source-version'})
        records.append({'path': meta['url'], 'title': soup.h1.get_text().strip()[:250],
                        'version': version['content'], 'htmlSha': sha(raw), 'librarySha': sha(notebook.encode()),
                        'resources': sorted(assets.values(), key=lambda r: r['url'])})
    return notebook, serialize({'schema': 1, 'documents': sorted(records, key=lambda d: d['path'])})


def write_offline_catalog() -> None:
    notebook, manifest = artifacts()
    write_text_lf(NOTEBOOK, notebook)
    write_text_lf(MANIFEST, manifest)


def verify_offline() -> list[str]:
    errors = verify_vendor()
    if errors:
        return errors
    try:
        notebook, manifest = artifacts(reuse=False)
        expected = {meta['url'] for meta in eligible_documents().values()}
        if {d['path'] for d in json.loads(manifest)['documents']} != expected:
            errors.append('Offline bundles are missing current readers; regenerate all changed readers')
        for path, content in ((NOTEBOOK, notebook), (MANIFEST, manifest)):
            if not path.is_file() or path.read_text(encoding='utf-8') != content:
                errors.append(f'Stale offline artifact: {path.relative_to(BASE)}')
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f'Offline bundle verification failed: {error}')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-mermaid', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.vendor_mermaid:
        vendor_mermaid()
    if not args.check:
        write_offline_catalog()
    failures = verify_offline()
    print('\n'.join(failures) if failures else 'Offline readers and notebook verified')
    raise SystemExit(bool(failures))
