"""Reject unapproved history transitions while permitting a pinned equivalent release."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from _history_rewrite_transition import allows_transition


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Migration test')
        self.git('config', 'user.email', 'migration@example.invalid')
        (self.root / 'source').write_text('preserved')
        self.git('add', 'source')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD')
        self.tree = self.git('rev-parse', 'HEAD^{tree}')
        self.git('commit', '--allow-empty', '-qm', 'transition code')
        self.tip = self.git('rev-parse', 'HEAD')
        self.previous = dict(sourceSha='a'*40, revision='b'*64,
                             runtimeFingerprint='c'*64, buildReceiptKey='site/builds/'+'d'*64+'.json')
        self.candidate = dict(self.previous, sourceSha=self.tip)
        self.config = dict(schema=1, previousPublication=self.previous.copy(),
                           rewrittenBase=self.base, unchangedTree=self.tree)
        (self.root / 'Scripts').mkdir()
        self.write_config()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def write_config(self):
        (self.root / 'Scripts/history-rewrite-transition.json').write_text(json.dumps(self.config))

    def test_exact_publication_to_mapped_descendant(self):
        self.assertTrue(allows_transition(self.root, self.previous, self.candidate))

    def test_changed_previous_marker_rejected(self):
        for field in self.previous:
            with self.subTest(field=field):
                self.assertFalse(allows_transition(self.root, dict(self.previous, **{field: 'unexpected'}), self.candidate))

    def test_content_or_runtime_change_rejected(self):
        for field in ('revision', 'runtimeFingerprint', 'buildReceiptKey'):
            with self.subTest(field=field):
                self.assertFalse(allows_transition(self.root, self.previous, dict(self.candidate, **{field: 'unexpected'})))

    def test_unknown_candidate_rejected(self):
        self.assertFalse(allows_transition(self.root, self.previous, dict(self.candidate, sourceSha='e'*40)))

    def test_unrelated_commit_rejected(self):
        unrelated = self.git('commit-tree', self.tree, '-m', 'unrelated root')
        self.assertFalse(allows_transition(self.root, self.previous, dict(self.candidate, sourceSha=unrelated)))

    def test_wrong_tree_rejected(self):
        self.config['unchangedTree'] = 'f'*40
        self.write_config()
        self.assertFalse(allows_transition(self.root, self.previous, self.candidate))

    def test_missing_or_invalid_config_rejected(self):
        path = self.root / 'Scripts/history-rewrite-transition.json'
        path.write_text('{')
        self.assertFalse(allows_transition(self.root, self.previous, self.candidate))
        path.unlink()
        self.assertFalse(allows_transition(self.root, self.previous, self.candidate))

    def test_missing_candidate_sha_rejected(self):
        candidate = self.candidate.copy()
        del candidate['sourceSha']
        self.assertFalse(allows_transition(self.root, self.previous, candidate))


if __name__ == '__main__':
    unittest.main()
