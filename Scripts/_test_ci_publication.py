"""CI trust boundaries, preparation retries, and lifecycle intent regression tests."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import _bootstrap_ci as bootstrap
import _ci_study_pr as ci
import _generated_artifacts as contract
import _prepared_study as prepared
import _rewrite_manifest_reference_links as reference_links
import _validate_study_change as validation
from _validate_study_change import infer_intent
from _study_catalog import StudyStatus


class PreparationTests(unittest.TestCase):
    def test_intent_is_not_label_dependent(self):
        self.assertEqual(infer_intent('', ['Studies/A/A.md'], 'base'),'study-update')
        self.assertEqual(infer_intent('Proposal issue: #12', ['Studies/A/A.md'], 'base'),'new-study')
        self.assertEqual(infer_intent('Target status: released', [], 'base'),'status-change')
        self.assertIsNone(infer_intent('', ['Assets/icon.svg'], 'base'))

    def test_unprepared_source_is_allowed_only_for_same_repository_portal_draft(self):
        body = 'Proposal issue: #12\nPortal-GitHub: @author\n'
        event = {'pull_request': {'draft': True, 'head': {'repo': {'full_name': 'owner/repo'}}}}
        self.assertTrue(validation.is_portal_preparation(event, body, 'owner/repo'))
        self.assertFalse(validation.is_portal_preparation(event, body, 'fork/repo'))
        self.assertFalse(validation.is_portal_preparation(
            {'pull_request': {**event['pull_request'], 'draft': False}}, body, 'owner/repo'))
        self.assertFalse(validation.is_portal_preparation(event, 'Proposal issue: #12\n', 'owner/repo'))

    def test_unprepared_portal_first_draft_rechecks_registered_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'A.md'
            source.write_text('# A\n', encoding='utf-8')
            ongoing = SimpleNamespace(status=StudyStatus.ONGOING)
            common = [
                patch.object(validation, 'detect_study_renames', return_value=[]),
                patch.object(validation, 'changed_markdown_slugs', return_value=['A']),
                patch.object(validation, 'changed_study_slugs', return_value=['A']),
                patch.object(validation, 'iter_pdf_study_rows', return_value=[]),
                patch.object(validation, 'old_text', return_value='[]'),
                patch.object(validation, 'get_study_row', return_value=(ongoing, None)),
                patch.object(validation, 'study_md', return_value=source),
                patch.object(validation, 'registry_row_for_slug', return_value={'issueNumber': 12}),
                patch.object(validation, 'gh_request', return_value={
                    'state': 'open', 'labels': [{'name': 'proposal-approved'}]}),
                patch.object(validation, 'cross_study_section_errors', return_value=[]),
                patch.object(validation, 'references_changed', return_value=False),
                patch.object(validation, 'study_references_changed', return_value=False),
                patch.dict(validation.os.environ, {'GITHUB_REPOSITORY': 'owner/repo'}),
            ]
            for mocked in common:
                mocked.start()
                self.addCleanup(mocked.stop)
            with self.assertRaisesRegex(ValueError, 'prepare its first draft'):
                validation.validate('base', 'Proposal issue: #12\n')
            validation.validate(
                'base',
                'Proposal issue: #12\n',
                allow_unprepared_new_study=True,
            )
            validation.registry_row_for_slug.return_value = {'issueNumber': 13}
            with self.assertRaisesRegex(ValueError, 'linked approval does not match'):
                validation.validate(
                    'base',
                    'Proposal issue: #12\n',
                    allow_unprepared_new_study=True,
                )

    def test_preparation_rewrites_only_changed_study_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changed = root / 'Studies/A/A.md'
            unchanged = root / 'Studies/B/B.md'
            changed.parent.mkdir(parents=True)
            unchanged.parent.mkdir(parents=True)
            link = '[source](../../References/Book.pdf)\n'
            changed.write_text(link, encoding='utf-8')
            unchanged.write_text(link, encoding='utf-8')
            with patch.object(ci, 'BASE', root), \
                 patch.object(ci, 'changed_paths', return_value=(
                     ('A', 'Studies/A/A.md'), ('M', 'Scripts/tool.py'))), \
                 patch.object(reference_links, 'delivery_map', return_value={
                     'References/Book.pdf': 'https://cdn.example/Book.pdf'}):
                self.assertEqual(ci.rewrite_changed_reference_links('base'), 1)
            self.assertIn('https://cdn.example/Book.pdf', changed.read_text(encoding='utf-8'))
            self.assertEqual(unchanged.read_text(encoding='utf-8'), link)

    def test_accept_requires_exact_head_open_draft_and_same_repository(self):
        pr={'number':1,'state':'open','draft':True,'head':{'sha':'a'*40,'repo':{'full_name':'owner/repo'}},'base':{'ref':'master','sha':'b'*40}}
        payload={'schema':1,'pr':1,'repository':'owner/repo','head':'a'*40,'files':{'sitemap.xml':base64.b64encode(b'new').decode(),'Studies/A/discussion.html':None}}
        from _verification_identity import intent_hash
        payload.update(base=pr['base']['sha'], intent=intent_hash(pr))
        self.assertEqual(prepared.validate(payload,pr,'owner/repo'),{'sitemap.xml':b'new','Studies/A/discussion.html':None})
        for change in [{'head':'b'*40},{'base':'c'*40},{'intent':'changed'},{'repository':'fork/repo'},{'pr':2},
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
