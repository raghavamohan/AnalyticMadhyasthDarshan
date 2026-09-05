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
  for (const match of [...source.matchAll(/from ['"]([^'"]+)['"]/g)]) {
    const target = match[1];
    const url = target.startsWith('.')
      ? await sourceUrl(path.resolve(path.dirname(file), target))
      : pathToFileURL(createRequire(pathToFileURL(file)).resolve(target)).href;
    source = source.replace(match[0], `from '${url}'`);
  }
  return 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
}
const worker = (await import(await sourceUrl(path.resolve('src/index.js')))).default;
const discussion = path.basename(process.cwd()) === 'discussions-worker';
const prefix = discussion ? '/api/discuss-auth' : '/api/auth';
const origin = 'https://analyticmadhyasthdarshan.org';
const url = suffix => 'https://api.example' + prefix + suffix;

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
