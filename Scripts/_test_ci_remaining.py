"""Failure-boundary checks for candidate gates and historical review recovery."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import _canary_publications as canary
import _review_artifacts as reviews
import _worker_deployment as deployment


class CandidateTests(unittest.TestCase):
    def test_receipt_binds_exact_executable_metadata_account_and_freshness(self):
        source, metadata = 'candidate', {'compatibility_flags': ['global_fetch_strictly_public']}
        receipt = {'schema': 1, 'passed': True, 'cleanup': 'complete', 'account': 'account',
                   'checkedAt': datetime.now(timezone.utc).isoformat(),
                   'candidates': {'worker': {'fingerprint': canary.candidate_key(source, metadata)}}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'receipt.json'
            path.write_text(json.dumps(receipt))
            canary.require_receipt(path, 'worker', source, metadata, 'account')
            for incoming in [('other', metadata, 'account'), (source, {}, 'account'), (source, metadata, 'other')]:
                with self.assertRaises(ValueError):
                    canary.require_receipt(path, 'worker', *incoming)
            receipt['checkedAt'] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                canary.require_receipt(path, 'worker', source, metadata, 'account')

    def test_deploy_never_uploads_or_checks_active_state_before_required_canary(self):
        with patch.dict('os.environ', {'AMD_REQUIRE_CANARY': '1', 'AMD_CANARY_RECEIPT': 'missing'}), \
             patch.object(canary, 'require_receipt', side_effect=ValueError('failed canary')), \
             patch.object(deployment, 'active_fingerprint') as active:
            uploader = unittest.mock.Mock()
            with self.assertRaises(ValueError):
                deployment.deploy_source('token', 'account', 'worker', 'source', {}, uploader)
            active.assert_not_called()
            uploader.assert_not_called()

    def test_failed_audit_cleans_only_owned_route_and_script_and_emits_no_pass(self):
        import _publish_mcp_server_card as uploader
        calls = []
        def api(method, path, token, payload=None, **kwargs):
            calls.append((method, path, payload))
            if method == 'GET':
                return {'result': [{'id': 'ours', 'pattern': 'analyticmadhyasthdarshan.org/__amd_ci/' + 'a'*16 + '/candidate/*',
                                    'script': 'amd-ci-' + 'a'*16 + '-candidate'},
                                   {'id': 'production', 'pattern': 'analyticmadhyasthdarshan.org/*', 'script': 'amd-site'}]}
            return {'success': True}
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(canary.uuid, 'uuid4', return_value=unittest.mock.Mock(hex='a'*32)), \
             patch.object(canary, 'candidates', return_value={'candidate': ('export default {};', {})}), \
             patch.object(canary, 'audit', side_effect=ValueError('bad response')), \
             patch.object(canary.cf, 'load_repo_env'), \
             patch.object(canary.cf, 'cloudflare_api_token', return_value='token'), \
             patch.object(canary.cf, 'resolve_zone_id', return_value='zone'), \
             patch.object(uploader, 'resolve_account_id', return_value='account'), \
             patch.object(uploader, 'multipart_put', return_value={'success': True}), \
             patch.object(canary.cf, '_api_request', side_effect=api):
            path = Path(temporary) / 'receipt.json'
            with self.assertRaises(ValueError):
                canary.run(path)
            self.assertFalse(path.exists())
        deletes = [path for method, path, _ in calls if method == 'DELETE']
        self.assertEqual(len(deletes), 2)
        self.assertTrue(any(path.endswith('/ours') for path in deletes))
        self.assertFalse(any('production' in path or path.endswith('/amd-site') for path in deletes))


class RecoveryTests(unittest.TestCase):
    def test_recent_closed_fork_unmerged_and_future_prs_cannot_supply_recovery(self):
        repo = 'owner/repo'
        def pr(number, **changes):
            return {**{'number': number, 'merged_at': 'date', 'merge_commit_sha': str(number)*40,
                       'head': {'sha': 'h', 'repo': {'full_name': repo}},
                       'base': {'ref': 'master', 'repo': {'full_name': repo}}}, **changes}
        old, current = pr(1), pr(2)
        fork = pr(3, head={'repo': {'full_name': 'fork/repo'}})
        unmerged = pr(4, merged_at=None)
        future = pr(5)
        def ancestry(command, **kwargs):
            return subprocess.CompletedProcess(command, 1 if command[-2] == '5'*40 else 0)
        gh = unittest.mock.Mock(side_effect=[[current], [future, current, old, fork, unmerged]])
        with patch.object(reviews.subprocess, 'run', side_effect=ancestry):
            self.assertEqual(reviews.recovery_prs(repo, 'target', gh), [current, old])
        self.assertEqual(gh.call_count, 2)


class RetentionTests(unittest.TestCase):
    def test_only_old_unreachable_exact_backup_matches_are_candidates(self):
        from _plan_r2_gc import plan
        now = datetime.now(timezone.utc)
        sha = 'a'*64
        row = {'bucket': 'bucket', 'key': 'site/objects/' + sha, 'etag': 'etag', 'bytes': 4,
               'last_modified': (now-timedelta(days=100)).isoformat()}
        backup = {'objects': [{**row, 'sha256': sha}]}
        result = plan([row], set(), backup, now)
        self.assertEqual(len(result['candidates']), 1)
        self.assertFalse(result['deletionAuthorized'])
        for rows, protected, saved in [([row], {row['key']}, backup),
                                        ([{**row, 'last_modified':now.isoformat()}], set(), backup),
                                        ([row], set(), {'objects':[{**row, 'etag':'changed', 'sha256':sha}]}),
                                        ([{**row, 'key':'References/source.pdf'}], set(), backup)]:
            self.assertFalse(plan(rows, protected, saved, now)['candidates'])

    def test_all_retained_releases_and_shared_asset_bindings_protect_blobs(self):
        from _plan_r2_gc import reachable
        sha = 'a'*64
        record = {'key':'site/objects/'+sha, 'sha256':sha, 'bytes':4, 'archive':True}
        release = {'schema':1,'revision':'b'*64,'files':{'/Studies/Retired/Retired.pdf':record}}
        self.assertIn(record['key'], reachable({'site/releases/'+'b'*64+'.json':release}))
        with self.assertRaises(ValueError):
            reachable({'site/releases/'+'b'*64+'.json':{**release,'files':{'/../secret':record}}})


class SummaryTests(unittest.TestCase):
    def test_failed_jobs_do_not_turn_selection_into_completion(self):
        from _publication_summary import summary
        plan = {'nodes':{'A':{'family':'markdown'}},'build':['A'],'reuse':{},'sourceSha':'source'}
        text = summary(plan, [{'kind':'worker','name':'amd-site','outcome':'audit failed; restored prior version'}],
                       {'pdfs':{'result':'failure'}})
        self.assertIn('1 selected for build', text)
        self.assertIn('restored prior version', text)
        self.assertIn('| pdfs | failure |', text)
        self.assertIn('No staging receipt', text)


if __name__ == '__main__':
    unittest.main()
