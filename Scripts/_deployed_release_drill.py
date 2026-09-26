"""Exercise the real publisher and offline reader on disposable deployed resources.

This never edits production routes, versions or buckets. Lifecycle state inputs
are fixtures; GitHub approvals/authenticated submissions are separately accepted.
Core Cloudflare/R2/audit/rollback responses are real, not mocked.
"""
import argparse
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from unittest.mock import patch
import uuid

import _cloudflare_performance as cf
import _generated_pdf_inventory as inventory
import _publish_generated_pdfs as artifacts
import _publish_site_release as publisher
import _site_release as release
from _common import BASE
from _r2_s3 import R2S3Client, load_r2_config


def run(output: Path, bucket_receipt: Path | None = None):
    output.mkdir(parents=True, exist_ok=True)
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    from _publish_mcp_server_card import resolve_account_id
    account = resolve_account_id(token)
    subdomain = publisher._workers_subdomain(token, account)
    nonce = uuid.uuid4().hex[:16]
    worker, canary = 'amd-ci-drill-' + nonce, 'amd-ci-drill-canary-' + nonce
    if bucket_receipt:
        owned = json.loads(bucket_receipt.read_bytes())
        if not re.fullmatch(r'amd-ci-acceptance-[a-f0-9]{16}', owned['name']) or owned['account'] != account:
            raise ValueError('Bucket receipt is not an isolated owned fixture')
        bucket = owned['name']
    else:
        bucket = 'amd-ci-acceptance-' + nonce
        cf._api_request('POST', f'/accounts/{account}/r2/buckets', token, {'name': bucket})
    client = R2S3Client(replace(load_r2_config(), bucket=bucket))
    report = {'schema': 1, 'sourceSha': subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
              'environment': 'isolated deployed Cloudflare Worker and R2 bucket', 'worker': worker, 'bucket': bucket,
              'productionMutations': 0, 'externalLifecycle': 'not exercised: approved GitHub proposal/submission matrix is separate',
              'checks': [], 'cleanup': 'pending'}
    root = output / 'source'
    root.mkdir()
    study = root / 'Studies/CI-Acceptance/CI-Acceptance.md'
    study.parent.mkdir(parents=True)
    browser = None
    def git(*args):
        return subprocess.check_output(['git','-c','user.name=CI fixture','-c','user.email=fixture@example.test',*args],cwd=root,text=True).strip()
    def write(path, body):
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(body.encode() if isinstance(body, str) else body)
    def check(name, **fields):
        report['checks'].append({'name': name, 'passed': True, **fields})
        print(name + ': passed', flush=True)
    def browser_action(value):
        browser.stdin.write(json.dumps(value)+'\n'); browser.stdin.flush()
        while True:
            line = browser.stdout.readline()
            if not line:
                raise ValueError('Browser drill exited before reporting')
            if line.startswith('{'):
                result = json.loads(line)
                if not result.get('passed'):
                    raise ValueError('Deployed browser check failed: ' + str(result))
                return result
    try:
        git('init', '-b', 'master')
        write('Scripts/_cloudflare_performance.py',(BASE/'Scripts/_cloudflare_performance.py').read_bytes())
        write('infra/site-worker/withdrawals.json',(BASE/'infra/site-worker/withdrawals.json').read_bytes())
        # Include the shipped reader and service worker resource closure.
        for path in (BASE / 'Assets').rglob('*'):
            if path.is_file() and (path.is_relative_to(BASE/'Assets/reader') or path.is_relative_to(BASE/'Assets/KaTeX') or path.is_relative_to(BASE/'Assets/Icons')):
                write(path.relative_to(BASE), path.read_bytes())
        write('reader-sw.js', (BASE/'reader-sw.js').read_bytes())
        from _build_reader_offline import notebook_html
        write('Studies/notebook.html', notebook_html())
        write('index.html', '<!doctype html><html><body><h1>Isolated CI publication acceptance</h1><a href="/Studies/CI-Acceptance/CI-Acceptance.html">Reader</a></body></html>')
        stamp = subprocess.check_output(['powershell.exe','-NoProfile','-Command','Get-Date -Format "MMMM d, yyyy, h:mm tt"'],text=True).strip()+' IST' if sys.platform=='win32' else datetime.now(timezone.utc).strftime('%B %d, %Y, %I:%M %p UTC')
        versions, releases = {}, {}
        with ExitStack() as stack:
            stack.enter_context(patch.object(publisher, 'WORKER', worker))
            stack.enter_context(patch.object(publisher, 'CANARY', canary))
            stack.enter_context(patch.object(publisher, 'BASE', root))
            stack.enter_context(patch.object(publisher, 'R2S3Client', lambda _: client))
            stack.enter_context(patch.object(artifacts, 'mapped_path', lambda destination, configured: destination / configured.relative_to(root)))
            for phase in ('planned', 'draft', 'released', 'retired'):
                status = phase.capitalize()
                rows = [] if phase=='retired' else [{'slug':'CI-Acceptance','title':'CI acceptance','description':'Disposable CI fixture',
                         'category':'CI','status':'ongoing' if phase=='planned' else phase,'updated':stamp,'collection':'topical'}]
                for family in ('topical','formal','applied'):
                    write(f'Studies/catalog-{family}.json',json.dumps(rows if family=='topical' else []))
                write('Studies/catalog-all.json',json.dumps(rows))
                specs = ()
                if phase in ('draft','released'):
                    write(study.relative_to(root),f'# CI acceptance\n\n**Author:** CI fixture\n\n**Edited on:** {stamp}\n\n**Status:** {status}\n\n## Purpose\n\nDisposable publication and recovery evidence.\n\n## Result\n\nThis fixture has no scholarly publication claim.\n')
                    from _study_pdf_pipeline import _regenerate_pdf
                    from _study_pdf_metadata import StudyStatus
                    _regenerate_pdf(study, StudyStatus.DRAFT if phase=='draft' else StudyStatus.RELEASED, study.with_suffix('.html'), False)
                    specs = (inventory.GeneratedPdfSpec('Studies/CI-Acceptance/CI-Acceptance.pdf',study,study.with_suffix('.pdf'),'markdown'),)
                    resources = []
                    files = [study.with_suffix('.html'),root/'Studies/notebook.html'] + [p for p in (root/'Assets').rglob('*') if p.is_file() and p.suffix in ('.js','.css','.woff2','.svg','.png','.ico')]
                    for file in files:
                        resources.append({'url':'/'+file.relative_to(root).as_posix(),'sha256':release.digest(file.read_bytes()),'bytes':file.stat().st_size})
                    write('Studies/offline-manifest.json',json.dumps({'schema':1,'documents':[{'path':'/Studies/CI-Acceptance/CI-Acceptance.html','title':'CI acceptance',
                          'version':release.digest(study.read_bytes()),'resources':resources}]}))
                else:
                    write('Studies/offline-manifest.json',json.dumps({'schema':1,'documents':[]}))
                git('add','.');git('commit','-m','Fixture '+phase)
                sha = git('rev-parse','HEAD')
                sources = {'/'+p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts
                           and not p.is_relative_to(root/'Scripts') and not p.is_relative_to(root/'infra')
                           and (not p.is_relative_to(study.parent) or phase in ('draft','released')) and p.suffix!='.pdf'}
                bundle = output / phase
                with patch.object(inventory,'generated_pdf_specs',return_value=specs), patch.object(release,'static_sources',return_value=sources):
                    manifest = release.build(bundle, root, root=root, source_sha=sha)
                    publisher.publish(bundle, promote=True)
                revision = manifest['revision']
                versions[phase] = publisher.deployments(token,account)[0]['versions'][0]['version_id']
                releases[phase] = revision
                base = f'https://{worker}.{subdomain}.workers.dev'
                check(phase+' publication', revision=revision,sourceSha=sha,version=versions[phase])
                if phase=='draft':
                    browser=subprocess.Popen(['node',str(BASE/'Scripts/_deployed_release_browser.cjs'),base,'/Studies/CI-Acceptance/CI-Acceptance.html'],
                                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(output/'browser.log').open('w'),text=True,encoding='utf-8')
                    check('deployed offline save', **browser_action({'action':'save','revision':revision}))
                if phase=='released':
                    check('open reader through deployment and disconnection', **browser_action({'action':'after','savedRevision':releases['draft']}))
                if phase=='retired':
                    from urllib.error import HTTPError
                    from urllib.request import urlopen
                    try:
                        urlopen(base+'/Studies/CI-Acceptance/CI-Acceptance.html',timeout=30)
                    except HTTPError as error:
                        if error.code != 404: raise
                    else:
                        raise ValueError('Retired canonical reader is still published')
                    check('retired canonical path absent')
                    publisher.rollback(releases['draft'])
                    check('controlled deployed rollback',revision=releases['draft'])
                    publisher.activate_version(token,account,versions['retired'])
                    publisher.audit(base,bundle,manifest)
                    check('forward recovery promotion',revision=revision)
        report['passed'] = True
    finally:
        if browser:
            try:
                browser.stdin.write(json.dumps({'action':'close'})+'\n');browser.stdin.flush()
            except Exception: pass
            try: browser.wait(timeout=20)
            except subprocess.TimeoutExpired: browser.kill();browser.wait()
        failures=[]
        for name in (canary,worker):
            try: cf._api_request('DELETE',f'/accounts/{account}/workers/scripts/{name}',token,allow_404=True)
            except Exception as error: failures.append(str(error))
        # Only a uniquely named owned test bucket is ever cleared, never either
        # production bucket. Bucket/Worker receipts identify cleanup after failure.
        try:
            for key in client.list_objects(''):
                client._request('DELETE',client._object_path(key))
            cf._api_request('DELETE',f'/accounts/{account}/r2/buckets/{bucket}',token)
        except Exception as error: failures.append(str(error))
        report['cleanup']='complete' if not failures else failures
        report['generatedAt']=datetime.now(timezone.utc).isoformat()
        (output/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        if failures: raise RuntimeError('Isolated drill cleanup failed: '+'; '.join(failures))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--owned-bucket-receipt',type=Path)
    args=parser.parse_args()
    run(args.output.resolve(),args.owned_bucket_receipt)
