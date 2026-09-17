"""Recognize one pinned, byte-preserving publication history transition."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


def allows_transition(root: Path, previous: dict, candidate: dict) -> bool:
    path = root / 'Scripts' / 'history-rewrite-transition.json'
    if not path.is_file():
        return False
    try:
        transition = json.loads(path.read_text(encoding='utf-8'))
        if transition['schema'] != 1:
            return False
        expected = transition['previousPublication']
        fields = ('sourceSha', 'revision', 'runtimeFingerprint', 'buildReceiptKey')
        if any(not expected.get(key) or previous.get(key) != expected[key] for key in fields):
            return False
        # Permit provenance migration only: site bytes, runtime and artifact
        # receipt must still be exactly the approved active publication.
        if any(candidate.get(key) != expected[key] for key in fields[1:]):
            return False
        base, tree = transition['rewrittenBase'], transition['unchangedTree']
        if any(not isinstance(value, str) or not re.fullmatch('[a-f0-9]{40}', value)
               for value in (base, tree, candidate.get('sourceSha'))):
            return False
        actual = subprocess.run(['git', 'rev-parse', base + '^{tree}'], cwd=root,
                                capture_output=True, text=True, check=False)
        if actual.returncode or actual.stdout.strip() != tree:
            return False
        return subprocess.run(['git', 'merge-base', '--is-ancestor', base, candidate['sourceSha']],
                              cwd=root, capture_output=True, check=False).returncode == 0
    except (KeyError, TypeError, ValueError, OSError):
        return False
