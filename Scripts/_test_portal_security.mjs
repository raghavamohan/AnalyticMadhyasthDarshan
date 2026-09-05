import assert from 'node:assert/strict';
import { readFile, mkdtemp, writeFile, rm, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import test from 'node:test';
import { privateResponse, rejectUnsafeWrite } from '../infra/shared/http-security.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const moduleUrl = async relative => 'data:text/javascript;base64,' + Buffer.from(
  await readFile(path.join(root, relative), 'utf8'),
).toString('base64');
const auth = await import(await moduleUrl('infra/worker/src/auth.js'));
const db = await import(await moduleUrl('infra/discussions-worker/src/db.js'));
const origin = 'https://analyticmadhyasthdarshan.org';
const env = { SESSION_SECRET: 'test-only-session-secret', GITHUB_CLIENT_ID: 'test-client', GITHUB_CLIENT_SECRET: 'test-only' };
const callback = (state, nonce = state.nonce) => new Request('https://api.example/api/auth/callback?code=example&state=' + nonce, {
  headers: { Cookie: `amd_oauth_state=${state.cookie}` },
});

test('OAuth binds signed state to callback, expires, and uses S256 PKCE', async () => {
  const state = await auth.buildOAuthState(origin + '/Studies/submit.html', env);
  const second = await auth.buildOAuthState(origin, env);
  assert.notEqual(state.nonce, second.nonce);
  const verified = await auth.parseOAuthState(callback(state), env);
  assert.ok(verified);
  assert.equal(await auth.parseOAuthState(callback(state, second.nonce), env), null);
  assert.equal(await auth.parseOAuthState(new Request(callback(state).url), env), null);
  assert.equal(await auth.parseOAuthState(callback({ ...state, cookie: state.cookie + 'x' }), env), null);
  const url = new URL(auth.githubAuthorizeUrl(env, callback(state), state));
  assert.equal(url.searchParams.get('state'), state.nonce);
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.equal(url.searchParams.get('code_challenge'), Buffer.from(await crypto.subtle.digest(
    'SHA-256', new TextEncoder().encode(verified.verifier),
  )).toString('base64url'));
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (target, options) => {
      assert.equal(target, 'https://github.com/login/oauth/access_token');
      assert.equal(JSON.parse(options.body).code_verifier, verified.verifier);
      return Response.json({ access_token: 'test-token' });
    };
    assert.equal(await auth.exchangeGitHubCode('example', env, callback(state), verified.verifier), 'test-token');
  } finally { globalThis.fetch = originalFetch; }
  const originalNow = Date.now;
  try {
    Date.now = () => originalNow() + 601000;
    assert.equal(await auth.parseOAuthState(callback(state), env), null);
  } finally { Date.now = originalNow; }
});

test('GitHub tokens stay server-side and logout invalidates the stored session', async () => {
  const user = { login: 'tester', userId: 1, accessToken: 'never-in-the-cookie' };
  await assert.rejects(auth.createSession(env, user), /storage/);
  const data = new Map();
  const configured = { ...env, SESSIONS: {
    put: async (key, value) => data.set(key, value),
    get: async key => data.get(key), delete: async key => data.delete(key),
  } };
  const token = await auth.createSession(configured, user);
  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
  assert.deepEqual(Object.keys(payload).sort(), ['exp', 'sid']);
  const request = new Request(origin, { headers: { Cookie: `amd_session=${token}` } });
  assert.equal((await auth.getSession(request, configured)).accessToken, user.accessToken);
  assert.equal(await auth.getSession(request, env), null);
  await auth.destroySession(request, configured);
  assert.equal(await auth.getSession(request, configured), null);
  // A signed OAuth cookie cannot be used as a session either.
  const state = await auth.buildOAuthState(origin, env);
  assert.equal(await auth.getSession(new Request(origin, { headers: { Cookie: `amd_session=${state.cookie}` } }), configured), null);
});

test('write boundary rejects hostile/missing origins and simple form types', () => {
  const request = headers => new Request(origin + '/api/auth/logout', { method: 'POST', headers });
  assert.equal(rejectUnsafeWrite(request({ Origin: origin, 'Content-Type': 'application/json; charset=utf-8' }), [origin]), null);
  for (const Origin of ['https://evil.example', 'null', origin + '.evil.example']) {
    assert.equal(rejectUnsafeWrite(request({ Origin, 'Content-Type': 'application/json' }), [origin]).status, 403);
  }
  assert.equal(rejectUnsafeWrite(request({ 'Content-Type': 'application/json' }), [origin]).status, 403);
  for (const type of ['text/plain', 'application/x-www-form-urlencoded', 'multipart/form-data']) {
    assert.equal(rejectUnsafeWrite(request({ Origin: origin, 'Content-Type': type }), [origin]).status, 415);
  }
  const notification = headers => new Request(origin + '/api/notify', { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers } });
  assert.equal(rejectUnsafeWrite(notification({}), [origin], { machinePath: '/api/notify' }), null);
  assert.equal(rejectUnsafeWrite(notification({ Cookie: 'amd_session=test' }), [origin], { machinePath: '/api/notify' }).status, 403);
});

test('private responses retain redirects and both cookies while preventing caching', () => {
  const headers = new Headers({ Location: origin });
  headers.append('Set-Cookie', 'session=a; HttpOnly');
  headers.append('Set-Cookie', 'oauth=; Max-Age=0');
  const result = privateResponse(new Response(null, { status: 302, headers }));
  assert.equal(result.status, 302);
  assert.equal(result.headers.get('Location'), origin);
  assert.equal(result.headers.getSetCookie().length, 2);
  assert.equal(result.headers.get('Cache-Control'), 'private, no-store');
  assert.match(result.headers.get('Vary'), /Cookie/);
  assert.match(result.headers.get('Vary'), /Origin/);
  assert.equal(result.headers.get('Referrer-Policy'), 'no-referrer');
});

test('magic-link storage and consumption use only the token digest', async () => {
  const token = 'test-secret';
  const digest = await db.hashMagicToken(token);
  assert.equal(digest.length, 64);
  let stored;
  const fake = { prepare: sql => ({ bind: (...args) => ({
    run: async () => { stored = args; },
    first: async () => { assert.match(sql, /UPDATE magic_tokens/); assert.equal(args[1], digest); return null; },
  }) }) };
  await db.storeMagicToken(fake, { token, email: 'USER@example.org', displayName: 'Test', expiresAt: 123 });
  assert.equal(stored[0], digest);
  assert.ok(!stored.includes(token));
  assert.equal(await db.consumeMagicToken(fake, token), null);
});

test('catalog dates sort correctly across AM/PM, month boundaries and invalid dates', async () => {
  const html = await readFile(path.join(root, 'Studies/index.html'), 'utf8');
  const source = html.match(/const catalogTimestamp = updated => \{[\s\S]*?\n  \};/)[0];
  const parse = new Function(source + '; return catalogTimestamp;')();
  assert.equal(parse('Sep 5, 2026, 9:44 AM IST'), Date.parse('2026-09-05T04:14:00Z'));
  assert.equal(parse('Sep 5, 2026, 12:00 AM IST'), Date.parse('2026-09-04T18:30:00Z'));
  assert.equal(parse('Sep 5, 2026, 12:00 PM IST'), Date.parse('2026-09-05T06:30:00Z'));
  assert.ok(parse('Sep 1, 2026, 1:00 AM IST') > parse('Aug 31, 2026, 11:59 PM IST'));
  for (const invalid of ['', 'bad', 'Feb 30, 2026, 9:00 AM IST', 'Sep 5, 2026, 13:00 AM IST']) assert.ok(Number.isNaN(parse(invalid)));
});

test('PDF resources exclude network, sibling files and scripts', async () => {
  const { allowedPdfResource } = createRequire(import.meta.url)('./_pdf_resource_policy.cjs');
  const dir = await mkdtemp(path.join(tmpdir(), 'amd-resource-test-'));
  try {
    await mkdir(path.join(dir, 'study'));
    await mkdir(path.join(dir, 'fonts'));
    for (const file of ['study/index.html', 'study/figure.svg', 'study/active.js', 'secret.txt', 'fonts/math.woff2']) await writeFile(path.join(dir, file), 'test');
    const input = path.join(dir, 'study/index.html');
    const fontDir = path.join(dir, 'fonts');
    const allowed = (relative, type) => allowedPdfResource(pathToFileURL(path.join(dir, relative)).href, type, input, fontDir);
    assert.ok(allowed('study/index.html', 'document'));
    assert.ok(allowed('study/figure.svg', 'image'));
    assert.ok(allowed('fonts/math.woff2', 'font'));
    assert.ok(!allowed('secret.txt', 'image'));
    assert.ok(!allowed('study/active.js', 'script'));
    assert.ok(!allowed('study/figure.svg', 'document'));
    assert.ok(!allowedPdfResource('https://evil.example', 'image', input, fontDir));
  } finally { await rm(dir, { recursive: true, force: true }); }
});
