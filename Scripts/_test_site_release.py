"""Failure, isolation, and version consistency tests for complete site releases."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import _site_release as release
import _publish_site_release as publisher
from _common import BASE


class FakeStore:
    def __init__(self, fail_at=None):
        self.objects = {}
        self.calls = 0
        self.fail_at = fail_at

    def head_object(self, key):
        return self.objects.get(key)

    def put_object(self, key, body, **kwargs):
        self.calls += 1
        if self.calls == self.fail_at:
            raise OSError('simulated interrupted upload')
        headers = {'x-amz-meta-sha256': release.digest(body), 'content-length': str(len(body))}
        self.objects[key] = headers
        return headers


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.files = {'/index.html': b'<html><head></head><body><a href="/Studies/A/A.html">A</a></body></html>',
                      '/Studies/A/A.html': b'<html><head></head><body>A</body></html>',
                      '/Assets/a.css': b'body { color: black }'}

    def build(self, output='bundle'):
        sources = {}
        for name, body in self.files.items():
            path = self.source / name.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            sources[name] = path
        with patch.object(release, 'static_sources', return_value=sources):
            return release.build(self.root / output, None, root=self.source, source_sha='a'*40)

    def test_unchanged_release_is_deterministic_and_source_is_untouched(self):
        first = self.build()
        second = self.build('second')
        self.assertEqual(first, second)
        self.assertEqual((self.source / 'index.html').read_bytes(), self.files['/index.html'])
        self.assertIn(('?r=' + first['revision']).encode(), (self.root/'bundle/assets/index.html').read_bytes())
        self.files['/Studies/A/A.html'] = b'<html><head></head><body>Changed</body></html>'
        self.assertNotEqual(first['revision'], self.build('third')['revision'])

    def test_planned_and_internal_files_are_excluded(self):
        published = {('Studies','A')}
        for path in ['Studies/Planned/Planned.html','Studies/Planned/discussion.html','Studies/proposal-registry.json',
                     'Studies/A/.proposal-meta.json','.env','Scripts/_publish_site_release.py','Studies/A/Research-Template-X.md']:
            with self.subTest(path=path):
                self.assertFalse(release.eligible_static(path,published))
        self.assertTrue(release.eligible_static('Studies/A/A.html',published))
        self.assertTrue(release.eligible_static('Assets/reader/reader.js',published))

    def test_html_pinning_preserves_canonical_external_and_reference_urls(self):
        data = b'''<html><head lang="en"><link rel="canonical" href="/Studies/A/A.html"></head><a href="/Studies/A/A.html?find=a&amp;section=b#c">A</a><a href="https://example.org/x">X</a><a href="/References/a.pdf">R</a></html>'''
        output = release.pin_html(data,'/index.html','b'*64,{'/Studies/A/A.html','/References/a.pdf'}).decode()
        self.assertIn('rel="canonical" href="/Studies/A/A.html"',output)
        self.assertIn('find=a&amp;section=b&amp;r=' + 'b'*64 + '#c',output)
        self.assertIn('href="/References/a.pdf"',output)
        self.assertIn('href="https://example.org/x"',output)
        self.assertIn('window.AMD_RELEASE',output)

    def test_corrupt_bundle_and_traversal_fail_before_upload(self):
        self.build()
        (self.root/'bundle/assets/index.html').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'checksum'):
            release.validate_bundle(self.root/'bundle')
        for path in ['/../secret','//host/a','/A/./a','/A\\a','/a?b']:
            self.assertFalse(release.safe_path(path))

    def test_partial_stage_retains_old_objects_and_retry_is_idempotent(self):
        manifest = self.build()
        store = FakeStore(fail_at=2)
        store.objects['old-live-key'] = {'x-amz-meta-sha256':'old','content-length':'3'}
        with self.assertRaises(OSError):
            publisher.stage_objects(store,self.root/'bundle',manifest)
        self.assertIn('old-live-key',store.objects)
        self.assertNotIn('site/releases/' + manifest['revision'] + '.json',store.objects)
        store.fail_at = None
        publisher.stage_objects(store,self.root/'bundle',manifest)
        calls = store.calls
        publisher.stage_objects(store,self.root/'bundle',manifest)
        self.assertEqual(store.calls,calls)
        self.assertIn('old-live-key',store.objects)

    def test_immutable_collision_is_fatal(self):
        store = FakeStore()
        publisher.put_verified(store,'key',b'one','text/plain',filename='one.txt')
        with self.assertRaisesRegex(ValueError,'collision'):
            publisher.put_verified(store,'key',b'two','text/plain',filename='one.txt')

    def test_large_retained_reference_is_segmented_but_never_archived(self):
        self.files['/References/large.pdf'] = b'x' * (26*1024*1024)
        manifest = self.build()
        record = manifest['files']['/References/large.pdf']
        self.assertFalse(record['archive'])
        self.assertEqual(len(record['parts']),2)
        release.validate_bundle(self.root/'bundle')
        store = FakeStore()
        publisher.stage_objects(store,self.root/'bundle',manifest)
        self.assertNotIn(record['key'],store.objects)
        (self.root/'bundle/assets'/record['parts'][1].lstrip('/')).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'segment'):
            release.validate_bundle(self.root/'bundle')

    def test_old_or_unrelated_run_cannot_promote(self):
        with patch.object(publisher.subprocess,'run') as run:
            run.return_value.returncode = 1
            with self.assertRaisesRegex(ValueError,'older or unrelated'):
                publisher.assert_forward({'sourceSha':'b'*40},{'sourceSha':'a'*40})
            run.return_value.returncode = 0
            publisher.assert_forward({'sourceSha':'a'*40},{'sourceSha':'b'*40})

    def test_failed_production_audit_restores_previous_deployment(self):
        manifest = self.build()
        old_version = [{'versions':[{'version_id':'previous-version'}]}]
        with ExitStack() as stack:
            for name,value in [('load_repo_env',None),('cloudflare_api_token','token'),('resolve_zone_id','zone')]:
                stack.enter_context(patch.object(publisher.cf,name,return_value=value))
            for name,value in [('_zone_account_id','account'),('_workers_subdomain','subdomain'),('load_r2_config',{}),
                               ('R2S3Client',FakeStore()),('deployments',old_version),
                               ('public_state',{'revision':'f'*64,'sourceSha':'b'*40}),('assert_forward',None)]:
                stack.enter_context(patch.object(publisher,name,return_value=value))
            stack.enter_context(patch('_generated_pdf_inventory.generated_pdf_specs',return_value=()))
            stack.enter_context(patch.object(publisher,'deploy',return_value='candidate-version'))
            stack.enter_context(patch.object(publisher,'audit',side_effect=[None,OSError('production audit failed')]))
            activate=stack.enter_context(patch.object(publisher,'activate_version'))
            with self.assertRaisesRegex(OSError,'production audit'):
                publisher.publish(self.root/'bundle',promote=True)
            self.assertEqual([call.args[2] for call in activate.call_args_list],['candidate-version','previous-version'])

    def test_same_source_different_bytes_does_not_silently_replace_release(self):
        with self.assertRaisesRegex(ValueError,'different bytes'):
            publisher.assert_forward({'sourceSha':'a'*40,'revision':'b'*64},{'sourceSha':'a'*40,'revision':'c'*64})

    def test_initial_deployment_receipt_uses_version_id_not_script_name(self):
        with patch.object(publisher, 'upload_assets', return_value='asset-jwt'), \
             patch.object(publisher, '_multipart_put', return_value={'success': True, 'result': {'id': 'amd-site'}}), \
             patch.object(publisher, 'reference_bucket_name', return_value='references'), \
             patch.object(publisher.cf, '_api_request', side_effect=[{}, {'result': {'deployments': [{'versions': [{'version_id': 'real-version'}]}]}}]):
            client = type('Client', (), {'bucket': lambda self: 'generated'})()
            version = publisher.deploy('token', 'account', publisher.WORKER, client, self.root, {}, version_only=False)
            self.assertEqual(version, 'real-version')

    def test_cutover_batches_purges_and_restores_reference_routes_on_audit_failure(self):
        import _cutover_site_release as cutover
        manifest = {'files': {f'/file-{i}.html': {} for i in range(65)}}
        previous = [{'id': 'reference-route', 'pattern': f'{cutover.cf.SITE_HOST}/References/*', 'script': 'amd-generated-pdfs'}]
        installed = [{'id': 'site-route', 'pattern': f'{cutover.cf.SITE_HOST}/*', 'script': cutover.WORKER}]
        with ExitStack() as stack:
            stack.enter_context(patch.object(cutover, 'validate_bundle', return_value=manifest))
            for name, value in [('load_repo_env', None), ('cloudflare_api_token', 'token'), ('resolve_zone_id', 'zone')]:
                stack.enter_context(patch.object(cutover.cf, name, return_value=value))
            stack.enter_context(patch.object(cutover, '_zone_account_id', return_value='account'))
            stack.enter_context(patch.object(cutover, '_workers_subdomain', return_value='subdomain'))
            stack.enter_context(patch.object(cutover.cf, 'list_worker_routes', side_effect=[previous, installed]))
            stack.enter_context(patch.object(cutover.cf, 'ensure_worker_route'))
            stack.enter_context(patch.object(cutover, 'audit', side_effect=[None, OSError('public audit failed')]))
            purge = stack.enter_context(patch.object(cutover.cf, 'purge_cache_files'))
            api = stack.enter_context(patch.object(cutover.cf, '_api_request'))
            with self.assertRaisesRegex(OSError, 'public audit'):
                cutover.cutover(self.root, apply=True)
            self.assertEqual([len(call.args[2]) for call in purge.call_args_list], [30, 30, 5])
            self.assertEqual(api.call_args_list[0].args[:2], ('DELETE', '/zones/zone/workers/routes/reference-route'))
            self.assertEqual(api.call_args_list[-1].args[3], {key: previous[0][key] for key in ('pattern', 'script')})

    def test_worker_serves_one_revision_ranges_and_retired_paths(self):
        worker = self.root/'worker'
        worker.mkdir()
        for source, target in [(BASE/'infra/site-worker/src/index.js','index.js'),
                               (BASE/'infra/generated-pdf-worker/src/index.js','pdf.js'),
                               (BASE/'infra/generated-pdf-worker/src/generated-pdf-keys.js','generated-pdf-keys.js')]:
            shutil.copyfile(source,worker/target)
        (worker/'release.js').write_bytes(b'export default {};')
        (worker/'package.json').write_bytes(b'{"type":"module"}')
        shutil.copyfile(BASE/'Scripts/_test_site_worker.mjs',worker/'test.mjs')
        result = subprocess.run(['node',str(worker/'test.mjs')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)


if __name__ == '__main__':
    unittest.main()
