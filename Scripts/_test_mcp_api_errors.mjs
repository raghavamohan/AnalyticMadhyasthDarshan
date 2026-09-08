// Contract tests for the generated MCP/Studies Worker. Generate its ignored
// bundle first with Scripts/_publish_mcp_server_card.py --generate-only.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const bundlePath = path.resolve('infra/mcp-worker/src/index.js');
const source = await readFile(bundlePath, 'utf8');

async function loadWorker(tag) {
  const taggedSource = `${source}\n// test instance: ${tag}\n`;
  const url = 'data:text/javascript;base64,' + Buffer.from(taggedSource).toString('base64');
  return (await import(url)).default;
}

async function loadWorkerModule(tag) {
  const taggedSource = `${source}\n// test module: ${tag}\n`;
  const url = 'data:text/javascript;base64,' + Buffer.from(taggedSource).toString('base64');
  return import(url);
}

async function assertHttpError(response, status, code) {
  assert.equal(response.status, status);
  assert.match(response.headers.get('Content-Type') || '', /^application\/json\b/i);
  assert.equal(response.headers.get('Cache-Control'), 'no-store');
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), '*');
  assert.match(response.headers.get('Access-Control-Expose-Headers') || '', /x-request-id/i);
  const payload = await response.json();
  assert.deepEqual(Object.keys(payload).sort(), ['code', 'message', 'requestId', 'success']);
  assert.equal(payload.success, false);
  assert.equal(payload.code, code);
  assert.equal(typeof payload.message, 'string');
  assert.ok(payload.message.length > 0);
  assert.match(payload.requestId, /^[0-9a-f-]{36}$/i);
  assert.equal(response.headers.get('X-Request-ID'), payload.requestId);
}

test('Studies API 404 uses the common HTTP error envelope', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => Response.json([]);
    const worker = await loadWorker('not-found');
    const response = await worker.fetch(
      new Request('https://analyticmadhyasthdarshan.org/api/studies/Unknown-Study'),
    );
    await assertHttpError(response, 404, 'not_found');
  } finally {
    globalThis.fetch = original;
  }
});

test('Studies OpenAPI operations exactly match the runtime route table', async () => {
  const workerModule = await loadWorkerModule('route-parity');
  const spec = JSON.parse(await readFile(path.resolve('openapi/studies.json'), 'utf8'));
  const documented = Object.entries(spec.paths)
    .filter(([route]) => route.startsWith('/api/'))
    .flatMap(([route, item]) => Object.keys(item)
      .filter(method => ['get', 'post', 'put', 'patch', 'delete'].includes(method))
      .map(method => [method, route]))
    .sort();
  const implemented = [...workerModule.STUDIES_API_OPERATIONS]
    .map(value => [...value])
    .sort();
  assert.deepEqual(implemented, documented);
});

test('Studies API 502 uses the common HTTP error envelope', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new Error('fixture upstream failure'); };
    const worker = await loadWorker('upstream-error');
    const response = await worker.fetch(
      new Request('https://analyticmadhyasthdarshan.org/api/studies'),
    );
    await assertHttpError(response, 502, 'upstream_error');
  } finally {
    globalThis.fetch = original;
  }
});

test('Studies API pagination is bounded and advertises the edge quota', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => Response.json([
      {slug:'One',title:'One',status:'draft',collection:'topical'},
      {slug:'Two',title:'Two',status:'draft',collection:'topical'},
      {slug:'Three',title:'Three',status:'released',collection:'formal'},
    ]);
    const worker = await loadWorker('pagination');
    const response = await worker.fetch(new Request(
      'https://analyticmadhyasthdarshan.org/api/studies?limit=1&offset=1',
    ));
    assert.equal(response.status,200);
    assert.match(response.headers.get('RateLimit-Policy'),/edge-ip/);
    const payload = await response.json();
    assert.equal(payload.count,1);
    assert.equal(payload.total,3);
    assert.equal(payload.hasMore,true);
    assert.equal(payload.nextOffset,2);
    assert.equal(payload.studies[0].slug,'Two');
    const invalid = await worker.fetch(new Request(
      'https://analyticmadhyasthdarshan.org/api/studies?limit=0',
    ));
    await assertHttpError(invalid,400,'invalid_request');
    const oversizedSlug = await worker.fetch(new Request(
      'https://analyticmadhyasthdarshan.org/api/cite/' + 'A'.repeat(61),
    ));
    await assertHttpError(oversizedSlug,400,'invalid_request');
  } finally {
    globalThis.fetch = original;
  }
});

test('MCP JSON-RPC errors retain the protocol envelope and expose requestId', async () => {
  const worker = await loadWorker('json-rpc-error');
  const response = await worker.fetch(new Request(
    'https://analyticmadhyasthdarshan.org/mcp',
    {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{'},
  ));
  assert.equal(response.status, 400);
  assert.equal(response.headers.get('Cache-Control'), 'no-store');
  const payload = await response.json();
  assert.equal(payload.jsonrpc, '2.0');
  assert.equal(payload.error.code, -32700);
  assert.equal(payload.error.data.requestId, response.headers.get('X-Request-ID'));
  assert.match(payload.error.data.requestId, /^[0-9a-f-]{36}$/i);
});

test('MCP accepts the exact body boundary and rejects one byte over it', async () => {
  const worker = await loadWorker('body-boundary');
  const message = {jsonrpc:'2.0',id:1,method:'ping',padding:''};
  let raw = JSON.stringify(message);
  message.padding = 'x'.repeat(65536 - raw.length);
  raw = JSON.stringify(message);
  assert.equal(Buffer.byteLength(raw),65536);
  const exact = await worker.fetch(new Request('https://analyticmadhyasthdarshan.org/mcp',{
    method:'POST',headers:{'Content-Type':'application/json'},body:raw,
  }));
  assert.equal(exact.status,200);
  const oversized = await worker.fetch(new Request('https://analyticmadhyasthdarshan.org/mcp',{
    method:'POST',headers:{'Content-Type':'application/json','Content-Length':'65537'},body:'{}',
  }));
  assert.equal(oversized.status,413);
  assert.equal((await oversized.json()).error.code,-32600);
});
