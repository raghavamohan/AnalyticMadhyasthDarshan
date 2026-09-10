"""Idempotent verification keyed by exact head, upstream base and PR intent."""
import hashlib
import json


def intent_hash(pr: dict) -> str:
    return hashlib.sha256((pr.get('body') or '').strip().encode()).hexdigest()


def verification_key(pr: dict) -> str:
    value = {'head': pr['head']['sha'], 'base': pr['base']['sha'], 'intent': intent_hash(pr)}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def is_preparing(pr: dict | None, report: str = '') -> bool:
    return bool(pr and pr.get('draft') and not report and 'Portal-GitHub: @' in (pr.get('body') or '')
                and pr['head']['repo']['full_name'] == pr['base']['repo']['full_name'])


def dispatch(repo: str, pr: dict) -> None:
    from _bootstrap_ci import command, gh, status
    key = verification_key(pr)
    title = f'verify / {key}'
    runs = gh('api', f"repos/{repo}/actions/workflows/studies-index-check.yml/runs?head_sha={pr['head']['sha']}&per_page=100")
    if any(run.get('display_title') == title and (run.get('status') != 'completed' or run.get('conclusion') == 'success')
           for run in runs.get('workflow_runs', [])):
        print(f'Exact head/base/intent verification is already queued or successful: {key}')
        return
    status(repo, pr['head']['sha'], 'pending', 'Prepared source is waiting for complete verification.')
    command('gh', 'workflow', 'run', 'studies-index-check.yml', '--repo', repo, '--ref', pr['head']['ref'],
            '-f', f"report_sha={pr['head']['sha']}", '-f', f"pr_number={pr['number']}", '-f', f'verification_key={key}')


def complete(repo: str, run: dict) -> None:
    """Trusted workflow_run consumer; never executes files from the producer."""
    from _bootstrap_ci import command, gh
    if (run.get('path') != '.github/workflows/studies-index-check.yml'
            or run.get('event') != 'workflow_dispatch' or run.get('conclusion') != 'success'
            or run.get('head_repository', {}).get('full_name') != repo):
        return
    prs = gh('api', f"repos/{repo}/commits/{run['head_sha']}/pulls")
    for pr in prs:
        if (pr.get('state') == 'open' and pr.get('draft') and pr['head']['sha'] == run['head_sha']
                and pr['head']['repo']['full_name'] == repo and 'Portal-GitHub: @' in (pr.get('body') or '')
                and run.get('display_title') == f'verify / {verification_key(pr)}'):
            command('gh', 'pr', 'ready', str(pr['number']), '--repo', repo)


if __name__ == '__main__':
    import os
    from pathlib import Path
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    complete(os.environ['GITHUB_REPOSITORY'], event['workflow_run'])
