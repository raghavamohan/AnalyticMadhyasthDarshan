"""Trust boundaries, source ownership and recovery for incremental publication."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import _review_artifacts as review
import _worker_deployment as workers
import _verification_identity as identity
import _publication_plan as planner


class PublicationProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.node = {'family': 'markdown', 'fingerprint': 'a'*64}
        self.key = 'Studies/A/A.pdf'
        self.body = b'%PDF-1.7 verified fixture bytes'
        self.record = {'node': self.node, 'sha256': hashlib.sha256(self.body).hexdigest(), 'bytes': len(self.body)}
        self.proof = {'schema': 1, 'repository': 'owner/repo', 'head': 'a'*40,
                      'artifacts': {self.key: self.record}}

    def archive(self, proof=None, body=None, extra=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr(review.PROOF, json.dumps(proof or self.proof))
            archive.writestr(self.key, self.body if body is None else body)
            for name, data in (extra or {}).items():
                archive.writestr(name, data)
        return buffer.getvalue()

    def read(self, data, nodes=None):
        return review.read_proof(data, repository='owner/repo', head='a'*40,
                                 nodes=nodes or {self.key: self.node}, wanted={self.key})

    def test_exact_input_review_can_be_reused_without_rendering(self):
        accepted, bodies = self.read(self.archive())
        self.assertEqual(accepted[self.key], self.record)
        self.assertEqual(bodies[self.key], self.body)

    def test_fork_head_and_checksum_cannot_claim_a_review(self):
        for field, value in [('repository', 'fork/repo'), ('head', 'b'*40), ('schema', 0)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.read(self.archive({**self.proof, field: value}))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.read(self.archive(body=b'tampered'))

    def test_changed_inputs_are_rebuilt_instead_of_reusing_old_review(self):
        self.assertEqual(self.read(self.archive(), {self.key: {**self.node, 'fingerprint': 'b'*64}})[0], {})

    def test_archive_paths_cannot_escape_or_smuggle_duplicates(self):
        for name in ['../escape', '/absolute', 'C:/drive', 'Studies\\escape']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unsafe'):
                self.read(self.archive(extra={name: b'bad'}).replace(b'Studies/escape', b'Studies\\escape'))

    def test_deck_review_requires_both_outputs(self):
        node = {'family': 'presentations', 'deck': 'a'}
        proof = copy.deepcopy(self.proof)
        proof['artifacts'][self.key]['node'] = node
        nodes = {self.key: node, 'Studies/A/A-notes.pdf': node}
        accepted, _ = review.read_proof(self.archive(proof), repository='owner/repo', head='a'*40,
                                        nodes=nodes, wanted=set(nodes))
        self.assertEqual(accepted, {})

    def test_protected_receipt_checksum_and_reuse_authority(self):
        receipt = {'schema': 1, 'artifacts': {self.key: {'node': self.node, 'record': self.record}}}
        client = unittest.mock.Mock()
        client.get_object.return_value = json.dumps(receipt).encode()
        key = planner.receipt_key(receipt)
        self.assertEqual(planner.load_receipt(client, key), receipt)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            planner.load_receipt(client, 'site/builds/' + 'f'*64 + '.json')
        plan = {'baseline': {'buildReceiptKey': key}, 'reuse': copy.deepcopy(receipt['artifacts'])}
        planner.verify_reuse_authority(client, plan)
        plan['reuse'][self.key]['record']['sha256'] = 'b'*64
        with self.assertRaisesRegex(ValueError, 'protected receipt'):
            planner.verify_reuse_authority(client, plan)

    def test_verification_identity_tracks_head_base_and_intent(self):
        pr = {'head': {'sha': 'a'*40}, 'base': {'sha': 'b'*40}, 'body': 'Study-Action: update'}
        key = identity.verification_key(pr)
        for field in ['head', 'base', 'body']:
            changed = copy.deepcopy(pr)
            if field == 'body':
                changed[field] += '\nStudy: Other'
            else:
                changed[field]['sha'] = 'c'*40
            self.assertNotEqual(identity.verification_key(changed), key)

    def test_portal_source_is_preparing_until_explicit_verification(self):
        pr = {'draft': True, 'body': 'Portal-GitHub: @author',
              'head': {'repo': {'full_name': 'owner/repo'}}, 'base': {'repo': {'full_name': 'owner/repo'}}}
        self.assertTrue(identity.is_preparing(pr))
        self.assertFalse(identity.is_preparing(pr, 'a'*40))
        self.assertFalse(identity.is_preparing({**pr, 'draft': False}))
        pr['head']['repo']['full_name'] = 'fork/repo'
        self.assertFalse(identity.is_preparing(pr))

    def test_preparation_contract_accepts_only_declared_companion_outputs(self):
        from _generated_artifacts import permits
        prefix = 'Studies/The-Ontology-of-Coexistence/'
        for name in ['Presenters-Companion-Ontology-of-Existence.docx',
                     'Presenters-Companion-Ontology-of-Existence.notes.json',
                     'The-Ontology-of-Existence-Madhyasth-Darshan.pptx']:
            self.assertTrue(permits(prefix + name), name)
        self.assertFalse(permits(prefix + 'Unregistered.pptx'))
        # Its contents are separately checked against trusted ownership before
        # acceptance; path permission alone cannot redefine binary write access.
        self.assertTrue(permits('Scripts/companion-pipeline.json'))

    def test_no_redundant_dispatch_for_same_successful_verification(self):
        pr = {'number': 1, 'head': {'sha': 'a'*40, 'ref': 'branch'}, 'base': {'sha': 'b'*40}}
        run = {'display_title': 'verify / ' + identity.verification_key(pr), 'status': 'completed', 'conclusion': 'success'}
        with patch('_bootstrap_ci.gh', return_value={'workflow_runs': [run]}), patch('_bootstrap_ci.command') as command:
            identity.dispatch('owner/repo', pr)
            command.assert_not_called()

    def test_unchanged_worker_skips_upload_but_changed_binding_does_not(self):
        metadata = {'bindings': [{'name': 'STORE', 'bucket_name': 'one'}]}
        key = workers.digest({'schema': 1, 'source': 'export default {}', 'metadata': metadata})
        upload = unittest.mock.Mock(return_value={'success': True})
        with patch.object(workers, 'active_fingerprint', return_value=key):
            workers.deploy_source('token', 'account', 'worker', 'export default {}', metadata, upload)
            upload.assert_not_called()
            workers.deploy_source('token', 'account', 'worker', 'export default {}', {'bindings': []}, upload)
        self.assertEqual(upload.call_count, 1)
        self.assertIn(workers.ANNOTATION, upload.call_args.args[-1]['annotations']['workers/message'])

    def test_worker_uses_active_version_after_rollback(self):
        with patch.object(workers.cf, '_api_request', side_effect=[
            {'result': {'deployments': [{'versions': [{'version_id': 'rollback', 'percentage': 100}]}]}},
            {'result': {'annotations': {'workers/message': workers.ANNOTATION + 'a'*64}}},
        ]) as request:
            self.assertEqual(workers.active_fingerprint('token', 'account', 'worker'), 'a'*64)
            self.assertTrue(request.call_args.args[1].endswith('/versions/rollback'))

    def test_worker_scope_follows_imports_and_config_but_not_frontend(self):
        (self.root / 'wrangler.toml').write_bytes(b'name="fixture"\nmain="index.js"\n')
        (self.root / 'package-lock.json').write_bytes(b'{}')
        (self.root / 'index.js').write_bytes(b"import './helper.js';\nexport default {}")
        (self.root / 'helper.js').write_bytes(b'export const a = 1')
        with patch.object(workers.cf, 'BASE', self.root):
            first = workers.directory_fingerprint(self.root)
            (self.root / 'submit.html').write_bytes(b'changed frontend')
            self.assertEqual(workers.directory_fingerprint(self.root), first)
            (self.root / 'helper.js').write_bytes(b'export const a = 2')
            self.assertNotEqual(workers.directory_fingerprint(self.root), first)

    def test_companion_outputs_match_canonical_sources(self):
        from _verify_companion_outputs import verify
        self.assertEqual(verify(), [])

    def test_docx_rebuild_is_byte_identical(self):
        from _build_presenters_companion import build_docx
        source, output = self.root / 'note.md', self.root / 'note.docx'
        source.write_bytes(b'# Note\n\nOne paragraph.\n')
        build_docx(source, output)
        first = output.read_bytes()
        build_docx(source, output)
        self.assertEqual(output.read_bytes(), first)

    def test_release_navigation_and_mixed_offline_contract(self):
        import subprocess
        result = subprocess.run(['node', str(review.BASE / 'Scripts/_test_release_navigation.mjs')],
                                cwd=review.BASE, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_partial_job_artifacts_preserve_all_deck_provenance(self):
        from types import SimpleNamespace
        downloads, output = self.root / 'downloads', self.root / 'merged'
        for name, deck in [('generated-reviewed-pdfs', 'a'), ('generated-presentation-pdfs', 'b')]:
            directory = downloads / name
            directory.mkdir(parents=True)
            (directory / 'presentation-build-provenance.json').write_bytes(json.dumps({
                'schemaVersion': 1, 'rendererProfile': 'pinned', 'artifacts': [{'id': deck}]}).encode())
        directory = downloads / 'generated-markdown-pdfs'
        target = directory / self.key
        target.parent.mkdir(parents=True)
        target.write_bytes(self.body)
        (directory / 'markdown-build-provenance.json').write_bytes(b'{}')
        with patch('_generated_pdf_inventory.generated_pdf_specs', return_value=(SimpleNamespace(key=self.key),)), \
             patch('_reference_artifacts.load_manifest', return_value={'artifacts': []}):
            review.merge_outputs(downloads, output)
            self.assertEqual((output / self.key).read_bytes(), self.body)
            self.assertEqual({r['id'] for r in json.loads((output / 'presentation-build-provenance.json').read_bytes())['artifacts']}, {'a', 'b'})
            (directory / 'untrusted.py').write_bytes(b'print("bad")')
            with self.assertRaisesRegex(ValueError, 'Unexpected'):
                review.merge_outputs(downloads, output)

    def test_batch_search_finalizes_once_and_never_after_failed_batch(self):
        import _study_search as search
        with patch.object(search, 'eligible_documents', return_value={}) as final, \
             patch.object(search, 'write_text_lf'), patch.object(search, 'DATA', self.root), \
             patch('_build_reader_offline.write_offline_catalog'):
            with search.batch_search_updates():
                search.write_search_catalog()
                with search.batch_search_updates():
                    search.write_search_catalog()
                final.assert_not_called()
            final.assert_called_once()
            final.reset_mock()
            with self.assertRaises(ValueError), search.batch_search_updates():
                search.write_search_catalog()
                raise ValueError('failed document')
            final.assert_not_called()


if __name__ == '__main__':
    unittest.main()
