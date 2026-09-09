"""CI trust boundaries, preparation retries, and lifecycle intent regression tests."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import _bootstrap_ci as bootstrap
import _generated_artifacts as contract
import _prepared_study as prepared
from _validate_study_change import infer_intent


class PreparationTests(unittest.TestCase):
    def test_intent_is_not_label_dependent(self):
        self.assertEqual(infer_intent('', ['Studies/A/A.md'], 'base'),'study-update')
        self.assertEqual(infer_intent('Proposal issue: #12', ['Studies/A/A.md'], 'base'),'new-study')
        self.assertEqual(infer_intent('Target status: released', [], 'base'),'status-change')
        self.assertIsNone(infer_intent('', ['Assets/icon.svg'], 'base'))

    def test_accept_requires_exact_head_open_draft_and_same_repository(self):
        pr={'number':1,'state':'open','draft':True,'head':{'sha':'a'*40,'repo':{'full_name':'owner/repo'}},'base':{'ref':'master'}}
        payload={'schema':1,'pr':1,'repository':'owner/repo','head':'a'*40,'files':{'sitemap.xml':base64.b64encode(b'new').decode(),'Studies/A/discussion.html':None}}
        self.assertEqual(prepared.validate(payload,pr,'owner/repo'),{'sitemap.xml':b'new','Studies/A/discussion.html':None})
        for change in [{'head':'b'*40},{'repository':'fork/repo'},{'pr':2},
                       {'files':{'.github/workflows/escalate.yml':base64.b64encode(b'bad').decode()}},
                       {'files':{'Studies/../.env':None}}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                prepared.validate({**payload,**change},pr,'owner/repo')
        with self.assertRaises(ValueError):
            prepared.validate(payload,{**pr,'draft':False},'owner/repo')

    def test_approval_is_rechecked_and_closed_issue_is_not_resurrected(self):
        bootstrap.assert_approved({'state':'open','labels':[{'name':'proposal-approved'}]})
        for issue in [{'state':'closed','labels':[{'name':'proposal-approved'}]},{'state':'open','labels':[]}]:
            with self.assertRaises(ValueError):
                bootstrap.assert_approved(issue)

    def test_bootstrap_resumes_publication_after_already_completed_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); studies=root/'Studies'; studies.mkdir()
            (studies/'proposal-registry.json').write_bytes(json.dumps({'proposals':[{'issueNumber':5,'slug':'A','phase':'pre-catalog'}]}).encode())
            (studies/'catalog-topical.json').write_bytes(b'[{"slug":"A","status":"ongoing"}]')
            with patch.object(bootstrap,'BASE',root),patch.object(bootstrap,'gh') as gh,patch.object(bootstrap,'command',return_value='a'*40) as command,patch.object(bootstrap,'output') as output:
                gh.side_effect=[{'state':'open','labels':[{'name':'proposal-approved'}]},{'can_approve_pull_request_reviews':True}]
                bootstrap.prepare('owner/repo',5,'ci/bootstrap-proposal-5')
                output.assert_called_once_with('complete','true')
                self.assertTrue(any('publish-site.yml' in call.args for call in command.call_args_list))
                self.assertFalse(any('switch' in call.args for call in command.call_args_list))

    def test_disabled_pr_creation_fails_before_source_generation(self):
        with patch.object(bootstrap,'gh') as gh,patch.object(bootstrap,'command') as command:
            gh.side_effect=[{'state':'open','labels':[{'name':'proposal-approved'}]},{'can_approve_pull_request_reviews':False}]
            with self.assertRaisesRegex(ValueError,'Allow GitHub Actions'):
                bootstrap.prepare('owner/repo',5,'ci/bootstrap-proposal-5')
            command.assert_not_called()

    def test_same_status_request_does_not_refresh_timestamp_or_render(self):
        import _set_study_status as status
        from _study_pdf_metadata import PdfStudyRow,StudyStatus
        with patch.object(status,'get_study_row',return_value=(PdfStudyRow('A','A',StudyStatus.DRAFT),None)), \
             patch.object(status,'verify_timestamp_sync',return_value=[]), \
             patch.object(status,'now_ist') as clock, patch.object(status,'regenerate_pdf') as render:
            status.set_study_status('A',new_status=StudyStatus.DRAFT,dry_run=False,skip_pdf=False,check_timestamps=True)
            clock.assert_not_called()
            render.assert_not_called()

    def test_renamed_study_must_have_synchronized_metadata_before_review(self):
        import _validate_study_change as validation
        with patch.object(validation, 'detect_study_renames', return_value=[('Old', 'New')]), \
             patch.object(validation, 'get_study_row', return_value=None), \
             patch.object(validation, 'verify_rename_metadata', side_effect=SystemExit('stale rename metadata')) as verify:
            with self.assertRaisesRegex(SystemExit, 'stale rename'):
                validation.validate('base')
            verify.assert_called_once_with('Old', 'New', None)


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.git('init','-q')
        for name in ['sitemap.xml','llms.txt','llms-full.txt','.github/ISSUE_TEMPLATE/study-feedback.yml','Studies/A/discussion.html']:
            path=self.root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b'old')
        self.git('add','.')
        self.git('-c','user.name=Fixture','-c','user.email=fixture@example.test','commit','-qm','base')

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,stderr=subprocess.PIPE).decode()

    def test_complete_fanout_and_deletions_are_staged(self):
        (self.root/'sitemap.xml').write_bytes(b'new')
        (self.root/'llms.txt').write_bytes(b'new')
        (self.root/'llms-full.txt').write_bytes(b'new')
        (self.root/'.github/ISSUE_TEMPLATE/study-feedback.yml').write_bytes(b'new')
        (self.root/'Studies/A/discussion.html').unlink()
        paths=contract.stage(self.root)
        self.assertEqual(len(paths),5)
        self.assertIn('D\tStudies/A/discussion.html',self.git('diff','--cached','--name-status'))
        self.assertEqual(self.git('diff','--name-only'),'')

    def test_unexpected_staged_or_untracked_changes_fail_before_staging(self):
        (self.root/'.env').write_bytes(b'private')
        with self.assertRaisesRegex(ValueError,'outside'):
            contract.stage(self.root)
        self.assertEqual(self.git('diff','--cached','--name-only'),'')
        self.git('add','.env')
        with self.assertRaisesRegex(ValueError,'outside'):
            contract.stage(self.root)


if __name__ == '__main__':
    unittest.main()
