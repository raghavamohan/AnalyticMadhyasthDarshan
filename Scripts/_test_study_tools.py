"""Enforce private-note and offline-bundle integrity, including generated assets."""
import json
import subprocess
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from _common import BASE
from _build_reader_offline import artifacts, verify_offline, allowed_resource, notebook_html
from _study_search import eligible_documents
from _study_reader import reader_controls


class StudyToolsTests(unittest.TestCase):
    def test_notes_and_offline_worker(self):
        result = subprocess.run(['node', str(BASE / 'Scripts/_test_study_tools.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_inventory_and_complete_reproducible_bundles(self):
        self.assertEqual(verify_offline(), [])
        notebook, raw = artifacts()
        self.assertEqual((notebook, raw), artifacts(reuse=False))
        bundles = json.loads(raw)['documents']
        self.assertEqual({doc['path'] for doc in bundles}, {doc['url'] for doc in eligible_documents().values()})
        for doc in bundles:
            with self.subTest(document=doc['path']):
                urls = {r['url'].split('?')[0] for r in doc['resources']}
                self.assertIn(doc['path'], urls)
                self.assertIn('/Studies/notebook.html', urls)
                self.assertIn('/Assets/reader/offline-client.js', urls)
                self.assertLessEqual(sum(r['bytes'] for r in doc['resources']), 20000000)
                self.assertLessEqual(len(doc['resources']), 150)
                soup = BeautifulSoup((BASE / doc['path'].lstrip('/')).read_text(encoding='utf-8'), 'html.parser')
                if soup.select_one('.mermaid'):
                    self.assertIn('/Assets/Mermaid/mermaid.min.js', urls)
                    self.assertNotIn('cdn.jsdelivr.net/npm/mermaid', str(soup))
                if soup.select_one('.katex'):
                    self.assertTrue(any('/KaTeX/fonts/' in url for url in urls))

    def test_resource_boundary(self):
        document = '/Studies/Test/Test.html'
        for url in ['/api/private', '/Studies/Test/Test.pdf', '/Studies/Other/figure.svg',
                    'https://elsewhere.test/figure.svg', '/Assets/reader/reader.js?token=secret', '/Studies/Test/../../private.svg']:
            self.assertFalse(allowed_resource(url, document), url)
        self.assertTrue(allowed_resource('/Studies/Test/figure.svg', document))

    def test_controls_are_labeled_and_notebook_is_independent(self):
        soup = BeautifulSoup(reader_controls(), 'html.parser')
        self.assertEqual([tab.text for tab in soup.select('[role=tab]')], ['Contents','Find','Notes','Bookmarks','Listen','Display'])
        for node in soup.select('[aria-controls]'):
            self.assertIsNotNone(soup.find(id=node['aria-controls']))
        page = BeautifulSoup(notebook_html(), 'html.parser')
        self.assertIsNone(page.select_one('[role=tabpanel]'))
        self.assertIsNotNone(page.select_one('#notebook #notes-list'))
        self.assertIsNotNone(page.select_one('#offline-library'))
        self.assertEqual(len(page.select('[id]')), len({node['id'] for node in page.select('[id]')}))


if __name__ == '__main__':
    unittest.main()
