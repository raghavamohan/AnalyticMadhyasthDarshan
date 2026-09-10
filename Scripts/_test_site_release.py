"""Failure, isolation, and version consistency tests for complete site releases."""
from __future__ import annotations

import json
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import urlsplit
from urllib.error import HTTPError

import _site_release as release
import _publish_site_release as publisher
from _common import BASE


class FakeStore:
    def __init__(self, fail_at=None):
        self.objects = {}
        self.calls = 0
        self.fail_at = fail_at

    def bucket(self):
        return 'test-generated'

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

    def build(self, output='bundle', source_sha='a'*40):
        sources = {}
        for name, body in self.files.items():
            path = self.source / name.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            sources[name] = path
        with patch.object(release, 'static_sources', return_value=sources):
            return release.build(self.root / output, None, root=self.source, source_sha=source_sha)

    def test_unchanged_release_is_deterministic_and_source_is_untouched(self):
        first = self.build()
        second = self.build('second')
        self.assertEqual(first, second)
        self.assertEqual((self.source / 'index.html').read_bytes(), self.files['/index.html'])
        self.assertIn(b"searchParams.get('r')", (self.root/'bundle/assets/index.html').read_bytes())
        self.assertNotIn(first['revision'].encode(), (self.root/'bundle/assets/index.html').read_bytes())
        source_only = self.build('source-only', source_sha='b'*40)
        self.assertEqual(source_only['revision'], first['revision'])
        self.assertEqual(source_only['files'], first['files'])
        self.assertEqual(source_only['sourceSha'], 'b'*40)
        self.files['/Studies/A/A.html'] = b'<html><head></head><body>Changed</body></html>'
        third = self.build('third')
        self.assertNotEqual(first['revision'], third['revision'])
        self.assertEqual(first['files']['/index.html'], third['files']['/index.html'])
        self.assertEqual(first['files']['/Assets/a.css'], third['files']['/Assets/a.css'])

    def test_content_revert_reuses_immutable_manifest(self):
        store = FakeStore()
        first = self.build('a')
        publisher.stage_objects(store, self.root/'a', first)
        original = self.files['/index.html']
        self.files['/index.html'] += b'changed'
        middle = self.build('b', source_sha='b'*40)
        publisher.stage_objects(store, self.root/'b', middle)
        self.files['/index.html'] = original
        restored = self.build('c', source_sha='c'*40)
        calls = store.calls
        publisher.stage_objects(store, self.root/'c', restored)
        self.assertEqual(first['revision'], restored['revision'])
        self.assertEqual(store.calls, calls)
        self.assertNotIn('sourceSha', release.content_manifest(restored))

    def test_partial_bundle_reuses_pdf_without_local_body_and_rechecks_remote(self):
        import _publication_plan as planner
        key = 'Studies/A/A.pdf'
        sha = release.digest(b'verified PDF')
        node = {'family': 'markdown', 'fingerprint': 'f'*64, 'inputs': {},
                'metadata': {}, 'producer': 'test', 'schema': 1}
        record = {'key': f'site/objects/{sha}', 'sha256': sha, 'bytes': 12,
                  'type': 'application/pdf', 'archive': True}
        pdf = {'sourceSha256': 'b'*64, 'sha256': sha, 'kind': 'markdown'}
        receipt = {'schema': 1, 'artifacts': {key: {'node': node, 'record': record, 'pdf': pdf}}}
        store = FakeStore()
        store.objects[record['key']] = {'x-amz-meta-sha256': sha, 'content-length': '12'}
        plan = planner.create_plan({key: node}, {'buildReceiptKey': planner.receipt_key(receipt)},
                                   receipt, store, store, source_sha='a'*40)
        plan_path = self.root/'plan.json'
        plan_path.write_bytes(release.encode(plan))
        page = self.source/'index.html'
        page.write_bytes(self.files['/index.html'])
        bundle = self.root/'partial'
        with patch.object(release, 'static_sources', return_value={'/index.html': page}), \
             patch.object(planner, 'build_graph', return_value={key: node}), \
             patch('_generated_pdf_inventory.generated_pdf_specs', return_value=()):
            manifest = release.build(bundle, self.root/'absent-render-job', root=self.source,
                                     source_sha='a'*40, plan_path=plan_path)
            self.assertFalse((bundle/'assets'/key).exists())
            self.assertEqual(release.validate_bundle(bundle), manifest)
            publisher.stage_objects(store, bundle, manifest)
            store.objects.pop(record['key'])
            with self.assertRaisesRegex(ValueError, 'disappeared during publication'):
                publisher.stage_objects(store, bundle, manifest)

    def test_deployment_receipts_allow_repeat_source_deployments(self):
        store = FakeStore()
        manifest = self.build()
        publisher.record_source_deployment(store, manifest, 'one')
        publisher.record_source_deployment(store, manifest, 'one')
        publisher.record_source_deployment(store, manifest, 'two')
        self.assertEqual(store.calls, 2)

    def test_runtime_fingerprint_tracks_delivery_modules_and_bindings(self):
        store = FakeStore()
        original = publisher.runtime_fingerprint(store)
        file = self.root/'worker.js'
        file.write_bytes(publisher.SOURCE.read_bytes() + b'\n// changed runtime\n')
        with patch.object(publisher, 'SOURCE', file):
            self.assertNotEqual(original, publisher.runtime_fingerprint(store))
        with patch.object(store, 'bucket', return_value='other-bucket'):
            self.assertNotEqual(original, publisher.runtime_fingerprint(store))

    def test_planned_and_internal_files_are_excluded(self):
        published = {('Studies','A')}
        for path in ['Studies/Planned/Planned.html','Studies/Planned/discussion.html','Studies/proposal-registry.json',
                     'Studies/companion-artifacts.json','Studies/README.md','Studies/A/.proposal-meta.json','.env',
                     'Scripts/_publish_site_release.py','Studies/A/Research-Template-X.md']:
            with self.subTest(path=path):
                self.assertFalse(release.eligible_static(path,published))
        self.assertTrue(release.eligible_static('Studies/A/A.html',published))
        self.assertTrue(release.eligible_static('Assets/reader/reader.js',published))

    def test_audit_identifies_itself_on_publication_get_and_asset_get_head_requests(self):
        manifest = self.build()
        requests = []
        def respond(request, **kwargs):
            self.assertEqual(request.get_header('User-agent'), publisher.AUDIT_USER_AGENT)
            requests.append(request)
            path = urlsplit(request.full_url).path
            if path == '/.well-known/publication.json':
                body = release.encode({'revision': manifest['revision'], 'sourceSha': manifest['sourceSha']})
            else:
                expected = ('v=' + manifest['files'][path]['sha256'] if path.endswith('.css') else 'r=' + manifest['revision'])
                self.assertIn(expected, request.full_url)
                body = (self.root / 'bundle/assets' / path.lstrip('/')).read_bytes()
            response = io.BytesIO(body)
            response.status = 200
            response.headers = {'Content-Length': str(len(body))}
            return response
        with patch.object(publisher, 'urlopen', side_effect=respond):
            publisher.audit('https://canary.example', self.root / 'bundle', manifest)
        self.assertEqual(len(requests), len(manifest['files']) + 1)
        self.assertEqual({request.get_method() for request in requests}, {'GET', 'HEAD'})

    def test_rejected_audit_request_still_fails_closed(self):
        with patch.object(publisher, 'urlopen', side_effect=HTTPError('https://canary.example', 403, 'Forbidden', {}, None)):
            with self.assertRaises(HTTPError):
                publisher.audit('https://canary.example', self.root, {'revision': 'a' * 64, 'files': {}})

    def test_markdown_without_length_is_downloaded_and_checksum_verified(self):
        path = '/.well-known/agent-skills/add-study/SKILL.md'
        body = b'# Skill\n'
        manifest = {'revision': 'a' * 64, 'files': {path: {'bytes': len(body), 'sha256': release.digest(body)}}}
        for returned in [body, b'# Wrong\n']:
            with self.subTest(returned=returned):
                response = io.BytesIO(returned)
                response.status = 200
                response.headers = {}
                with patch.object(publisher, 'public_state', return_value={'revision': manifest['revision']}), \
                     patch.object(publisher, 'urlopen', return_value=response) as fetch, \
                     patch.object(publisher.time, 'sleep') as sleep:
                    if returned == body:
                        publisher.audit('https://site.example', self.root, manifest)
                    else:
                        with self.assertRaisesRegex(ValueError, 'checksum/size'):
                            publisher.audit('https://site.example', self.root, manifest)
                    self.assertEqual(fetch.call_args.args[0].get_method(), 'GET')
                    self.assertEqual(fetch.call_count, 1)
                    sleep.assert_not_called()

    def test_managed_robots_preserves_exact_origin_and_rejects_other_changes(self):
        origin = b'User-agent: *\nAllow: /\n\nSitemap: https://example.org/sitemap.xml\n'
        record = {'bytes':len(origin), 'sha256':release.digest(origin)}
        wrapper = b'# Policy comments\n# BEGIN Cloudflare Managed content\nUser-agent: *\nContent-Signal: search=yes,ai-train=no\nAllow: /\nUser-agent: GPTBot\nDisallow: /\n# END Cloudflare Managed Content\n\n'
        self.assertTrue(publisher.edge_response_matches('/robots.txt', wrapper + origin + b'\n', record))
        for altered in [wrapper + origin.replace(b'Allow: /',b'Disallow: /'),
                        b'Disallow: /\n' + wrapper + origin,
                        wrapper.replace(b'User-agent:',b'Unexpected:') + origin,
                        wrapper.replace(b'# END Cloudflare Managed Content',b'') + origin]:
            self.assertFalse(publisher.edge_response_matches('/robots.txt', altered, record))
        self.assertFalse(publisher.edge_response_matches('/llms.txt', wrapper + origin, record))

    def test_managed_security_requires_identical_fields_and_verified_source(self):
        source = b'Contact: https://example.org/security\nExpires: 2027-06-23T23:59:59.000Z\nPreferred-Languages: en\n'
        record = {'bytes':len(source), 'sha256':release.digest(source)}
        public = b'Preferred-Languages: en\nExpires: 2027-06-23T23:59:59Z\nContact: https://example.org/security\n'
        self.assertTrue(publisher.edge_response_matches('/.well-known/security.txt', public, record, source))
        for altered in [public.replace(b'/security',b'/other'), public.replace(b'2027-',b'2026-'),
                        public + b'Contact: https://other.example\n', public.replace(b'Expires:',b'Malformed')]:
            self.assertFalse(publisher.edge_response_matches('/.well-known/security.txt', altered, record, source))
        self.assertFalse(publisher.edge_response_matches('/.well-known/security.txt', public, record, source+b'\n'))
        self.assertFalse(publisher.edge_response_matches('/.well-known/security.txt', public, record))

    def test_public_security_audit_checks_the_pinned_release_origin(self):
        path = '/.well-known/security.txt'
        source = b'Contact: https://example.org/security\nExpires: 2027-06-23T23:59:59.000Z\n'
        public = b'Expires: 2027-06-23T23:59:59Z\nContact: https://example.org/security\n'
        manifest = {'revision':'a'*64,'files':{path:{'bytes':len(source),'sha256':release.digest(source)}}}
        for origin_body in [source, source.replace(b'/security', b'/other')]:
            requests = []
            def respond(request, **kwargs):
                requests.append(request)
                body = origin_body if request.full_url.startswith('https://origin.example') else public
                response = io.BytesIO(body)
                response.status = 200
                response.headers = {}
                return response
            with patch.object(publisher, 'public_state', return_value={'revision':manifest['revision']}), \
                 patch.object(publisher, 'urlopen', side_effect=respond):
                if origin_body == source:
                    publisher.audit('https://' + publisher.cf.SITE_HOST, self.root, manifest, origin_base='https://origin.example')
                else:
                    with self.assertRaisesRegex(ValueError, 'checksum/size'):
                        publisher.audit('https://' + publisher.cf.SITE_HOST, self.root, manifest, origin_base='https://origin.example')
            self.assertEqual(requests[-1].full_url, 'https://origin.example' + path + '?r=' + manifest['revision'])

    def test_canary_audit_does_not_accept_managed_security_transformations(self):
        source = b'Contact: https://example.org/security\nExpires: 2027-06-23T23:59:59.000Z\n'
        public = source.replace(b'.000Z', b'Z')
        manifest = {'revision':'a'*64,'files':{'/.well-known/security.txt':{'bytes':len(source),'sha256':release.digest(source)}}}
        response = io.BytesIO(public)
        response.status = 200
        response.headers = {}
        with patch.object(publisher, 'public_state', return_value={'revision':manifest['revision']}), \
             patch.object(publisher, 'urlopen', return_value=response) as fetch:
            with self.assertRaisesRegex(ValueError, 'checksum/size'):
                publisher.audit('https://canary.example', self.root, manifest, origin_base='https://origin.example')
            self.assertEqual(fetch.call_count, 1)

    def test_audit_waits_for_revision_and_asset_propagation(self):
        body = b'page'
        manifest = {'revision': 'a' * 64, 'files': {'/index.html': {'bytes':len(body), 'sha256':release.digest(body)}}}
        response = io.BytesIO(body)
        response.status = 200
        response.headers = {}
        with patch.object(publisher, 'public_state', side_effect=[{'revision':'b'*64}, {'revision':'a'*64}]), \
             patch.object(publisher, 'urlopen', side_effect=[HTTPError('https://site.example/index.html',404,'Not Found',{},None), response]) as fetch, \
             patch.object(publisher.time, 'sleep') as sleep:
            publisher.audit('https://site.example', self.root, manifest)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2,2])

    def test_audit_propagation_retries_are_bounded_and_fail_closed(self):
        for code in [404,502,503,504,403]:
            def unavailable(*args, **kwargs):
                raise HTTPError('https://site.example',code,'Unavailable',{},None)
            with self.subTest(code=code), \
                 patch.object(publisher, 'urlopen', side_effect=unavailable) as fetch, \
                 patch.object(publisher.time, 'sleep') as sleep:
                with self.assertRaises(HTTPError):
                    publisher.audit('https://site.example', self.root, {'revision':'a'*64,'files':{}})
                self.assertEqual(fetch.call_count, 1 if code == 403 else 6)
                self.assertEqual(sleep.call_count, 0 if code == 403 else 5)
        with patch.object(publisher, 'public_state', return_value={'revision':'b'*64}) as state, \
             patch.object(publisher.time, 'sleep'):
            with self.assertRaises(publisher.ReleaseNotReady):
                publisher.audit('https://site.example', self.root, {'revision':'a'*64,'files':{}})
            self.assertEqual(state.call_count, 6)

    def test_full_r2_range_requires_complete_size_and_checksum(self):
        body = b'PDF content'
        path = '/Studies/A/A.pdf'
        manifest = {'revision': 'a' * 64, 'files': {path: {'bytes': len(body), 'sha256': release.digest(body)}}}
        complete = f'bytes 0-{len(body) - 1}/{len(body)}'
        for content_range, returned, valid in [(complete, body, True), ('bytes 0-2/11', body[:3], False),
                                                (complete, body[:-1], False), (complete, b'bad content', False),
                                                (None, body, False)]:
            with self.subTest(content_range=content_range, returned=returned):
                response = io.BytesIO(returned)
                response.status = 206
                response.headers = {'Content-Range': content_range}
                with patch.object(publisher, 'public_state', return_value={'revision': manifest['revision']}), \
                     patch.object(publisher, 'urlopen', return_value=response):
                    if valid:
                        publisher.audit('https://canary.example', self.root, manifest)
                    else:
                        with self.assertRaises(ValueError):
                            publisher.audit('https://canary.example', self.root, manifest)

    def test_html_pinning_preserves_canonical_external_and_reference_urls(self):
        data = b'''<html><head lang="en"><link rel="canonical" href="/Studies/A/A.html"></head><a href="/Studies/A/A.html?find=a&amp;section=b#c">A</a><a href="https://example.org/x">X</a><a href="/References/a.pdf">R</a></html>'''
        output = release.pin_html(data,'/index.html','b'*64,{'/Studies/A/A.html','/References/a.pdf'}).decode()
        self.assertIn('rel="canonical" href="/Studies/A/A.html"',output)
        self.assertIn('find=a&amp;section=b#c',output)
        self.assertIn('href="/References/a.pdf"',output)
        self.assertIn('href="https://example.org/x"',output)
        self.assertIn('window.AMD_RELEASE',output)

    def test_asset_changes_only_recompile_their_consumers(self):
        self.files['/Assets/font.woff2'] = b'font'
        self.files['/Assets/a.css'] = b'body{src:url("/Assets/font.woff2")}'
        self.files['/index.html'] = b'<html><head><link href="/Assets/a.css" rel="stylesheet"></head><body>Home</body></html>'
        first = self.build('a')
        css = (self.root / 'a/assets/Assets/a.css').read_bytes()
        self.assertIn(('v=' + release.digest(b'font')).encode(), css)
        self.assertIn(('v=' + release.digest(css)).encode(), (self.root / 'a/assets/index.html').read_bytes())
        self.files['/Assets/font.woff2'] = b'changed-font'
        second = self.build('b')
        self.assertNotEqual(first['files']['/index.html'], second['files']['/index.html'])
        self.assertEqual(first['files']['/Studies/A/A.html'], second['files']['/Studies/A/A.html'])

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

    def test_source_only_advance_skips_r2_staging_and_full_url_audits(self):
        manifest = self.build(source_sha='b'*40)
        active = {'revision': manifest['revision'], 'sourceSha': 'a'*40,
                  'runtimeFingerprint': publisher.runtime_fingerprint(FakeStore())}
        old_version = [{'versions': [{'version_id': 'previous-version'}]}]
        with ExitStack() as stack:
            for name, value in [('load_repo_env', None), ('cloudflare_api_token', 'token'), ('resolve_zone_id', 'zone')]:
                stack.enter_context(patch.object(publisher.cf, name, return_value=value))
            for name, value in [('_zone_account_id', 'account'), ('_workers_subdomain', 'subdomain'),
                                ('load_r2_config', {}), ('R2S3Client', FakeStore()),
                                ('deployments', old_version), ('public_state', active), ('assert_forward', None)]:
                stack.enter_context(patch.object(publisher, name, return_value=value))
            stack.enter_context(patch('_generated_pdf_inventory.generated_pdf_specs', return_value=()))
            deploy = stack.enter_context(patch.object(
                publisher, 'deploy', side_effect=['canary-version', 'candidate-version']
            ))
            marker = stack.enter_context(patch.object(publisher, 'audit_publication_marker'))
            public_marker = stack.enter_context(patch.object(publisher, 'audit_public_marker_if_active'))
            stage = stack.enter_context(patch.object(publisher, 'stage_objects'))
            audit = stack.enter_context(patch.object(publisher, 'audit'))
            activate = stack.enter_context(patch.object(publisher, 'activate_version'))
            receipt = stack.enter_context(patch.object(publisher, 'record_source_deployment'))
            publisher.publish(self.root/'bundle', promote=True)

        self.assertEqual([call.args[2] for call in deploy.call_args_list], [publisher.CANARY, publisher.WORKER])
        self.assertEqual([call.args[2] for call in activate.call_args_list], ['candidate-version'])
        self.assertEqual(marker.call_count, 2)
        public_marker.assert_called_once()
        stage.assert_not_called()
        audit.assert_not_called()
        receipt.assert_called_once()

    def test_same_content_with_changed_runtime_requires_full_canary_audit(self):
        manifest = self.build(source_sha='b'*40)
        active = {'revision': manifest['revision'], 'sourceSha': 'a'*40, 'runtimeFingerprint': 'old-runtime'}
        with ExitStack() as stack:
            for name, value in [('load_repo_env', None), ('cloudflare_api_token', 'token'), ('resolve_zone_id', 'zone')]:
                stack.enter_context(patch.object(publisher.cf, name, return_value=value))
            for name, value in [('_zone_account_id', 'account'), ('_workers_subdomain', 'subdomain'),
                                ('load_r2_config', {}), ('R2S3Client', FakeStore()),
                                ('deployments', [{'versions': [{'version_id': 'old'}]}]),
                                ('public_state', active), ('assert_forward', None)]:
                stack.enter_context(patch.object(publisher, name, return_value=value))
            stack.enter_context(patch('_generated_pdf_inventory.generated_pdf_specs', return_value=()))
            stage = stack.enter_context(patch.object(publisher, 'stage_objects'))
            deploy = stack.enter_context(patch.object(publisher, 'deploy', return_value='canary'))
            audit = stack.enter_context(patch.object(publisher, 'audit'))
            shortcut = stack.enter_context(patch.object(publisher, 'advance_source_pointer'))
            publisher.publish(self.root / 'bundle', promote=False)
            stage.assert_called_once()
            deploy.assert_called_once()
            audit.assert_called_once()
            shortcut.assert_not_called()

    def test_marker_audit_requires_expected_runtime_and_build_receipt(self):
        marker = {'revision': 'a'*64, 'sourceSha': 'b'*40, 'runtimeFingerprint': 'c'*64, 'buildReceiptKey': 'receipt'}
        for field in ('runtimeFingerprint', 'buildReceiptKey'):
            with patch.object(publisher, 'public_state', return_value={**marker, field: 'stale'}), \
                 patch.object(publisher, 'audit_retry', side_effect=lambda operation, _: operation()):
                with self.assertRaises(publisher.ReleaseNotReady):
                    publisher.audit_publication_marker('https://canary.example', marker)

    def test_source_only_advance_rolls_back_failed_production_marker(self):
        manifest = self.build(source_sha='b'*40)
        active = {'revision': manifest['revision'], 'sourceSha': 'a'*40,
                  'runtimeFingerprint': publisher.runtime_fingerprint(FakeStore())}
        old_version = [{'versions': [{'version_id': 'previous-version'}]}]
        with ExitStack() as stack:
            for name, value in [('load_repo_env', None), ('cloudflare_api_token', 'token'), ('resolve_zone_id', 'zone')]:
                stack.enter_context(patch.object(publisher.cf, name, return_value=value))
            for name, value in [('_zone_account_id', 'account'), ('_workers_subdomain', 'subdomain'),
                                ('load_r2_config', {}), ('R2S3Client', FakeStore()),
                                ('deployments', old_version), ('public_state', active), ('assert_forward', None)]:
                stack.enter_context(patch.object(publisher, name, return_value=value))
            stack.enter_context(patch('_generated_pdf_inventory.generated_pdf_specs', return_value=()))
            stack.enter_context(patch.object(
                publisher, 'deploy', side_effect=['canary-version', 'candidate-version']
            ))
            stack.enter_context(patch.object(
                publisher, 'audit_publication_marker', side_effect=[None, OSError('marker failed')]
            ))
            stack.enter_context(patch.object(publisher, 'audit_public_marker_if_active'))
            activate = stack.enter_context(patch.object(publisher, 'activate_version'))
            receipt = stack.enter_context(patch.object(publisher, 'record_source_deployment'))

            with self.assertRaisesRegex(OSError, 'marker failed'):
                publisher.publish(self.root/'bundle', promote=True)

        self.assertEqual(
            [call.args[2] for call in activate.call_args_list],
            ['candidate-version', 'previous-version'],
        )
        receipt.assert_not_called()

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
