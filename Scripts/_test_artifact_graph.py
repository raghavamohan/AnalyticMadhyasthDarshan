"""Counterfactual dependency and publication-receipt regression tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import _artifact_graph as graph
import _publication_plan as planner


class Store:
    def __init__(self):
        self.objects = {}

    def head_object(self, key):
        return self.objects.get(key)


class ArtifactGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write('Studies/catalog-topical.json', json.dumps([
            {'slug': 'A', 'status': 'draft', 'description': 'First'},
            {'slug': 'B', 'status': 'released', 'description': 'Second'}]))
        self.write('Studies/A/A.md', '# A\n\n![figure](used.svg)\n\n[B](../B/B.pdf)\n')
        self.write('Studies/A/Note.md', '# Note\n')
        self.write('Studies/B/B.md', '# B\n')
        self.write('Studies/B/B.html', '<h1>B</h1>')
        self.write('Studies/A/used.svg', '<svg><image href="detail.png"/></svg>')
        self.write('Studies/A/detail.png', 'image')
        self.write('Studies/A/unused.gif', 'unused')
        self.write('Studies/A/Deck.pptx', 'deck')
        self.write('Scripts/presentation-pipeline.json', json.dumps({
            'productionProfile': 'pinned', 'rendererProfiles': {'pinned': {'version': '1'}},
            'decks': [{'id': 'a', 'source': 'Studies/A/Deck.pptx', 'slidesPdf': 'Studies/A/Deck.pdf',
                       'notesPdf': 'Studies/A/Deck-notes.pdf', 'requiredFonts': ['Example']}]}))
        self.write('Scripts/_study_pdf_pipeline.py', 'from _convert_to_pdf import convert_to_html\n')
        self.write('Scripts/_convert_to_pdf.py', 'from _study_reader import reader\n')
        self.write('Scripts/_study_reader.py', 'reader = 1\n')
        self.write('Scripts/_html_to_pdf.js', '// printer')
        self.write('Assets/KaTeX/font.woff2', 'font')
        self.before = graph.build_graph(self.root)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode())

    def changed(self):
        return set(graph.select_changed(graph.build_graph(self.root), self.before))

    def test_only_embedded_figure_and_recursive_resources_select_their_document(self):
        self.write('Studies/A/unused.gif', 'another figure')
        self.assertEqual(self.changed(), set())
        self.write('Studies/A/detail.png', 'changed nested image')
        self.assertEqual(self.changed(), {'Studies/A/A.pdf'})

    def test_companion_source_does_not_select_canonical_or_deck(self):
        self.write('Studies/A/Note.md', '# Revised note')
        self.assertEqual(self.changed(), {'Studies/A/Note.pdf'})

    def test_deck_edit_selects_just_its_two_outputs(self):
        self.write('Studies/A/Deck.pptx', 'changed notes or order')
        self.assertEqual(self.changed(), {'Studies/A/Deck.pdf', 'Studies/A/Deck-notes.pdf'})

    def test_web_only_changes_select_no_pdf(self):
        for name in ['Studies/glossary.json', 'Studies/offline-manifest.json', 'Studies/search-data/new.json',
                     'Studies/submit.html', 'Assets/favicon.svg', 'Assets/reader/reader.js', 'Scripts/_study_reader.py']:
            self.write(name, 'changed')
            self.assertEqual(self.changed(), set(), name)

    def test_description_does_not_affect_printed_output(self):
        path = self.root / 'Studies/catalog-topical.json'
        rows = json.loads(path.read_bytes())
        rows[0]['description'] = 'Changed catalog copy'
        self.write('Studies/catalog-topical.json', json.dumps(rows))
        self.assertEqual(self.changed(), set())

    def test_linked_draft_to_released_does_not_change_the_printed_link(self):
        path = self.root / 'Studies/catalog-topical.json'
        rows = json.loads(path.read_bytes())
        rows[1]['status'] = 'draft'
        self.write('Studies/catalog-topical.json', json.dumps(rows))
        self.assertEqual(self.changed(), set())

    def test_reference_body_metadata_does_not_invalidate_a_printed_url(self):
        self.write('Studies/A/A.md', '# A\n\n[Reference](../../References/R.pdf)\n')
        row = {'repo_path': 'References/R.pdf', 'source': {'sha256': 'a'*64, 'bytes': 12},
               'target': {'storage': 'r2-public', 'public_url': 'https://example.test/References/R.pdf'}}
        self.write('References/r2-artifacts.json', json.dumps({'artifacts': [row]}))
        before = graph.document_node(self.root / 'Studies/A/A.md', self.root)
        row['source']['sha256'] = 'b'*64
        self.write('References/r2-artifacts.json', json.dumps({'artifacts': [row]}))
        self.assertEqual(graph.document_node(self.root / 'Studies/A/A.md', self.root), before)
        row['target']['public_url'] = 'https://publisher.example/new.pdf'
        self.write('References/r2-artifacts.json', json.dumps({'artifacts': [row]}))
        self.assertNotEqual(graph.document_node(self.root / 'Studies/A/A.md', self.root), before)

    def test_runner_image_is_not_an_artifact_input(self):
        with patch.dict('os.environ', {'ImageOS': 'different', 'ImageVersion': 'future'}):
            self.assertEqual(self.changed(), set())

    def test_generated_pdf_presence_is_not_an_input(self):
        for name in ['Studies/B/B.pdf', 'Studies/A/A.pdf', 'Studies/A/Deck.pdf']:
            self.write(name, 'cached output')
            self.assertEqual(self.changed(), set(), name)

    def test_deck_link_consumes_pptx_existence_without_an_html_reader(self):
        self.write('Studies/B/B.md', '# B\n\n[Slides](../A/Deck.pdf)\n')
        before = graph.document_node(self.root / 'Studies/B/B.md', self.root)
        self.write('Studies/A/Deck.html', 'Unrelated diagnostic output')
        self.assertEqual(graph.document_node(self.root / 'Studies/B/B.md', self.root), before)
        (self.root / 'Studies/A/Deck.pptx').unlink()
        self.assertNotEqual(graph.document_node(self.root / 'Studies/B/B.md', self.root), before)

    def test_active_translation_link_consumes_sibling_pdf_presence_not_bytes(self):
        name = 'References/Madhyasth-Darshan/KD-Karm-Darshan-English/Chapter'
        self.write('Studies/B/B.md', '# B\n\n[Translation](../../' + name + '.md)\n')
        self.write(name + '.md', '# Translation')
        before = graph.document_node(self.root / 'Studies/B/B.md', self.root)
        self.write(name + '.pdf', 'First approved version')
        after = graph.document_node(self.root / 'Studies/B/B.md', self.root)
        self.assertNotEqual(before, after)
        self.write(name + '.pdf', 'Revised bytes, same public URL')
        self.assertEqual(after, graph.document_node(self.root / 'Studies/B/B.md', self.root))
        selected = graph.affected_outputs({name + '.pdf'}, root=self.root)
        self.assertIn('Studies/B/B.pdf', selected)

    def test_linked_target_body_change_does_not_rebuild_referrer(self):
        self.write('Studies/B/B.md', '# New body')
        self.assertEqual(self.changed(), {'Studies/B/B.pdf'})

    def test_target_becoming_planned_invalidates_referrer_and_retires_outputs(self):
        path = self.root / 'Studies/catalog-topical.json'
        rows = json.loads(path.read_bytes())
        rows[1]['status'] = 'ongoing'
        self.write('Studies/catalog-topical.json', json.dumps(rows))
        self.assertEqual(self.changed(), {'Studies/A/A.pdf'})
        self.assertNotIn('Studies/B/B.pdf', graph.build_graph(self.root))

    def test_print_engine_change_selects_all_markdown_only(self):
        self.write('Scripts/_html_to_pdf.js', '// changed printer')
        self.assertEqual(self.changed(), {'Studies/A/A.pdf', 'Studies/A/Note.pdf', 'Studies/B/B.pdf'})

    def test_font_change_does_not_select_presentations(self):
        self.write('Assets/KaTeX/font.woff2', 'new font')
        self.assertEqual(self.changed(), {'Studies/A/A.pdf', 'Studies/A/Note.pdf', 'Studies/B/B.pdf'})

    def test_real_deck_renderer_closure_excludes_planning_and_web_dependencies(self):
        inputs = graph.presentation_inputs()
        self.assertTrue({'Scripts/_pptx_to_pdf.py', 'Scripts/_build_deck_notes_pdf.py',
                         'Scripts/_verify_presentations.py'} <= inputs)
        self.assertFalse(inputs.intersection({'Scripts/_artifact_graph.py', 'Scripts/_publication_plan.py',
            'Scripts/_pdf_build_cache.py', 'Scripts/_html_to_pdf.js', 'Scripts/_site_release.py',
            'Scripts/_build_studies_index.py', 'Scripts/_study_reader.py'}))

    def test_active_receipt_carries_pending_work_across_failed_merges(self):
        store = Store()
        receipt = {'schema': 1, 'artifacts': {}}
        for key, node in self.before.items():
            sha = graph.fingerprint(key)
            record = {'key': f'site/objects/{sha}', 'sha256': sha, 'bytes': 123}
            receipt['artifacts'][key] = {'node': node, 'record': record, 'pdf': {}}
            store.objects[record['key']] = {'x-amz-meta-sha256': sha, 'content-length': '123'}
        active = {'revision': 'a' * 64, 'buildReceiptKey': planner.receipt_key(receipt)}
        # A changed in a failed merge. B changes in the next merge. Neither
        # change is lost even if the immediate Git diff contains only B.
        self.write('Studies/A/A.md', '# Pending A')
        self.write('Studies/B/B.md', '# New B')
        nodes = graph.build_graph(self.root)
        plan = planner.create_plan(nodes, active, receipt, store, store)
        self.assertEqual(set(plan['build']), {'Studies/A/A.pdf', 'Studies/B/B.pdf'})
        self.assertEqual(len(plan['reuse']), 3)
        missing = receipt['artifacts']['Studies/A/Note.pdf']['record']['key']
        store.objects.pop(missing)
        repaired = planner.create_plan(nodes, active, receipt, store, store)
        self.assertIn('Studies/A/Note.pdf', repaired['build'])
        self.assertEqual(len(planner.create_plan(nodes, active, receipt, store, store, force=True)['build']), 5)
        # Losing just the notes object still rebuilds the entire deck pair.
        store.objects.pop(receipt['artifacts']['Studies/A/Deck-notes.pdf']['record']['key'])
        repaired_pair = planner.create_plan(self.before, active, receipt, store, store)
        self.assertTrue({'Studies/A/Deck.pdf', 'Studies/A/Deck-notes.pdf'} <= set(repaired_pair['build']))

    def test_tampered_or_stale_plan_is_rejected(self):
        plan = planner.create_plan(self.before, None, None, None, None)
        planner.validate_plan(plan, root=self.root)
        bad = copy.deepcopy(plan)
        bad['build'].pop()
        with self.assertRaisesRegex(ValueError, 'exact current inventory'):
            planner.validate_plan(bad, root=self.root)
        self.write('Studies/A/Note.md', '# Changed after planning')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            planner.validate_plan(plan, root=self.root)


if __name__ == '__main__':
    unittest.main()
