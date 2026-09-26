"""Validate explicitly approved hard-withdrawal path prefixes."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
POLICY = BASE / 'infra/site-worker/withdrawals.json'


def load() -> dict:
    policy = json.loads(POLICY.read_bytes())
    if policy.get('schema') != 1 or not isinstance(policy.get('withdrawals'), list):
        raise ValueError('Invalid hard withdrawal policy')
    seen = set()
    for entry in policy['withdrawals']:
        path = entry.get('path', '')
        if (not path.startswith(('/Studies/', '/Applications/', '/References/', '/Assets/'))
                or path in seen or '?' in path or '#' in path or '\\' in path or '%' in path
                or any(part in ('.', '..') for part in path.split('/'))
                or len(path.strip('/').split('/')) < 2 or not entry.get('reason') or not entry.get('approvedBy')):
            raise ValueError('Withdrawal requires a precise approved public path/prefix')
        seen.add(path)
    return policy
