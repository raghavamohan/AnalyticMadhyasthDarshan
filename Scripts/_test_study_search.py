"""Passage identity, public search inventory and incremental freshness contracts."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup

from _common import BASE
from _study_passages import annotate_passages, passage_key, search_text
import _study_search as search


class PassageTests(unittest.TestCase):
    def test_math_is_read_once_and_diagram_syntax_is_not_a_search_result(self):
        html = '<main id="main"><p id="a" data-reader-passage>Let <span class="katex"><span class="katex-mathml"><math><semantics><mi>x</mi><annotation>x_1</annotation></semantics></math></span><span class="katex-html">x1</span></span> be a value.</p><div class="mermaid" id="b" data-reader-passage>flowchart TD A --&gt; B</div></main>'
        data = search.document_data(Path('test.md'), html)
        self.assertEqual([(p['id'], p['text']) for p in data['passages']], [('a', 'Let x be a value.')])

    def test_query_and_source_contracts(self):
        result = subprocess.run(['node', str(BASE / 'Scripts/_test_study_search.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ids_preserve_existing_bookmarks_and_ignore_unrelated_insertions(self):
        samples = ['section\nज्ञान and jīvan', 'intro\nA 😀 passage', ' section  text\n spaced ', 'cafe\u0301']
        result = subprocess.run(['node', '-e',
            "const R=require('./Assets/reader/reader.js');let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).map(R.passageKey))));"],
            cwd=BASE, input=json.dumps(samples), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), [passage_key(text) for text in samples])
        fragment = '<nav class="study-toc"><p>Contents</p></nav><h2 id="s">Section</h2><p>A <em>passage</em>.</p><ul><li>List<p>nested</p></li></ul><table><tr><td><p>Cell</p></td></tr></table><p>A <em>passage</em>.</p>'
        fragment += '<p class="study-reading-key">Reader help</p>'
        soup = BeautifulSoup(annotate_passages(fragment), 'html.parser')
        passages = soup.select('[data-reader-passage]')
        self.assertEqual(len(passages), 5)
        self.assertIsNone(soup.select_one('.study-toc [id]'))
        self.assertIsNone(soup.select_one('.study-reading-key[data-reader-passage]'))
        self.assertEqual(passages[0]['id'], 's')
        self.assertEqual(passages[-1]['id'], passages[1]['id'] + '-2')
        changed = BeautifulSoup(annotate_passages(fragment.replace('<p>A ', '<p>Unrelated.</p><p>A ', 1)), 'html.parser')
        self.assertEqual(changed.find(id=passages[1]['id']).get_text(), 'A passage.')
        self.assertEqual(annotate_passages(str(soup)), str(soup))

    def test_generated_corpus_is_fresh_unique_and_has_no_duplicate_format_entries(self):
        self.assertEqual(search.verify_search(), [])
        documents = search.eligible_documents()
        self.assertGreater(len(documents), 10)
        urls = [doc['url'] for doc in documents.values()]
        self.assertEqual(len(urls), len(set(urls)))
        for source, metadata in documents.items():
            with self.subTest(document=source.stem):
                data = json.loads(search.shard_path(metadata).read_text(encoding='utf-8'))
                ids = [p['id'] for p in data['passages']]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(all(not p['text'].startswith(('Author:', 'Edited on:')) for p in data['passages']))
                self.assertTrue(all('Dotted underline: definition' not in p['text'] for p in data['passages']))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.rows = [SimpleNamespace(slug='Public', status=search.StudyStatus.DRAFT),
                     SimpleNamespace(slug='Pending', status=search.StudyStatus.ONGOING)]
        for name in ('Public/Public', 'Public/Note', 'Public/Research-Template-X', 'Public/Private', 'Pending/Pending'):
            path = self.root / ('Studies/' + name + '.md')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'# Test\n')
        self.tracked = b'Studies/Public/Public.md\0Studies/Public/Note.md\0Studies/Public/Research-Template-X.md\0Studies/Pending/Pending.md\0'
        for target, value in [('BASE', self.root), ('DATA', self.root / 'Studies/search-data'),
                              ('CATALOG_TABLES', [search.StudyTable.TOPICAL])]:
            patcher = patch.object(search, target, value)
            patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch.object(search, 'load_catalog_rows', side_effect=lambda _: self.rows)
        patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch.object(search.subprocess, 'check_output', side_effect=lambda *a, **kw: self.tracked)
        patcher.start(); self.addCleanup(patcher.stop)

    def build(self):
        for source in search.eligible_documents():
            version = search.digest(source.read_bytes())
            rendered = f'<html lang="hi"><head><meta name="amd-source-version" content="{version}"/></head><body><h1>Test</h1><main id="main">' + annotate_passages('<h2 id="s">Section</h2><p>ज्ञान and text.</p>') + '</main></body></html>'
            source.with_suffix('.html').write_bytes(rendered.encode())
            search.write_search_document(source, rendered)

    def test_only_tracked_published_studies_and_notes_enter_search(self):
        docs = search.eligible_documents()
        self.assertEqual({p.stem for p in docs}, {'Public', 'Note'})
        self.assertEqual({m['kind'] for m in docs.values()}, {'study', 'companion'})
        self.build()
        self.assertEqual(search.verify_search(), [])
        before = (search.DATA / 'manifest.json').read_bytes()
        search.write_search_catalog()
        self.assertEqual((search.DATA / 'manifest.json').read_bytes(), before)

    def test_edits_change_one_shard_and_source_versions_are_checked(self):
        self.build()
        docs = search.eligible_documents()
        note = self.root / 'Studies/Public/Note.md'
        untouched = search.shard_path(docs[note]).read_bytes()
        source = self.root / 'Studies/Public/Public.md'
        source.write_bytes(b'# Changed\n')
        self.assertTrue(any('Stale reader' in e for e in search.verify_search()))
        self.build()
        self.assertEqual(search.shard_path(docs[note]).read_bytes(), untouched)
        self.assertEqual(search.verify_search(), [])
        search.shard_path(docs[note]).write_bytes(b'{invalid')
        self.assertTrue(any('Invalid search catalog' in e for e in search.verify_search()))

    def test_unpublishing_and_renaming_remove_superseded_search_content(self):
        self.build()
        old = set(search.DATA.glob('study-*.json'))
        self.rows[0].status = search.StudyStatus.ONGOING
        search.write_search_catalog()
        self.assertFalse(any(p.exists() for p in old))
        self.assertEqual(search.verify_search(), [])
        self.rows[0].status = search.StudyStatus.RELEASED
        self.build()
        old_source = self.root / 'Studies/Public/Note.md'
        new_source = old_source.with_name('Renamed.md')
        new_source.write_bytes(old_source.read_bytes())
        self.tracked = self.tracked.replace(b'Public/Note.md', b'Public/Renamed.md')
        self.build()
        self.assertEqual(search.verify_search(), [])
        self.assertFalse(any('/Note.html' in d['url'] for d in search.eligible_documents().values()))


if __name__ == '__main__':
    unittest.main()
