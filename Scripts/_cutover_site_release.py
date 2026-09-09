"""One-time public-route migration after a complete production release is audited.

API routes retain their owners. Old generated-PDF and reference overrides are
removed only after installing the complete site route. A failure restores the
previous route table for the exact patterns changed here.
"""
import argparse
from pathlib import Path

import _cloudflare_performance as cf
from _publish_generated_pdf_worker import _zone_account_id, _workers_subdomain, MANAGED_ROUTES
from _publish_site_release import WORKER, audit
from _site_release import validate_bundle


def cutover(root: Path, *, apply: bool) -> None:
    manifest = validate_bundle(root)
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = _zone_account_id(token, zone)
    subdomain = _workers_subdomain(token, account)
    audit(f'https://{WORKER}.{subdomain}.workers.dev', root, manifest)
    patterns = {f'{cf.SITE_HOST}/*', *MANAGED_ROUTES}
    previous = [route for route in cf.list_worker_routes(token, zone) if route['pattern'] in patterns]
    if any(route.get('script') not in {WORKER, 'amd-generated-pdfs'} for route in previous):
        raise ValueError('A cutover pattern has another owner; inspect it before migration.')
    print('Audited production release. Changes: root site route -> amd-site; remove legacy PDF/reference overrides.')
    if not apply:
        return
    try:
        cf.ensure_worker_route(token, zone, f'{cf.SITE_HOST}/*', WORKER)
        for route in previous:
            if route['pattern'] != f'{cf.SITE_HOST}/*':
                cf._api_request('DELETE', f'/zones/{zone}/workers/routes/{route["id"]}', token)
        urls = [f'https://{cf.SITE_HOST}{path}' for path in manifest['files']]
        for offset in range(0, len(urls), 30):
            cf.purge_cache_files(token, zone, urls[offset:offset + 30])
        audit(f'https://{cf.SITE_HOST}', root, manifest,
              origin_base=f'https://{WORKER}.{subdomain}.workers.dev')
    except Exception:
        for route in cf.list_worker_routes(token, zone):
            if route['pattern'] in patterns:
                cf._api_request('DELETE', f'/zones/{zone}/workers/routes/{route["id"]}', token)
        for route in previous:
            cf._api_request('POST', f'/zones/{zone}/workers/routes', token, {key:route[key] for key in ('pattern','script')})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-root', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    cutover(args.release_root, apply=args.apply)
