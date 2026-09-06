"""Contributor receipt, draft and preview contract regressions."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from bs4 import BeautifulSoup
import markdown

from _common import BASE
from _safe_study_html import sanitize_author_html
from _cloudflare_performance import CSP


class ContributorTests(unittest.TestCase):
    def test_transaction_contracts(self):
        result = subprocess.run(['node', str(BASE / 'Scripts/_test_contributor.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_content_addressed_portal_assets_are_current(self):
        result = subprocess.run(['python',str(BASE / 'Scripts/_build_contributor_assets.py'),'--check'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout + result.stderr)

    def test_checked_in_javascript_syntax(self):
        portal = (BASE / 'Studies/submit.html').read_text(encoding='utf-8')
        scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', portal, re.S)
        scripts += [(BASE / 'Studies/portal' / name).read_text(encoding='utf-8') for name in ['drafts.js','contributor.js','preview.js']]
        for script in scripts:
            result = subprocess.run(['node', '--check'], input=script, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_vendored_preview_integrity_and_math_version(self):
        directory = BASE / 'Studies/portal/vendor'
        manifest = json.loads((directory / 'manifest.json').read_text())
        for row in manifest:
            self.assertEqual(hashlib.sha256((directory / row['file']).read_bytes()).hexdigest(), row['sha256'])
        lock = json.loads((BASE / 'Scripts/package-lock.json').read_text())
        self.assertEqual(next(row['version'] for row in manifest if row['package'] == 'katex'), lock['packages']['node_modules/katex']['version'])

    def test_common_markdown_structure_matches_production(self):
        source = '# Title\n\n## Section\n\nA **bold** claim with *emphasis* and `code`.\n\n| A | B |\n| --- | --- |\n| One | Two |\n\n> A quote.\n\n- First\n- Second\n\n```mermaid\nflowchart LR\n A --> B\n```\n'
        renderer = "const md=require('./Studies/portal/vendor/markdown-it.min.js')({html:true,typographer:true});let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>process.stdout.write(md.render(s)));"
        result = subprocess.run(['node','-e',renderer],cwd=BASE,input=source,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        production = BeautifulSoup(sanitize_author_html(markdown.markdown(source,extensions=['tables','fenced_code','smarty'])),'html.parser')
        preview = BeautifulSoup(sanitize_author_html(result.stdout),'html.parser')
        def semantic(soup):
            return [(tag.name,tag.get_text(' ',strip=True)) for tag in soup.find_all(['h1','h2','strong','em','code','th','td','blockquote','li'])]
        self.assertEqual(semantic(preview),semantic(production))

    def test_preview_is_isolated_and_dependencies_are_lazy(self):
        portal = BeautifulSoup((BASE / 'Studies/submit.html').read_text(encoding='utf-8'),'html.parser')
        frame = portal.find('iframe',id='s-preview-frame')
        self.assertEqual(list(frame['sandbox']),['allow-scripts'])
        self.assertNotIn('src',frame.attrs)
        self.assertFalse(any('vendor/' in script.get('src','') for script in portal.find_all('script')))
        preview = BeautifulSoup((BASE / 'Studies/portal/preview.html').read_text(),'html.parser')
        policy = preview.find('meta',attrs={'http-equiv':'Content-Security-Policy'})['content']
        for restriction in ["connect-src 'none'","base-uri 'none'","form-action 'none'","img-src data:"]:
            self.assertIn(restriction,policy)
        self.assertIn('https://analyticmadhyasthdarshan.org/Studies/portal/preview.html;',CSP)
        self.assertIn("font-src 'self' data:;",CSP)


if __name__ == '__main__':
    unittest.main()
