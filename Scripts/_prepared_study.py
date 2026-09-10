"""Transfer prepared files across CI's read-only build / trusted writer boundary.

The writer never executes code from the prepared checkout. It validates paths,
payload size, PR identity and exact head, then adds one non-force commit.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from _generated_artifacts import BASE, changed_paths, permits


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *args], cwd=root, text=True, encoding='utf-8').strip()


def export(path: Path) -> None:
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    pr = event['pull_request']
    files = {}
    for name in changed_paths(BASE):
        target = BASE / name
        deleted = not target.exists()
        if not permits(name, deleted=deleted) or target.is_symlink() or not target.resolve().is_relative_to(BASE.resolve()):
            raise ValueError(f'Unexpected preparation output: {name}')
        files[name] = None if deleted else base64.b64encode(target.read_bytes()).decode()
    payload = {'schema': 1, 'pr': pr['number'], 'head': pr['head']['sha'],
               'repository': pr['head']['repo']['full_name'], 'files': files}
    from _verification_identity import intent_hash
    payload.update(base=pr['base']['sha'], intent=intent_hash(pr))
    path.write_bytes(json.dumps(payload, ensure_ascii=False).encode())


def validate(payload: dict, pr: dict, repo: str) -> dict[str, bytes | None]:
    from _verification_identity import intent_hash
    if (payload.get('schema') != 1 or payload.get('repository') != repo
            or payload.get('pr') != pr['number'] or pr['state'] != 'open' or not pr['draft']
            or pr['head']['repo']['full_name'] != repo or pr['base']['ref'] != 'master'
            or payload.get('head') != pr['head']['sha'] or not re.fullmatch(r'[a-f0-9]{40}', payload.get('head', ''))):
        raise ValueError('Preparation is stale, or does not belong to this open draft PR.')
    if not pr['base'].get('sha') or payload.get('base') != pr['base']['sha'] or payload.get('intent') != intent_hash(pr):
        raise ValueError('Preparation base or lifecycle intent changed; prepare again.')
    if not isinstance(payload.get('files'), dict) or len(payload['files']) > 5000:
        raise ValueError('Invalid preparation file inventory.')
    files = {}
    total = 0
    for name, content in payload['files'].items():
        if not permits(name, deleted=content is None):
            raise ValueError(f'Forbidden preparation output: {name}')
        raw = None if content is None else base64.b64decode(content, validate=True)
        total += len(raw or b'')
        if total > 100_000_000:
            raise ValueError('Preparation exceeds 100 MB.')
        files[name] = raw
    return files


def accept(path: Path) -> None:
    from _bootstrap_ci import gh, command, status
    if path.stat().st_size > 140_000_000:
        raise ValueError('Preparation payload is too large.')
    payload = json.loads(path.read_bytes())
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    producer = event['workflow_run']
    if (producer['head_sha'] != payload.get('head') or producer.get('path') != '.github/workflows/prepare-study.yml'
            or producer.get('event') != 'pull_request' or producer.get('conclusion') != 'success'):
        raise ValueError('Payload does not belong to the expected successful preparation run.')
    repo = os.environ['GITHUB_REPOSITORY']
    number = payload.get('pr')
    if not isinstance(number, int) or number <= 0:
        raise ValueError('Invalid PR number.')
    pr = gh('api', f'repos/{repo}/pulls/{number}')
    if pr['head']['sha'] != payload.get('head'):
        current = gh('api', f"repos/{repo}/commits/{pr['head']['sha']}")
        trailer = f"AMD-Prepared-From: {payload.get('head')}"
        if (trailer in current.get('commit', {}).get('message', '').splitlines()
                and payload.get('head') in {item['sha'] for item in current.get('parents', [])}
                and pr['head']['repo']['full_name'] == repo and pr.get('state') == 'open'):
            from _verification_identity import intent_hash, dispatch
            if payload.get('base') == pr['base']['sha'] and payload.get('intent') == intent_hash(pr):
                dispatch(repo, pr)
                return
    files = validate(payload, pr, repo)
    branch = pr['head']['ref']
    git(BASE, 'check-ref-format', '--branch', branch)
    git(BASE, 'fetch', 'origin', payload['head'])
    with tempfile.TemporaryDirectory() as directory:
        checkout = Path(directory) / 'prepared'
        git(BASE, 'worktree', 'add', '--detach', str(checkout), payload['head'])
        try:
            for name, body in files.items():
                target = checkout / name
                if target.is_symlink() or not target.resolve().is_relative_to(checkout.resolve()):
                    raise ValueError(f'Unsafe prepared target: {name}')
                if body is None:
                    target.unlink(missing_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(body)
            if files:
                git(checkout, 'add', '-A', '--', *files)
            if git(checkout, 'diff', '--cached', '--name-only'):
                git(checkout, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                    'commit', '-m', 'Prepare study artifacts for review\n\nAMD-Prepared-From: ' + payload['head'])
            head = git(checkout, 'rev-parse', 'HEAD')
            live = gh('api', f'repos/{repo}/pulls/{number}')
            validate(payload, live, repo)
            git(checkout, 'push', 'origin', f'HEAD:refs/heads/{branch}')
        finally:
            git(BASE, 'worktree', 'remove', '--force', str(checkout))
    try:
        from _verification_identity import dispatch
        dispatch(repo, gh('api', f'repos/{repo}/pulls/{number}'))
    except Exception:
        status(repo, head, 'failure', 'Prepared-head verification could not be queued.')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['export', 'accept'])
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    (export if args.mode == 'export' else accept)(args.path)
