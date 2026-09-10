import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('Scripts/_release_assets.py', 'utf8');
const script = source.match(/CLIENT = r'''<script>([\s\S]*?)<\/script>'''/)[1];
const old = 'a'.repeat(64), live = 'b'.repeat(64), asset = 'c'.repeat(64);
const origin = 'https://analyticmadhyasthdarshan.org';
const handlers = {}, calls = [];
let mutation;
function anchor(href, isLive = false) {
  return {nodeType: 1, href: origin + href, hasAttribute: () => isLive,
    getAttribute() { return this.href; }, matches: () => true, querySelectorAll: () => []};
}
const study = anchor('/Studies/A/A.html?find=example#section');
const dashboard = anchor(`/Studies/A/A.html?r=${live}`, true);
const context = {
  URL, Request, location: {href: `${origin}/Studies/submit.html?r=${old}`, origin},
  window: {fetch: async (...args) => { calls.push(args); return {}; }},
  document: {addEventListener: (name, fn) => handlers[name] = fn, body: {},
    documentElement: {nodeType: 1, matches: () => false, querySelectorAll: () => [study, dashboard]}},
  MutationObserver: class { constructor(fn) { mutation = fn; } observe() {} },
};
vm.runInNewContext(script, context);
handlers.DOMContentLoaded();
assert.equal(new URL(study.href).searchParams.get('r'), old);
assert.equal(new URL(study.href).searchParams.get('find'), 'example');
assert.equal(new URL(study.href).hash, '#section');
assert.equal(new URL(dashboard.href).searchParams.get('r'), live);
for (const event of ['pointerdown', 'click', 'auxclick', 'contextmenu']) {
  handlers[event]({target: {closest: () => dashboard}});
  assert.equal(new URL(dashboard.href).searchParams.get('r'), live);
}
const dynamic = anchor('/Studies/B/B.pdf');
mutation([{type: 'childList', addedNodes: [dynamic]}]);
assert.equal(new URL(dynamic.href).searchParams.get('r'), old);
await context.window.fetch('/Studies/catalog-all.json');
await context.window.fetch(`/Assets/reader/reader.js?v=${asset}`);
await context.window.fetch('/api/studies');
assert.equal(new URL(calls[0][0]).searchParams.get('r'), old);
assert.equal(new URL(calls[1][0]).searchParams.get('r'), null);
assert.equal(calls[2][0], '/api/studies');

const policyScope = {self: {}, URL};
vm.runInNewContext(fs.readFileSync('Assets/reader/offline-policy.js', 'utf8'), policyScope);
const policy = policyScope.self.AMDOfflinePolicy;
const bundle = {path: '/Studies/A/A.html', title: 'A', version: old, resources: [
  {url: `/Studies/A/A.html?r=${old}`, sha256: live, bytes: 10},
  {url: `/Studies/notebook.html?r=${old}`, sha256: live, bytes: 10},
  {url: `/Assets/reader/reader.js?v=${asset}`, sha256: asset, bytes: 10},
]};
assert.equal(policy.bundle(bundle, origin), bundle);
const mixed = structuredClone(bundle);
mixed.resources[1].url = `/Studies/notebook.html?r=${live}`;
assert.throws(() => policy.bundle(mixed, origin), /Mixed offline/);
const corrupt = structuredClone(bundle);
corrupt.resources[2].sha256 = live;
assert.throws(() => policy.bundle(corrupt, origin), /Mixed offline/);
console.log('Release navigation preserves snapshot, live-link, asset and offline identities.');
