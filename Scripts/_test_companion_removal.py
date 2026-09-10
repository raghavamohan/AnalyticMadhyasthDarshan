"""Prove that companion deletion and entire-study retirement have different scope."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import _ci_study_pr as ci
import _remove_study as whole
import _remove_study_companions as selected
from _study_catalog import StudyRow, StudyStatus, StudyTable


class CompanionRemovalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()

    def fixture(self, collection='Studies'):
        self.parent = self.root / collection / 'Example'
        self.prefix = f'{collection}/Example'
        self.parent.mkdir(parents=True)
        for name in ('Example.md', 'Example.html', 'Example.pdf', '.proposal-meta.json',
                     'Technical-Note-One.md', 'Technical-Note-One.html', 'Technical-Note-One.pdf',
                     'Research-Note-Keep.md', 'Research-Note-Keep.html', 'figure.svg', 'Deck.pptx',
                     'Deck.pdf', 'Deck-notes.pdf', 'Presenters-Companion-Deck.md',
                     'Presenters-Companion-Deck.html', 'Presenters-Companion-Deck.pdf',
                     'Presenters-Companion-Deck.docx', 'Presenters-Companion-Deck.notes.json'):
            (self.parent / name).write_text(name, encoding='utf-8')
        (self.parent / 'nested').mkdir()
        (self.parent / 'nested/image.png').write_bytes(b'nested image')
        (self.root / 'Scripts').mkdir()
        (self.root / 'Studies').mkdir(exist_ok=True)
        (self.root / 'Studies/catalog-topical.json').write_text('catalog bytes', encoding='utf-8')
        (self.root / 'Studies/proposal-registry.json').write_text(json.dumps({'proposals': [{'slug': 'Example'}, {'slug': 'Keep'}]}), encoding='utf-8')
        self.manifests = {
            'presentation-pipeline.json': {'schemaVersion': 1, 'decks': [
                {'id': 'example', 'source': f'{self.prefix}/Deck.pptx', 'slidesPdf': f'{self.prefix}/Deck.pdf', 'notesPdf': f'{self.prefix}/Deck-notes.pdf'},
                {'id': 'keep', 'source': 'Studies/Keep/Deck.pptx', 'slidesPdf': 'Studies/Keep/Deck.pdf', 'notesPdf': 'Studies/Keep/Deck-notes.pdf'}]},
            'companion-pipeline.json': {'schema': 1, 'companions': [
                {'deck': 'example', 'markdown': f'{self.prefix}/Presenters-Companion-Deck.md'},
                {'deck': 'keep', 'markdown': 'Studies/Keep/Presenters-Companion-Deck.md'}]},
        }
        for name, data in self.manifests.items():
            (self.root / 'Scripts' / name).write_text(json.dumps(data), encoding='utf-8')

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def preserved_study(self, before):
        for name in (f'{self.prefix}/Example.md', f'{self.prefix}/Example.html', f'{self.prefix}/Example.pdf',
                     f'{self.prefix}/.proposal-meta.json', f'{self.prefix}/figure.svg',
                     f'{self.prefix}/Research-Note-Keep.md', 'Studies/catalog-topical.json', 'Studies/proposal-registry.json'):
            self.assertEqual((self.root / name).read_bytes(), before[name], name)

    def test_one_note_deletion_keeps_the_study_deck_and_shared_figure(self):
        self.fixture()
        before = self.snapshot()
        plan = selected.remove_selected('Example', ['Technical-Note-One.md'], root=self.root, dry_run=True)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(set(plan), {f'{self.prefix}/Technical-Note-One{ext}' for ext in ('.md', '.html', '.pdf')})
        selected.remove_selected('Example', ['Technical-Note-One.md'], root=self.root)
        self.preserved_study(before)
        self.assertTrue((self.parent / 'Deck.pptx').is_file())
        with patch.object(ci, 'BASE', self.root), patch.object(ci, 'STUDIES', self.root / 'Studies'), patch.object(ci, 'changed_paths', return_value=[('D', p) for p in plan]):
            self.assertFalse(ci.study_was_removed('base', 'Example'))

    def test_multiple_companions_remove_only_owned_chains_under_applications(self):
        self.fixture('Applications')
        before = self.snapshot()
        selected.remove_selected('Example', ['Technical-Note-One.md', 'Deck.pptx'], root=self.root)
        self.preserved_study(before)
        self.assertFalse(any(self.parent.glob('Presenters-Companion-Deck.*')))
        self.assertFalse((self.parent / 'Deck.pptx').exists())
        self.assertEqual([d['id'] for d in json.loads((self.root / 'Scripts/presentation-pipeline.json').read_bytes())['decks']], ['keep'])
        self.assertEqual([d['deck'] for d in json.loads((self.root / 'Scripts/companion-pipeline.json').read_bytes())['companions']], ['keep'])
        selected.remove_selected('Example', ['Technical-Note-One.md', 'Deck.pptx'], root=self.root, previous=self.manifests)
        self.preserved_study(before)

    def test_removing_presenter_text_keeps_its_deck(self):
        self.fixture()
        selected.remove_selected('Example', ['Presenters-Companion-Deck.md'], root=self.root)
        self.assertTrue((self.parent / 'Deck.pptx').is_file())
        self.assertTrue((self.parent / 'Deck.pdf').is_file())
        self.assertEqual(len(json.loads((self.root / 'Scripts/presentation-pipeline.json').read_bytes())['decks']), 2)

    def test_removing_every_companion_still_keeps_the_study(self):
        self.fixture()
        before = self.snapshot()
        selected.remove_selected('Example', ['Technical-Note-One.md', 'Research-Note-Keep.md', 'Deck.pptx'], root=self.root)
        for name in ('Example.md', 'Example.html', 'Example.pdf', '.proposal-meta.json', 'figure.svg'):
            self.assertEqual((self.parent / name).read_bytes(), before[f'{self.prefix}/{name}'])
        self.assertTrue(self.parent.is_dir())
        self.assertEqual((self.root / 'Studies/catalog-topical.json').read_bytes(), before['Studies/catalog-topical.json'])
        self.assertEqual((self.root / 'Studies/proposal-registry.json').read_bytes(), before['Studies/proposal-registry.json'])

    def test_ci_companion_operations_never_dispatch_whole_study_removal(self):
        self.fixture()
        before = self.snapshot()
        row = StudyRow('Example', '', '', StudyStatus.DRAFT, table=StudyTable.TOPICAL)
        with patch.multiple(ci, BASE=self.root, STUDIES=self.root / 'Studies',
                            changed_paths=Mock(return_value=[('D', f'{self.prefix}/Technical-Note-One.md')]),
                            detect_study_renames=Mock(return_value=[]), changed_study_slugs=Mock(return_value=['Example']),
                            get_study_row=Mock(return_value=(row, StudyTable.TOPICAL)),
                            sync_catalog_timestamp_from_md=Mock(), pdf_regeneration_reason=Mock(return_value=None),
                            verify_timestamp_sync=Mock(return_value=[]), references_changed=Mock(return_value=False),
                            study_references_changed=Mock(return_value=False), changed_markdown_slugs=Mock(return_value=[]),
                            cross_study_section_errors=Mock(return_value=[])), \
             patch.object(selected, 'prepare_deleted') as cleanup, \
             patch.object(ci.subprocess, 'run', side_effect=AssertionError('Must not invoke whole-study removal')) as process:
            for operation in ('delete-note', 'delete-presentation'):
                ci.handle_study_update(f'Study slug: Example\nOperation: {operation}\n', 'base')
            self.assertEqual(cleanup.call_count, 2)
            process.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_portal_partial_deck_deletion_cleans_owned_presenter_outputs(self):
        self.fixture()
        before = self.snapshot()
        (self.parent / 'Deck.pptx').unlink()
        manifest = copy.deepcopy(self.manifests['presentation-pipeline.json'])
        manifest['decks'] = manifest['decks'][1:]
        (self.root / 'Scripts/presentation-pipeline.json').write_text(json.dumps(manifest), encoding='utf-8')
        with patch.object(selected, 'previous_manifests', return_value=self.manifests):
            selected.prepare_deleted([('D', f'{self.prefix}/Deck.pptx')], 'base', root=self.root)
        self.preserved_study(before)
        self.assertFalse(any(self.parent.glob('Presenters-Companion-Deck.*')))

    def test_rejects_canonical_paths_and_hostile_manifest_before_any_deletion(self):
        self.fixture()
        before = self.snapshot()
        for name in ('Example.md', '../Example.md', 'Example.html', 'figure.svg', 'nested', 'Other/Note.md', 'Example.md:stream.md'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                selected.remove_selected('Example', ['Technical-Note-One.md', name], root=self.root)
            self.assertEqual(self.snapshot(), before)
        self.manifests['presentation-pipeline.json']['decks'][0]['slidesPdf'] = f'{self.prefix}/Example.pdf'
        (self.root / 'Scripts/presentation-pipeline.json').write_text(json.dumps(self.manifests['presentation-pipeline.json']), encoding='utf-8')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            selected.remove_selected('Example', ['Deck.pptx'], root=self.root)
        self.assertEqual(self.snapshot(), before)

    def test_entire_study_retirement_removes_all_companions_and_nested_files(self):
        self.fixture()
        references = self.root / 'References'
        references.mkdir()
        (references / 'MANIFEST.md').write_text('# References\n\n## By tag\n\n## Summary\n', encoding='utf-8')
        row = StudyRow('Example', '', '', StudyStatus.DRAFT, table=StudyTable.TOPICAL)
        with patch.multiple(whole, BASE=self.root, STUDIES=self.root / 'Studies', APPLICATIONS=self.root / 'Applications',
                            REFERENCES=references, PROPOSAL_REGISTRY_PATH=self.root / 'Studies/proposal-registry.json',
                            PRESENTATION_MANIFEST_PATH=self.root / 'Scripts/presentation-pipeline.json'), \
             patch.object(whole, 'study_dir', return_value=self.parent), \
             patch.object(whole, 'find_study_table', return_value=StudyTable.TOPICAL), \
             patch.object(whole, 'load_catalog_rows', return_value=[row]), \
             patch.object(whole, 'write_studies_catalog') as catalog, \
             patch.object(whole, 'write_references_readme_row'):
            whole.remove_study('Example', dry_run=False, assume_yes=True)
        self.assertFalse(self.parent.exists())
        self.assertEqual(catalog.call_args.args[0], [])
        self.assertEqual([r['slug'] for r in json.loads((self.root / 'Studies/proposal-registry.json').read_bytes())['proposals']], ['Keep'])
        for name, field in (('presentation-pipeline.json', 'decks'), ('companion-pipeline.json', 'companions')):
            self.assertEqual(len(json.loads((self.root / 'Scripts' / name).read_bytes())[field]), 1)


if __name__ == '__main__':
    unittest.main()
