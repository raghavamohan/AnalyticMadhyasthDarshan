"""Plan from the active publication's verified artifacts, never the previous push."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess

from _artifact_graph import BASE, build_graph, explain, fingerprint


def object_matches(client, record: dict) -> bool:
    headers = client.head_object(record['key'])
    return bool(headers and headers.get('x-amz-meta-sha256') == record['sha256']
                and int(headers.get('content-length', '-1')) == record['bytes'])


def validate_record(record: dict, *, reference: bool = False) -> None:
    sha = record.get('sha256', '')
    if not re.fullmatch('[a-f0-9]{64}', sha) or not isinstance(record.get('bytes'), int) or record['bytes'] <= 0:
        raise ValueError('Invalid verified artifact checksum or size')
    if not reference and record.get('key') != f'site/objects/{sha}':
        raise ValueError('Generated PDF receipt is not content addressed')


def load_receipt(client, key: str) -> dict:
    if not re.fullmatch(r'site/builds/[a-f0-9]{64}\.json', key):
        raise ValueError('Invalid protected build receipt key')
    receipt = json.loads(client.get_object(key))
    if receipt.get('schema') != 1 or key != receipt_key(receipt):
        raise ValueError('Protected build receipt checksum mismatch')
    return receipt


def receipt_key(receipt: dict) -> str:
    # Include output bytes so separate builds of the same input cannot collide.
    # Input-to-output authority is the receipt embedded in the active deployment.
    return f'site/builds/{fingerprint(receipt)}.json'


def create_plan(nodes: dict, active: dict | None, receipt: dict | None, client,
                reference_client, *, force: bool = False, source_sha: str = '') -> dict:
    previous = (receipt or {}).get('artifacts', {})
    plan = {'schema': 1, 'sourceSha': source_sha, 'baseline': active or {}, 'nodes': nodes,
            'build': [], 'reuse': {}, 'reasons': {}, 'force': force}

    def select(pair):
        key, item = pair
        if item['family'] == 'references' and reference_client and not force:
            ref = item['metadata']['reference']
            record = {'key': key, 'sha256': ref['source']['sha256'], 'bytes': ref['source']['bytes']}
            # The reviewed reference manifest itself owns immutable reference
            # bytes. No PDF renderer or prior release receipt is needed to prove
            # an already uploaded approved object matches that manifest.
            if object_matches(reference_client, record):
                return key, {'node': item, 'record': record, 'pdf': None}, []
        old = previous.get(key)
        reason = explain(item, old.get('node') if old else None)
        if force:
            reason = ['Explicit force rebuild']
        if old and not reason and old['node']['fingerprint'] == item['fingerprint']:
            record = old['record']
            reference = item['family'] == 'references'
            validate_record(record, reference=reference)
            if reference and record['key'] != key:
                raise ValueError(f'Reference receipt key differs: {key}')
            store = reference_client if reference else client
            if object_matches(store, record):
                return key, old, []
            reason = ['Verified output is absent or has different R2 metadata']
        return key, None, reason or ['Artifact fingerprint changed']

    with ThreadPoolExecutor(max_workers=8) as executor:
        for key, reused, reasons in executor.map(select, nodes.items()):
            if reused:
                plan['reuse'][key] = reused
            else:
                plan['build'].append(key)
                plan['reasons'][key] = reasons
    plan['build'].sort()
    # Slides and notes are one atomic rendering unit, including missing-object
    # repairs: never combine slide images from a new render with an old pair.
    decks = {nodes[key]['deck'] for key in plan['build'] if nodes[key]['family'] == 'presentations'}
    for key, item in nodes.items():
        if item.get('deck') in decks and key not in plan['build']:
            plan['reuse'].pop(key, None)
            plan['build'].append(key)
            plan['reasons'][key] = ['Rebuild the complete slides/notes pair']
    plan['build'].sort()
    return plan


def validate_plan(plan: dict, *, root: Path = BASE) -> dict:
    if plan.get('schema') != 1:
        raise ValueError('Unsupported publication plan')
    nodes = build_graph(root)
    if nodes != plan['nodes']:
        raise ValueError('Publication inputs changed after planning')
    build, reused = set(plan['build']), set(plan['reuse'])
    if build & reused or build | reused != set(nodes) or len(build) != len(plan['build']):
        raise ValueError('Publication plan does not cover the exact current inventory')
    for key, value in plan['reuse'].items():
        if value['node'] != nodes[key]:
            raise ValueError(f'Stale reuse receipt: {key}')
        validate_record(value['record'], reference=nodes[key]['family'] == 'references')
        if nodes[key]['family'] == 'references':
            source = nodes[key]['metadata']['reference']['source']
            expected = {'key': key, 'sha256': source['sha256'], 'bytes': source['bytes']}
            if value['record'] != expected:
                raise ValueError(f'Reference reuse differs from approved bytes: {key}')
    for key, value in plan.get('reviewArtifacts', {}).items():
        if key not in build or not re.fullmatch('[a-f0-9]{64}', value.get('sha256', '')):
            raise ValueError('Invalid reviewed output selection')
    return plan


def selected_specs(path: Path, family: str):
    from _generated_pdf_inventory import generated_pdf_specs
    plan = validate_plan(json.loads(path.read_bytes()))
    return tuple(spec for spec in generated_pdf_specs() if spec.key in plan['build'] and spec.key not in plan.get('reviewArtifacts', {})
                 and plan['nodes'][spec.key]['family'] == family)


def receipt_for_release(manifest: dict, plan: dict) -> dict:
    artifacts = {}
    for key, item in plan['nodes'].items():
        if item['family'] == 'references':
            ref = item['metadata']['reference']
            record = {'key': key, 'sha256': ref['source']['sha256'], 'bytes': ref['source']['bytes']}
            pdf = None
        else:
            record = manifest['files']['/' + key]
            pdf = manifest['pdfs']['/' + key]
        artifacts[key] = {'node': item, 'record': record, 'pdf': pdf}
    return {'schema': 1, 'artifacts': artifacts}


def verify_reuse_authority(client, plan: dict) -> None:
    """Publisher independently reloads the trusted receipt before reusing bytes."""
    generated = {key: reused for key, reused in plan['reuse'].items() if reused['node']['family'] != 'references'}
    if not generated:
        return
    receipt = load_receipt(client, plan['baseline'].get('buildReceiptKey', ''))
    for key, reused in generated.items():
        if receipt['artifacts'].get(key) != reused:
            raise ValueError(f'Reused artifact differs from protected receipt: {key}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--offline', action='store_true', help='Cold plan without reading or writing remote state')
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    nodes = build_graph()
    active = receipt = client = reference_client = None
    if not args.offline:
        from _common import site_base_url
        from _publish_site_release import public_state
        from _publish_reference_artifacts import s3_client, bucket_name
        from _r2_s3 import R2S3Client, load_r2_config
        from _cloudflare_performance import load_repo_env
        load_repo_env()
        client = R2S3Client(load_r2_config())
        reference_client = s3_client(bucket_name())
        # A failed read is not an empty baseline. Fail closed and retry later.
        active = public_state(site_base_url().rstrip('/'))
        if active.get('buildReceiptKey'):
            receipt = load_receipt(client, active['buildReceiptKey'])
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASE, text=True).strip()
    plan = create_plan(nodes, active, receipt, client, reference_client, force=args.force, source_sha=source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(plan, sort_keys=True) + '\n').encode())
    families = {family: any(nodes[key]['family'] == family for key in plan['build'])
                for family in ('markdown', 'presentations', 'references')}
    print(f"Publication plan: {len(plan['build'])} build, {len(plan['reuse'])} reuse; baseline {plan['baseline'].get('revision', 'cold')}")
    for key in plan['build']:
        print(f"  {key}: {', '.join(plan['reasons'][key])}")
    if args.github_output:
        with args.github_output.open('a', encoding='utf-8', newline='\n') as handle:
            handle.writelines(f'{key}={str(value).lower()}\n' for key, value in families.items())
            reference_pdfs = any(nodes[key]['family'] == 'references' and key.endswith('.pdf') and
                                 nodes[key]['metadata']['reference']['target']['storage'] == 'r2-public' for key in plan['build'])
            handle.write(f'reference_pdfs={str(reference_pdfs).lower()}\n')
            handle.write(f"any_build={str(families['markdown'] or families['presentations'] or reference_pdfs).lower()}\n")


if __name__ == '__main__':
    main()
