// Run from either API Worker's directory after npm ci. Load the real routing
// source as ESM; the submissions package also contains CommonJS tooling.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import test from 'node:test';

async function sourceUrl(file) {
  let source = await readFile(file, 'utf8');
  if (path.basename(process.cwd()) === 'worker' && file === path.resolve('src/index.js'))
    source += '\nexport {submissionStage,aggregateCheckRuns,fetchPrReviewState,buildDashboard,buildDashboardStatus};\n';
  for (const match of [...source.matchAll(/from ['"]([^'"]+)['"]/g)]) {
    const target = match[1];
    const url = target.startsWith('.')
      ? await sourceUrl(path.resolve(path.dirname(file), target))
      : pathToFileURL(createRequire(pathToFileURL(file)).resolve(target)).href;
    source = source.replace(match[0], `from '${url}'`);
  }
  return 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
}
const workerModule = await import(await sourceUrl(path.resolve('src/index.js')));
const worker = workerModule.default;
const discussion = path.basename(process.cwd()) === 'discussions-worker';
const prefix = discussion ? '/api/discuss-auth' : '/api/auth';
const origin = 'https://analyticmadhyasthdarshan.org';
const url = suffix => 'https://api.example' + prefix + suffix;

if (!discussion) test('dashboard separates workflow state and reports current failed checks',async () => {
  assert.equal(workerModule.submissionStage({labels:[]},{state:'open',changesRequested:true}),'changes_requested');
  const original=globalThis.fetch;
  try {
    globalThis.fetch=async () => Response.json({check_runs:[
      {id:1,name:'Study PR',app:{id:1},status:'completed',conclusion:'failure'},
      {id:2,name:'Study PR',app:{id:1},status:'completed',conclusion:'success'},
      {id:3,name:'Security',app:{id:1},status:'completed',conclusion:'failure',output:{title:'A real error',summary:'Fix the indicated rule.'}},
    ],total_count:3});
    const summary=await workerModule.aggregateCheckRuns('head',{}, {githubRequests:0});
    assert.equal(summary.state,'failure');assert.equal(summary.details.length,1);assert.equal(summary.details[0].name,'Security');
    globalThis.fetch=async () => Response.json([{id:1,user:{login:'reviewer'},state:'CHANGES_REQUESTED',body:'Clarify §2.'}]);
    const review=await workerModule.fetchPrReviewState(1,{},'test',{githubRequests:0});
    assert.equal(review.state,'changes_requested');assert.equal(review.feedback[0].body,'Clarify §2.');
  } finally {globalThis.fetch=original;}
});

if (!discussion) test('dashboard status uses the open-PR head and enriches without a PR detail request',async () => {
  const original=globalThis.fetch;
  const calls=[];
  try {
    globalThis.fetch=async input => {
      const url=String(input);calls.push(url);
      if (url.includes('/pulls?state=open')) return Response.json([{
        number:7,state:'open',draft:false,html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/7',
        body:'Proposal issue: #3\nPortal-GitHub: @alice',labels:[{name:'new-study'}],
        user:{login:'portal-bot'},head:{sha:'head-sha'},
      }]);
      if (url.endsWith('/pulls/7/reviews')) return Response.json([
        {id:1,user:{login:'reviewer'},state:'CHANGES_REQUESTED',body:'Clarify the argument.'},
      ]);
      if (url.includes('/commits/head-sha/check-runs')) return Response.json({
        check_runs:[{id:1,name:'Study PR',app:{id:1},status:'completed',conclusion:'success'}],total_count:1,
      });
      throw new Error('Unexpected dashboard status request: '+url);
    };
    const result=await workerModule.buildDashboardStatus({login:'alice',accessToken:'test'},{});
    assert.equal(result.statuses.length,1);
    assert.equal(result.statuses[0].stage,'changes_requested');
    assert.equal(result.statuses[0].checks.state,'success');
    assert.equal(result.meta.githubRequests,3);
    assert.equal(calls.some(url => new URL(url).pathname.endsWith('/pulls/7')),false);

    const auth=await import(await sourceUrl(path.resolve('src/auth.js')));
    const kv=new Map();
    const env={SESSION_SECRET:'fixture-only',SESSIONS:{
      put:async (key,value) => kv.set(key,value),get:async key => kv.get(key),
    }};
    const token=await auth.createSession(env,{login:'alice',userId:1,accessToken:'test'});
    const response=await worker.fetch(new Request('https://api.example/api/me/submissions/status',{
      headers:{Cookie:auth.setSessionCookie(token,env).split(';')[0]},
    }),env);
    const payload=await response.json();
    assert.equal(response.status,200);
    assert.equal(payload.statuses[0].number,7);
    assert.match(response.headers.get('Server-Timing'),/^github-status;dur=\d+$/);
  } finally {globalThis.fetch=original;}
});

if (!discussion) test('full dashboard avoids the historical PR search on the blocking path',async () => {
  const originalFetch=globalThis.fetch;
  const originalCaches=globalThis.caches;
  const calls=[];
  try {
    globalThis.caches={default:{
      match:async request => {
        const url=String(request.url || request);
        if (url.endsWith('/catalog-maps-v2')) return Response.json({
          statuses:{'Test-Study':'draft'},categories:{'Test-Study':['Human']},
        });
        if (url.endsWith('/proposal-registry')) return Response.json({
          version:1,proposals:[{issueNumber:3,slug:'Test-Study',phase:'catalog'}],
        });
        return null;
      },
      put:async () => {},
    }};
    globalThis.fetch=async input => {
      const url=String(input);calls.push(url);
      if (url.includes('/issues?creator=alice')) return Response.json([{
        number:3,state:'closed',title:'Study proposal: Test Study',
        body:'### Slug\n\nTest-Study\n\n### Category\n\nHuman',
        labels:[{name:'study-proposal'},{name:'proposal-approved'}],
        user:{login:'alice'},html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/3',
      }]);
      if (url.includes('/pulls?state=open')) return Response.json([]);
      throw new Error('Unexpected full dashboard request: '+url);
    };
    const result=await workerModule.buildDashboard({login:'alice',accessToken:'test'},{});
    assert.equal(result.submissions.length,1);
    assert.equal(result.submissions[0].stage,'merged');
    assert.equal(result.submissions[0].slug,'Test-Study');
    assert.equal(result.meta.githubRequests,2);
    assert.equal(calls.length,2);
    assert.equal(calls.some(url => url.includes('/search/issues')),false);
  } finally {
    globalThis.fetch=originalFetch;
    if (originalCaches === undefined) delete globalThis.caches;
    else globalThis.caches=originalCaches;
  }
});

test('real routes apply write checks and private headers before handlers', async () => {
  for (const headers of [{}, { Origin: 'https://evil.example', 'Content-Type': 'application/json' }]) {
    const response = await worker.fetch(new Request(url('/logout'), { method: 'POST', headers }), {});
    assert.equal(response.status, 403);
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
  }
  const response = await worker.fetch(new Request(url('/logout'), {
    method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json' },
  }), {});
  assert.equal(response.status, 200);
  assert.match(response.headers.get('Set-Cookie'), /Max-Age=0/);
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
  const me = await worker.fetch(new Request(url('/me')), {});
  assert.deepEqual(await me.json(), { loggedIn: false });
  assert.equal(me.headers.get('Cache-Control'), 'private, no-store');
  const missing = await worker.fetch(new Request('https://api.example/unknown'), {});
  assert.equal(missing.status, 404);
  assert.equal(missing.headers.get('Cache-Control'), 'private, no-store');
});

if (discussion) test('comment listing includes an email-free viewer summary', async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const env = {
    SESSION_SECRET:'fixture-only',
    ADMIN_EMAILS:'alice@example.test',
    DB:{prepare:() => ({bind:() => ({all:async () => ({results:[]})})})},
  };
  const signedOut = await worker.fetch(new Request('https://api.example/api/discussions/Test-Study'), env);
  assert.deepEqual(await signedOut.json(), {slug:'Test-Study',viewer:{loggedIn:false},comments:[]});

  const token = await auth.createSession(env, {
    userId:'user-1',email:'alice@example.test',displayName:'Alice',
  });
  const signedIn = await worker.fetch(new Request('https://api.example/api/discussions/Test-Study', {
    headers:{Cookie:auth.setSessionCookie(token,env).split(';')[0]},
  }), env);
  const payload = await signedIn.json();
  assert.deepEqual(payload.viewer, {loggedIn:true,isAdmin:true});
  assert.equal(JSON.stringify(payload).includes('alice@example.test'), false);
});

if (!discussion) test('auth snapshot includes notification state without exposing the email address', async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv = new Map();
  const env = {
    SESSION_SECRET: 'fixture-only',
    RESEND_API_KEY: 'fixture-only',
    SESSIONS: {
      put: async (key, value) => kv.set(key, value),
      get: async key => kv.get(key),
    },
  };
  const token = await auth.createSession(env, {login:'alice',userId:1,accessToken:'test'});
  await env.SESSIONS.put('notify:alice', JSON.stringify({email:'alice@example.test',enabled:true}));
  const response = await worker.fetch(new Request(url('/me'), {
    headers:{Cookie:auth.setSessionCookie(token,env).split(';')[0]},
  }), env);
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.deepEqual(payload.notifications, {configured:true,hasEmail:true,enabled:true});
  assert.equal(JSON.stringify(payload).includes('alice@example.test'), false);
});

if (!discussion) test('callback rejects mismatched state before any GitHub request', async () => {
  const configured = { GITHUB_CLIENT_ID: 'test', GITHUB_CLIENT_SECRET: 'test', SESSION_SECRET: 'test', SESSIONS: {} };
  const login = await worker.fetch(new Request(url('/github')), configured);
  assert.equal(login.status, 302);
  const oauthUrl = new URL(login.headers.get('Location'));
  assert.equal(oauthUrl.searchParams.get('code_challenge_method'), 'S256');
  const original = globalThis.fetch;
  let calls = 0;
  try {
    globalThis.fetch = async () => { calls++; throw new Error('Unexpected upstream request'); };
    const result = await worker.fetch(new Request(url('/callback?code=test&state=wrong'), {
      headers: { Cookie: login.headers.get('Set-Cookie').split(';')[0] },
    }), configured);
    assert.equal(result.status, 302);
    assert.match(result.headers.get('Location'), /auth_error=/);
    assert.equal(calls, 0);
    assert.match(result.headers.get('Set-Cookie'), /Max-Age=0/);
  } finally { globalThis.fetch = original; }
});

if (!discussion) test('revision routes reject stale source and replay a receipt without another GitHub write',async () => {
  const {storageFixture} = await import('./_test_contributor.mjs');
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv = new Map(), objects = new Map();
  const env = {SESSION_SECRET:'fixture-only',GITHUB_TOKEN:'fixture-only',TURNSTILE_SECRET_KEY:'fixture-only',
    SESSIONS:{put:async (key,value) => kv.set(key,value),get:async key => kv.get(key)}};
  const token = await auth.createSession(env,{login:'alice',userId:1,accessToken:'fixture-only'});
  const cookie = auth.setSessionCookie(token,env).split(';')[0];
  env.CONTRIBUTOR_OPERATIONS = {idFromName:value => value,get:id => {
    if (!objects.has(id)) objects.set(id,new workerModule.ContributorOperations({storage:storageFixture()},env));
    return objects.get(id);
  }};
  const headers={Origin:origin,'Content-Type':'application/json',Cookie:cookie};
  const pr={state:'open',number:7,labels:[{name:'new-study'}],body:'Slug: Test-Study\nPortal-GitHub: @alice',
    head:{ref:'test-branch',sha:'head-sha',repo:{full_name:'raghavamohan/AnalyticMadhyasthDarshan'}},html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/7'};
  let writes=0, latestMessage='';
  const original=globalThis.fetch;
  globalThis.fetch=async (input,options={}) => {
    const url=String(input);
    if (url.includes('/siteverify')) return Response.json({success:true});
    if (url.endsWith('/pulls/7')) return Response.json(pr);
    if (url.includes('/contents/Studies/Test-Study/Test-Study.md')) {
      if (options.method==='PUT') {writes++;latestMessage=JSON.parse(options.body).message;return Response.json({content:{sha:'b'.repeat(40)}});}
      return Response.json({content:btoa('# Test study\n\nSource text'),sha:'a'.repeat(40)});
    }
    if (url.includes('/search/issues')) return Response.json({items:[],total_count:0});
    if (url.includes('/commits?')) return Response.json([{commit:{message:'CI regenerated artifacts'}},{commit:{message:latestMessage}}]);
    throw new Error('Unexpected fixture request: '+url);
  };
  const post = data => worker.fetch(new Request('https://api.example/api/revise',{method:'POST',headers,body:JSON.stringify(data)}),env);
  const base={prNumber:7,author:'Alice',content:'# Test study\n\nA revised study.',turnstileToken:'fixture'};
  try {
    const loaded=await worker.fetch(new Request('https://api.example/api/revision-source?pr=7',{headers}),env);
    assert.equal((await loaded.json()).sourceSha,'a'.repeat(40));
    const stale=await post({...base,operationId:crypto.randomUUID(),sourceSha:'b'.repeat(40)});
    assert.equal(stale.status,409);assert.equal(writes,0);
    const id=crypto.randomUUID(), body={...base,operationId:id,sourceSha:'a'.repeat(40)};
    const first=await post(body);assert.equal(first.status,200);assert.equal(writes,1);
    const again=await post({...body,turnstileToken:'fresh-token'});assert.equal(again.status,200);assert.equal(writes,1);
    const checked=await worker.fetch(new Request('https://api.example/api/operation?id='+id,{headers}),env);
    assert.equal((await checked.json()).success,true);assert.equal(writes,1);
    const changed=await post({...body,content:'Different content'});assert.equal(changed.status,409);assert.equal((await changed.json()).uncertain,true);assert.equal(writes,1);
    const missing=await post({...base,sourceSha:'a'.repeat(40)});assert.equal(missing.status,400);assert.equal(writes,1);
    const signedOut=await worker.fetch(new Request('https://api.example/api/operation?id='+id),env);assert.equal(signedOut.status,401);
  } finally {globalThis.fetch=original;}
});
