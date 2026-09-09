"""Bind verification to one immutable PR head and its upstream base."""
import json
import os
from pathlib import Path
import re
import subprocess

from _bootstrap_ci import gh, output


def main() -> None:
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    repo = os.environ['GITHUB_REPOSITORY']
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    report = os.environ.get('REPORT_SHA', '')
    if report and (not re.fullmatch(r'[a-f0-9]{40}', report) or report != head):
        raise ValueError('Checked-out commit differs from the exact requested SHA.')
    pr = event.get('pull_request')
    number = os.environ.get('PR_NUMBER', '')
    if number:
        if not re.fullmatch(r'[1-9][0-9]*', number):
            raise ValueError('Invalid PR number.')
        os.environ['GH_TOKEN'] = os.environ['GITHUB_TOKEN']
        pr = gh('api', f'repos/{repo}/pulls/{number}')
    if pr:
        if pr['head']['sha'] != head or pr['base']['repo']['full_name'] != repo:
            raise ValueError('PR moved or has a different upstream base.')
        base = pr['base']['sha']
        subprocess.run(['git', 'fetch', f'https://github.com/{repo}.git', base], check=True)
        body = pr.get('body') or ''
    else:
        base = subprocess.check_output(['git', 'rev-parse', 'HEAD^'], text=True).strip()
        body = ''
    Path(os.environ['RUNNER_TEMP'], 'verified-pr-body.txt').write_text(body, encoding='utf-8', newline='\n')
    output('head', head)
    output('base', base)


if __name__ == '__main__':
    main()
