"""Audit exact discovery/API candidates on disposable same-zone routes.

Only the unique /__amd_ci/<nonce>/ prefix is routed. Production names, routes,
redirects and pointers are never edited. A receipt is written after all audits
and cleanup succeed; protected deployment requires the same candidate hashes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
import uuid

import _cloudflare_performance as cf
from _worker_deployment import digest


def candidates() -> dict:
    import _publish_agent_skills_snippet as skills
    import _publish_mcp_server_card as mcp
    import _publish_auth_md_snippet as auth
    import _publish_api_catalog_snippet as catalog
    simple = lambda module: {'main_module': 'index.js', 'compatibility_date': module.COMPATIBILITY_DATE}
    return {
        skills.WORKER_NAME: (skills.generate_worker_source(), simple(skills)),
        mcp.WORKER_NAME: (mcp.generate_worker_source(), mcp.deployment_metadata()),
        auth.WORKER_NAME: (auth.worker_js(auth.AUTH_MD_PATH.read_text(encoding='utf-8')), simple(auth)),
        catalog.WORKER_NAME: (catalog.worker_js(json.loads(catalog.CATALOG_PATH.read_bytes())), simple(catalog)),
    }


def candidate_key(source, metadata):
    return digest({'schema': 1, 'source': source, 'metadata': metadata})


def wrap(source: str, prefix: str) -> str:
    if source.count('export default ') != 1:
        raise ValueError('Canary requires exactly one default Worker export')
    return source.replace('export default ', 'const AMD_CANDIDATE = ', 1) + '''
export default {async fetch(request, env, ctx) {
  const url = new URL(request.url), prefix = PREFIX;
  if (!url.pathname.startsWith(prefix)) return new Response('Not Found', {status:404});
  url.pathname = url.pathname.slice(prefix.length - 1);
  return AMD_CANDIDATE.fetch(new Request(url, request), env, ctx);
}};
'''.replace('PREFIX', json.dumps(prefix))


def read(base: str, path: str, payload=None):
    headers = {'User-Agent': 'AMD-Publication-Audit/1.0', 'Cache-Control': 'no-cache'}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers.update({'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Origin': 'https://' + cf.SITE_HOST})
    request = Request(base + path.lstrip('/'), data=data, headers=headers)
    from _publish_site_release import audit_retry
    def fetch():
        with urlopen(request, timeout=45) as response:
            if response.status != 200 or response.headers.get('cf-mitigated') == 'challenge':
                raise ValueError(f'Canary request failed: {path}')
            return response.read()
    return audit_retry(fetch, 'canary ' + path)


def rpc(base, method, params=None):
    reply = json.loads(read(base, '/mcp', {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}))
    if reply.get('error') or reply.get('id') != 1 or 'result' not in reply or reply['result'].get('isError'):
        raise ValueError(f'MCP canary failed: {method}: {reply}')
    return reply['result']


def audit(base: str, name: str) -> list[str]:
    import _publish_agent_skills_snippet as skills
    import _publish_auth_md_snippet as auth
    import _publish_api_catalog_snippet as catalog
    import _publish_mcp_server_card as mcp
    checks = []
    def exact(path, expected, *, structured=True):
        actual = read(base, path)
        actual = json.loads(actual) if structured else actual.decode('utf-8')
        if actual != expected:
            raise ValueError('Canary content mismatch: ' + path)
        checks.append(path)
    if name == skills.WORKER_NAME:
        exact('/.well-known/agent-skills/index.json', json.loads(skills.INDEX_PATH.read_bytes()))
        exact('/.well-known/agent-skills/index-maintainer.json', json.loads(skills.MAINTAINER_INDEX_PATH.read_bytes()))
        published = skills.load_published_skills()
        key = sorted(published)[0]
        exact('/.well-known/agent-skills/' + key + '/SKILL.md', published[key], structured=False)
    elif name == auth.WORKER_NAME:
        exact('/auth.md', auth.AUTH_MD_PATH.read_text(encoding='utf-8'), structured=False)
    elif name == catalog.WORKER_NAME:
        exact('/.well-known/api-catalog', json.loads(catalog.CATALOG_PATH.read_bytes()))
    elif name == mcp.WORKER_NAME:
        exact('/.well-known/mcp/server-card.json', json.loads(mcp.CARD_PATH.read_bytes()))
        rpc(base, 'initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'ci-canary', 'version': '1'}})
        for uri in ('studies://catalog-all', 'studies://glossary', 'studies://start-here'):
            result = rpc(base, 'resources/read', {'uri': uri})
            contents = result.get('contents', [])
            if not contents or not contents[0].get('text'):
                raise ValueError('Empty MCP resource: ' + uri)
            decoded = json.loads(contents[0]['text'])
            if uri == 'studies://catalog-all':
                if not isinstance(decoded, list) or not decoded:
                    raise ValueError('Empty deployed catalog')
                slug = next(row['slug'] for row in decoded if row.get('status') in ('draft', 'released'))
            checks.append(uri)
        for tool, args in (('search_studies', {'query': '', 'limit': 1}), ('get_study_outline', {'slug': slug})):
            rpc(base, 'tools/call', {'name': tool, 'arguments': args})
            checks.append(tool)
        result = rpc(base, 'resources/read', {'uri': 'studies://study/' + slug})
        if not result.get('contents', [{}])[0].get('text', '').strip():
            raise ValueError('Empty deployed Markdown')
        checks.append('deployed-markdown')
        for path in ('/api/studies', '/api/glossary', '/api/start-here', '/api/studies/' + slug):
            data = json.loads(read(base, path))
            if not data or data.get('error'):
                raise ValueError('API canary failed: ' + path)
            checks.append(path)
    else:
        raise ValueError('Unknown publication candidate: ' + name)
    return checks


def run(output: Path) -> dict:
    import _publish_mcp_server_card as uploader
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        raise ValueError('Cloudflare token required')
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = uploader.resolve_account_id(token)
    nonce = uuid.uuid4().hex[:16]
    prefix = '/__amd_ci/' + nonce + '/'
    definitions = candidates()
    created = []
    results = {}
    try:
        for name, (source, metadata) in definitions.items():
            temporary = 'amd-ci-' + nonce + '-' + name.removeprefix('amd-')
            route_prefix = prefix + name + '/'
            pattern = cf.SITE_HOST + route_prefix + '*'
            created.append((temporary, pattern))
            result = uploader.multipart_put(f'{cf.API_BASE}/accounts/{account}/workers/scripts/{temporary}',
                                            token, 'index.js', wrap(source, route_prefix), metadata)
            if not result.get('success'):
                raise ValueError('Canary upload failed: ' + temporary)
            cf._api_request('POST', f'/zones/{zone}/workers/routes', token, {'pattern': pattern, 'script': temporary})
            results[name] = {'fingerprint': candidate_key(source, metadata),
                             'checks': audit('https://' + cf.SITE_HOST + route_prefix, name)}
            print(f'{name}: same-zone candidate passed {len(results[name]["checks"])} checks.', flush=True)
    finally:
        # Discover exact owned routes too: a successful POST may lose its response.
        failures = []
        routes = cf._api_request('GET', f'/zones/{zone}/workers/routes', token).get('result', [])
        for temporary, pattern in reversed(created):
            try:
                for route in routes:
                    if route.get('pattern') == pattern and route.get('script') == temporary:
                        cf._api_request('DELETE', f'/zones/{zone}/workers/routes/{route["id"]}', token)
                cf._api_request('DELETE', f'/accounts/{account}/workers/scripts/{temporary}', token, allow_404=True)
            except Exception as exc:
                failures.append(f'{temporary}: {exc}')
        if failures:
            raise RuntimeError('Canary cleanup failed: ' + '; '.join(failures))
    receipt = {'schema': 1, 'passed': True, 'checkedAt': datetime.now(timezone.utc).isoformat(),
               'zone': zone, 'account': account, 'candidates': results, 'cleanup': 'complete'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    return receipt


def require_receipt(path: Path, name: str, source: str, metadata: dict, account: str):
    receipt = json.loads(path.read_bytes())
    stamp = datetime.fromisoformat(receipt['checkedAt'])
    age = time.time() - stamp.timestamp()
    if (receipt.get('schema') != 1 or receipt.get('passed') is not True or receipt.get('cleanup') != 'complete'
            or receipt.get('account') != account or not 0 <= age <= 3600
            or receipt.get('candidates', {}).get(name, {}).get('fingerprint') != candidate_key(source, metadata)):
        raise ValueError('Missing, expired or mismatched same-zone canary receipt: ' + name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
