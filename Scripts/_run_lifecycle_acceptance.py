"""Run isolated lifecycle/browser acceptance and retain explicit evidence.

This never creates live proposals or changes a production publication. The
report distinguishes these checks from the separately recorded live matrix.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

from _common import write_text_lf

BASE = Path(__file__).resolve().parents[1]
BROWSER_INPUTS = {'Studies/submit.html', 'Scripts/_serve_contributor_fixture.py',
                  'Scripts/_test_contributor_harness.js', 'Scripts/_lifecycle_browser_acceptance.js',
                  'Scripts/_run_lifecycle_acceptance.py', '.github/workflows/studies-index-check.yml'}


def needs_browser(base: str) -> bool:
    paths = subprocess.check_output(['git','diff','--name-only',f'{base}...HEAD'],cwd=BASE,text=True).splitlines()
    return any(path in BROWSER_INPUTS or path.startswith(('Studies/portal/','infra/worker/src/')) for path in paths)


def run(output: Path, *, browser: bool = True, browser_only: bool = False) -> bool:
    output.mkdir(parents=True, exist_ok=True)
    report = {'environment':'isolated fixtures', 'generatedAt':datetime.now(timezone.utc).isoformat(),
              'sourceSha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
              'workingTreeDirty':bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=BASE,text=True).strip()),
              'liveAcceptance':'pending separately recorded deployed-revision and recovery scenarios', 'checks':[]}
    def execute(name, command, cwd=BASE):
        try:
            result = subprocess.run(command,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
        except subprocess.TimeoutExpired:
            result = subprocess.CompletedProcess(command,1,'','Acceptance command exceeded five minutes.\n')
        write_text_lf(output/f'{name}.log',result.stdout+result.stderr)
        report['checks'].append({'name':name,'status':'passed' if result.returncode==0 else 'failed','log':f'{name}.log'})
        print(f'{name}: {report["checks"][-1]["status"]}',flush=True)
        return result.returncode == 0
    passed = True
    suites = () if browser_only else ('_test_lifecycle_extensions','_test_companion_lifecycle','_test_companion_removal',
                                      '_test_proposal_workflow','_test_ci_study_pr','_test_artifact_graph','_test_ci_publication')
    for name in suites:
        passed = execute(name,[sys.executable,str(BASE/'Scripts'/f'{name}.py')]) and passed
    if browser:
        from _serve_contributor_fixture import Handler, ThreadingHTTPServer
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            passed = execute('browser',[shutil.which('node') or 'node',str(BASE/'Scripts/_lifecycle_browser_acceptance.js'),
                                         f'http://127.0.0.1:{server.server_port}',str(output)]) and passed
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)
    write_text_lf(output/'acceptance.json',json.dumps(report,indent=2)+'\n')
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope',action='store_true')
    parser.add_argument('--base-ref')
    parser.add_argument('--output',type=Path,default=BASE/'tmp/lifecycle-acceptance')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--browser-only',action='store_true')
    args = parser.parse_args()
    if args.scope:
        selected = needs_browser(args.base_ref) if args.base_ref else True
        value = f'browser={str(selected).lower()}'
        print(value)
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8',newline='\n') as stream: stream.write(value+'\n')
    else:
        raise SystemExit(0 if run(args.output.resolve(),browser=not args.no_browser,browser_only=args.browser_only) else 1)
