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
    source += '\nexport {submissionStage,aggregateCheckRuns,fetchPrReviewState,buildDashboard,buildDashboardStatus,githubRequest};\n';
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
const apiErrors = await import(await sourceUrl(path.resolve('../shared/api-errors.mjs')));
const apiContract = await import(await sourceUrl(path.resolve('../shared/api-contract.mjs')));
const discussion = path.basename(process.cwd()) === 'discussions-worker';
if (!discussion) await import('./_test_submission_files.mjs');
const prefix = discussion ? '/api/discuss-auth' : '/api/auth';
const origin = 'https://analyticmadhyasthdarshan.org';
const url = suffix => 'https://api.example' + prefix + suffix;

async function assertErrorEnvelope(response, {status, code, privateHeaders = true} = {}) {
  assert.equal(response.status, status);
  assert.match(response.headers.get('Content-Type') || '', /^application\/json\b/i);
  const payload = await response.json();
  assert.equal(payload.success, false);
  assert.equal(payload.code, code);
  assert.equal(typeof payload.message, 'string');
  assert.ok(payload.message.length > 0);
  assert.match(payload.requestId, /^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/);
  assert.equal(response.headers.get('X-Request-ID'), payload.requestId);
  assert.equal('error' in payload, false);
  if (privateHeaders) {
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
    assert.equal(response.headers.get('Pragma'), 'no-cache');
    assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
    assert.equal(response.headers.get('X-Content-Type-Options'), 'nosniff');
    const vary = (response.headers.get('Vary') || '').split(',').map(value => value.trim());
    assert.ok(vary.includes('Origin'));
    assert.ok(vary.includes('Cookie'));
  }
  return payload;
}

async function withDashboardPublicationFetch(publicationResponse, run, repositorySha = 'a'.repeat(40)) {
  const originalFetch = globalThis.fetch;
  const originalCaches = globalThis.caches;
  try {
    globalThis.caches = {default:{
      match:async request => {
        const url=String(request.url || request);
        if (url.includes('/catalog-maps-v2?sha=')) return Response.json({
          statuses:{'Test-Study':'draft'},categories:{'Test-Study':['Human']},
        });
        if (url.includes('/proposal-registry?sha=')) return Response.json({
          version:1,proposals:[{issueNumber:3,slug:'Test-Study',phase:'catalog'}],
        });
        return null;
      },
      put:async () => {},
    }};
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes('/issues?creator=alice')) return Response.json([{
        number:3,state:'closed',title:'Study proposal: Test Study',
        body:'### Slug\n\nTest-Study\n\n### Category\n\nHuman',
        labels:[{name:'study-proposal'},{name:'proposal-approved'}],
        user:{login:'alice'},html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/3',
      }]);
      if (url.includes('/pulls?state=open')) return Response.json([]);
      if (url.includes('/git/refs/heads/master')) return Response.json({object:{sha:repositorySha}});
      if (url.endsWith('/.well-known/publication.json')) return publicationResponse();
      throw new Error('Unexpected full dashboard request: '+url);
    };
    const result = await workerModule.buildDashboard({login:'alice',accessToken:'test'},{});
    await run(result);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalCaches === undefined) delete globalThis.caches;
    else globalThis.caches = originalCaches;
  }
}

test('shared HTTP errors cover every reusable OpenAPI status', async () => {
  const cases = new Map([
    [400, 'invalid_request'], [401, 'authentication_required'], [403, 'forbidden'],
    [409, 'conflict'], [413, 'payload_too_large'], [415, 'unsupported_media_type'],
    [429, 'rate_limited'], [503, 'service_unavailable'],
  ]);
  for (const [status, code] of cases) {
    const response = await apiErrors.normalizeApiErrorResponse(
      new Request('https://api.example/test'),
      Response.json({success:false,error:`Fixture ${status}`,fixtureStatus:status},{status}),
    );
    const payload = await assertErrorEnvelope(response, {status, code, privateHeaders: false});
    assert.equal(payload.details.fixtureStatus, status);
  }
});

test('request IDs are generated at the edge instead of accepting a client value', async () => {
  const response = await apiErrors.normalizeApiErrorResponse(
    new Request('https://api.example/test', {headers:{'X-Request-ID':'client-controlled-id'}}),
    Response.json({success:false,error:'Fixture'},{status:400}),
  );
  assert.notEqual(response.headers.get('X-Request-ID'), 'client-controlled-id');
  assert.equal((await response.json()).requestId, response.headers.get('X-Request-ID'));
});

test('shared request bounds count UTF-8 bytes and pagination rejects coercion', async () => {
  assert.deepEqual(await apiContract.readJsonWithin(new Request('https://api.example/test', {
    method:'POST',body:'{"x":"é"}',headers:{'Content-Type':'application/json'},
  }), 10), {x:'é'});
  await assert.rejects(
    apiContract.readJsonWithin(new Request('https://api.example/test', {
      method:'POST',body:'{"x":"é"}',headers:{'Content-Type':'application/json'},
    }), 9),
    error => error.status === 413,
  );
  assert.deepEqual(apiContract.parsePagination(new URL('https://api.example/test?limit=100&offset=7')), {limit:100,offset:7});
  for (const query of ['limit=0','limit=1.5','limit=101','offset=-1','offset=10001']) {
    assert.throws(() => apiContract.parsePagination(new URL('https://api.example/test?'+query)), error => error.status === 400);
  }
});

test('health reports dependency readiness, request identity, and aggregate metrics', async () => {
  const points = [];
  const metrics = {writeDataPoint: point => points.push(point)};
  const env = discussion ? {
    DB:{}, SESSION_SECRET:'fixture', TURNSTILE_SECRET_KEY:'fixture', RESEND_API_KEY:'fixture',
    API_METRICS:metrics, CF_VERSION_METADATA:{id:'fixture-version'},
  } : {
    GITHUB_TOKEN:'fixture', GITHUB_CLIENT_ID:'fixture', GITHUB_CLIENT_SECRET:'fixture',
    SESSIONS:{}, SESSION_SECRET:'fixture', CONTRIBUTOR_OPERATIONS:{},
    TURNSTILE_SECRET_KEY:'fixture', API_METRICS:metrics,
    CF_VERSION_METADATA:{id:'fixture-version'},
  };
  const endpoint = discussion ? '/api/discussions/health' : '/api/health';
  const response = await worker.fetch(new Request('https://api.example' + endpoint), env);
  assert.equal(response.status, 200);
  assert.match(response.headers.get('X-Request-ID'), /^[0-9a-f-]{36}$/i);
  const payload = await response.json();
  assert.equal(payload.status, 'ok');
  assert.equal(payload.schemaVersion, 1);
  assert.equal(points.length, 1);
  assert.deepEqual(points[0].blobs.slice(0, 5), [
    'v1', discussion ? 'discussions' : 'submissions',
    discussion ? 'getDiscussionsHealth' : 'getHealth', 'GET', '2xx',
  ]);
  const rendered = JSON.stringify(points[0]);
  for (const forbidden of ['Cookie', 'token', 'email', 'draft']) {
    assert.equal(rendered.toLowerCase().includes(forbidden.toLowerCase()), false);
  }
});

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
      if (url.endsWith('/commits/head-sha/status')) return Response.json({statuses:[]});
      throw new Error('Unexpected dashboard status request: '+url);
    };
    const result=await workerModule.buildDashboardStatus({login:'alice',accessToken:'test'},{});
    assert.equal(result.statuses.length,1);
    assert.equal(result.statuses[0].stage,'changes_requested');
    assert.equal(result.statuses[0].checks.state,'success');
    assert.equal(result.meta.githubRequests,4);
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
        if (url.includes('/catalog-maps-v2?sha=')) return Response.json({
          statuses:{'Test-Study':'draft'},categories:{'Test-Study':['Human']},
        });
        if (url.includes('/proposal-registry?sha=')) return Response.json({
          version:1,proposals:[{issueNumber:3,slug:'Test-Study',phase:'catalog'}],
        });
        return null;
      },
      put:async () => {},
    }};
    globalThis.fetch=async (input, init={}) => {
      const url=String(input);calls.push({url, init});
      if (url.includes('/issues?creator=alice')) return Response.json([{
        number:3,state:'closed',title:'Study proposal: Test Study',
        body:'### Slug\n\nTest-Study\n\n### Category\n\nHuman',
        labels:[{name:'study-proposal'},{name:'proposal-approved'}],
        user:{login:'alice'},html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/3',
      }]);
      if (url.includes('/pulls?state=open')) return Response.json([]);
      if (url.includes('/git/refs/heads/master')) return Response.json({object:{sha:'a'.repeat(40)}});
      if (url.endsWith('/.well-known/publication.json')) return Response.json({schema:1,revision:'b'.repeat(64),sourceSha:'a'.repeat(40),studies:{'Test-Study':{status:'draft'}}});
      throw new Error('Unexpected full dashboard request: '+url);
    };
    const result=await workerModule.buildDashboard({login:'alice',accessToken:'test'},{});
    assert.equal(result.submissions.length,1);
    assert.equal(result.submissions[0].stage,'merged');
    assert.equal(result.submissions[0].slug,'Test-Study');
    assert.equal(result.meta.githubRequests,3);
    assert.equal(calls.length,4);
    assert.equal(calls.filter(call=>call.url.includes('/git/refs/heads/')).length,1);
    assert.equal(result.submissions[0].publication.state,'published');
    assert.equal(result.submissions[0].publication.status,'draft');
    assert.equal(result.submissions[0].publication.repositorySha,'a'.repeat(40));
    assert.equal(result.meta.repositorySha,'a'.repeat(40));
    const publicationCall = calls.find(call => call.url.endsWith('/.well-known/publication.json'));
    assert.equal(publicationCall.init.headers['User-Agent'],'AMD-Submission-Portal/1.0');
    assert.equal(calls.some(call => call.url.includes('/search/issues')),false);
  } finally {
    globalThis.fetch=originalFetch;
    if (originalCaches === undefined) delete globalThis.caches;
    else globalThis.caches=originalCaches;
  }
});

if (!discussion) test('dashboard treats a blocked publication endpoint as unknown, never published', async () => {
  await withDashboardPublicationFetch(
    () => new Response('<!DOCTYPE html>challenge', {status: 403, headers: {'Content-Type': 'text/html'}}),
    result => {
      assert.equal(result.submissions[0].publication.state, 'unknown');
      assert.equal(result.submissions[0].publication.status, null);
      assert.equal(result.meta.repositorySha, 'a'.repeat(40));
    },
  );
});

if (!discussion) test('dashboard reports publishing when the public source SHA lags GitHub', async () => {
  await withDashboardPublicationFetch(
    () => Response.json({schema:1,revision:'b'.repeat(64),sourceSha:'c'.repeat(40),studies:{'Test-Study':{status:'draft'}}}),
    result => {
      assert.equal(result.submissions[0].publication.state, 'publishing');
      assert.equal(result.submissions[0].publication.status, 'draft');
      assert.equal(result.submissions[0].publication.sourceSha, 'c'.repeat(40));
      assert.equal(result.submissions[0].publication.repositorySha, 'a'.repeat(40));
    },
  );
});

test('real routes apply write checks and private headers before handlers', async () => {
  for (const headers of [{}, { Origin: 'https://evil.example', 'Content-Type': 'application/json' }]) {
    const response = await worker.fetch(new Request(url('/logout'), { method: 'POST', headers }), {});
    await assertErrorEnvelope(response, {status: 403, code: 'forbidden'});
  }
  const wrongMediaType = await worker.fetch(new Request(url('/logout'), {
    method: 'POST', headers: { Origin: origin },
  }), {});
  await assertErrorEnvelope(wrongMediaType, {status: 415, code: 'unsupported_media_type'});
  const response = await worker.fetch(new Request(url('/logout'), {
    method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json' },
  }), {});
  assert.equal(response.status, 200);
  assert.match(response.headers.get('Set-Cookie'), /Max-Age=0/);
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
  const me = await worker.fetch(new Request(url('/me')), {});
  assert.deepEqual(await me.json(), { loggedIn: false });
  assert.match(me.headers.get('X-Request-ID'), /^[0-9a-f-]{36}$/i);
  assert.equal(me.headers.get('Cache-Control'), 'private, no-store');
  const missing = await worker.fetch(new Request('https://api.example/unknown'), {});
  assert.equal(missing.status, 404);
  assert.equal(missing.headers.get('Cache-Control'), 'private, no-store');

  const protectedUrl = discussion
    ? 'https://api.example/api/discussions/Test-Study/comments'
    : 'https://api.example/api/propose';
  const unauthorized = await worker.fetch(new Request(protectedUrl, {
    method: 'POST',
    headers: { Origin: origin, 'Content-Type': 'application/json' },
    body: '{}',
  }), {});
  assert.equal(unauthorized.headers.get('WWW-Authenticate'), null);
  await assertErrorEnvelope(unauthorized, {status: 401, code: 'authentication_required'});

  if (discussion) {
    const malformed = await worker.fetch(new Request(url('/magic-link'), {
      method: 'POST',
      headers: { Origin: origin, 'Content-Type': 'application/json' },
      body: '{',
    }), { DB: {} });
    await assertErrorEnvelope(malformed, {status: 400, code: 'invalid_request'});

    const unavailable = await worker.fetch(
      new Request('https://api.example/api/discussions/stats'), {},
    );
    await assertErrorEnvelope(unavailable, {status: 503, code: 'service_unavailable'});
  } else {
    const unavailable = await worker.fetch(new Request(url('/github')), {});
    await assertErrorEnvelope(unavailable, {status: 503, code: 'service_unavailable'});
  }
});

if (discussion) test('comment listing includes an email-free viewer summary', async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const env = {
    SESSION_SECRET:'fixture-only',
    ADMIN_EMAILS:'alice@example.test',
    DB:{prepare:() => ({bind:() => ({
      all:async () => ({results:[]}),
      first:async () => ({count:0}),
    })})},
  };
  const signedOut = await worker.fetch(new Request('https://api.example/api/discussions/Test-Study'), env);
  assert.deepEqual(await signedOut.json(), {
    slug:'Test-Study',viewer:{loggedIn:false},comments:[],
    meta:{total:0,limit:50,offset:0,hasMore:false,nextOffset:null},
  });

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

if (discussion) test('comment mutations reject a stale source identifier before writing', async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv = new Map(); let updates = 0;
  const env = {
    SESSION_SECRET:'fixture-only',
    SESSIONS:{put:async (key,value) => kv.set(key,value),get:async key => kv.get(key)},
    DB:{prepare:sql => ({bind:() => ({
      first:async () => sql.includes('FROM comments')
        ? {id:'comment-1',thread_slug:'Test-Study',user_id:'user-1',status:'visible',updated_at:42}
        : null,
      run:async () => {updates++;return {meta:{changes:1}};},
    })})},
  };
  const token = await auth.createSession(env,{userId:'user-1',email:'alice@example.test',displayName:'Alice'});
  const response = await worker.fetch(new Request(
    'https://api.example/api/discussions/Test-Study/comments/comment-1/delete',
    {method:'POST',headers:{Origin:origin,'Content-Type':'application/json',Cookie:auth.setSessionCookie(token,env).split(';')[0]},body:'{"sourceUpdatedAt":41}'},
  ),env);
  const payload = await assertErrorEnvelope(response,{status:409,code:'conflict'});
  assert.deepEqual(payload.details,{currentSource:42,providedSource:41});
  assert.equal(updates,0);
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

if (!discussion) test('notification updates require the current opaque source identifier', async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv = new Map();
  const env = {SESSION_SECRET:'fixture-only',SESSIONS:{
    put:async (key,value) => kv.set(key,value),get:async key => kv.get(key),
  }};
  const token = await auth.createSession(env,{login:'alice',userId:1,accessToken:'test'});
  await env.SESSIONS.put('notify:alice',JSON.stringify({email:'alice@example.test',enabled:true,sourceVersion:'current'}));
  const response = await worker.fetch(new Request('https://api.example/api/me/notifications',{
    method:'POST',headers:{Origin:origin,'Content-Type':'application/json',Cookie:auth.setSessionCookie(token,env).split(';')[0]},
    body:JSON.stringify({enabled:false,sourceVersion:'stale'}),
  }),env);
  const payload = await assertErrorEnvelope(response,{status:409,code:'conflict'});
  assert.equal(payload.details.currentSource,'current');
  assert.equal(JSON.parse(await env.SESSIONS.get('notify:alice')).enabled,true);
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

if (!discussion) test('status changes and deletions require the durable receipt service before handlers run',async () => {
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv = new Map();
  const env = {SESSION_SECRET:'fixture-only',SESSIONS:{
    put:async (key,value) => kv.set(key,value),get:async key => kv.get(key),
  }};
  const token = await auth.createSession(env,{login:'alice',userId:1,accessToken:'fixture-only'});
  const headers={Origin:origin,'Content-Type':'application/json',Cookie:auth.setSessionCookie(token,env).split(';')[0]};
  const cases=[
    ['/api/status-change',{slug:'Test-Study',targetStatus:'released',operationId:crypto.randomUUID()}],
    ['/api/delete-artifact',{slug:'Test-Study',artifactType:'study',operationId:crypto.randomUUID()}],
  ];
  for (const [route,body] of cases) {
    const response=await worker.fetch(new Request('https://api.example'+route,{method:'POST',headers,body:JSON.stringify(body)}),env);
    await assertErrorEnvelope(response,{status:503,code:'service_unavailable'});
  }
});

if (!discussion) test('GitHub writes carry the receipt marker used for operation reconciliation',async () => {
  const original=globalThis.fetch, id=crypto.randomUUID();
  let requestBody;
  try {
    globalThis.fetch=async (_input,options={}) => {
      requestBody=JSON.parse(options.body);
      return Response.json({number:12});
    };
    await workerModule.githubRequest('/pulls','POST',{body:'Pull request body'},
      {GITHUB_TOKEN:'fixture-only',operationId:id});
    assert.equal(requestBody.body,`Pull request body\n\nPortal-Operation: ${id}`);
  } finally {globalThis.fetch=original;}
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
  const pr={state:'open',number:7,node_id:'PR_fixture',draft:false,labels:[{name:'new-study'}],body:'Slug: Test-Study\nPortal-GitHub: @alice',
    head:{ref:'test-branch',sha:'head-sha',repo:{full_name:'raghavamohan/AnalyticMadhyasthDarshan'}},html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/7'};
  let writes=0, latestMessage='';
  const original=globalThis.fetch;
  globalThis.fetch=async (input,options={}) => {
    const url=String(input);
    if (url.includes('/siteverify')) return Response.json({success:true});
    if (url.endsWith('/pulls/7')) return Response.json(pr);
    if (url.endsWith('/graphql')) {assert.match(JSON.parse(options.body).query,/convertPullRequestToDraft/);pr.draft=true;return Response.json({data:{convertPullRequestToDraft:{pullRequest:{id:pr.node_id}}}});}
    if (url.includes('/contents/Studies/Test-Study/Test-Study.md')) {
      if (options.method==='PUT') {assert.equal(pr.draft,true);writes++;latestMessage=JSON.parse(options.body).message;return Response.json({content:{sha:'b'.repeat(40)}});}
      return Response.json({content:btoa('# Test study\n\nSource text'),sha:'a'.repeat(40)});
    }
    if (url.includes('/search/issues')) return Response.json({items:[],total_count:0});
    if (url.includes('/commits?')) return Response.json([{commit:{message:'CI regenerated artifacts'}},{commit:{message:latestMessage}}]);
    throw new Error('Unexpected fixture request: '+url);
  };
  const post = data => worker.fetch(new Request('https://api.example/api/revise',{method:'POST',headers,body:JSON.stringify(data)}),env);
  const base={prNumber:7,author:'Alice',content:'# Test study\n\nA revised study.',turnstileToken:'fixture'};
  try {
    const malformed = await worker.fetch(new Request('https://api.example/api/revise', {
      method:'POST', headers, body:'{',
    }), env);
    await assertErrorEnvelope(malformed, {status:400,code:'invalid_request'});
    const loaded=await worker.fetch(new Request('https://api.example/api/revision-source?pr=7',{headers}),env);
    assert.equal((await loaded.json()).sourceSha,'a'.repeat(40));
    const stale=await post({...base,operationId:crypto.randomUUID(),sourceSha:'b'.repeat(40)});
    const stalePayload=await assertErrorEnvelope(stale,{status:409,code:'conflict'});
    assert.equal(stalePayload.details.currentSource,'a'.repeat(40));assert.equal(writes,0);
    const id=crypto.randomUUID(), body={...base,operationId:id,sourceSha:'a'.repeat(40)};
    const first=await post(body);assert.equal(first.status,200);assert.equal((await first.json()).state,'complete');assert.equal(writes,1);
    const again=await post({...body,turnstileToken:'fresh-token'});assert.equal(again.status,200);assert.equal((await again.json()).state,'complete');assert.equal(writes,1);
    const checked=await worker.fetch(new Request('https://api.example/api/operation?id='+id,{headers}),env);
    const checkedBody=await checked.json();assert.equal(checkedBody.success,true);assert.equal(checkedBody.state,'complete');assert.equal(checkedBody.operationId,id);assert.equal(writes,1);
    const unusedId=crypto.randomUUID();
    const notStarted=await worker.fetch(new Request('https://api.example/api/operation?id='+unusedId,{headers}),env);
    const notStartedBody=await notStarted.json();assert.equal(notStartedBody.state,'notStarted');assert.equal(notStartedBody.operationId,unusedId);assert.equal(notStartedBody.retryAllowed,true);
    const changed=await post({...body,content:'Different content'});const conflict=await assertErrorEnvelope(changed,{status:409,code:'conflict'});assert.equal(conflict.details.uncertain,true);assert.equal(writes,1);
    const missing=await post({...base,sourceSha:'a'.repeat(40)});await assertErrorEnvelope(missing,{status:400,code:'invalid_request'});assert.equal(writes,1);
    const signedOut=await worker.fetch(new Request('https://api.example/api/operation?id='+id),env);await assertErrorEnvelope(signedOut,{status:401,code:'authentication_required'});
  } finally {globalThis.fetch=original;}
});

if (!discussion) test('bulk deletion checks every source before writes and removes only selected ownership', async () => {
  const {storageFixture} = await import('./_test_contributor.mjs');
  const auth = await import(await sourceUrl(path.resolve('src/auth.js')));
  const kv=new Map(), objects=new Map(), writes=[], prefix='Applications/Test-Study/';
  const env={SESSION_SECRET:'fixture',GITHUB_TOKEN:'fixture',TURNSTILE_SECRET_KEY:'fixture',
    SESSIONS:{put:async(k,v)=>kv.set(k,v),get:async k=>kv.get(k)}};
  env.CONTRIBUTOR_OPERATIONS={idFromName:v=>v,get:id=>{
    if (!objects.has(id)) objects.set(id,new workerModule.ContributorOperations({storage:storageFixture()},env));
    return objects.get(id);
  }};
  const token=await auth.createSession(env,{login:'alice',userId:1,accessToken:'fixture'});
  const headers={Origin:origin,'Content-Type':'application/json',Cookie:auth.setSessionCookie(token,env).split(';')[0]};
  const sources=new Map([
    [prefix+'Test-Study.md','# Parent'],[prefix+'Technical-Note-One.md','# Note'],
    [prefix+'Deck.pptx','deck'],[prefix+'Presenters-Companion-Deck.md','# Presenter'],
    ['Scripts/presentation-pipeline.json',JSON.stringify({decks:[{id:'deck',source:prefix+'Deck.pptx'}]})],
    ['Scripts/companion-pipeline.json',JSON.stringify({schema:1,companions:[{deck:'deck',markdown:prefix+'Presenters-Companion-Deck.md'}]})],
  ]);
  const originalFetch=globalThis.fetch, originalCaches=globalThis.caches;
  globalThis.caches={default:{match:async request=>{
    const key=request.url;
    if (key.includes('companion-artifacts')) return Response.json({schemaVersion:1,studies:[{
      slug:'Test-Study',root:'Applications',notes:['Technical-Note-One.md'],presentations:['Deck.pptx'],presenters:['Presenters-Companion-Deck.md'],
    }]});
    if (key.includes('proposal-registry')) return Response.json({version:1,proposals:[{slug:'Test-Study',submitter:'alice'}]});
    return null;
  },put:async()=>{}}};
  globalThis.fetch=async(input,options={})=>{
    const url=new URL(String(input)), method=options.method || 'GET';
    if (url.pathname.includes('/siteverify')) return Response.json({success:true});
    if (url.pathname.endsWith('/git/refs/heads/master')) return Response.json({object:{sha:'b'.repeat(40)}});
    if (url.pathname.includes('/search/issues')) return Response.json({items:[],total_count:0});
    if (url.pathname.includes('/contents/')) {
      const name=decodeURIComponent(url.pathname.split('/contents/')[1]);
      if (method==='PUT') {writes.push({method,name});sources.set(name,Buffer.from(JSON.parse(options.body).content,'base64').toString());return Response.json({});}
      if (method==='DELETE') {writes.push({method,name});sources.delete(name);return Response.json({});}
      return sources.has(name) ? Response.json({sha:'a'.repeat(40),content:Buffer.from(sources.get(name)).toString('base64')}) : Response.json({message:'Not Found'},{status:404});
    }
    if (method==='POST') {
      writes.push({method,name:url.pathname});
      if (url.pathname.endsWith('/pulls')) return Response.json({number:9,html_url:'https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/9'});
      return Response.json({});
    }
    throw new Error('Unexpected deletion fixture request: '+url);
  };
  const post=artifacts=>worker.fetch(new Request('https://api.example/api/delete-artifact',{method:'POST',headers,
    body:JSON.stringify({slug:'Test-Study',artifactType:'companions',artifacts,turnstileToken:'fixture',operationId:crypto.randomUUID()})}),env);
  const note={artifactType:'note',fileName:'Technical-Note-One.md',sourceSha:'a'.repeat(40)};
  const deck={artifactType:'presentation',fileName:'Deck.pptx',sourceSha:'a'.repeat(40)};
  try {
    await assertErrorEnvelope(await post([note,{...deck,sourceSha:'c'.repeat(40)}]),{status:409,code:'conflict'});
    assert.equal(writes.length,0);
    await assertErrorEnvelope(await post([{artifactType:'study',fileName:'Test-Study.md',sourceSha:'a'.repeat(40)}]),{status:400,code:'invalid_request'});
    assert.equal(writes.length,0);
    const response=await post([note,deck]);
    const body=await response.json();
    assert.equal(response.status,200,JSON.stringify(body));
    assert.equal(body.state,'complete');
    assert.equal(sources.get(prefix+'Test-Study.md'),'# Parent');
    assert.deepEqual(JSON.parse(sources.get('Scripts/presentation-pipeline.json')).decks,[]);
    assert.deepEqual(JSON.parse(sources.get('Scripts/companion-pipeline.json')).companions,[]);
    assert.ok(writes.filter(item=>item.method==='DELETE').every(item=>[prefix+'Technical-Note-One.md',prefix+'Deck.pptx'].includes(item.name)));
    // CI's shared deletion finalizer removes the deck's remaining owned chain.
    assert.ok(sources.has(prefix+'Presenters-Companion-Deck.md'));
  } finally {globalThis.fetch=originalFetch;globalThis.caches=originalCaches;}
});
