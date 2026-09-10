"""Export verified PDFs and reuse matching builds from a merged same-repo PR.

Protected publication reads data only from successful, allowlisted producers.
Every reused file must match the current consumed-input graph and its SHA-256;
fork artifacts, unrelated runs, stale toolchains and arbitrary ZIP paths fail
closed. A missing/expired proof simply leaves the artifact selected for build.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

from _artifact_graph import BASE, build_graph
from _publication_plan import validate_plan

PROOF = 'review-build-proof.json'
PRODUCERS = {
    '.github/workflows/studies-index-check.yml': {'study-review-pdfs', 'presentation-review-pdfs'},
    '.github/workflows/prepare-study.yml': {'prepared-review-pdfs'},
}


def export(root: Path, *, local: bool = False) -> None:
    from _generated_pdf_inventory import generated_pdf_specs
    from _publish_generated_pdfs import verify_artifacts
    nodes = build_graph()
    specs = tuple(spec for spec in generated_pdf_specs() if (spec.output if local else root / spec.key).is_file())
    verified = verify_artifacts(specs, BASE if local else root)
    artifacts = {}
    root.mkdir(parents=True, exist_ok=True)
    for item in verified:
        if local:
            target = root / item.spec.key
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item.path, target)
        artifacts[item.spec.key] = {'node': nodes[item.spec.key], 'sha256': item.sha256,
                                    'bytes': item.path.stat().st_size, 'pages': item.pages}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASE, text=True).strip()
    proof = {'schema': 1, 'repository': os.environ.get('GITHUB_REPOSITORY'), 'head': head, 'artifacts': artifacts}
    (root / PROOF).write_bytes((json.dumps(proof, sort_keys=True) + '\n').encode())
    print(f'Exported {len(artifacts)} verified PDF input/output proofs.')


def read_proof(data: bytes, *, repository: str, head: str, nodes: dict, wanted: set[str]) -> tuple[dict, dict]:
    if len(data) > 200_000_000:
        raise ValueError('Review artifact exceeds 200 MB')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > 5000 or sum(info.file_size for info in infos) > 200_000_000:
            raise ValueError('Review artifact expands beyond allowed limits')
        names = set()
        for info in infos:
            path = PurePosixPath(info.filename)
            if (info.orig_filename != info.filename or info.filename in names or path.is_absolute()
                    or '..' in path.parts or '\\' in info.filename or ':' in info.filename
                    or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe or duplicate review artifact path')
            names.add(info.filename)
        if PROOF not in names:
            return {}, {}
        proof = json.loads(archive.read(PROOF))
        if (proof.get('schema') != 1 or proof.get('repository') != repository or proof.get('head') != head):
            raise ValueError('Review proof does not belong to its trusted producer')
        accepted, bodies = {}, {}
        for key, record in proof.get('artifacts', {}).items():
            if key not in wanted or key not in nodes or record.get('node') != nodes[key]:
                continue
            if key not in names:
                raise ValueError(f'Proof output is missing: {key}')
            body = archive.read(key)
            if len(body) != record.get('bytes') or hashlib.sha256(body).hexdigest() != record.get('sha256'):
                raise ValueError(f'Review PDF checksum differs from proof: {key}')
            accepted[key], bodies[key] = record, body
        for deck in {nodes[key].get('deck') for key in accepted if nodes[key]['family'] == 'presentations'}:
            pair = {key for key in wanted if nodes[key].get('deck') == deck}
            if not pair.issubset(accepted):
                for key in pair:
                    accepted.pop(key, None)
                    bodies.pop(key, None)
        if 'presentation-build-provenance.json' in names:
            bodies['presentation-build-provenance.json'] = archive.read('presentation-build-provenance.json')
        return accepted, bodies


def import_merged(plan_path: Path, output: Path) -> None:
    from _bootstrap_ci import gh
    plan = validate_plan(json.loads(plan_path.read_bytes()))
    repo = os.environ['GITHUB_REPOSITORY']
    prs = gh('api', f"repos/{repo}/commits/{plan['sourceSha']}/pulls")
    candidates = []
    for pr in prs:
        if (not pr.get('merged_at') or pr.get('merge_commit_sha') != plan['sourceSha']
                or pr.get('head', {}).get('repo', {}).get('full_name') != repo):
            continue
        heads = {pr['head']['sha']}
        commit = gh('api', f"repos/{repo}/commits/{pr['head']['sha']}")
        for line in commit.get('commit', {}).get('message', '').splitlines():
            if line.startswith('AMD-Prepared-From: '):
                parent = line.removeprefix('AMD-Prepared-From: ')
                if parent in {item['sha'] for item in commit.get('parents', [])}:
                    heads.add(parent)
        for head in heads:
            runs = gh('api', f'repos/{repo}/actions/runs?head_sha={head}&status=success&per_page=100')['workflow_runs']
            for run in runs:
                path = run.get('path', '').split('@')[0]
                if (path in PRODUCERS and run.get('conclusion') == 'success'
                        and run.get('event') in {'pull_request', 'workflow_dispatch'}
                        and run.get('head_repository', {}).get('full_name') == repo and run.get('head_sha') == head):
                    candidates.append((run, path, head))
    reviewed = {}
    for run, path, head in candidates:
        artifacts = gh('api', f"repos/{repo}/actions/runs/{run['id']}/artifacts")['artifacts']
        for artifact in artifacts:
            if artifact.get('expired') or artifact.get('size_in_bytes', 0) > 200_000_000 or artifact['name'] not in PRODUCERS[path]:
                continue
            wanted = set(plan['build']) - set(reviewed)
            if not wanted:
                break
            result = subprocess.run(['gh', 'api', f"repos/{repo}/actions/artifacts/{int(artifact['id'])}/zip"],
                                    cwd=BASE, check=True, capture_output=True)
            accepted, bodies = read_proof(result.stdout, repository=repo, head=head, nodes=plan['nodes'], wanted=wanted)
            if not accepted:
                continue
            for key in accepted:
                target = output / key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(bodies[key])
                reviewed[key] = {'run': run['id'], 'artifact': artifact['id'], 'sha256': accepted[key]['sha256']}
            if any(plan['nodes'][key]['family'] == 'presentations' for key in accepted):
                target = output / 'presentation-build-provenance.json'
                incoming = json.loads(bodies['presentation-build-provenance.json'])
                if target.is_file():
                    previous = json.loads(target.read_bytes())
                    by_id = {item['id']: item for item in previous['artifacts'] + incoming['artifacts']}
                    incoming['artifacts'] = list(by_id.values())
                target.write_bytes((json.dumps(incoming) + '\n').encode())
    # Re-run structural/output verification in the protected checkout, without a
    # renderer. An artifact's producer cannot turn its proof into executable code.
    if reviewed:
        from _generated_pdf_inventory import generated_pdf_specs
        from _publish_generated_pdfs import verify_artifacts
        verify_artifacts(tuple(spec for spec in generated_pdf_specs() if spec.key in reviewed), output)
    plan['reviewArtifacts'] = reviewed
    plan_path.write_bytes((json.dumps(plan, sort_keys=True) + '\n').encode())
    write_outputs(plan)
    print(f'Reused {len(reviewed)} verified PDFs from merged same-repository PR builds.')


def write_outputs(plan: dict) -> None:
    from _bootstrap_ci import output
    render = set(plan['build']) - set(plan.get('reviewArtifacts', {}))
    for family in ('markdown', 'presentations', 'references'):
        output(family, str(any(plan['nodes'][key]['family'] == family for key in render)).lower())
    reference_pdfs = any(plan['nodes'][key]['family'] == 'references' and key.endswith('.pdf') and
                         plan['nodes'][key]['metadata']['reference']['target']['storage'] == 'r2-public' for key in render)
    output('reference_pdfs', str(reference_pdfs).lower())
    output('any_build', str(any(key.endswith('.pdf') for key in plan['build'])).lower())
    output('review_used', str(bool(plan.get('reviewArtifacts'))).lower())


def restore_prepared(output: Path, base: str) -> None:
    from _bootstrap_ci import gh, output as emit
    from _artifact_graph import affected_outputs
    from _pdf_build_cache import git_changed_paths
    repo = os.environ['GITHUB_REPOSITORY']
    nodes = build_graph()
    wanted = {key for key in affected_outputs(git_changed_paths(base), base=base, nodes=nodes)
              if nodes[key]['family'] == 'markdown'}
    accepted = {}
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    pr = event.get('pull_request')
    number = event.get('inputs', {}).get('pr_number')
    if number:
        pr = gh('api', f'repos/{repo}/pulls/{int(number)}')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASE, text=True).strip()
    if pr and pr['head']['repo']['full_name'] == repo and pr['head']['sha'] == head:
        commit = gh('api', f'repos/{repo}/commits/{head}')
        parents = {item['sha'] for item in commit.get('parents', [])}
        origins = [line.removeprefix('AMD-Prepared-From: ') for line in commit.get('commit', {}).get('message', '').splitlines()
                   if line.startswith('AMD-Prepared-From: ') and line.removeprefix('AMD-Prepared-From: ') in parents]
        origins.append(head)  # Preparation may have produced no tracked diff.
        for parent in origins:
            runs = gh('api', f'repos/{repo}/actions/workflows/prepare-study.yml/runs?head_sha={parent}&status=success&per_page=30')['workflow_runs']
            for run in runs:
                if (run.get('conclusion') != 'success' or run.get('event') != 'pull_request' or run.get('head_sha') != parent
                        or run.get('path') != '.github/workflows/prepare-study.yml' or run.get('head_repository', {}).get('full_name') != repo):
                    continue
                artifacts = gh('api', f"repos/{repo}/actions/runs/{run['id']}/artifacts")['artifacts']
                for artifact in artifacts:
                    if artifact['name'] != 'prepared-review-pdfs' or artifact.get('expired') or artifact.get('size_in_bytes', 0) > 200_000_000:
                        continue
                    data = subprocess.run(['gh', 'api', f"repos/{repo}/actions/artifacts/{int(artifact['id'])}/zip"],
                                          check=True, capture_output=True).stdout
                    records, bodies = read_proof(data, repository=repo, head=parent, nodes=nodes, wanted=wanted - set(accepted))
                    for key, record in records.items():
                        target = output / key
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(bodies[key])
                        accepted[key] = record
    output.mkdir(parents=True, exist_ok=True)
    (output / PROOF).write_bytes((json.dumps({'schema': 1, 'repository': repo, 'head': head, 'artifacts': accepted}) + '\n').encode())
    emit('render', str(bool(wanted - set(accepted))).lower())
    print(f'Restored {len(accepted)} exact-input preparation PDFs; {len(wanted - set(accepted))} require rendering.')


def merge_outputs(downloads: Path, output: Path) -> None:
    """Combine partial job outputs without overwriting another deck's provenance."""
    from _generated_pdf_inventory import generated_pdf_specs
    from _reference_artifacts import load_manifest
    allowed = {spec.key for spec in generated_pdf_specs()}
    allowed.update(row['repo_path'] for row in load_manifest().get('artifacts', [])
                   if row.get('target', {}).get('storage') == 'r2-public')
    provenance = None
    records = {}
    for directory in sorted(downloads.iterdir()):
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError('Expected one directory per downloaded artifact')
        for source in sorted(directory.rglob('*')):
            if source.is_symlink():
                raise ValueError('Downloaded output contains a symbolic link')
            if not source.is_file():
                continue
            key = source.relative_to(directory).as_posix()
            if key == 'presentation-build-provenance.json':
                incoming = json.loads(source.read_bytes())
                contract = {k: v for k, v in incoming.items() if k != 'artifacts'}
                if provenance is not None and contract != provenance:
                    raise ValueError('Presentation jobs used different rendering contracts')
                provenance = contract
                for item in incoming['artifacts']:
                    if item['id'] in records and records[item['id']] != item:
                        raise ValueError('Conflicting deck build proofs')
                    records[item['id']] = item
            elif key in allowed:
                target = output / key
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_file() and target.read_bytes() != source.read_bytes():
                    raise ValueError(f'Conflicting generated output: {key}')
                shutil.copyfile(source, target)
            elif key not in {PROOF, 'markdown-build-provenance.json'}:
                raise ValueError(f'Unexpected artifact output: {key}')
    if provenance is not None:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'presentation-build-provenance.json').write_bytes(
            (json.dumps({**provenance, 'artifacts': list(records.values())}) + '\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--from-local', action='store_true')
    parser.add_argument('--import-plan', type=Path)
    parser.add_argument('--prepared-base')
    parser.add_argument('--merge-downloads', type=Path)
    args = parser.parse_args()
    if args.merge_downloads:
        merge_outputs(args.merge_downloads, args.root)
    elif args.prepared_base:
        restore_prepared(args.root, args.prepared_base)
    elif args.import_plan:
        import_merged(args.import_plan, args.root)
    else:
        export(args.root, local=args.from_local)
