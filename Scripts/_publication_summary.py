"""Record publication outcomes and write one PDF/R2/Worker run summary."""
import argparse
import json
import os
from pathlib import Path


def record(kind: str, **fields):
    filename = os.environ.get('AMD_PUBLICATION_EVENTS')
    if filename:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps({'kind': kind, **fields}, sort_keys=True) + '\n')


def summary(plan: dict, events: list[dict], jobs: dict) -> str:
    lines = ['## Publication result', '', '| Change class | Outcome |', '|---|---|']
    reviewed = set(plan.get('reviewArtifacts', {}))
    for family in ('markdown', 'presentations', 'references'):
        nodes = {key for key, node in plan.get('nodes', {}).items() if node['family'] == family}
        built = nodes.intersection(plan.get('build', [])) - reviewed
        reuse = nodes.intersection(plan.get('reuse', {}))
        review = nodes.intersection(reviewed)
        lines.append(f'| {family} outputs | {len(built)} selected for build; {len(review)} reviewed; {len(reuse)} verified reuse |')
    staged = [e for e in events if e['kind'] == 'r2']
    lines.append('| R2 objects | ' + (f'{sum(e["uploaded"] for e in staged)} uploaded; '
                 f'{sum(e["reused"] for e in staged)} reused; no deletion' if staged else 'No staging receipt; see job outcome') + ' |')
    workers = [e for e in events if e['kind'] == 'worker']
    lines.append('| Worker deployments | ' + ('; '.join(e['name'] + ': ' + e['outcome'] for e in workers)
                 if workers else 'No deployment receipt; see job outcome') + ' |')
    if jobs:
        lines.extend(['', '| Job | Result |', '|---|---|'])
        for name, job in jobs.items():
            lines.append(f'| {name} | {job.get("result", "unknown")} |')
    lines.extend(['', 'Source: `' + plan.get('sourceSha', os.environ.get('GITHUB_SHA', 'unknown')) + '`.',
                  'Build selections are intent; deployment/staging rows are observed outcomes. A failed or skipped job does not establish completion.', ''])
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--events', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes()) if args.plan and args.plan.is_file() else {}
    events = [json.loads(line) for line in args.events.read_text(encoding='utf-8').splitlines() if line.strip()] if args.events and args.events.is_file() else []
    report = summary(plan, events, json.loads(os.environ.get('AMD_PUBLICATION_JOBS', '{}')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding='utf-8', newline='\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8', newline='\n') as stream:
            stream.write(report)
    print(report)
