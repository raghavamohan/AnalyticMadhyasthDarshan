"""Observable lifecycle behavior in disposable studies and Git histories."""
import copy
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import _add_study as add
import _bootstrap_proposal_study as bootstrap
import _common as common
import _presentation_pipeline as presentations
import _prepared_study as prepared
import _relocate_study_companion as move
import _remove_study_companions as remove
import _restore_study as restore
import _study_catalog as catalog
from _study_collection import proposal_collection


class LifecycleExtensions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.patchers = ExitStack()
        self.addCleanup(self.patchers.close)
        for module in (add, bootstrap, common, catalog, presentations):
            for name in ('BASE', 'STUDIES', 'APPLICATIONS', 'REFERENCES'):
                if hasattr(module, name):
                    self.patchers.enter_context(patch.object(module, name, self.root if name == 'BASE' else self.root / name.title()))
        for family in ('topical', 'formal', 'applied'):
            self.write(f'Studies/catalog-{family}.json', [])
        self.write('Studies/proposal-registry.json', {'version':1,'proposals':[]})
        self.write('References/README.md', '<!-- studies-catalog -->\n| Paper | Tags |\n|---|---|\n<!-- /studies-catalog -->\n')
        self.write('References/MANIFEST.md', '# References\n\n## By tag\n')
        self.write('Scripts/presentation-pipeline.json', {'schemaVersion':1,'productionProfile':'pinned',
            'rendererProfiles':{'pinned':{'engine':'libreoffice','version':'1','status':'production'}},'decks':[]})
        self.write('Scripts/companion-pipeline.json', {'schema':1,'companions':[]})
        self.patchers.enter_context(patch.object(bootstrap, 'REGISTRY_PATH', self.root / 'Studies/proposal-registry.json'))
        self.patchers.enter_context(patch.object(catalog, 'PROPOSAL_REGISTRY_PATH', self.root / 'Studies/proposal-registry.json'))
        # Exercise real source/metadata changes; global web production is
        # independently checked by the finalizer/index and dependency suites.
        def write_catalog(rows, table, **_kwargs):
            self.write(f'Studies/catalog-{table.value}.json', catalog.catalog_json_payload(rows))
        self.patchers.enter_context(patch.object(add, 'write_studies_catalog', side_effect=write_catalog))
        self.patchers.enter_context(patch.object(catalog, 'write_studies_catalog', side_effect=write_catalog))

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((json.dumps(value) if isinstance(value, (dict,list)) else value).encode('utf-8'))
        return path

    def read(self, name):
        return json.loads((self.root / name).read_bytes())

    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts}

    def git(self, *args):
        return subprocess.check_output(['git','-c','user.name=Fixture','-c','user.email=fixture@example.test',*args], cwd=self.root, stderr=subprocess.PIPE).decode().strip()

    def parent(self, family='Studies', slug='A'):
        path = self.write(f'{family}/{slug}/{slug}.md', f'# {slug}\n\n**Author:** Fixture\n\n**Edited on:** January 1, 2020, 9:00 AM IST\n\n**Status:** Draft\n')
        return path.parent

    def deck(self):
        parent = self.parent()
        for name, text in {'Deck.pptx':'deck source','Deck.pdf':'slides','Deck-notes.pdf':'notes',
                           'Presenters-Companion-Deck.md':'# Delivery\n\n![image](figure.svg)\n',
                           'Presenters-Companion-Deck.docx':'docx','Presenters-Companion-Deck.notes.json':'{}',
                           'figure.svg':'<svg/>','Technical-Note-One.md':'# One\n\n![figure](figure.svg)\n'}.items():
            self.write(f'Studies/A/{name}', text)
        manifest = self.read('Scripts/presentation-pipeline.json')
        manifest['decks'] = [{'id':'a','source':'Studies/A/Deck.pptx','slidesPdf':'Studies/A/Deck.pdf',
                              'notesPdf':'Studies/A/Deck-notes.pdf','requiredFonts':['Example']}]
        self.write('Scripts/presentation-pipeline.json', manifest)
        self.write('Scripts/companion-pipeline.json', {'schema':1,'companions':[{'deck':'a','markdown':'Studies/A/Presenters-Companion-Deck.md'}]})
        return parent

    def test_add_applied_places_source_catalog_and_references_in_applications(self):
        source = self.write('Input.md', '# Application\n\nAn applied argument.\n')
        with patch.object(add, 'regenerate_pdf') as render, patch.object(add, 'pdfs_for_tags', return_value=[]), patch.object(add, 'verify_timestamp_sync', return_value=[]):
            add.add_study(source, title='Application', slug='New-App', category='Domain', description='Applied study',
                tags='MVD', status=catalog.StudyStatus.DRAFT, formal=False, applied=True, dry_run=False,
                force=False, skip_pdf=False, check_timestamps=True, convert=False, no_keep_pdf=False)
        expected = self.root / 'Applications/New-App/New-App.md'
        self.assertTrue(expected.is_file())
        self.assertFalse((self.root / 'Studies/New-App').exists())
        self.assertIn('**Status:** Draft', expected.read_text())
        render.assert_called_once_with(expected, catalog.StudyStatus.DRAFT)
        self.assertEqual(self.read('Studies/catalog-applied.json')[0]['slug'], 'New-App')
        for name in ('README.md','MANIFEST.md'):
            self.assertIn('../Applications/New-App/New-App.pdf', (self.root/'References'/name).read_text())

    def test_applied_bootstrap_keeps_planned_metadata_and_rejects_collection_changes(self):
        fields = bootstrap.ProposalFields('Applied','Applied','Domain','Summary','Scope',False,'alice',12,True)
        bootstrap.bootstrap_proposal(fields)
        self.assertTrue((self.root/'Applications/Applied/.proposal-meta.json').is_file())
        self.assertEqual(common.study_dir('Applied'), self.root/'Applications/Applied')
        self.assertEqual(self.read('Studies/catalog-applied.json')[0]['status'], 'ongoing')
        before = self.snapshot()
        bootstrap.bootstrap_proposal(fields)
        self.assertEqual(before, self.snapshot())
        fields.applied = False
        with self.assertRaises(SystemExit): bootstrap.bootstrap_proposal(fields)
        self.assertEqual(before, self.snapshot())

    def test_collection_parser_supports_legacy_and_new_forms(self):
        for text, expected in [('Applied Studies','applied'),('Formal Studies','formal'),
                               ('- [x] Register in the Formal Studies table','formal'),
                               ('- [ ] Register in the Formal Studies table','topical')]:
            self.assertEqual(proposal_collection(text), expected)
        with self.assertRaises(ValueError): proposal_collection('- [x] Formal\n- [x] Applied')

    def test_final_global_deck_removal_leaves_valid_empty_manifest_and_parent(self):
        parent = self.deck()
        remove.remove_selected('A', ['Deck.pptx'], root=self.root)
        manifest = presentations.load_manifest(self.root/'Scripts/presentation-pipeline.json')
        self.assertEqual(manifest.decks, ())
        self.assertEqual(presentations.manifest_errors(manifest), [])
        self.assertTrue((parent/'A.md').is_file())
        self.assertTrue((parent/'figure.svg').is_file())

    def test_move_deck_chain_between_collections_and_keep_shared_figure(self):
        old = self.deck()
        new = self.parent('Applications','B')
        before = (old/'A.md').read_bytes(), (new/'B.md').read_bytes()
        previous = {name:self.read('Scripts/'+name) for name in ('presentation-pipeline.json','companion-pipeline.json')}
        move.relocate('A','Deck.pptx','B','Teaching.pptx',root=self.root)
        self.assertEqual(before, ((old/'A.md').read_bytes(), (new/'B.md').read_bytes()))
        self.assertTrue((old/'figure.svg').is_file())
        self.assertIn('../../Studies/A/figure.svg', (new/'Presenters-Companion-Deck.md').read_text())
        self.assertEqual(self.read('Scripts/presentation-pipeline.json')['decks'][0]['source'], 'Applications/B/Teaching.pptx')
        with patch.object(remove, 'previous_manifests', return_value=previous):
            remove.prepare_deleted([('D','Studies/A/Deck.pptx'),('D','Studies/A/Presenters-Companion-Deck.md')], 'base', root=self.root)
        self.assertTrue((new/'Teaching.pptx').is_file())
        self.assertTrue((new/'Presenters-Companion-Deck.md').is_file())

    def test_note_rename_repairs_inbound_links_and_rejects_collisions_before_writes(self):
        parent = self.deck()
        (parent/'A.md').write_text((parent/'A.md').read_text() + '\n[Note](Technical-Note-One.html)\n')
        before = self.snapshot()
        move.relocate('A','Technical-Note-One.md','A','Technical-Note-Two.md',root=self.root,dry_run=True)
        self.assertEqual(before,self.snapshot())
        move.relocate('A','Technical-Note-One.md','A','Technical-Note-Two.md',root=self.root)
        self.assertIn('Technical-Note-Two.html',(parent/'A.md').read_text())
        self.assertNotIn('January 1, 2020',(parent/'A.md').read_text())
        before = self.snapshot()
        with self.assertRaises(ValueError): move.relocate('A','Technical-Note-Two.md','A','A.md',root=self.root)
        self.assertEqual(before,self.snapshot())

    def historical(self):
        self.parent()
        entry = catalog.StudyRow('A','Domain','Summary',catalog.StudyStatus.DRAFT,
                                catalog.parse_edited_on((self.root/'Studies/A/A.md').read_text()))
        self.write('Studies/catalog-topical.json', catalog.catalog_json_payload([entry]))
        self.git('init','-b','master')
        self.git('add','.')
        self.git('commit','-m','Registered fixture')
        return self.git('rev-parse','HEAD')

    def test_restore_retired_study_is_bound_to_merged_history_and_exact_source(self):
        self.deck()
        revision = self.historical()
        self.git('rm','-r','Studies/A')
        self.write('Studies/catalog-topical.json', [])
        for manifest, key in [('presentation-pipeline.json','decks'),('companion-pipeline.json','companions')]:
            data = self.read('Scripts/'+manifest); data[key] = []; self.write('Scripts/'+manifest,data)
        self.git('add','.'); self.git('commit','-m','Retire fixture')
        before = self.snapshot()
        restore.restore('A',revision,base='master',root=self.root,dry_run=True)
        self.assertEqual(before,self.snapshot())
        restore.restore('A',revision,base='master',root=self.root)
        body = f'Operation: restore-study\nRestore from: {revision}\n'
        self.assertEqual(restore.restoration_errors('A',body,'master',root=self.root),[])
        self.assertTrue((self.root/'Studies/A/Deck.pptx').is_file())
        self.assertFalse((self.root/'Studies/A/Deck.pdf').exists())
        (self.root/'Studies/A/A.md').write_text('Invented replacement')
        self.assertTrue(restore.restoration_errors('A',body,'master',root=self.root))

    def test_restore_companion_keeps_parent_and_does_not_overwrite_changed_shared_asset(self):
        self.deck(); revision = self.historical()
        remove.remove_selected('A',['Technical-Note-One.md'],root=self.root)
        before = (self.root/'Studies/A/A.md').read_bytes()
        restore.restore('A',revision,base='master',names=['Technical-Note-One.md'],root=self.root)
        self.assertEqual(before,(self.root/'Studies/A/A.md').read_bytes())
        remove.remove_selected('A',['Technical-Note-One.md'],root=self.root)
        self.write('Studies/A/figure.svg','<svg><text>New shared image</text></svg>')
        before = self.snapshot()
        with self.assertRaises(ValueError): restore.restore('A',revision,base='master',names=['Technical-Note-One.md'],root=self.root)
        self.assertEqual(before,self.snapshot())

    def test_trusted_writer_accepts_only_committed_new_companion_ownership(self):
        self.deck(); revision = self.historical()
        manifests = prepared.read_source_manifests(revision,root=self.root)
        from _companion_lifecycle import output_contract
        outputs, _ = output_contract(manifests)
        self.assertIn('Studies/A/Presenters-Companion-Deck.docx',outputs)
        from _verification_identity import intent_hash
        import base64
        pr = {'number':1,'state':'open','draft':True,'head':{'sha':revision,'repo':{'full_name':'fixture/repo'}},
              'base':{'ref':'master','sha':revision}}
        payload = {'schema':1,'pr':1,'repository':'fixture/repo','head':revision,'base':revision,
                   'intent':intent_hash(pr),'files':{'Studies/A/Presenters-Companion-Deck.docx':base64.b64encode(b'docx').decode()}}
        self.assertEqual(prepared.validate(payload,pr,'fixture/repo',source_manifests=manifests),
                         {'Studies/A/Presenters-Companion-Deck.docx':b'docx'})
        payload['files'] = {'Studies/A/Unowned.docx':base64.b64encode(b'forged').decode()}
        with self.assertRaises(ValueError): prepared.validate(payload,pr,'fixture/repo',source_manifests=manifests)
        forged = copy.deepcopy(manifests)
        forged['presentation-pipeline.json']['decks'][0]['source'] = 'Studies/Other/Deck.pptx'
        with self.assertRaises(ValueError): output_contract(forged)
        self.git('switch','-c','unmerged')
        self.write('Studies/A/A.md','Unmerged content')
        self.git('add','.'); self.git('commit','-m','Unmerged')
        with self.assertRaises(ValueError): restore.historical_row('A',self.git('rev-parse','HEAD'),'master',root=self.root)

    def test_restore_transitive_svg_resources_and_reject_conflicting_deck_outputs(self):
        self.deck()
        self.write('Studies/A/figure.svg', '<svg><image href="detail.png"/></svg>')
        self.write('Studies/A/detail.png', 'image fixture')
        revision = self.historical()
        remove.remove_selected('A',['Technical-Note-One.md'],root=self.root)
        (self.root/'Studies/A/detail.png').unlink()
        restore.restore('A',revision,base='master',names=['Technical-Note-One.md'],root=self.root)
        self.assertEqual((self.root/'Studies/A/detail.png').read_text(),'image fixture')
        manifests = {n:self.read('Scripts/'+n) for n in ('presentation-pipeline.json','companion-pipeline.json')}
        manifests['presentation-pipeline.json']['decks'].append({**manifests['presentation-pipeline.json']['decks'][0], 'id':'overlap'})
        from _companion_lifecycle import output_contract
        with self.assertRaises(ValueError): output_contract(manifests)

    def test_scope_selection_works_before_dependency_installation(self):
        repository = Path(__file__).resolve().parents[1]
        runner = self.root/'Scripts/_run_lifecycle_acceptance.py'
        runner.write_bytes((repository/'Scripts/_run_lifecycle_acceptance.py').read_bytes())
        self.git('init','-b','master'); self.git('add','.'); self.git('commit','-m','Scope fixture')
        result = subprocess.run([sys.executable,'-S',str(runner),
                                 '--scope','--base-ref','HEAD'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'browser=false')

    def test_guided_slides_links_follow_remaining_inventory(self):
        import _build_studies_index as index
        html = '<article data-study-slug="A" data-presentation-pdf="A/Old.pdf"><a data-study-slides href="A/Old.pdf">Slides</a></article>'
        with patch.object(index,'presentation_links_by_slug',return_value={}):
            removed = index.render_start_here_presentations(html)
            self.assertIn('data-presentation-pdf=""',removed)
            self.assertIn('href="#" hidden',removed)
        with patch.object(index,'presentation_links_by_slug',return_value={'A':[{'href':'A/Other.pdf'}]}):
            updated = index.render_start_here_presentations(html)
            self.assertNotIn('Old.pdf',updated)
            self.assertIn('data-presentation-pdf="A/Other.pdf"',updated)
            self.assertIn('data-study-slides href="A/Other.pdf"',updated)

    def test_applied_deck_slug_resolution_and_source_response_contract(self):
        from _pptx_to_pdf import resolve_pptx
        parent = self.parent('Applications','Applied')
        (parent/'Deck.pptx').write_bytes(b'fixture')
        self.assertEqual(resolve_pptx(None,'Applied','Deck.pptx'),parent/'Deck.pptx')
        self.assertEqual(resolve_pptx(None,'Applied',None),parent/'Deck.pptx')
        repository = Path(__file__).resolve().parents[1]
        schema = json.loads((repository/'openapi/submissions.json').read_bytes())
        request_kinds = next(p['schema']['enum'] for p in schema['paths']['/api/study-source']['get']['parameters'] if p['name'] == 'artifactType')
        response_kinds = schema['components']['schemas']['StudySource']['properties']['artifactType']['enum']
        self.assertTrue(set(request_kinds).issubset(response_kinds))


if __name__ == '__main__':
    unittest.main()
