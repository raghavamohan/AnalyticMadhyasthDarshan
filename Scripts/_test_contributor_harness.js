/* This file is injected only by _serve_contributor_fixture.py. */
(() => {
  const realFetch = window.fetch.bind(window), realIDB = window.indexedDB;
  Object.defineProperty(window, 'indexedDB', {value:{open:(_,version) => { if(new URLSearchParams(location.search).get('storage') === 'blocked') throw new Error('Browser storage unavailable in this test. Download a backup before leaving.'); return realIDB.open('amd-contributor-fixture-v2',version); }}});
  const response = (data,status=200) => Promise.resolve(new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}}));
  const study = '# Test study\n\n**Author:** Alice\n\n## Introduction\n\nA comparison of approaches.\n\n## Table\n\n| Tradition | Claim |\n| --- | --- |\n| MD | Coexistence |\n\n## Equation\n\n$E=mc^2$ and $$x=\\frac{a}{b}$$\n\n```mermaid\nflowchart LR\n  A[Question] --> B[Study]\n```\n\n## References\n\n[Source](https://example.org)\n';
  const registry = {studies:[{slug:'Test-Study',root:'Studies',title:'Test study',notes:['Research-Note-Test.md'],presentations:['Test-Deck.pptx']},{slug:'Second-Study',root:'Applications',title:'Second study',notes:[],presentations:[]}]};
  let account = sessionStorage.getItem('fixture-account') || 'alice';
  window.fetch = async (input, options={}) => {
    const url = new URL(typeof input === 'string' ? input : input.url,location.href);
    if (url.pathname.endsWith('/companion-artifacts.json')) return response(registry);
    if (!url.pathname.startsWith('/api/') && url.origin === location.origin) return realFetch(input,options);
    if (url.pathname === '/api/auth/me') return response({loggedIn:account !== 'signed-out',login:account,userId:account === 'alice' ? 1 : 2});
    if (url.pathname === '/api/auth/logout') { account = 'signed-out'; sessionStorage.setItem('fixture-account',account); return response({success:true}); }
    if (url.pathname === '/api/me/notifications') return response({configured:false,enabled:false});
    if (url.pathname === '/api/me/submissions') return response({success:true,submissions:[{title:'Test study',slug:'Test-Study',stage:'changes_requested',kindLabel:'Study',catalogStatus:'draft',categories:['Ontology'],pullRequest:{number:123,url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/123'},feedback:[{reviewer:'reviewer',body:'Clarify the comparison in §2. <script>alert(1)</script>',url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/123#pullrequestreview-1'}],checks:{state:'failure',url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/123/checks',details:[{name:'Study PR',conclusion:'failure',title:'Missing References section',summary:'Add ## References and run the reference verifier.',url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/1'}]},actions:[]}],meta:{}});
    if (url.pathname === '/api/study-source' || url.pathname === '/api/revision-source') {
      if (document.getElementById('fixture-delay')?.checked) await new Promise(resolve => setTimeout(resolve,2500));
      return response({success:true,slug:url.searchParams.get('slug') || 'Test-Study',content:study,sourceSha:'a'.repeat(40),prNumber:123});
    }
    if (url.pathname === '/api/operation') {
      const saved = sessionStorage.getItem('fixture-operation-' + url.searchParams.get('id'));
      return response(saved ? {...JSON.parse(saved),completed:true} : {success:false,notStarted:true});
    }
    if (['/api/submit','/api/revise','/api/propose'].includes(url.pathname)) {
      const data = JSON.parse(options.body), mode = document.getElementById('fixture-submit').value;
      if (mode === 'not-reached') throw new Error('Simulated connection failure before arrival');
      if (mode === 'conflict') return response({success:false,error:'The source changed. Download your draft, load current source and compare.'},409);
      const result = {success:true,number:123,issueNumber:123,url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/123'};
      sessionStorage.setItem('fixture-operation-' + data.operationId,JSON.stringify(result));
      document.getElementById('fixture-payload').textContent = JSON.stringify(data,null,2);
      if (mode === 'lost') throw new Error('Simulated lost response after success');
      return response(result);
    }
    if (url.pathname === '/api/proposal-status') return response({success:true,approved:true,ownedByYou:true,workspaceReady:true,slug:'Test-Study',state:'approved'});
    throw new Error('Fixture blocked unexpected request: ' + url.pathname);
  };
  addEventListener('DOMContentLoaded', () => {
    const bar = document.createElement('aside');
    bar.style.cssText='padding:12px;background:#fff4cf;color:#111;position:relative;z-index:1000';
    bar.innerHTML='<strong>LOCAL FIXTURE — no real submissions</strong> <label>Test account <select id="fixture-account"><option>alice</option><option>bob</option><option>signed-out</option></select></label> <label><input id="fixture-delay" type="checkbox">Delay source</label> <label>Submit outcome <select id="fixture-submit"><option value="success">Success</option><option value="lost">Lost response after success</option><option value="not-reached">Never reached server</option><option value="conflict">Source conflict</option></select></label><details><summary>Last mock payload</summary><pre id="fixture-payload"></pre></details>';
    document.body.prepend(bar);
    document.getElementById('fixture-account').value=account;
    document.getElementById('fixture-account').onchange=async event => {account=event.target.value;sessionStorage.setItem('fixture-account',account);await refreshAuthState();};
    for(const form of document.querySelectorAll('form')) {const input=document.createElement('input');input.type='hidden';input.name='cf-turnstile-response';input.value='fixture';form.append(input);}
  });
})();
