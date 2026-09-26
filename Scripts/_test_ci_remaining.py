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


if __name__ == '__main__':
    unittest.main()
