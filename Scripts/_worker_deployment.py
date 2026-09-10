"""Deploy a Worker only when its executable/configuration fingerprint changes.

The active Cloudflare version annotation is the receipt. Local Actions caches
and the previous Git push are not deployment authority, including after rollback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib

import _cloudflare_performance as cf

ANNOTATION = 'amd-input-sha256:'


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def active_fingerprint(token: str, account: str, name: str) -> str | None:
    prefix = f'/accounts/{account}/workers/scripts/{name}'
    try:
        payload = cf._api_request('GET', prefix + '/deployments', token).get('result', {})
    except RuntimeError as error:
        if re.search(r'HTTP\s*404\b', str(error)):
            return None
        raise
    deployments = payload.get('deployments', []) if isinstance(payload, dict) else payload
    versions = deployments[0].get('versions', []) if deployments else []
    if len(versions) != 1 or versions[0].get('percentage', 100) != 100:
        return None
    version = cf._api_request('GET', prefix + '/versions/' + versions[0]['version_id'], token).get('result', {})
    message = version.get('annotations', {}).get('workers/message', '')
    return message[len(ANNOTATION):] if re.fullmatch(ANNOTATION + '[a-f0-9]{64}', message) else None


def deploy_source(token: str, account: str, name: str, source: str, metadata: dict, uploader) -> dict:
    key = digest({'schema': 1, 'source': source, 'metadata': metadata})
    if active_fingerprint(token, account, name) == key:
        print(f'{name}: executable and bindings are unchanged; deployment skipped.')
        return {'result': {'skipped': True, 'fingerprint': key}}
    annotated = {**metadata, 'annotations': {**metadata.get('annotations', {}), 'workers/message': ANNOTATION + key}}
    return uploader(f'{cf.API_BASE}/accounts/{account}/workers/scripts/{name}', token, 'index.js', source, annotated)


def directory_fingerprint(directory: Path) -> str:
    config = tomllib.loads((directory / 'wrangler.toml').read_text(encoding='utf-8'))
    pending = [(directory / config['main']).resolve()]
    files = {}
    while pending:
        path = pending.pop()
        if not path.is_relative_to(cf.BASE.resolve()):
            raise ValueError(f'Worker import escapes repository: {path}')
        name = path.relative_to(cf.BASE).as_posix()
        if name in files:
            continue
        source = path.read_text(encoding='utf-8')
        files[name] = hashlib.sha256(source.encode()).hexdigest()
        imports = re.findall(r'(?:from\s*|import\s*(?:\(\s*)?|require\s*\()\s*[\"\x27](\.[^\"\x27]+)[\"\x27]', source)
        pending.extend((path.parent / item).resolve() for item in imports)
    files['package-lock.json'] = hashlib.sha256((directory / 'package-lock.json').read_bytes()).hexdigest()
    return digest({'schema': 1, 'node': '24', 'config': config, 'files': files})


def observability_settings(config: dict) -> dict | None:
    """Build the API setting; Wrangler does not yet expose query redaction."""
    if not config.get('observability'):
        return None
    settings = json.loads(json.dumps(config['observability']))
    settings.setdefault('logs', {})['redact_query_string'] = True
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--deploy', action='store_true')
    args = parser.parse_args()
    directory = args.directory.resolve()
    key = directory_fingerprint(directory)
    if not args.deploy:
        print(key)
        return
    cf.load_repo_env()
    token, account = cf.cloudflare_api_token(), cf.cloudflare_account_id()
    if not token or not account:
        raise ValueError('Cloudflare token and account ID are required')
    config = tomllib.loads((directory / 'wrangler.toml').read_text(encoding='utf-8'))
    if active_fingerprint(token, account, config['name']) == key:
        print(f"{config['name']}: executable and configuration are unchanged; deployment skipped.")
    else:
        command = ['node', str(directory / 'node_modules/wrangler/bin/wrangler.js'), 'deploy', '--message', ANNOTATION + key]
        subprocess.run(command, cwd=directory, check=True)
    observability = observability_settings(config)
    if observability:
        cf._api_request(
            'PATCH',
            f"/accounts/{account}/workers/scripts/{config['name']}/script-settings",
            token,
            {'observability': observability},
        )
        print(f"{config['name']}: persistent Worker logs enabled with query-string redaction.")


if __name__ == '__main__':
    main()
