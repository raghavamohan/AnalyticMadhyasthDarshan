import assert from "node:assert/strict";
import worker, {
  objectKey,
  rangeHeaders,
} from "../infra/generated-pdf-worker/src/index.js";

const KEY = "Studies/Nature-Of-Time/Nature-Of-Time.pdf";
const BYTES = new TextEncoder().encode("%PDF-generated-pdf-worker-test");

function r2Object({ body = BYTES, range = undefined } = {}) {
  const object = {
    size: BYTES.length,
    httpEtag: '"test-etag"',
    customMetadata: { sha256: "test-sha256" },
    uploaded: new Date("2026-09-03T00:00:00Z"),
    range,
    writeHttpMetadata(headers) {
      headers.set("Content-Type", "application/pdf");
      headers.set("Content-Disposition", 'inline; filename="Nature-Of-Time.pdf"');
      headers.set("Cache-Control", "public, max-age=300, s-maxage=3600");
    },
  };
  if (body !== null) object.body = body;
  return object;
}

function environment({ missing = false } = {}) {
  const calls = [];
  return {
    calls,
    env: {
      GENERATED_PDFS: {
        async head(key) {
          calls.push(["head", key]);
          return missing ? null : r2Object({ body: null });
        },
        async get(key, options) {
          calls.push(["get", key, options]);
          if (missing) return null;
          const range = options.range.get("Range");
          if (range === "bytes=0-3") {
            return r2Object({ body: BYTES.slice(0, 4), range: { offset: 0, length: 4 } });
          }
          if (range === "bytes=999-") throw new Error("InvalidRange");
          if (options.onlyIf.get("If-None-Match") === '"test-etag"') {
            return r2Object({ body: null });
          }
          return r2Object();
        },
      },
    },
  };
}

async function bodyBytes(response) {
  return new Uint8Array(await response.arrayBuffer());
}

assert.equal(objectKey("/Studies/Nature-Of-Time/Nature-Of-Time.pdf"), KEY);
assert.equal(objectKey("/References/source.pdf"), null);
assert.equal(objectKey("/%GG.pdf"), null);

const syntheticHeaders = new Headers();
assert.equal(rangeHeaders(syntheticHeaders, r2Object()), 200);
assert.equal(syntheticHeaders.get("Content-Length"), String(BYTES.length));

let originCalls = 0;
globalThis.fetch = async () => {
  originCalls += 1;
  return new Response("origin", { status: 200, headers: { "X-Origin": "github-pages" } });
};

{
  const { env, calls } = environment();
  const response = await worker.fetch(new Request("https://example.test/Studies/index.html"), env);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("X-Origin"), "github-pages");
  assert.equal(originCalls, 1);
  assert.deepEqual(calls, []);
}

{
  const { env } = environment();
  const response = await worker.fetch(
    new Request("https://amd-generated-pdfs.example.workers.dev/Studies/index.html"), env,
  );
  assert.equal(response.status, 404);
  assert.equal(originCalls, 1);
}

{
  const { env, calls } = environment();
  const response = await worker.fetch(
    new Request("https://example.test/Studies/Unknown/Unknown.pdf"), env,
  );
  assert.equal(response.status, 404);
  assert.equal(await response.text(), "Generated PDF not published");
  assert.deepEqual(calls, []);
}

{
  const { env, calls } = environment();
  const response = await worker.fetch(new Request(`https://example.test/${KEY}`), env);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Content-Type"), "application/pdf");
  assert.equal(response.headers.get("ETag"), '"test-etag"');
  assert.equal(response.headers.get("Accept-Ranges"), "bytes");
  assert.equal(response.headers.get("X-AMD-PDF-Origin"), "r2");
  assert.equal(response.headers.get("X-AMD-PDF-SHA256"), "test-sha256");
  assert.deepEqual(await bodyBytes(response), BYTES);
  assert.equal(calls[0][0], "get");
}

{
  const { env, calls } = environment();
  const response = await worker.fetch(
    new Request(`https://example.test/${KEY}`, { method: "HEAD" }), env,
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Content-Length"), String(BYTES.length));
  assert.equal((await response.arrayBuffer()).byteLength, 0);
  assert.equal(calls[0][0], "head");
}

{
  const { env } = environment();
  const response = await worker.fetch(
    new Request(`https://example.test/${KEY}`, { headers: { Range: "bytes=0-3" } }), env,
  );
  assert.equal(response.status, 206);
  assert.equal(response.headers.get("Content-Range"), `bytes 0-3/${BYTES.length}`);
  assert.equal(response.headers.get("Content-Length"), "4");
  assert.deepEqual(await bodyBytes(response), BYTES.slice(0, 4));
}

{
  const { env } = environment();
  const response = await worker.fetch(
    new Request(`https://example.test/${KEY}`, { headers: { Range: "bytes=999-" } }), env,
  );
  assert.equal(response.status, 416);
  assert.equal(response.headers.get("Content-Range"), `bytes */${BYTES.length}`);
}

{
  const { env } = environment();
  const response = await worker.fetch(
    new Request(`https://example.test/${KEY}`, { headers: { "If-None-Match": '"test-etag"' } }), env,
  );
  assert.equal(response.status, 304);
}

{
  const { env } = environment({ missing: true });
  const response = await worker.fetch(new Request(`https://example.test/${KEY}`), env);
  assert.equal(response.status, 404);
}

{
  const { env } = environment();
  const response = await worker.fetch(
    new Request(`https://example.test/${KEY}`, { method: "POST" }), env,
  );
  assert.equal(response.status, 405);
  assert.equal(response.headers.get("Allow"), "GET, HEAD, OPTIONS");
}

console.log("generated PDF Worker tests passed");
